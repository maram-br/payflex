"""Avertissements non critiques issus de SonarQube (ne fait jamais échouer le job)."""
import json
import os

try:
    with open("sonar-measures.json") as f:
        measures = json.load(f)["component"]["measures"]
except Exception as e:
    print(f"::warning::Mesures Sonar indisponibles ({e})")
    raise SystemExit(0)

m = {x["metric"]: float(x["value"]) for x in measures}

smells = int(m.get("code_smells", 0))
cov = m.get("coverage", 0.0)
debt = int(m.get("sqale_index", 0))  # minutes

msgs = []
if smells > 0:
    msgs.append(f"{smells} code smell(s), dette technique ≈ {debt} min")
if 70 <= cov < 80:
    msgs.append(f"Attention, couverture à {cov:.1f}%")

for t in msgs:
    print(f"::warning::{t}")

summary = os.environ.get("GITHUB_STEP_SUMMARY")
if msgs and summary:
    with open(summary, "a") as f:
        f.write("## ⚠️ Avertissements Sonar\n" + "\n".join(f"- {t}" for t in msgs) + "\n")