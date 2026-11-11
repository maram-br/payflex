"""Quality Gate PayFlex : classe les écarts et échoue sur tout critère critique."""

import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


stage = sys.argv[1] if len(sys.argv) > 1 else ""
critical = []
warnings = []
metrics = {}
reports_dir = Path("reports")
reports_dir.mkdir(exist_ok=True)


def load_json(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


if stage == "unit":
    coverage_path = Path("coverage.xml")
    if not coverage_path.exists():
        critical.append("Rapport coverage.xml absent")
    else:
        try:
            rate = float(ET.parse(coverage_path).getroot().attrib["line-rate"]) * 100
            metrics["coverage_percent"] = round(rate, 2)
            print(f"Couverture : {rate:.1f}%")
            if rate < 70:
                critical.append(f"Couverture {rate:.1f}% < 70%")
            elif rate < 80:
                warnings.append(f"Couverture {rate:.1f}% comprise entre 70% et 80%")
        except (ET.ParseError, KeyError, ValueError) as error:
            critical.append(f"Rapport de couverture invalide : {error}")

elif stage == "perf":
    summary_path = Path("k6-summary.json")
    if not summary_path.exists():
        critical.append("Rapport k6-summary.json absent : le tir de charge a échoué")
    else:
        try:
            k6_metrics = load_json(summary_path)["metrics"]
            p95 = float(k6_metrics["http_req_duration"]["values"]["p(95)"])
            http_error_rate = float(k6_metrics["http_req_failed"]["values"]["rate"]) * 100
            check_error_rate = (1 - float(k6_metrics["checks"]["values"]["rate"])) * 100
            error_rate = max(http_error_rate, check_error_rate)
            metrics.update(
                {
                    "p95_ms": round(p95, 2),
                    "http_error_percent": round(http_error_rate, 2),
                    "check_error_percent": round(check_error_rate, 2),
                    "effective_error_percent": round(error_rate, 2),
                }
            )
            print(f"p95 = {p95:.1f} ms | taux d'erreur effectif = {error_rate:.2f}%")
            if p95 > 500 or error_rate > 2:
                critical.append(
                    f"Performance critique : p95={p95:.0f}ms, erreurs={error_rate:.2f}%"
                )
            else:
                if p95 > 200:
                    warnings.append(f"Latence p95 élevée : {p95:.0f}ms (zone 200-500ms)")
                if error_rate >= 1:
                    warnings.append(
                        f"Taux d'erreur élevé : {error_rate:.2f}% (zone 1-2%)"
                    )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            critical.append(f"Rapport k6 invalide : {error}")

elif stage == "secrets":
    report_paths = [Path(path) for path in sys.argv[2:]]
    if not report_paths:
        report_paths = [Path("gitleaks-source.json"), Path("gitleaks-artifacts.json")]

    leaks = []
    for report_path in report_paths:
        if not report_path.exists():
            critical.append(f"Rapport Gitleaks absent : {report_path}")
            continue
        try:
            content = load_json(report_path) or []
            if not isinstance(content, list):
                raise ValueError("le rapport doit contenir une liste JSON")
            leaks.extend(content)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            critical.append(f"Rapport Gitleaks invalide ({report_path}) : {error}")

    confidentiality_rate = 100 if not leaks and not critical else 0
    metrics.update(
        {
            "leaks_count": len(leaks),
            "confidentiality_percent": confidentiality_rate,
            "scanned_reports": [str(path) for path in report_paths],
        }
    )
    print(f"Taux de confidentialité : {confidentiality_rate}%")
    if leaks:
        details = []
        for leak in leaks:
            rule = leak.get("RuleID", "règle-inconnue")
            filename = leak.get("File", "fichier-inconnu")
            line = leak.get("StartLine")
            details.append(f"{rule}@{filename}" + (f":{line}" if line else ""))
        critical.append(f"{len(leaks)} fuite(s) détectée(s) : " + ", ".join(details))

else:
    print("Usage : quality_gate.py [unit|perf|secrets] [rapports-gitleaks...]")
    raise SystemExit(2)


status = "critical" if critical else "warning" if warnings else "passed"
quality_report = {
    "stage": stage,
    "status": status,
    "metrics": metrics,
    "warnings": warnings,
    "critical_errors": critical,
}
(reports_dir / f"quality-report-{stage}.json").write_text(
    json.dumps(quality_report, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
for warning in warnings:
    print(f"::warning::{warning}")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as stream:
            stream.write(f"- ⚠️ {warning}\n")

if critical:
    incident = (
        f"# Rapport d'incident\n\n**Étape** : {stage}\n\n"
        + "\n".join(f"- ❌ {error}" for error in critical)
        + "\n"
    )
    (reports_dir / f"incident-{stage}.md").write_text(incident, encoding="utf-8")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as stream:
            stream.write(incident)
    for error in critical:
        print(f"::error::{error}")
    raise SystemExit(1)

print("✅ Quality gate OK")
