from pathlib import Path

for path in [
    "outputs/evidence/devpulse_demo_report.txt",
    "outputs/evidence/agentic_demo_report.txt",
    "outputs/reports/devpulse_final_demo_report.txt"
]:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Missing {path}. Run PYTHONPATH=. python3 scripts/run_devpulse_complete_v3.py first.")
    print(p.read_text(encoding="utf-8"))
