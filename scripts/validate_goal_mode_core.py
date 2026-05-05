from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    path = Path("outputs/evidence/goal_mode_core_probe.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    deltas = data["dependency_delta_report"]
    tasks = data["agent_task_plan"]
    runs = data["agent_task_execution_trace"]
    recoveries = data["recovery_decision_log"]
    plan = data["plan_summary_report"]

    statuses = {r["final_status"] for r in runs}
    recovery_actions = {r["recovery_action"] for r in recoveries}

    checks = [
        {
            "name": "six_agentic_components_present",
            "passed": data["component_count"] == 6,
            "observed": data["components"]
        },
        {
            "name": "goal_parser_extracts_five_dependencies",
            "passed": len(data["agent_goal"]["dependency_list"]) == 5,
            "observed": len(data["agent_goal"]["dependency_list"])
        },
        {
            "name": "delta_detector_covers_major_patch_unknown",
            "passed": {"major", "patch", "unknown"}.issubset({d["version_delta_type"] for d in deltas}),
            "observed": sorted({d["version_delta_type"] for d in deltas})
        },
        {
            "name": "target_versions_use_controlled_registry",
            "passed": all(
                d["target_source"] == "controlled_demo_registry"
                for d in deltas
                if d["version_status"] == "resolved"
            ),
            "observed": sorted({str(d["target_source"]) for d in deltas})
        },
        {
            "name": "task_plan_ordered_by_priority",
            "passed": [t["priority"] for t in tasks] == sorted(t["priority"] for t in tasks),
            "observed": [t["priority"] for t in tasks]
        },
        {
            "name": "task_executor_links_query_ids",
            "passed": all(r["query_id"].startswith("query_") for r in runs),
            "observed": [r["query_id"] for r in runs]
        },
        {
            "name": "safe_risky_blocked_statuses_seen",
            "passed": {"safe", "risky", "blocked"}.issubset(statuses),
            "observed": sorted(statuses)
        },
        {
            "name": "recovery_decider_has_escalation_and_retry",
            "passed": {"skip_and_escalate", "retry_with_related_version_evidence"}.issubset(recovery_actions),
            "observed": sorted(recovery_actions)
        },
        {
            "name": "retry_cap_respected",
            "passed": all(r["retry_count"] <= 2 for r in runs),
            "observed": [r["retry_count"] for r in runs]
        },
        {
            "name": "plan_summary_blocks_critical_goal",
            "passed": plan["aggregate_verdict"] == "BLOCKED" and plan["recommended_action"] == "Do not proceed",
            "observed": {"aggregate_verdict": plan["aggregate_verdict"], "recommended_action": plan["recommended_action"]}
        },
        {
            "name": "staged_recommendation_present",
            "passed": all(
                k in plan["staged_recommendation"]
                for k in [
                    "safe_tasks_can_proceed_independently",
                    "risky_tasks_require_caveats_and_reviewer_approval",
                    "blocked_or_escalated_tasks_block_full_migration"
                ]
            ),
            "observed": plan["staged_recommendation"]
        }
    ]

    status = "pass" if all(c["passed"] for c in checks) else "fail"

    payload = {
        "artifact": "goal_mode_core_validation",
        "status": status,
        "check_count": len(checks),
        "passed_count": sum(c["passed"] for c in checks),
        "checks": checks,
        "evidence_statement": "Validates DevPulse Goal Mode core: 6 agentic components, controlled target registry, deterministic task planning, Query Mode task execution, bounded recovery, and aggregate plan summary."
    }

    out_path = Path("outputs/validation/goal_mode_core_validation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("goal_mode_core_validation complete")
    print(f"status: {status}")
    print(f"passed_count: {payload['passed_count']}/{payload['check_count']}")
    print(f"wrote {out_path}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
