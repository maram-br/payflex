import sys, json, os
import xml.etree.ElementTree as ET

stage = sys.argv[1] if len(sys.argv) > 1 else ""
crit, warn = [], []

if stage == "unit":
    rate = float(ET.parse("coverage.xml").getroot().attrib["line-rate"]) * 100
    print(f"Couverture : {rate:.1f}%")
    if rate < 70:
        crit.append(f"Couverture {rate:.1f}% < 70%")
    elif rate < 80:
        warn.append(f"Attention, couverture à {rate:.1f}%")

elif stage == "perf":
    m = json.load(open("k6-summary.json"))["metrics"]
    p95 = m["http_req_duration"]["values"]["p(95)"]
    err = m["http_req_failed"]["values"]["rate"] * 100
    print(f"p95 = {p95:.1f} ms | erreurs = {err:.2f}%")
    if p95 > 500 or err > 2:
        crit.append(f"Performance : p95={p95:.0f}ms, erreurs={err:.2f}%")
    elif p95 > 200:
        warn.append(f"Latence p95 élevée : {p95:.0f}ms")

elif stage == "secrets":
    leaks = json.load(open("gitleaks.json")) or []
    taux = 100 if len(leaks) == 0 else 0
    print(f"Taux de confidentialité : {taux}%")
    if taux < 100:
        crit.append(f"{len(leaks)} fuite(s) : " +
                    ", ".join(f"{l['RuleID']}@{l['File']}" for l in leaks))
else:
    print("Usage : quality_gate.py [unit|perf|secrets]")
    sys.exit(2)

summary = os.environ.get("GITHUB_STEP_SUMMARY")
for w in warn:
    print(f"::warning::{w}")
    if summary:
        open(summary, "a").write(f"- ⚠️ {w}\n")

if crit:
    report = f"# Rapport d'incident\n\n**Étape** : {stage}\n\n" + "\n".join(f"- ❌ {c}" for c in crit) + "\n"
    open("incident-report.md", "w").write(report)
    if summary:
        open(summary, "a").write(report)
    for c in crit:
        print(f"::error::{c}")
    sys.exit(1)

print("✅ Quality gate OK")