"""Hooks for the packaged scans; private state never becomes an artifact."""
import json
import os
from pathlib import Path
import secrets
import sys
import time
import urllib.request
from datetime import datetime, timezone

import yaml

sys.path.insert(0, os.environ['DAST_CONFIG'])
from run import TARGET, same_origin, verify_auth


def zap_started(zap, target):
    private = Path(os.environ['DAST_PRIVATE'])
    mode = os.environ['DAST_MODE']
    if mode == 'baseline':
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(TARGET + '/', timeout=10) as response:
            if response.status != 200 or not same_origin(response.url):
                raise ValueError('Owned target is not reachable with HTTP 200')
        return
    password = secrets.token_hex(24)
    email = 'zap-' + secrets.token_hex(8) + '@example.invalid'
    secret_values = [password]
    (private / 'secrets.json').write_text(json.dumps(secret_values))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def post(path, body):
        request = urllib.request.Request(TARGET + path, data=json.dumps(body).encode(),
                                         headers={'Content-Type': 'application/json'})
        with opener.open(request, timeout=20) as response:
            return json.load(response)

    registered = post('/api/Users', {'email': email, 'password': password, 'passwordRepeat': password})
    user_id = registered['data']['id']
    authentication = post('/rest/user/login', {'email': email, 'password': password})['authentication']
    token, basket_id = authentication['token'], authentication['bid']
    secret_values.append(token)
    (private / 'secrets.json').write_text(json.dumps(secret_values))
    plan = yaml.safe_load((Path(os.environ['DAST_CONFIG']) / 'plan.yaml').read_text())
    bearer = 'Authorization: Bearer ' + token
    requests = [
        {'url': TARGET + '/rest/user/whoami', 'headers': ['Cookie: token=' + token], 'responseCode': 200},
        {'url': TARGET + f'/rest/basket/{basket_id}', 'headers': [bearer], 'responseCode': 200},
        {'url': TARGET + f'/rest/basket/{basket_id}', 'headers': ['Authorization: Bearer invalid-token'], 'responseCode': 401},
        {'url': TARGET + '/rest/products/search?q=apple', 'headers': [bearer], 'responseCode': 200},
    ]
    if mode == 'api':
        requests.append({'url': TARGET + '/b2b/v2/orders', 'method': 'POST',
                         'headers': [bearer, 'Content-Type: application/json'],
                         'data': '{"cid":"DAST-LAB","orderLinesData":"[]"}', 'responseCode': 200})
    plan['jobs'][0]['requests'] = requests
    plan_path = private / 'authenticated.yaml'
    plan_path.write_text(yaml.safe_dump(plan))
    plan_id = zap.automation.run_plan(str(plan_path))
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        progress = zap.automation.plan_progress(plan_id)
        if progress.get('finished'):
            break
        time.sleep(1)
    else:
        raise ValueError('Authenticated AF plan timed out')
    if progress.get('error') or progress.get('warn'):
        raise ValueError('Authenticated AF plan reported errors or warnings')
    messages = zap.core.messages(baseurl=TARGET, start=0, count=500)
    verify_auth(messages, TARGET, email, user_id, basket_id, token)
    if mode == 'api' and not any('/b2b/v2/orders' in msg['requestHeader']
                                 and msg['responseHeader'].startswith('HTTP/1.1 200') for msg in messages):
        raise ValueError('B2B API authenticated request was not demonstrated')
    (private / 'auth-proof.json').write_text(json.dumps({'authenticated': True, 'negativeControl': True,
                                                       'afPlan': True, 'apiVerified': mode == 'api'}))
    zap.replacer.add_rule('ephemeral-bearer', 'true', 'REQ_HEADER', 'false', 'Authorization',
                          'Bearer ' + token, url=r'http://juice-shop:3000/.*')


def zap_pre_shutdown(zap):
    private = Path(os.environ['DAST_PRIVATE'])
    urls = zap.core.urls(baseurl=TARGET)
    if not urls or not all(same_origin(url) for url in urls):
        raise ValueError('Missing coverage or out-of-scope URL')
    auth_path = private / 'auth-proof.json'
    proof = json.loads(auth_path.read_text()) if auth_path.exists() else {'authenticated': False}
    messages = zap.core.messages(baseurl=TARGET, start=0, count=500)
    successful = sum(bool(msg.get('responseHeader', '').splitlines())
                     and len(msg['responseHeader'].split()) > 1
                     and msg['responseHeader'].split()[1].isdigit()
                     and 200 <= int(msg['responseHeader'].split()[1]) < 400 for msg in messages)
    proof.update({'target': TARGET, 'urls': urls, 'zapVersion': zap.core.version,
                  'scannedAt': datetime.now(timezone.utc).isoformat(),
                  'successfulResponses': successful, 'responseSampleSize': len(messages),
                  'activeScanLimitMinutes': int(zap.ascan.option_max_scan_duration_in_mins)})
    (private / 'coverage.json').write_text(json.dumps(proof, indent=2))


def zap_tuned(zap):
    # Use the versioned API: unknown -config keys are silently ignored by ZAP.
    zap.ascan.set_option_max_scan_duration_in_mins(5)
    zap.ascan.set_option_thread_per_host(2)
    if int(zap.ascan.option_max_scan_duration_in_mins) != 5:
        raise ValueError('Active scan time limit was not applied')
