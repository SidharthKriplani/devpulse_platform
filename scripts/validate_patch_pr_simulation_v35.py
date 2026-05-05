from __future__ import annotations

import json
from pathlib import Path


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def exists_nonempty(path: str) -> bool:
    p = Path(path)
    return p.exists() and p.stat().st_size > 0


def main() -> None:
    required = [
        "outputs/patches/proposed_file_changes.json",
        "outputs/patches/proposed_migration_patch.diff",
        "outputs/reports/patch_risk_report.json",
        "outputs/test_simulation/before_tests_report.json",
        "outputs/test_simulation/after_patch_tests_report.json",
        "outputs/test_simulation/test_failure_triage_report.json",
        "outputs/pr_simulation/pr_title.txt",
        "outputs/pr_simulation/pr_body.md",
        "outputs/pr_simulation/pr_diff.patch",
        "outputs/pr_simulation/reviewer_checklist.md",
        "outputs/pr_simulation/rollback_plan.md",
        "outputs/reports/patch_pr_simulation_summary_v35.json"
    ]

    changes = load("outputs/patches/proposed_file_changes.json")
    risk = load("outputs/reports/patch_risk_report.json")
    before = load("outputs/test_simulation/before_tests_report.json")
    after = load("outputs/test_simulation/after_patch_tests_report.json")
    triage = load("outputs/test_simulation/test_failure_triage_report.json")
    summary = load("outputs/reports/patch_pr_simulation_summary_v35.json")
    patch_text = Path("outputs/patches/proposed_migration_patch.diff").read_text(encoding="utf-8")
    pr_body = Path("outputs/pr_simulation/pr_body.md").read_text(encoding="utf-8")

    checks = [
        {
            "name": "required_artifacts_present",
            "passed": all(exists_nonempty(p) for p in required),
            "observed": required
        },
        {
            "name": "patch_has_multiple_file_changes",
            "passed": changes["change_count"] >= 4,
            "observed": changes["change_count"]
        },
        {
            "name": "patch_is_proposal_only",
            "passed": changes["auto_apply"] is False and changes["review_required"] is True,
            "observed": {"auto_apply": changes["auto_apply"], "review_required": changes["review_required"]}
        },
        {
            "name": "diff_contains_auth_and_profile_changes",
            "passed": "authenticate(process.env.AUTH_CLIENT_ID!" in patch_text and "getUserProfile" in patch_text,
            "observed": "checked patch text"
        },
        {
            "name": "patch_risk_blocks_autonomous_apply",
            "passed": risk["patch_apply_recommendation"] == "DO_NOT_APPLY_WITHOUT_REVIEW",
            "observed": risk["patch_apply_recommendation"]
        },
        {
            "name": "before_tests_pass",
            "passed": before["status"] == "pass",
            "observed": before["status"]
        },
        {
            "name": "after_patch_review_blocked",
            "passed": after["status"] == "review_blocked" and after["patch_applied_to_source_repo"] is False,
            "observed": {"status": after["status"], "patch_applied": after["patch_applied_to_source_repo"]}
        },
        {
            "name": "triage_has_actionable_root_causes",
            "passed": len(triage["root_causes"]) >= 2 and triage["triage_status"] == "review_required",
            "observed": {"root_causes": len(triage["root_causes"]), "triage_status": triage["triage_status"]}
        },
        {
            "name": "pr_body_truth_boundary_present",
            "passed": "not a real GitHub PR" in pr_body and "Do not merge automatically" in pr_body,
            "observed": "checked pr body"
        },
        {
            "name": "summary_pass",
            "passed": summary["status"] == "pass",
            "observed": summary["status"]
        }
    ]

    status = "pass" if all(c["passed"] for c in checks) else "fail"

    payload = {
        "artifact": "patch_pr_simulation_validation_v35",
        "status": status,
        "check_count": len(checks),
        "passed_count": sum(c["passed"] for c in checks),
        "checks": checks,
        "evidence_statement": "Validates DevPulse v3.5 patch proposal, test simulation, failure triage, and PR-ready migration bundle."
    }

    out = Path("outputs/validation/patch_pr_simulation_validation_v35.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("patch_pr_simulation_validation_v35 complete")
    print(f"status: {status}")
    print(f"passed_count: {payload['passed_count']}/{payload['check_count']}")
    print(f"wrote {out}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
