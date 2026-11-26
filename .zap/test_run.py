import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location('dast_run', Path(__file__).with_name('run.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class DastPolicyTests(unittest.TestCase):
    def setUp(self):
        self.target = 'http://juice-shop:3000'
        self.coverage = {'target': self.target, 'urls': [self.target + '/'], 'authenticated': False,
                         'successfulResponses': 1}

    def report(self, rule=None):
        alerts = [] if rule is None else [{'pluginid': str(rule), 'riskcode': '2', 'instances': [{'uri': self.target + '/'}]}]
        return {'site': [{'@name': self.target, 'alerts': alerts}]}

    def test_only_required_header_regressions_block_passive_modes(self):
        for mode in ('baseline', 'authenticated', 'full', 'api'):
            coverage = dict(self.coverage, authenticated=mode != 'baseline')
            for rule, blocked in ((10020, mode in ('baseline', 'authenticated')),
                                  (10021, mode in ('baseline', 'authenticated')), (10038, False)):
                with self.subTest(mode=mode, rule=rule):
                    result = runner.validate_report(self.report(rule), coverage, mode, {10020, 10021})
                    self.assertEqual(bool(result['blocking']), blocked)

    def test_clean_report_requires_real_coverage(self):
        self.assertFalse(runner.validate_report(self.report(), self.coverage, 'baseline', {10020, 10021})['blocking'])
        for coverage in ({}, dict(self.coverage, urls=[]), dict(self.coverage, successfulResponses=0),
                         dict(self.coverage, urls=['https://example.org/']),
                         dict(self.coverage, target='https://example.org/')):
            with self.subTest(coverage=coverage), self.assertRaises(ValueError):
                runner.validate_report(self.report(), coverage, 'baseline', {10020, 10021})

    def test_rejects_missing_or_malformed_report_and_external_alerts(self):
        for report in ({}, {'site': []}, {'site': [{'@name': self.target}]},
                       {'site': [{'@name': 'https://example.org', 'alerts': []}]}):
            with self.subTest(report=report), self.assertRaises(ValueError):
                runner.validate_report(report, self.coverage, 'baseline', {10020, 10021})
        report = self.report(10020)
        report['site'][0]['alerts'][0]['instances'][0]['uri'] = 'https://example.org/'
        with self.assertRaises(ValueError):
            runner.validate_report(report, self.coverage, 'baseline', {10020, 10021})

    def test_authenticated_mode_does_not_fall_back_to_anonymous(self):
        with self.assertRaises(ValueError):
            runner.validate_report(self.report(), self.coverage, 'authenticated', {10020, 10021})

    def test_sanitizes_exact_escaped_and_unlisted_jwt_values(self):
        import base64
        import secrets
        secret = 'pass<&"word'
        header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').decode().rstrip('=')
        payload = base64.urlsafe_b64encode(b'{"fixture":true}').decode().rstrip('=')
        token = header + '.' + payload + '.' + secrets.token_urlsafe(24)
        text = 'pass<&"word pass&lt;&amp;&quot;word ' + token
        clean = runner.sanitize(text, [secret])
        self.assertNotIn('pass', clean)
        self.assertNotIn('eyJ', clean)
        self.assertIn('[REDACTED]', clean)


class AuthProofTests(unittest.TestCase):
    def setUp(self):
        self.target = 'http://juice-shop:3000'
        self.token = 'test-ephemeral-token'
        self.messages = [
            {'requestHeader': 'GET http://juice-shop:3000/rest/user/whoami HTTP/1.1\r\nCookie: token=test-ephemeral-token\r\n',
             'responseHeader': 'HTTP/1.1 200 OK\r\n', 'responseBody': '{"user":{"email":"scan@example.invalid","id":42}}'},
            {'requestHeader': 'GET http://juice-shop:3000/rest/basket/7 HTTP/1.1\r\nAuthorization: Bearer test-ephemeral-token\r\n',
             'responseHeader': 'HTTP/1.1 200 OK\r\n', 'responseBody': '{"data":{"id":7,"UserId":42}}'},
            {'requestHeader': 'GET http://juice-shop:3000/rest/basket/7 HTTP/1.1\r\nAuthorization: Bearer invalid-token\r\n',
             'responseHeader': 'HTTP/1.1 401 Unauthorized\r\n', 'responseBody': '{}'},
        ]

    def verify(self, messages):
        return runner.verify_auth(messages, self.target, 'scan@example.invalid', 42, 7, self.token)

    def test_proves_identity_basket_and_rejection_from_zap_messages(self):
        self.assertTrue(self.verify(self.messages))

    def test_rejects_anonymous_200_wrong_identity_or_no_negative_control(self):
        import copy
        for index, value in ((0, '{"user":{}}'), (0, '{"user":{"email":"other@example.invalid","id":42}}'),
                             (1, '{"data":{"id":8,"UserId":42}}')):
            messages = copy.deepcopy(self.messages)
            messages[index]['responseBody'] = value
            with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                self.verify(messages)
        with self.assertRaises(ValueError):
            self.verify(self.messages[:2])


if __name__ == '__main__':
    unittest.main()
