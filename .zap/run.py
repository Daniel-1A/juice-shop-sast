"""Run packaged ZAP scans; publish only validated, sanitized reports."""
import argparse
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import quote, urlsplit


TARGET = 'http://juice-shop:3000'


def sanitize(text, secrets):
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            for value in (secret, html.escape(secret), quote(secret, safe=''), json.dumps(secret)[1:-1]):
                text = text.replace(value, '[REDACTED]')
    return re.sub(r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b', '[REDACTED]', text)


def same_origin(url, target=TARGET):
    parsed, allowed = urlsplit(url), urlsplit(target)
    return (parsed.scheme, parsed.netloc) == (allowed.scheme, allowed.netloc)


def validate_report(report, coverage, mode, rules):
    if not isinstance(coverage, dict) or coverage.get('target') != TARGET:
        raise ValueError('Missing or unexpected scan target')
    urls = coverage.get('urls')
    if not isinstance(urls, list) or not urls or not all(isinstance(url, str) and same_origin(url) for url in urls):
        raise ValueError('Missing coverage or URLs outside the owned target')
    if not isinstance(coverage.get('successfulResponses'), int) or coverage['successfulResponses'] < 1:
        raise ValueError('No successful response from the owned target')
    if mode != 'baseline' and coverage.get('authenticated') is not True:
        raise ValueError('Authenticated traversal was not demonstrated inside ZAP')
    sites = report.get('site') if isinstance(report, dict) else None
    if not isinstance(sites, list) or not sites:
        raise ValueError('Missing ZAP sites')
    alerts = []
    for site in sites:
        if not same_origin(site.get('@name', '')) or not isinstance(site.get('alerts'), list):
            raise ValueError('Invalid ZAP site or missing alerts')
        for alert in site['alerts']:
            rule = int(alert['pluginid'])
            instances = alert.get('instances', [])
            if not isinstance(instances, list) or not all(same_origin(item.get('uri', '')) for item in instances):
                raise ValueError('Alert instance outside the owned target')
            alerts.append(rule)
    return {'mode': mode, 'urls': len(set(urls)), 'alerts': len(alerts),
            'blocking': sorted(set(alerts).intersection(rules)) if mode in ('baseline', 'authenticated') else []}


def verify_auth(messages, target, email, user_id, basket_id, token):
    identity = basket = rejected = False
    for message in messages:
        request = message.get('requestHeader', '')
        first = request.splitlines()[0].split() if request else []
        if len(first) < 2:
            continue
        url = first[1] if first[1].startswith('http') else target + first[1]
        if not same_origin(url, target):
            continue
        path = urlsplit(url).path
        response = message.get('responseHeader', '').split()
        if len(response) < 2:
            continue
        status = response[1]
        try:
            body = json.loads(message.get('responseBody', '{}'))
        except ValueError:
            body = {}
        if path == '/rest/user/whoami' and status == '200' and f'token={token}' in request:
            identity |= body.get('user', {}).get('email') == email and body.get('user', {}).get('id') == user_id
        if path == f'/rest/basket/{basket_id}':
            if status == '200' and f'Bearer {token}' in request:
                basket |= body.get('data', {}).get('id') == basket_id and body.get('data', {}).get('UserId') == user_id
            if status == '401' and 'Bearer invalid-token' in request:
                rejected = True
    if not (identity and basket and rejected):
        raise ValueError('ZAP history did not prove identity, owned basket and invalid-token rejection')
    return True


def load_rules(path):
    rules = set()
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            fields = line.split('\t')
            if len(fields) < 2 or fields[1] not in ('FAIL', 'WARN'):
                raise ValueError('Rules must explicitly use FAIL or WARN')
            if fields[1] == 'FAIL':
                rules.add(int(fields[0]))
    if not rules:
        raise ValueError('No blocking rules configured')
    return rules


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['baseline', 'authenticated', 'full', 'api'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = Path(__file__).resolve().parent
    public = args.output.resolve()
    public.mkdir(parents=True, exist_ok=True)
    for name in ('report.json', 'report.html', 'scan.log', 'coverage.json', 'summary.json'):
        (public / name).unlink(missing_ok=True)
    rules = load_rules(config / 'rules.tsv')
    summary = {'mode': args.mode, 'passed': False}
    exit_code = 1
    with tempfile.TemporaryDirectory(prefix='juice-dast-') as temp:
        private = Path(temp)
        env = dict(os.environ, DAST_PRIVATE=str(private), DAST_MODE=args.mode, DAST_CONFIG=str(config),
                   PYTHONDONTWRITEBYTECODE='1')
        script = {'full': 'zap-full-scan.py', 'api': 'zap-api-scan.py'}.get(args.mode, 'zap-baseline.py')
        command = [sys.executable, '/zap/' + script, '-t', TARGET, '-I', '-T', '5',
                   '-r', str(private / 'report.html'), '-J', str(private / 'report.json'),
                   '--hook', str(config / 'hooks.py'), '-z',
                   '-config spider.maxDepth=3 -config spider.maxChildren=20 '
                   '-config autoupdate.checkOnStart=false']
        if args.mode in ('baseline', 'authenticated'):
            command += ['-c', str(config / 'rules.tsv'), '-m', '1', '--autooff']
        elif args.mode == 'full':
            command += ['-m', '1']
        else:
            import yaml
            schema = yaml.safe_load((config.parent / 'swagger.yml').read_text())
            schema['servers'] = [{'url': TARGET + '/b2b/v2'}]
            schema_file = private / 'swagger.yaml'
            schema_file.write_text(yaml.safe_dump(schema))
            command[command.index('-t') + 1] = str(schema_file)
            command += ['-f', 'openapi']
        try:
            with (private / 'scan.log').open('w') as log:
                result = subprocess.run(command, cwd='/zap/wrk', env=env, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=900)
            summary['scannerExit'] = result.returncode
            report = json.loads((private / 'report.json').read_text())
            coverage = json.loads((private / 'coverage.json').read_text())
            summary.update(validate_report(report, coverage, args.mode, rules))
            if result.returncode != 0 or summary['blocking']:
                raise ValueError(f'Scanner exit {result.returncode}; blocking rules {summary["blocking"]}')
            if not (private / 'report.html').is_file():
                raise ValueError('Missing HTML report')
            summary['passed'] = True
            exit_code = 0
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
            summary['error'] = str(error)
        finally:
            secrets_path = private / 'secrets.json'
            secrets = json.loads(secrets_path.read_text()) if secrets_path.exists() else []
            for name in ('report.json', 'report.html', 'scan.log', 'coverage.json'):
                path = private / name
                if path.is_file():
                    cleaned = sanitize(path.read_text(errors='replace'), secrets)
                    if any(secret and secret in cleaned for secret in secrets):
                        raise ValueError('Unredacted ephemeral secret in output')
                    (public / name).write_text(cleaned)
            clean_summary = sanitize(json.dumps(summary, indent=2), secrets)
            (public / 'summary.json').write_text(clean_summary)
            print(clean_summary)
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
