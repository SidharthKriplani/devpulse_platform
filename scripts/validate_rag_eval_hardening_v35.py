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
        "outputs/rag_eval/retrieval_ablation_report.json",
        "outputs/rag_eval/reranker_simulation_report.json",
        "outputs/rag_eval/conflict_confusion_matrix.json",
        "outputs/rag_eval/traffic_backtest_37_day_report.json",
        "outputs/rag_eval/corpus_perturbation_report.json",
        "outputs/rag_eval/rag_eval_hardening_summary_v35.json"
    ]

    ablation = load("outputs/rag_eval/retrieval_ablation_report.json")
    reranker = load("outputs/rag_eval/reranker_simulation_report.json")
    conflict = load("outputs/rag_eval/conflict_confusion_matrix.json")
    backtest = load("outputs/rag_eval/traffic_backtest_37_day_report.json")
    perturbation = load("outputs/rag_eval/corpus_perturbation_report.json")
    summary = load("outputs/rag_eval/rag_eval_hardening_summary_v35.json")

    bm25 = ablation["ablation"]["bm25_only"]
    vector = ablation["ablation"]["vector_only"]
    hybrid = ablation["ablation"]["hybrid_rrf_with_version_filter"]
    reranked = reranker["hybrid_plus_reranker"]

    checks = [
        {
            "name": "required_artifacts_present",
            "passed": all(exists_nonempty(p) for p in required),
            "observed": required
        },
        {
            "name": "eval_query_count_large_enough",
            "passed": ablation["eval_query_count"] >= 150,
            "observed": ablation["eval_query_count"]
        },
        {
            "name": "hybrid_beats_bm25_and_vector",
            "passed": hybrid["recall_at_5"] > bm25["recall_at_5"] and hybrid["recall_at_5"] > vector["recall_at_5"],
            "observed": {"bm25": bm25["recall_at_5"], "vector": vector["recall_at_5"], "hybrid": hybrid["recall_at_5"]}
        },
        {
            "name": "wrong_version_answer_rate_zero",
            "passed": ablation["query_mode_wrong_version_answer_rate"] == 0.0 and backtest["wrong_version_answer_rate"] == 0.0,
            "observed": {"eval": ablation["query_mode_wrong_version_answer_rate"], "backtest": backtest["wrong_version_answer_rate"]}
        },
        {
            "name": "reranker_improves_precision_or_recall",
            "passed": reranked["recall_at_5"] >= hybrid["recall_at_5"] and reranked["precision_at_5"] >= hybrid["precision_at_5"],
            "observed": {"hybrid": hybrid, "reranked": reranked}
        },
        {
            "name": "conflict_macro_f1_gate",
            "passed": conflict["macro_f1"] >= 0.90 and conflict["status"] == "pass",
            "observed": conflict["macro_f1"]
        },
        {
            "name": "backtest_37_days",
            "passed": backtest["day_count"] == 37 and backtest["status"] == "pass",
            "observed": {"days": backtest["day_count"], "status": backtest["status"]}
        },
        {
            "name": "backtest_has_substantial_query_volume",
            "passed": backtest["total_queries"] >= 2000,
            "observed": backtest["total_queries"]
        },
        {
            "name": "perturbation_tests_pass",
            "passed": perturbation["status"] == "pass" and perturbation["passed_count"] == perturbation["perturbation_count"],
            "observed": {"status": perturbation["status"], "passed": perturbation["passed_count"], "total": perturbation["perturbation_count"]}
        },
        {
            "name": "summary_pass",
            "passed": summary["status"] == "pass",
            "observed": summary["status"]
        }
    ]

    status = "pass" if all(c["passed"] for c in checks) else "fail"

    payload = {
        "artifact": "rag_eval_hardening_validation_v35",
        "status": status,
        "check_count": len(checks),
        "passed_count": sum(c["passed"] for c in checks),
        "checks": checks,
        "evidence_statement": "Validates DevPulse v3.5 RAG eval hardening: large eval set, retrieval ablation, reranker simulation, zero wrong-version rate, conflict F1, 37-day backtest, and corpus perturbation robustness."
    }

    out = Path("outputs/validation/rag_eval_hardening_validation_v35.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("rag_eval_hardening_validation_v35 complete")
    print(f"status: {status}")
    print(f"passed_count: {payload['passed_count']}/{payload['check_count']}")
    print(f"wrote {out}")

    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
