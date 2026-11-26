"""Strict adapter for sanitized ZAP JSON and native DefectDojo XML imports."""
import xml.etree.ElementTree as ET
from collections import Counter
import json
from pathlib import Path


def load_report(base, name, max_bytes=25 * 1024 * 1024):
    base = Path(base).resolve()
    relative = Path(name)
    if relative.is_absolute():
        raise ValueError('Report path must be relative')
    path = (base / relative).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError('Report must be a file inside the artifact directory')
    with path.open('rb') as stream:
        payload = stream.read(max_bytes + 1)
    if not payload or len(payload) > max_bytes:
        raise ValueError('Report empty or over size limit')
    document = json.loads(payload)
    if not isinstance(document, (dict, list)):
        raise ValueError('Report must be a JSON object or array')
    return document


def grype_inventory(report):
    matches = report.get('matches')
    if not isinstance(matches, list):
        raise ValueError('Full Grype JSON required; gate SARIF is incomplete')
    counts = Counter()
    for match in matches:
        severity = match['vulnerability']['severity']
        if severity not in ('Critical', 'High', 'Medium', 'Low', 'Negligible', 'Unknown'):
            raise ValueError('Unknown Grype severity')
        counts[severity] += 1
    return {'sourceResults': len(matches), 'severity': dict(counts)}


def zap_xml(report):
    sites = report.get('site')
    if not isinstance(sites, list) or not sites:
        raise ValueError('ZAP report has no scanned sites')
    root = ET.Element('OWASPZAPReport', version=str(report.get('@version', '')))
    for site in sites:
        target = ET.SubElement(root, 'site', {key[1:]: str(value) for key, value in site.items() if key.startswith('@')})
        alerts = ET.SubElement(target, 'alerts')
        for alert in site['alerts']:
            if str(alert.get('riskcode')) not in ('0', '1', '2', '3') or not str(alert.get('pluginid', '')).isdigit():
                raise ValueError('Invalid ZAP severity or plugin identity')
            item = ET.SubElement(alerts, 'alertitem')
            for field in ('pluginid', 'alert', 'desc', 'riskcode', 'confidence', 'solution', 'reference', 'cweid'):
                ET.SubElement(item, field).text = str(alert.get(field, ''))
            instances = ET.SubElement(item, 'instances')
            for instance in alert.get('instances', []):
                entry = ET.SubElement(instances, 'instance')
                for field in ('uri', 'method', 'param', 'attack', 'evidence'):
                    ET.SubElement(entry, field).text = str(instance.get(field, ''))
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def validate_import(result, expected):
    total = result.get('statistics', {}).get('after', {}).get('total', {}).get('total')
    test = result.get('test')
    if not isinstance(test, int) or test <= 0 or total != expected:
        raise ValueError('Dojo import did not confirm the expected finding count')
    return {'test': test, 'findings': total}
