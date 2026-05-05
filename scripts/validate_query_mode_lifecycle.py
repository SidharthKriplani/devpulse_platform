from __future__ import annotations

import json
from pathlib import Path


REQUIRED_ARTIFACTS = [
    "ingest_summary.json",
    "chunk_metadata_sample.json",
    "bm25_index_stats.txt",
    "pgvector_index_stats.txt",
    "version_coverage_matrix.json",
    "simple_query_results.json",
    "hybrid_retrieval_report.json",
    "version_filter_audit.json",
    "retrieval_traces_sample.json",
    "conflict_detection_report.json",
    "conflict_alerts_schema.sql",
    "migration_decision_samples.json",
    "synthesis_grounding_report.json",
    "citation_assembly_sample.json",
    "golden_eval_results.json",
    "adversarial_trap_results.json",
    "query_audit_log_sample.json",
    "fallback_events_log.json",
    "freshness_report.json",
    "embedding_swap_log.txt",
    "langfuse_trace_export.json",
    "sentry_error_summary.txt",
    "cost_latency_report.json",
    "devpulse_demo_report.txt",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    evidence_dir = Path("outputs/evidence")
    validation_dir = Path("outputs/validation")

    artifact_checks = []
    for name in REQUIRED_ARTIFACTS:
        p = evidence_dir / name
        artifact_checks.append({
            "name": name,
            "passed": p.exists() and p.stat().st_size > 0,
            "observed": str(p)
        })

    golden = load_json(evidence_dir / "golden_eval_results.json")
    version_audit = load_json(evidence_dir / "version_filter_audit.json")
    conflict = load_json(evidence_dir / "conflict_detection_report.json")
    failure = load_json(evidence_dir / "query_mode_failure_scenarios_f01_f10.json")
    migration = load_json(evidence_dir / "migration_decision_samples.json")

    semantic_checks = [
        {
            "name": "ea_01_to_ea_24_present",
            "passed": all(c["passed"] for c in artifact_checks),
            "observed": f"{sum(c['passed'] for c in artifact_checks)}/24"
        },
        {
            "name": "wrong_version_answer_rate_zero",
            "passed": version_audit["wrong_version_answer_rate"] == 0.0,
            "observed": version_audit["wrong_version_answer_rate"]
        },
        {
            "name": "golden_eval_pass",
            "passed": golden["status"] == "pass",
            "observed": golden["status"]
        },
        {
            "name": "all_9_conflict_types_covered",
            "passed": conflict["conflict_type_count"] == 9,
            "observed": conflict["conflict_type_count"]
        },
        {
            "name": "f01_to_f10_covered",
            "passed": failure["scenario_count"] == 10,
            "observed": failure["scenario_count"]
        },
        {
            "name": "safe_risky_blocked_decision_samples",
            "passed": set(["SAFE", "RISKY", "BLOCKED"]).issubset(set(migration["verdicts_seen"])),
            "observed": migration["verdicts_seen"]
        }
    ]

    checks = artifact_checks + semantic_checks
    status = "pass" if all(c["passed"] for c in checks) else "fail"

    payload = {
        "artifact": "query_mode_lifecycle_validation",
        "status": status,
        "check_count": len(checks),
        "passed_count": sum(c["passed"] for c in checks),
        "checks": checks,
        "evidence_statement": "Validates DevPulse Query Mode EA-01 to EA-24, F-01 to F-10, golden eval, version correctness, conflict coverage, and verdict coverage."
    }

    out_path = validation_dir / "query_mode_lifecycle_validation.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("query_mode_lifecycle_validation complete")
    print(f"status: {status}")
    print(f"passed_count: {payload['passed_count']}/{payload['check_count']}")
    print(f"wrote {out_path}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
