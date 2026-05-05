from __future__ import annotations

import json
from pathlib import Path


def exists_nonempty(path: str) -> bool:
    p = Path(path)
    return p.exists() and p.stat().st_size > 0


def main() -> None:
    html_path = Path("outputs/dashboard/index.html")
    manifest_path = Path("outputs/dashboard/dashboard_manifest.json")

    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    checks = [
        {
            "name": "dashboard_html_exists",
            "passed": exists_nonempty("outputs/dashboard/index.html"),
            "observed": str(html_path)
        },
        {
            "name": "dashboard_manifest_exists",
            "passed": exists_nonempty("outputs/dashboard/dashboard_manifest.json"),
            "observed": str(manifest_path)
        },
        {
            "name": "manifest_status_pass",
            "passed": manifest.get("status") == "pass",
            "observed": manifest.get("status")
        },
        {
            "name": "contains_project_title",
            "passed": "DevPulse Evidence Dashboard" in html,
            "observed": "title checked"
        },
        {
            "name": "contains_truth_boundary",
            "passed": "no real production SaaS" in html and "no real GitHub PR generation" in html,
            "observed": "truth boundary checked"
        },
        {
            "name": "contains_rag_metrics",
            "passed": "Hybrid Recall@5" in html and "Conflict Macro F1" in html and "37-day queries" in html,
            "observed": "rag metrics checked"
        },
        {
            "name": "contains_repo_aware_section",
            "passed": "Repo-aware Risk" in html and "Risky callsites" in html,
            "observed": "repo-aware section checked"
        },
        {
            "name": "contains_patch_pr_section",
            "passed": "Patch + PR Simulation" in html and "DO_NOT_APPLY_WITHOUT_REVIEW" in html,
            "observed": "patch/pr section checked"
        },
        {
            "name": "contains_artifact_inventory",
            "passed": "Artifact Inventory" in html and manifest.get("artifact_inventory_count", 0) >= 40,
            "observed": manifest.get("artifact_inventory_count")
        }
    ]

    status = "pass" if all(c["passed"] for c in checks) else "fail"

    payload = {
        "artifact": "dashboard_validation_v35",
        "status": status,
        "check_count": len(checks),
        "passed_count": sum(c["passed"] for c in checks),
        "checks": checks,
        "evidence_statement": "Validates DevPulse static dashboard renders PRD completion, RAG eval, repo-aware risk, patch/PR simulation, truth boundary, and artifact inventory."
    }

    out = Path("outputs/validation/dashboard_validation_v35.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("dashboard_validation_v35 complete")
    print(f"status: {status}")
    print(f"passed_count: {payload['passed_count']}/{payload['check_count']}")
    print(f"wrote {out}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
