from __future__ import annotations

import json
from pathlib import Path

from src.devpulse.core.query_mode import result_to_dict, run_query, write_json


PROBE_QUERIES = [
    "How does authenticate work in v3?",
    "What changed in authenticate from v2 to v3?",
    "Is fetchUser safe to use in v3?",
    "What is the rateLimit in v2?",
    "Is logging safe to use in v3?",
    "How should I migrate fetchUser from v2 to v3?"
]


def main() -> None:
    results = [result_to_dict(run_query(q)) for q in PROBE_QUERIES]

    verdicts = [r["migration_report"]["verdict"] for r in results]
    routes = [r["route_taken"] for r in results]
    conflict_types = sorted({
        alert["conflict_type"]
        for r in results
        for alert in r["conflict_alerts"]
    })

    payload = {
        "artifact": "query_mode_core_probe",
        "query_count": len(results),
        "routes_seen": sorted(set(routes)),
        "verdicts_seen": sorted(set(verdicts)),
        "conflict_types_seen": conflict_types,
        "blocked_count": verdicts.count("BLOCKED"),
        "risky_count": verdicts.count("RISKY"),
        "safe_count": verdicts.count("SAFE"),
        "results": results,
        "evidence_statement": "DevPulse Query Mode core can parse queries, extract versions, route requests, retrieve version-filtered evidence, detect deterministic conflicts, assemble citations, suppress synthesis for BLOCKED verdicts, and emit migration decision reports."
    }

    write_json("outputs/evidence/query_mode_core_probe.json", payload)

    print("query_mode_core_probe complete")
    print(f"query_count: {payload['query_count']}")
    print(f"routes_seen: {payload['routes_seen']}")
    print(f"verdicts_seen: {payload['verdicts_seen']}")
    print(f"conflict_types_seen: {payload['conflict_types_seen']}")
    print("wrote outputs/evidence/query_mode_core_probe.json")


if __name__ == "__main__":
    main()
