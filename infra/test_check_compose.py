import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


class ComposePolicyTests(unittest.TestCase):
    def setUp(self):
        self.service = {
            'user': '65532:65532',
            'ports': [{'host_ip': '127.0.0.1', 'target': 3000, 'published': '3000', 'protocol': 'tcp'}],
            'cap_drop': ['ALL'],
            'security_opt': ['no-new-privileges:true'],
            'pids_limit': 256, 'mem_limit': 1073741824, 'cpus': 2,
            'healthcheck': {'test': ['CMD', '/nodejs/bin/node', '-e', 'process.exit(0)']},
        }
        spec = importlib.util.spec_from_file_location('check_compose', Path(__file__).with_name('check-compose.py'))
        self.policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.policy)

    def config(self, service=None):
        return {'services': {'juice-shop': self.service if service is None else service}}

    def test_restricted_service_passes(self):
        self.assertEqual(self.policy.validate(self.config()), [])

    def test_compose_normalizes_memory_to_decimal_string(self):
        self.service['mem_limit'] = '1073741824'
        self.assertEqual(self.policy.validate(self.config()), [])

    def test_each_unsafe_override_is_rejected(self):
        overrides = [
            {'user': '0:0'}, {'user': 'root'}, {'user': 'app'},
            {'ports': [{'target': 3000, 'published': '3000'}]},
            {'ports': [{'host_ip': '0.0.0.0', 'target': 3000}]},
            {'privileged': True}, {'network_mode': 'host'}, {'pid': 'host'}, {'ipc': 'host'},
            {'cap_drop': []}, {'cap_add': ['SYS_ADMIN']}, {'security_opt': []},
            {'volumes': [{'type': 'bind', 'source': '/var/run/docker.sock', 'target': '/tmp/sock'}]},
            {'use_api_socket': True},
            {'volumes_from': ['container:host-access']},
            {'configs': [{'source': 'host-file', 'target': '/run/config'}]},
            {'secrets': [{'source': 'host-secret', 'target': '/run/secret'}]},
            {'devices': ['/dev/sda:/dev/sda']}, {'pids_limit': -1}, {'pids_limit': 0},
            {'mem_limit': 0}, {'mem_limit': 'invalid'}, {'mem_limit': '0'},
            {'cpus': 0}, {'healthcheck': {'disable': True}}, {'healthcheck': None},
            {'healthcheck': {'test': ['NONE']}},
        ]
        for override in overrides:
            with self.subTest(override=override):
                service = copy.deepcopy(self.service)
                service.update(override)
                self.assertTrue(self.policy.validate(self.config(service)))

    def test_missing_and_malformed_services_fail_closed(self):
        for config in (None, [], {}, {'services': {}}, {'services': None},
                       {'services': {'juice-shop': {}}}, {'services': {'juice-shop': None}}):
            with self.subTest(config=config):
                self.assertTrue(self.policy.validate(config))

    def test_unsafe_additional_service_is_checked(self):
        config = self.config()
        config['services']['other'] = {}
        self.assertTrue(self.policy.validate(config))

    def test_cli_exit_codes_and_report(self):
        script = str(Path(__file__).with_name('check-compose.py'))
        for data, expected in ((json.dumps(self.config()), 0), (json.dumps(self.config({})), 1), ('broken json', 2)):
            with self.subTest(expected=expected):
                result = subprocess.run([sys.executable, script], input=data, text=True, capture_output=True)
                self.assertEqual(result.returncode, expected)
                report = json.loads(result.stdout)
                self.assertEqual(report['passed'], expected == 0)


if __name__ == '__main__':
    unittest.main()
