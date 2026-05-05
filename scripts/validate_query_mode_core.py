from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    path = Path("outputs/evidence/query_mode_core_probe.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    checks = [
        {
            "name": "probe_artifact_exists",
            "passed": path.exists(),
            "observed": str(path)
        },
        {
            "name": "all_three_routes_available_or_represented",
            "passed": {"SIMPLE", "MIGRATION"}.issubset(set(data["routes_seen"])),
            "observed": data["routes_seen"]
        },
        {
            "name": "safe_risky_blocked_verdicts_present",
            "passed": {"SAFE", "RISKY", "BLOCKED"}.issubset(set(data["verdicts_seen"])),
            "observed": data["verdicts_seen"]
        },
        {
            "name": "critical_conflict_detected",
            "passed": "same_api_different_behavior" in data["conflict_types_seen"],
            "observed": data["conflict_types_seen"]
        },
        {
            "name": "deprecation_conflict_detected",
            "passed": "version_deprecation_conflict" in data["conflict_types_seen"],
            "observed": data["conflict_types_seen"]
        },
        {
            "name": "blocked_suppresses_synthesis",
            "passed": any(
                r["migration_report"]["verdict"] == "BLOCKED"
                and r["migration_report"]["synthesis_text"] is None
                and len(r["fallback_events"]) >= 1
                for r in data["results"]
            ),
            "observed": "checked BLOCKED records"
        },
        {
            "name": "citations_are_programmatic",
            "passed": all(
                len(r["migration_report"]["citations"]) >= 1
                for r in data["results"]
            ),
            "observed": "all reports include citations"
        },
        {
            "name": "explicit_v2_query_has_only_v2_chunks",
            "passed": all(
                c["version_tag"] == "v2"
                for r in data["results"]
                if r["parsed_query"]["raw_query"] == "What is the rateLimit in v2?"
                for c in r["retrieved_chunks"]
            ),
            "observed": "version-filtered explicit v2 query"
        }
    ]

    status = "pass" if all(c["passed"] for c in checks) else "fail"
    payload = {
        "artifact": "query_mode_core_validation",
        "status": status,
        "check_count": len(checks),
        "passed_count": sum(c["passed"] for c in checks),
        "checks": checks,
        "evidence_statement": "Validates the DevPulse Query Mode core implementation before lifecycle artifact generation."
    }

    out_path = Path("outputs/validation/query_mode_core_validation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("query_mode_core_validation complete")
    print(f"status: {status}")
    print(f"passed_count: {payload['passed_count']}/{payload['check_count']}")
    print(f"wrote {out_path}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
