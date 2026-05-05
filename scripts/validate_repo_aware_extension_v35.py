from __future__ import annotations

import json
from pathlib import Path


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    required_paths = [
        "sample_repos/checkout_app/package.json",
        "sample_repos/checkout_app/src/auth.ts",
        "sample_repos/checkout_app/src/profile.ts",
        "sample_repos/checkout_app/src/logging.ts",
        "sample_repos/checkout_app/src/analytics.ts",
        "outputs/repo_aware/repo_inspection_report.json",
        "outputs/repo_aware/dependency_usage_map.json",
        "outputs/repo_aware/risky_callsite_report.json",
        "outputs/repo_aware/repo_aware_extension_summary.json"
    ]

    repo = load("outputs/repo_aware/repo_inspection_report.json")
    usage = load("outputs/repo_aware/dependency_usage_map.json")
    risky = load("outputs/repo_aware/risky_callsite_report.json")
    summary = load("outputs/repo_aware/repo_aware_extension_summary.json")

    checks = [
        {
            "name": "required_files_present",
            "passed": all(Path(p).exists() and Path(p).stat().st_size > 0 for p in required_paths),
            "observed": required_paths
        },
        {
            "name": "sample_repo_scanned",
            "passed": repo["source_file_count"] >= 4,
            "observed": repo["source_file_count"]
        },
        {
            "name": "dependency_usage_map_covers_manifest",
            "passed": usage["dependency_usage_count"] >= 5,
            "observed": usage["dependency_usage_count"]
        },
        {
            "name": "callsites_found",
            "passed": repo["callsites_found"] >= 4,
            "observed": repo["callsites_found"]
        },
        {
            "name": "risky_callsites_present",
            "passed": risky["risky_callsite_count"] >= 2,
            "observed": risky["risky_callsite_count"]
        },
        {
            "name": "repo_readiness_not_empty",
            "passed": repo["aggregate_repo_migration_readiness"] in {"SAFE", "RISKY", "BLOCKED"},
            "observed": repo["aggregate_repo_migration_readiness"]
        },
        {
            "name": "truth_boundary_present",
            "passed": "real production PR generation" in repo["truth_boundary"]["not_claimed"],
            "observed": repo["truth_boundary"]
        },
        {
            "name": "extension_summary_pass",
            "passed": summary["status"] == "pass",
            "observed": summary["status"]
        }
    ]

    status = "pass" if all(c["passed"] for c in checks) else "fail"

    payload = {
        "artifact": "repo_aware_extension_validation_v35",
        "status": status,
        "check_count": len(checks),
        "passed_count": sum(c["passed"] for c in checks),
        "checks": checks,
        "evidence_statement": "Validates DevPulse v3.5 repo-aware migration simulation: sample repo inspection, dependency usage mapping, risky callsite detection, and honest non-claims."
    }

    out = Path("outputs/validation/repo_aware_extension_validation_v35.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("repo_aware_extension_validation_v35 complete")
    print(f"status: {status}")
    print(f"passed_count: {payload['passed_count']}/{payload['check_count']}")
    print(f"wrote {out}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
