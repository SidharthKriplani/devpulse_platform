from __future__ import annotations
import json
from pathlib import Path

required = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "configs/devpulse_prd_scope_v3.json",
    "docs/BUILD_PLAN.md",
    "src/devpulse/__init__.py",
    "src/devpulse/core/__init__.py",
    "src/devpulse/agentic/__init__.py",
    "outputs/evidence",
    "outputs/validation",
    "outputs/reports"
]

checks = [{"path": p, "exists": Path(p).exists()} for p in required]
scope = json.loads(Path("configs/devpulse_prd_scope_v3.json").read_text())

semantic = [
    ("query_layers_11", len(scope["query_mode"]["layers"]) == 11),
    ("goal_components_6", len(scope["goal_mode"]["components"]) == 6),
    ("evidence_artifacts_32", scope["completion_targets"]["evidence_artifacts"] == 32),
    ("failure_scenarios_19", scope["completion_targets"]["failure_recovery_scenarios"] == 19),
    ("lifecycle_37_days", scope["completion_targets"]["operating_lifecycle_days"] == 37)
]

checks += [{"path": k, "exists": v} for k, v in semantic]
status = "pass" if all(c["exists"] for c in checks) else "fail"

out = {
    "artifact": "repo_foundation_validation",
    "status": status,
    "passed_count": sum(c["exists"] for c in checks),
    "check_count": len(checks),
    "checks": checks
}

Path("outputs/validation").mkdir(parents=True, exist_ok=True)
Path("outputs/validation/repo_foundation_validation.json").write_text(json.dumps(out, indent=2))

print("repo_foundation_validation complete")
print(f"status: {status}")
print(f"passed_count: {out['passed_count']}/{out['check_count']}")
print("wrote outputs/validation/repo_foundation_validation.json")

if status != "pass":
    raise SystemExit(1)
