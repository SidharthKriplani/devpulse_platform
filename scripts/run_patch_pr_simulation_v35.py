from __future__ import annotations

import difflib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SAMPLE_REPO = Path("sample_repos/checkout_app")
PATCH_DIR = Path("outputs/patches")
TEST_DIR = Path("outputs/test_simulation")
PR_DIR = Path("outputs/pr_simulation")
REPORT_DIR = Path("outputs/reports")
REPO_AWARE_DIR = Path("outputs/repo_aware")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def unified_diff(path: Path, before: str, after: str) -> str:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm=""
        )
    )


def propose_file_changes() -> tuple[list[dict[str, Any]], str]:
    targets = [
        SAMPLE_REPO / "src" / "auth.ts",
        SAMPLE_REPO / "src" / "profile.ts",
        SAMPLE_REPO / "src" / "logging.ts",
        SAMPLE_REPO / "package.json",
    ]

    changes: list[dict[str, Any]] = []
    patch_parts: list[str] = []

    auth_path = targets[0]
    auth_before = read_text(auth_path)
    auth_after = auth_before.replace(
        'import { authenticate } from "auth-sdk";',
        'import { authenticate } from "auth-sdk";'
    ).replace(
        'const session = await authenticate(apiKey);',
        'const session = await authenticate(process.env.AUTH_CLIENT_ID!, process.env.AUTH_CLIENT_SECRET!);'
    )
    changes.append({
        "file_path": str(auth_path),
        "dependency_name": "auth-sdk",
        "change_type": "candidate_signature_migration",
        "before_snippet": "authenticate(apiKey)",
        "after_snippet": "authenticate(process.env.AUTH_CLIENT_ID!, process.env.AUTH_CLIENT_SECRET!)",
        "review_required": True,
        "risk_reason": "auth-sdk is a major migration and was escalated by DevPulse; patch is proposal-only."
    })
    patch_parts.append(unified_diff(auth_path, auth_before, auth_after))

    profile_path = targets[1]
    profile_before = read_text(profile_path)
    profile_after = profile_before.replace(
        'import { fetchUser } from "profile-sdk";',
        'import { getUserProfile } from "profile-sdk";'
    ).replace(
        'const profile = await fetchUser(userId);',
        'const profile = await getUserProfile(userId);'
    )
    changes.append({
        "file_path": str(profile_path),
        "dependency_name": "profile-sdk",
        "change_type": "candidate_replacement_api_migration",
        "before_snippet": "fetchUser(userId)",
        "after_snippet": "getUserProfile(userId)",
        "review_required": True,
        "risk_reason": "profile-sdk is a major migration and was escalated by DevPulse; patch is proposal-only."
    })
    patch_parts.append(unified_diff(profile_path, profile_before, profile_after))

    logging_path = targets[2]
    logging_before = read_text(logging_path)
    logging_after = logging_before.replace(
        'logger.info(eventName, payload);',
        'logger.info({ eventName, payload, schemaVersion: "v3-migration-review" });'
    )
    changes.append({
        "file_path": str(logging_path),
        "dependency_name": "logging-lib",
        "change_type": "candidate_structured_logging_payload",
        "before_snippet": "logger.info(eventName, payload)",
        "after_snippet": "logger.info({ eventName, payload, schemaVersion: \"v3-migration-review\" })",
        "review_required": True,
        "risk_reason": "logging-lib was classified as RISKY due stale/limited evidence; patch requires reviewer validation."
    })
    patch_parts.append(unified_diff(logging_path, logging_before, logging_after))

    package_path = targets[3]
    package_before = read_text(package_path)
    package_payload = json.loads(package_before)
    package_payload["dependencies"]["analytics-sdk"] = "1.2.3"
    package_payload["dependencies"]["auth-sdk"] = "3.0.0"
    package_payload["dependencies"]["profile-sdk"] = "3.0.0"
    package_payload["dependencies"]["logging-lib"] = "1.0.0"
    package_after = json.dumps(package_payload, indent=2) + "\n"
    changes.append({
        "file_path": str(package_path),
        "dependency_name": "multiple",
        "change_type": "candidate_manifest_version_bump",
        "before_snippet": "old dependency versions",
        "after_snippet": "controlled target versions from dependency_target_registry.json",
        "review_required": True,
        "risk_reason": "manifest bump is bundled with code changes but must not be merged while aggregate readiness is BLOCKED."
    })
    patch_parts.append(unified_diff(package_path, package_before, package_after))

    return changes, "\n".join(part for part in patch_parts if part.strip()) + "\n"


def main() -> None:
    repo_report = load_json(REPO_AWARE_DIR / "repo_inspection_report.json")
    usage_map = load_json(REPO_AWARE_DIR / "dependency_usage_map.json")
    risky_report = load_json(REPO_AWARE_DIR / "risky_callsite_report.json")

    changes, patch_text = propose_file_changes()

    proposed_file_changes = {
        "artifact": "proposed_file_changes_v35",
        "generated_at": now_iso(),
        "change_count": len(changes),
        "apply_mode": "proposal_only",
        "auto_apply": False,
        "review_required": True,
        "source_artifacts": [
            "outputs/repo_aware/repo_inspection_report.json",
            "outputs/repo_aware/dependency_usage_map.json",
            "outputs/repo_aware/risky_callsite_report.json",
            "outputs/evidence/plan_summary_report.json"
        ],
        "changes": changes,
        "truth_boundary": {
            "claim": "local patch proposal package generated from repo-aware risk evidence",
            "not_claimed": [
                "patch applied to production",
                "real GitHub PR opened",
                "tests executed against real CI",
                "autonomous merge approval"
            ]
        },
        "evidence_statement": "DevPulse generated reviewer-safe candidate file changes without mutating the source repo."
    }

    patch_risk_report = {
        "artifact": "patch_risk_report_v35",
        "generated_at": now_iso(),
        "repo_migration_readiness": repo_report["aggregate_repo_migration_readiness"],
        "patch_apply_recommendation": "DO_NOT_APPLY_WITHOUT_REVIEW",
        "reason": "Repo-aware scan found high-risk dependencies and all risky callsites require reviewer attention.",
        "risk_summary": {
            "callsites_found": repo_report["callsites_found"],
            "risky_callsite_count": risky_report["risky_callsite_count"],
            "high_risk_dependencies": repo_report["high_risk_dependencies"],
            "medium_risk_dependencies": repo_report["medium_risk_dependencies"],
            "low_risk_dependencies": repo_report["low_risk_dependencies"]
        },
        "review_gates": [
            "Confirm auth-sdk v3 authenticate signature and credential source.",
            "Confirm profile-sdk replacement API getUserProfile is correct.",
            "Confirm logging-lib structured payload shape against current docs.",
            "Run real package install and test suite before merge.",
            "Do not merge while aggregate repo readiness is BLOCKED."
        ],
        "safe_tasks_can_proceed": ["analytics-sdk manifest patch candidate"],
        "blocked_tasks": repo_report["high_risk_dependencies"],
        "evidence_statement": "Patch risk report keeps the extension honest: DevPulse proposes changes but blocks autonomous application when critical migration risk remains."
    }

    before_tests = {
        "artifact": "before_tests_report_v35",
        "generated_at": now_iso(),
        "mode": "simulated_local_test_report",
        "test_command": "npm test",
        "test_environment": "sample_repos/checkout_app",
        "status": "pass",
        "tests_total": 1,
        "tests_passed": 1,
        "tests_failed": 0,
        "notes": [
            "Baseline sample test confirms existing checkout analytics function is callable.",
            "This is a controlled local simulation, not a real CI run."
        ]
    }

    after_tests = {
        "artifact": "after_patch_tests_report_v35",
        "generated_at": now_iso(),
        "mode": "simulated_after_patch_validation",
        "patch_applied_to_source_repo": False,
        "patch_evaluated_as_preview": True,
        "status": "review_blocked",
        "tests_total": 3,
        "tests_passed": 1,
        "tests_failed": 2,
        "failed_checks": [
            {
                "check": "auth_sdk_runtime_credentials",
                "reason": "candidate patch requires AUTH_CLIENT_ID and AUTH_CLIENT_SECRET; reviewer must validate runtime config."
            },
            {
                "check": "profile_sdk_replacement_api",
                "reason": "getUserProfile replacement is inferred from controlled docs; reviewer must verify actual SDK export."
            }
        ],
        "passed_checks": [
            "analytics-sdk patch candidate remains low risk"
        ],
        "evidence_statement": "After-patch simulation intentionally blocks merge because high-risk migration changes need human review."
    }

    triage = {
        "artifact": "test_failure_triage_report_v35",
        "generated_at": now_iso(),
        "triage_status": "review_required",
        "root_causes": [
            {
                "dependency_name": "auth-sdk",
                "failure_category": "runtime_configuration_gap",
                "triage": "Need confirmed credential source and environment variable setup before applying authenticate signature change."
            },
            {
                "dependency_name": "profile-sdk",
                "failure_category": "replacement_api_verification",
                "triage": "Need reviewer or real SDK typecheck to confirm getUserProfile export and return contract."
            }
        ],
        "recommended_next_actions": [
            "Open PR-ready package for review, not merge.",
            "Ask SDK owner to confirm v3 auth signature.",
            "Run real npm install and typecheck in a live development environment.",
            "Apply analytics-sdk patch separately if reviewer accepts staged migration."
        ],
        "evidence_statement": "DevPulse simulated the verify loop and produced actionable failure triage instead of pretending patch success."
    }

    write_json(PATCH_DIR / "proposed_file_changes.json", proposed_file_changes)
    write_text(PATCH_DIR / "proposed_migration_patch.diff", patch_text)
    write_json(REPORT_DIR / "patch_risk_report.json", patch_risk_report)
    write_json(TEST_DIR / "before_tests_report.json", before_tests)
    write_json(TEST_DIR / "after_patch_tests_report.json", after_tests)
    write_json(TEST_DIR / "test_failure_triage_report.json", triage)

    pr_title = "DevPulse simulated migration package: SDK v2 to v3 reviewer-safe proposal"
    pr_body = f"""# DevPulse PR-Ready Migration Simulation

## Summary

This is a simulated PR-ready migration package generated by DevPulse v3.5.

It proposes candidate changes for the local sample repo, but does not claim real GitHub PR creation, production execution, or autonomous merge safety.

## Repo Readiness

- Repo migration readiness: {repo_report["aggregate_repo_migration_readiness"]}
- Risky callsites: {risky_report["risky_callsite_count"]}
- High-risk dependencies: {", ".join(repo_report["high_risk_dependencies"])}
- Medium-risk dependencies: {", ".join(repo_report["medium_risk_dependencies"])}

## Proposed Changes

- auth-sdk: candidate authenticate signature migration
- profile-sdk: candidate fetchUser to getUserProfile replacement
- logging-lib: candidate structured logging payload
- package.json: candidate target version bump from controlled demo registry

## Review Required

Do not merge automatically.

Reviewer gates:

1. Confirm auth-sdk v3 authenticate signature.
2. Confirm credential source and runtime environment variables.
3. Confirm profile-sdk replacement API and return contract.
4. Confirm logging-lib payload schema.
5. Run real install, typecheck, and test suite.

## Truth Boundary

This is a local PR simulation artifact. It is not a real GitHub PR, not a production patch, and not a live CI result.
"""
    reviewer_checklist = """# Reviewer Checklist

- [ ] Confirm auth-sdk target version and authenticate signature.
- [ ] Confirm AUTH_CLIENT_ID / AUTH_CLIENT_SECRET runtime configuration.
- [ ] Confirm profile-sdk replacement API: getUserProfile.
- [ ] Confirm logging-lib structured payload format.
- [ ] Confirm analytics-sdk patch can proceed independently.
- [ ] Run real npm install.
- [ ] Run real typecheck.
- [ ] Run real test suite.
- [ ] Confirm rollback path.
- [ ] Approve staged migration only after high-risk blockers are resolved.
"""

    rollback_plan = """# Rollback Plan

## Scope

This rollback plan applies to the simulated DevPulse migration package.

## Rollback Steps

1. Revert package.json dependency version bumps.
2. Revert auth-sdk authenticate signature change.
3. Revert profile-sdk getUserProfile replacement.
4. Revert logging payload shape change.
5. Reinstall previous dependency lockfile.
6. Run test suite.
7. Confirm checkout login/profile/logging flows return to baseline behavior.

## Rollback Trigger

Rollback immediately if:

- auth login fails
- profile loading fails
- logging ingestion rejects payloads
- typecheck fails on SDK imports
- any critical checkout path regresses

## Truth Boundary

This is a generated rollback plan for a controlled local simulation, not an executed production rollback.
"""

    write_text(PR_DIR / "pr_title.txt", pr_title + "\n")
    write_text(PR_DIR / "pr_body.md", pr_body)
    write_text(PR_DIR / "pr_diff.patch", patch_text)
    write_text(PR_DIR / "reviewer_checklist.md", reviewer_checklist)
    write_text(PR_DIR / "rollback_plan.md", rollback_plan)

    summary = {
        "artifact": "patch_pr_simulation_summary_v35",
        "status": "pass",
        "generated_at": now_iso(),
        "patch_change_count": len(changes),
        "patch_apply_recommendation": patch_risk_report["patch_apply_recommendation"],
        "before_test_status": before_tests["status"],
        "after_patch_status": after_tests["status"],
        "pr_bundle_artifacts": [
            "outputs/pr_simulation/pr_title.txt",
            "outputs/pr_simulation/pr_body.md",
            "outputs/pr_simulation/pr_diff.patch",
            "outputs/pr_simulation/reviewer_checklist.md",
            "outputs/pr_simulation/rollback_plan.md"
        ],
        "truth_boundary": {
            "claim": "PR-ready local migration simulation package",
            "not_claimed": [
                "real PR opened",
                "patch merged",
                "real CI passed",
                "production deployment"
            ]
        },
        "evidence_statement": "DevPulse generated a reviewer-safe patch proposal, simulated test/triage reports, and PR-ready package while blocking autonomous application."
    }

    write_json(REPORT_DIR / "patch_pr_simulation_summary_v35.json", summary)

    print("patch_pr_simulation_v35 complete")
    print(f"status: {summary['status']}")
    print(f"patch_change_count: {summary['patch_change_count']}")
    print(f"patch_apply_recommendation: {summary['patch_apply_recommendation']}")
    print(f"before_test_status: {summary['before_test_status']}")
    print(f"after_patch_status: {summary['after_patch_status']}")
    print("wrote outputs/patches/proposed_migration_patch.diff")
    print("wrote outputs/reports/patch_pr_simulation_summary_v35.json")


if __name__ == "__main__":
    main()
