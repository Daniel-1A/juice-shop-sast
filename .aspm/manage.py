"""Local-only ASPM bootstrap and evidence publication; no third-party packages."""
import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import date

from reports import grype_inventory, load_report, validate_import, zap_xml


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, base, headers=None):
        parsed = urllib.parse.urlsplit(base)
        if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.username or parsed.password:
            raise ValueError('Only the loopback service is allowed')
        self.base = base.rstrip('/')
        self.headers = dict(headers or {})
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def call(self, path, data=None, method=None, content_type='application/json'):
        if not path.startswith('/') or path.startswith('//') or '\\' in path:
            raise ValueError('API path must be local')
        headers = {**self.headers, 'Content-Type': content_type}
        payload = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
        request = urllib.request.Request(self.base + path, data=payload, method=method or ('GET' if data is None else 'POST'), headers=headers)
        try:
            with self.opener.open(request, timeout=60) as response:
                raw = response.read(30 * 1024 * 1024 + 1)
                if len(raw) > 30 * 1024 * 1024:
                    raise RuntimeError('API response exceeds limit')
                text = raw.decode()
                try:
                    result = json.loads(text) if text else None
                except json.JSONDecodeError:
                    result = text
                return result, response.headers
        except urllib.error.HTTPError as error:
            raise RuntimeError(f'Local API returned HTTP {error.code}') from None
        except (urllib.error.URLError, OSError):
            raise RuntimeError('Local API unavailable') from None


def public_receipt(values):
    allowed = {'sourceSHA', 'sourceRun', 'tool', 'sourceSHA256', 'sourceResults', 'findings', 'test', 'projectUuid', 'componentCount', 'policyUuid', 'processingComplete', 'reimported', 'verified', 'severity', 'scanWarnings'}
    return {key: value for key, value in values.items() if key in allowed}


def save_private(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    path.chmod(0o600)


def initialize(directory):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = directory / 'private.env'
    if target.exists():
        return
    values = {key: secrets.token_urlsafe(32) for key in ('DTRACK_DB_PASSWORD', 'DTRACK_ADMIN_PASSWORD', 'DOJO_DB_PASSWORD', 'DOJO_ADMIN_PASSWORD', 'DOJO_SECRET_KEY')}
    values['DOJO_AES_KEY'] = secrets.token_urlsafe(24)
    with target.open('x') as stream:
        stream.write(''.join(f'{key}={value}\n' for key, value in values.items()))
    target.chmod(0o600)


def read_env(directory):
    return dict(line.split('=', 1) for line in (directory / 'private.env').read_text().splitlines() if '=' in line and not line.startswith('#'))


def wait_ready(operation, attempts=180):
    for _ in range(attempts):
        try:
            return operation()
        except RuntimeError:
            time.sleep(2)
    raise RuntimeError('Local service readiness timed out')


def publish_bom(api, document, sha):
    if not document.get('components'):
        raise ValueError('SBOM has no components')
    token, _ = api.call('/api/v1/bom', {'projectName': 'juice-shop-sast', 'projectVersion': sha, 'autoCreate': True, 'bom': base64.b64encode(json.dumps(document).encode()).decode()}, method='PUT')
    for _ in range(180):
        status, _ = api.call('/api/v1/bom/token/' + urllib.parse.quote(token['token'], safe=''))
        if status.get('processing') is False:
            break
        time.sleep(2)
    else:
        raise RuntimeError('SBOM processing timed out')
    query = urllib.parse.urlencode({'name': 'juice-shop-sast', 'version': sha})
    project, _ = api.call('/api/v1/project/lookup?' + query)
    components, headers = api.call('/api/v1/component/project/' + project['uuid'] + '?pageSize=1&pageNumber=1')
    count = int(headers['X-Total-Count'])
    if count <= 0 or not components:
        raise ValueError('SBOM processing produced an empty inventory')
    return {'projectUuid': project['uuid'], 'componentCount': count, 'processingComplete': True}


def dtrack_credentials(directory):
    cache = directory / 'private-dtrack.json'
    if cache.exists():
        return json.loads(cache.read_text())
    env = read_env(directory)
    api = Client('http://127.0.0.1:18080')
    wait_ready(lambda: api.call('/health'))
    password = env['DTRACK_ADMIN_PASSWORD']
    form = lambda values: urllib.parse.urlencode(values).encode()
    try:
        token, _ = api.call('/api/v1/user/login', form({'username': 'admin', 'password': password}), content_type='application/x-www-form-urlencoded')
    except RuntimeError:
        api.call('/api/v1/user/forceChangePassword', form({'username': 'admin', 'password': 'admin', 'newPassword': password, 'confirmPassword': password}), content_type='application/x-www-form-urlencoded')
        token, _ = api.call('/api/v1/user/login', form({'username': 'admin', 'password': password}), content_type='application/x-www-form-urlencoded')
    admin = Client('http://127.0.0.1:18080', {'Authorization': 'Bearer ' + token})
    teams, _ = admin.call('/api/v1/team')
    team = next((item for item in teams if item['name'] == 'Juice Shop CI Publisher'), None)
    if team is None:
        team, _ = admin.call('/api/v1/team', {'name': 'Juice Shop CI Publisher'}, method='PUT')
    admin.call('/api/v1/permission/team', {'team': team['uuid'], 'permissions': ['BOM_UPLOAD', 'VIEW_PORTFOLIO', 'PROJECT_CREATION_UPLOAD', 'VIEW_POLICY_VIOLATION']}, method='PUT')
    policies, _ = admin.call('/api/v1/policy')
    policy = next((item for item in policies if item['name'] == 'Juice Shop - Critical vulnerabilities'), None)
    if policy is None:
        policy, _ = admin.call('/api/v1/policy', {'name': 'Juice Shop - Critical vulnerabilities', 'operator': 'ANY', 'violationState': 'WARN', 'global': True}, method='PUT')
        admin.call('/api/v1/policy/' + policy['uuid'] + '/condition', {'subject': 'SEVERITY', 'operator': 'IS', 'value': 'CRITICAL'}, method='PUT')
    key, _ = admin.call('/api/v1/team/' + team['uuid'] + '/key', method='PUT')
    credential = {'apiKey': key['key'], 'policyUuid': policy['uuid']}
    save_private(cache, credential)
    return credential


def prepare_report(tool, document):
    payload = json.dumps(document).encode()
    suffix = '.json'
    if tool == 'grype':
        inventory = grype_inventory(document)
        source = inventory['sourceResults']
        expected = len({(item['vulnerability']['id'], item['artifact']['name'], item['artifact']['version']) for item in document['matches']})
        scan_type = 'Anchore Grype'
    elif tool == 'semgrep':
        source = expected = len(document['results'])
        scan_type = 'Semgrep JSON Report'
    elif tool == 'gitleaks':
        source = expected = sum(len(run.get('results', [])) for run in document['runs'])
        scan_type = 'SARIF'
        suffix = '.sarif'
    elif tool == 'checkov':
        if document['summary']['parsing_errors']:
            raise ValueError('Checkov parsing errors')
        source = expected = len(document['results']['failed_checks'])
        scan_type = 'Checkov Scan'
    elif tool == 'trivy':
        matches = [item for result in document['Results'] for item in result.get('Vulnerabilities', [])]
        source = len(matches)
        expected = len({(item['VulnerabilityID'], item['PkgName'], item['InstalledVersion']) for item in matches})
        scan_type = 'Trivy Scan'
    elif tool.startswith('zap-'):
        source = expected = sum(len(site['alerts']) for site in document['site'])
        scan_type = 'ZAP Scan'
        suffix = '.xml'
        payload = zap_xml(document)
    else:
        raise ValueError('Unsupported report type')
    return {'scan_type': scan_type, 'suffix': suffix, 'payload': payload, 'expected': expected, 'sourceResults': source, 'scanWarnings': len(document.get('errors', [])) if tool == 'semgrep' else 0}


def list_all(api, endpoint, query=None):
    url = endpoint + '?' + urllib.parse.urlencode({'limit': 100, **(query or {})})
    items = []
    while url:
        data, _ = api.call(url)
        items.extend(data['results'])
        following = data.get('next')
        if following:
            parsed = urllib.parse.urlsplit(following)
            if parsed.scheme + '://' + parsed.netloc != api.base:
                raise ValueError('External pagination URL rejected')
            url = parsed.path + '?' + parsed.query
        else:
            url = None
    return items


def ensure_dojo(api, endpoint, name, body):
    existing = list_all(api, endpoint, {'name': name})
    item = next((item for item in existing if item['name'] == name), None)
    if item is None:
        item, _ = api.call(endpoint, {'name': name, **body})
    return item


def dojo_credentials(directory):
    cache = directory / 'private-dojo.json'
    if cache.exists():
        return json.loads(cache.read_text())
    api = Client('http://127.0.0.1:18082')
    env = read_env(directory)
    result, _ = wait_ready(lambda: api.call('/api/v2/api-token-auth/', {'username': 'admin', 'password': env['DOJO_ADMIN_PASSWORD']}))
    credential = {'token': result['token']}
    save_private(cache, credential)
    return credential


def multipart(fields, payload, filename):
    boundary = secrets.token_hex(24)
    chunks = []
    for key, value in fields.items():
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode() + payload + b'\r\n')
    chunks.append(f'--{boundary}--\r\n'.encode())
    return b''.join(chunks), 'multipart/form-data; boundary=' + boundary


def publish_dojo(api, engagement, tool, prepared):
    title = 'Juice Shop / ' + tool
    tests = list_all(api, '/api/v2/tests/', {'engagement': engagement})
    matches = [item for item in tests if item['title'] == title]
    if len(matches) > 1:
        raise ValueError('Duplicate publication scope detected')
    fields = {'scan_type': prepared['scan_type'], 'active': 'true', 'verified': 'false', 'close_old_findings': 'false'}
    if matches:
        fields['test'] = str(matches[0]['id'])
        endpoint = '/api/v2/reimport-scan/'
    else:
        fields.update({'engagement': str(engagement), 'test_title': title})
        endpoint = '/api/v2/import-scan/'
    payload, content_type = multipart(fields, prepared['payload'], tool + prepared['suffix'])
    result, _ = api.call(endpoint, payload, content_type=content_type)
    receipt = validate_import(result, prepared['expected'])
    findings, _ = api.call('/api/v2/findings/?' + urllib.parse.urlencode({'test': receipt['test'], 'limit': 1}))
    if findings['count'] != prepared['expected']:
        raise ValueError('Dojo readback count mismatch')
    receipt.update({'tool': tool, 'sourceResults': prepared['sourceResults'], 'scanWarnings': prepared['scanWarnings'], 'reimported': bool(matches), 'verified': False})
    return receipt


def write_receipt(output, name, document):
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / (name + '.tmp')
    temporary.write_text(json.dumps(document, indent=2))
    temporary.replace(output / name)


def execute(args):
    private = args.private_dir.resolve()
    if args.action == 'init':
        initialize(private)
        return
    if not args.output or not args.reports or not re.fullmatch(r'[a-f0-9]{40}', args.sha or '') or not re.fullmatch(r'[0-9]+', args.run or ''):
        raise ValueError('Publication requires report/output directories, full SHA and numeric run')
    output = args.output.resolve()
    if output.is_relative_to(private) or private.is_relative_to(output):
        raise ValueError('Private credentials and public output must be separate')
    provenance = {'sourceSHA': args.sha, 'sourceRun': int(args.run)}
    if args.action == 'dtrack':
        credential = dtrack_credentials(private)
        api = Client('http://127.0.0.1:18080', {'X-Api-Key': credential['apiKey']})
        document = load_report(args.reports, 'reporte-sca/sbom.cdx.json')
        receipt = publish_bom(api, document, args.sha)
        receipt.update(provenance, policyUuid=credential['policyUuid'], tool='dependency-track')
        receipt['sourceSHA256'] = hashlib.sha256((args.reports / 'reporte-sca/sbom.cdx.json').read_bytes()).hexdigest()
        write_receipt(output, 'dtrack-receipt.json', public_receipt(receipt))
        print(json.dumps(public_receipt(receipt)))
        return
    dtrack = load_report(output, 'dtrack-receipt.json')
    if dtrack.get('processingComplete') is not True or dtrack.get('sourceSHA') != args.sha or dtrack.get('sourceRun') != int(args.run) or dtrack.get('componentCount', 0) <= 0:
        raise ValueError('Matching verified Dependency-Track receipt required')
    credential = dojo_credentials(private)
    api = Client('http://127.0.0.1:18082', {'Authorization': 'Token ' + credential['token']})
    product_type = ensure_dojo(api, '/api/v2/product_types/', 'Academic SSDLC', {'description': 'Local academic evidence'})
    product = ensure_dojo(api, '/api/v2/products/', 'juice-shop-sast', {'description': 'Intentionally vulnerable training application', 'prod_type': product_type['id']})
    today = date.today().isoformat()
    engagement = ensure_dojo(api, '/api/v2/engagements/', 'Juice Shop CI / ' + args.sha, {'product': product['id'], 'target_start': today, 'target_end': today, 'engagement_type': 'CI/CD', 'status': 'In Progress'})
    sources = [('gitleaks', 'reporte-gitleaks/gitleaks.sarif'), ('semgrep', 'reporte-semgrep/semgrep.json'), ('grype', 'reporte-sca/grype.json'), ('checkov', 'reporte-iac-contenedor/checkov.json'), ('trivy', 'reporte-iac-contenedor/trivy-image.json')]
    modes = ['baseline', 'authenticated']
    if (args.reports / 'reporte-dast/full').exists() or (args.reports / 'reporte-dast/api').exists():
        modes.extend(['full', 'api'])
    for mode in modes:
        summary = load_report(args.reports, f'reporte-dast/{mode}/summary.json')
        if summary.get('passed') is not True:
            raise ValueError('Unsuccessful DAST report cannot be published as validated evidence')
        sources.append(('zap-' + mode, f'reporte-dast/{mode}/report.json'))
    receipts = []
    for tool, name in sources:
        document = load_report(args.reports, name)
        prepared = prepare_report(tool, document)
        receipt = publish_dojo(api, engagement['id'], tool, prepared)
        receipt.update(provenance, sourceSHA256=hashlib.sha256((args.reports / name).read_bytes()).hexdigest())
        receipts.append(public_receipt(receipt))
        print(json.dumps(public_receipt(receipt)))
    write_receipt(output, 'dojo-receipt.json', receipts)
    write_receipt(output, 'publication.json', {'complete': True, **provenance, 'engagement': engagement['id'], 'tools': [item['tool'] for item in receipts], 'feedsFullySynchronized': 'not asserted', 'persistentHistory': 'local deployment only; CI is ephemeral'})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('init', 'dtrack', 'dojo'))
    parser.add_argument('--private-dir', type=Path, required=True)
    parser.add_argument('--reports', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--sha')
    parser.add_argument('--run')
    args = parser.parse_args()
    try:
        execute(args)
    except Exception as error:
        print('ASPM publication failed: ' + type(error).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
