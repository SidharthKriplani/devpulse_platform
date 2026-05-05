from pathlib import Path

report = Path("outputs/evidence/devpulse_demo_report.txt")
if not report.exists():
    raise SystemExit("Run PYTHONPATH=. python3 scripts/seed_devpulse.py first")

print(report.read_text(encoding="utf-8"))
