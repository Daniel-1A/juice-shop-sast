"""Send existing DevSecOps reports to the team's two inventory services."""

import argparse
import json
import os
from pathlib import Path
import uuid
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def endpoint(variable):
    value = os.environ[variable].rstrip("/")
    parsed = urlsplit(value)
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or (parsed.scheme != "https" and
                not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}))):
        raise ValueError(f"{variable} must use HTTPS or local loopback HTTP")
    return value


def upload(url, auth, fields, filename, data, label):
    boundary = uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    chunks.extend([
        (f'--{boundary}\r\nContent-Disposition: form-data; name="{filename[0]}"; '
         f'filename="{filename[1]}"\r\nContent-Type: application/json\r\n\r\n').encode(),
        data,
        f'\r\n--{boundary}--\r\n'.encode(),
    ])
    request = Request(url, data=b"".join(chunks), method="POST", headers={
        **auth, "Content-Type": f"multipart/form-data; boundary={boundary}", "Accept": "application/json",
    })
    try:
        with build_opener(NoRedirect()).open(request, timeout=90) as response:
            result = json.load(response)
    except HTTPError as error:
        raise SystemExit(f"{label}: HTTP {error.code}") from None
    return result


def zap_findings(data):
    severity = {"0": "Info", "1": "Low", "2": "Medium", "3": "High"}
    alerts = {}
    for site in data["site"]:
        for alert in site["alerts"]:
            plugin = str(int(alert["pluginid"]))
            if plugin not in alerts:
                alerts[plugin] = {
                    "title": alert["name"],
                    "description": f"Alerta pasiva registrada por OWASP ZAP, regla {plugin}.",
                    "severity": severity[str(alert["riskcode"])],
                    "unique_id_from_tool": f"zap-{plugin}",
                }
    return json.dumps({"findings": list(alerts.values())}, ensure_ascii=False).encode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", type=Path, help="Directory of extracted workflow artifacts")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--run", required=True)
    args = parser.parse_args()

    dojo = endpoint("DOJO_URL")
    dtrack = endpoint("DTRACK_URL")
    dojo_auth = {"Authorization": "Token " + os.environ["DOJO_API_TOKEN"]}
    dtrack_auth = {"X-Api-Key": os.environ["DTRACK_API_KEY"]}
    product = os.environ["DOJO_PRODUCT_NAME"]
    engagement = os.environ["DOJO_ENGAGEMENT_NAME"]
    project = str(uuid.UUID(os.environ["DTRACK_PROJECT_ID"]))

    reports = []
    for title, kind, relative, required_field in (
        ("Semgrep", "Semgrep JSON Report", "reporte-semgrep/semgrep.json", "results"),
        ("Grype", "Anchore Grype", "reporte-sca/grype.json", "matches"),
        ("Checkov", "Checkov Scan", "reporte-iac-contenedor/checkov.json", "summary"),
        ("Trivy", "Trivy Scan", "reporte-iac-contenedor/trivy-image.json", "Results"),
        ("ZAP Baseline", "Generic Findings Import", "reporte-dast/baseline/report.json", "site"),
        ("ZAP Autenticado", "Generic Findings Import", "reporte-dast/authenticated/report.json", "site"),
    ):
        path = args.reports / relative
        data = path.read_bytes()
        parsed = json.loads(data)
        if required_field not in parsed:
            raise ValueError(f"Invalid report for {title}")
        if kind == "Generic Findings Import":
            data = zap_findings(parsed)
        reports.append((title, kind, title.replace(" ", "-").lower() + ".json", data))

    bom = (args.reports / "reporte-sca/sbom.cdx.json").read_bytes()
    parsed = json.loads(bom)
    if parsed.get("bomFormat") != "CycloneDX" or not parsed.get("components"):
        raise ValueError("Missing CycloneDX components")

    for title, kind, name, data in reports:
        result = upload(
            dojo + "/api/v2/reimport-scan/", dojo_auth,
            {
                "product_name": product, "engagement_name": engagement,
                "auto_create_context": "true", "scan_type": kind, "test_title": title,
                "active": "true", "verified": "false", "minimum_severity": "Info",
                "close_old_findings": "false", "background_import": "false",
                "commit_hash": args.commit, "build_id": args.run,
            },
            ("file", name), data, title,
        )
        print(f"{title}: test {int(result['test_id'])}")

    result = upload(dtrack + "/api/v1/bom", dtrack_auth, {"project": project},
                    ("bom", "sbom.cdx.json"), bom, "Dependency-Track")
    uuid.UUID(result["token"])
    print("Dependency-Track: BOM encolado para procesamiento")


if __name__ == "__main__":
    main()
