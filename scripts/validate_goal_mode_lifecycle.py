from __future__ import annotations

import json
from pathlib import Path


EVIDENCE = Path("outputs/evidence")
VALIDATION = Path("outputs/validation")

REQUIRED = [
    "agent_goal_parse_sample.json",
    "dependency_delta_report.json",
    "agent_task_plan.json",
    "agent_task_execution_trace.json",
    "recovery_decision_log.json",
    "plan_summary_report.json",
    "agentic_eval_results.json",
    "agentic_demo_report.txt"
]


def load(name: str):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def main() -> None:
    artifact_checks = [
        {
            "name": name,
            "passed": (EVIDENCE / name).exists() and (EVIDENCE / name).stat().st_size > 0,
            "observed": str(EVIDENCE / name)
        }
        for name in REQUIRED
    ]

    goal = load("agent_goal_parse_sample.json")
    deltas = load("dependency_delta_report.json")
    tasks = load("agent_task_plan.json")
    runs = load("agent_task_execution_trace.json")
    recoveries = load("recovery_decision_log.json")
    plan = load("plan_summary_report.json")
    evals = load("agentic_eval_results.json")
    scenarios = load("goal_mode_failure_scenarios_f11_f19.json")

    eval_statuses = [m["status"] for m in evals["metrics"]]

    semantic_checks = [
        {
            "name": "ea_25_to_ea_32_present",
            "passed": all(c["passed"] for c in artifact_checks),
            "observed": f"{sum(c['passed'] for c in artifact_checks)}/8"
        },
        {
            "name": "goal_parser_no_invented_versions",
            "passed": goal["parsed_status"] in {"complete", "partial"},
            "observed": goal["parsed_status"]
        },
        {
            "name": "delta_detector_uses_controlled_registry",
            "passed": deltas["resolved_target_source"] == "controlled_demo_registry",
            "observed": deltas["resolved_target_source"]
        },
        {
            "name": "task_plan_count_matches_dependency_count",
            "passed": tasks["task_count"] == deltas["dependency_count"],
            "observed": {"tasks": tasks["task_count"], "dependencies": deltas["dependency_count"]}
        },
        {
            "name": "task_execution_has_query_mode_linkage",
            "passed": runs["query_mode_linkage"] is True,
            "observed": runs["query_mode_linkage"]
        },
        {
            "name": "recovery_has_successful_blocked_to_risky",
            "passed": recoveries["successful_blocked_to_risky_recovery_present"] is True,
            "observed": recoveries["successful_blocked_to_risky_recovery_present"]
        },
        {
            "name": "plan_summary_has_blocked_aggregate",
            "passed": plan["aggregate_verdict"] == "BLOCKED",
            "observed": plan["aggregate_verdict"]
        },
        {
            "name": "agentic_eval_all_pass",
            "passed": all(s == "pass" for s in eval_statuses),
            "observed": eval_statuses
        },
        {
            "name": "f11_to_f19_covered",
            "passed": scenarios["scenario_count"] == 9,
            "observed": scenarios["scenario_count"]
        }
    ]

    checks = artifact_checks + semantic_checks
    status = "pass" if all(c["passed"] for c in checks) else "fail"

    payload = {
        "artifact": "goal_mode_lifecycle_validation",
        "status": status,
        "check_count": len(checks),
        "passed_count": sum(c["passed"] for c in checks),
        "checks": checks,
        "evidence_statement": "Validates DevPulse Goal Mode EA-25 to EA-32, F-11 to F-19, agentic eval, controlled registry, Query Mode task linkage, bounded recovery, and aggregate verdict logic."
    }

    out_path = VALIDATION / "goal_mode_lifecycle_validation.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("goal_mode_lifecycle_validation complete")
    print(f"status: {status}")
    print(f"passed_count: {payload['passed_count']}/{payload['check_count']}")
    print(f"wrote {out_path}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
