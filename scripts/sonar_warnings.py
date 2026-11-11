"""Avertissements non critiques issus de SonarQube (ne fait jamais échouer le job)."""
import json
import os
from pathlib import Path

try:
    with open("sonar-measures.json") as f:
        measures = json.load(f)["component"]["measures"]
except Exception as e:
    print(f"::warning::Mesures Sonar indisponibles ({e})")
    raise SystemExit(0)

m = {x["metric"]: float(x["value"]) for x in measures}

smells = int(m.get("code_smells", 0))
cov = m.get("coverage", 0.0)

warnings = []
if smells:
    warnings.append(f"{smells} code smell(s) à corriger (non critique)")
if 70 <= cov < 80:
    warnings.append(f"Couverture Sonar de {cov:.1f}% comprise entre 70% et 80%")

Path("reports").mkdir(exist_ok=True)
Path("reports/quality-report-sonar.json").write_text(
    json.dumps(
        {
            "stage": "sonar",
            "status": "warning" if warnings else "passed",
            "metrics": m,
            "warnings": warnings,
            "critical_errors": [],
        },
        indent=2,
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)

for warning in warnings:
    print(f"::warning::{warning}")

summary = os.environ.get("GITHUB_STEP_SUMMARY")
if warnings and summary:
    with open(summary, "a", encoding="utf-8") as stream:
        stream.write(
            "## ⚠️ Avertissements Sonar\n"
            + "\n".join(f"- {warning}" for warning in warnings)
            + "\n"
        )
