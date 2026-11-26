import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from manage import Client, public_receipt, initialize, publish_bom, prepare_report

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/reset':
            self.close_connection = True
            return
        if self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', 'https://example.invalid/private')
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ready":true}')
    def log_message(self, *args):
        pass

class ManageTest(unittest.TestCase):
    def test_semgrep_partial_parsing_warnings_are_not_hidden(self):
        prepared = prepare_report('semgrep', {'results': [], 'errors': [{'type': 'PartialParsing'}]})
        self.assertEqual(prepared['scanWarnings'], 1)

    def test_grype_import_uses_full_native_json_with_critical_and_duplicates(self):
        match = {'vulnerability': {'id': 'CVE-example', 'severity': 'Critical'}, 'artifact': {'name': 'example', 'version': '1.0'}}
        prepared = prepare_report('grype', {'matches': [match, match]})
        self.assertEqual(prepared['scan_type'], 'Anchore Grype')
        self.assertEqual(prepared['expected'], 1)
        self.assertEqual(prepared['sourceResults'], 2)
        self.assertEqual(json.loads(prepared['payload'])['matches'][0]['vulnerability']['severity'], 'Critical')

    def test_sbom_requires_finished_processing_and_nonempty_inventory(self):
        class API:
            def __init__(self, count):
                self.count = count
            def call(self, path, data=None, **kwargs):
                if path == '/api/v1/bom':
                    return {'token': 'processing-token'}, {}
                if '/bom/token/' in path:
                    return {'processing': False}, {}
                if '/project/lookup?' in path:
                    return {'uuid': 'project-id'}, {}
                return ([{'name': 'example'}] if self.count else []), {'X-Total-Count': str(self.count)}
        self.assertEqual(publish_bom(API(1), {'components': [{'name': 'example'}]}, 'abc')['componentCount'], 1)
        with self.assertRaises(ValueError):
            publish_bom(API(0), {'components': [{'name': 'example'}]}, 'abc')

    def test_client_only_uses_loopback_and_refuses_redirects(self):
        with self.assertRaises(ValueError):
            Client('https://example.invalid')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = Client(f'http://127.0.0.1:{server.server_port}')
            self.assertEqual(client.call('/ready')[0], {'ready': True})
            with self.assertRaises(RuntimeError):
                client.call('/redirect')
            with self.assertRaises(RuntimeError):
                client.call('/reset')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_receipt_is_allowlisted_and_excludes_credentials(self):
        result = public_receipt({'test': 4, 'findings': 3, 'token': 'private', 'password': 'private', 'sourceSHA': 'abc'})
        self.assertEqual(result, {'test': 4, 'findings': 3, 'sourceSHA': 'abc'})

    def test_initialization_preserves_credentials_on_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            initialize(Path(directory))
            before = (Path(directory) / 'private.env').read_bytes()
            initialize(Path(directory))
            self.assertEqual((Path(directory) / 'private.env').read_bytes(), before)
            text = before.decode()
            self.assertIn('DOJO_ADMIN_PASSWORD=', text)
            self.assertNotIn('=admin\n', text)

if __name__ == '__main__':
    unittest.main()
