from __future__ import annotations

from src.devpulse.agentic.goal_mode import run_goal_mode_probe, write_json


def main() -> None:
    payload = run_goal_mode_probe()
    write_json("outputs/evidence/goal_mode_core_probe.json", payload)

    plan = payload["plan_summary_report"]

    print("goal_mode_core_probe complete")
    print(f"components: {payload['component_count']}")
    print(f"dependencies: {len(payload['dependency_delta_report'])}")
    print(f"tasks: {len(payload['agent_task_plan'])}")
    print(f"task_runs: {len(payload['agent_task_execution_trace'])}")
    print(f"recoveries: {len(payload['recovery_decision_log'])}")
    print(f"aggregate_verdict: {plan['aggregate_verdict']}")
    print("wrote outputs/evidence/goal_mode_core_probe.json")


if __name__ == "__main__":
    main()
