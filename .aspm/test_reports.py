import unittest
import xml.etree.ElementTree as ET
import tempfile
from pathlib import Path
from reports import zap_xml, validate_import, grype_inventory, load_report

class ReportsTest(unittest.TestCase):
    def test_report_loading_rejects_escape_and_oversized_input(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'reports'
            base.mkdir()
            (Path(directory) / 'private.json').write_text('{"secret": "private"}')
            (base / 'valid.json').write_text('{"matches": []}')
            self.assertEqual(load_report(base, 'valid.json'), {'matches': []})
            for name in ('../private.json', str(Path(directory) / 'private.json')):
                with self.assertRaises(ValueError):
                    load_report(base, name)
            with self.assertRaises(ValueError):
                load_report(base, 'valid.json', max_bytes=2)

    def test_complete_grype_inventory_keeps_unfixed_critical(self):
        report = {'matches': [{'vulnerability': {'id': 'CVE-example', 'severity': 'Critical', 'fix': {'state': 'not-fixed', 'versions': []}}, 'artifact': {'name': 'example', 'version': '1.0'}}]}
        self.assertEqual(grype_inventory(report), {'sourceResults': 1, 'severity': {'Critical': 1}})
        with self.assertRaises(ValueError):
            grype_inventory({'runs': []})

    def test_zap_preserves_severity_identity_instances_and_escapes_xml(self):
        report = {'@version': '2.17.0', 'site': [{'@name': 'http://juice-shop:3000', 'alerts': [{'pluginid': '10038', 'alert': 'CSP missing', 'riskcode': '2', 'confidence': '3', 'desc': '<p>Missing</p>', 'solution': 'Set CSP', 'reference': 'https://example.invalid', 'cweid': '693', 'instances': [{'uri': 'http://juice-shop:3000/?a=1&b=2', 'method': 'GET', 'evidence': '<value>'}]}]}]}
        xml = ET.fromstring(zap_xml(report))
        alert = xml.find('site/alerts/alertitem')
        self.assertEqual(alert.findtext('riskcode'), '2')
        self.assertEqual(alert.findtext('pluginid'), '10038')
        self.assertEqual(alert.findtext('instances/instance/evidence'), '<value>')
        self.assertEqual(alert.findtext('instances/instance/uri'), 'http://juice-shop:3000/?a=1&b=2')

    def test_missing_or_unknown_severity_rejected(self):
        for alert in ({'pluginid': '1'}, {'pluginid': '1', 'riskcode': '9'}):
            with self.assertRaises(ValueError):
                zap_xml({'site': [{'alerts': [alert]}]})

    def test_import_must_confirm_expected_findings(self):
        for result in ({}, {'test': 1}, {'test': 1, 'statistics': {'after': {'total': {'total': 0}}}}):
            with self.assertRaises(ValueError):
                validate_import(result, 3)
        self.assertEqual(validate_import({'test': 5, 'statistics': {'after': {'total': {'total': 3}}}}, 3), {'test': 5, 'findings': 3})

if __name__ == '__main__':
    unittest.main()
