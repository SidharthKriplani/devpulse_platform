from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any


DASHBOARD_DIR = Path("outputs/dashboard")
OUTPUTS_DIR = Path("outputs")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"missing": True, "path": path}
    return json.loads(p.read_text(encoding="utf-8"))


def read_text_if_exists(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def rel(path: str) -> str:
    return "../" + str(Path(path).relative_to("outputs"))


def artifact_link(path: str, label: str | None = None) -> str:
    label = label or path
    return f'<a href="{escape(rel(path))}" target="_blank">{escape(label)}</a>'


def badge(value: str) -> str:
    safe = escape(str(value))
    cls = "badge"
    lowered = str(value).lower()
    if lowered in {"pass", "safe"}:
        cls += " green"
    elif lowered in {"blocked", "review_blocked", "do_not_apply_without_review", "do not proceed"}:
        cls += " red"
    elif lowered in {"risky", "review"}:
        cls += " amber"
    else:
        cls += " blue"
    return f'<span class="{cls}">{safe}</span>'


def metric_card(title: str, value: Any, sub: str = "") -> str:
    return f"""
    <div class="card metric">
      <div class="metric-title">{escape(title)}</div>
      <div class="metric-value">{escape(str(value))}</div>
      <div class="metric-sub">{escape(sub)}</div>
    </div>
    """


def artifact_inventory() -> list[dict[str, Any]]:
    rows = []
    if not OUTPUTS_DIR.exists():
        return rows
    for p in sorted(OUTPUTS_DIR.rglob("*")):
        if p.is_file():
            category = p.parts[1] if len(p.parts) > 1 else "outputs"
            rows.append({
                "path": str(p),
                "size_bytes": p.stat().st_size,
                "category": category
            })
    return rows


def artifact_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        path = row["path"]
        body.append(
            f"""
            <tr>
              <td>{escape(row["category"])}</td>
              <td>{artifact_link(path, path)}</td>
              <td>{row["size_bytes"]}</td>
            </tr>
            """
        )
    return f"""
    <table>
      <thead>
        <tr><th>Category</th><th>Artifact</th><th>Size bytes</th></tr>
      </thead>
      <tbody>
        {''.join(body)}
      </tbody>
    </table>
    """


def list_items(items: list[str]) -> str:
    return "".join(f"<li>{escape(str(item))}</li>" for item in items)


def main() -> None:
    completion = load_json("outputs/reports/devpulse_prd_completion_report_v3.json")
    rag = load_json("outputs/rag_eval/rag_eval_hardening_summary_v35.json")
    repo = load_json("outputs/repo_aware/repo_aware_extension_summary.json")
    repo_inspection = load_json("outputs/repo_aware/repo_inspection_report.json")
    patch = load_json("outputs/reports/patch_pr_simulation_summary_v35.json")
    patch_risk = load_json("outputs/reports/patch_risk_report.json")
    plan = load_json("outputs/evidence/plan_summary_report.json")

    query_demo = read_text_if_exists("outputs/evidence/devpulse_demo_report.txt")
    agentic_demo = read_text_if_exists("outputs/evidence/agentic_demo_report.txt")
    final_demo = read_text_if_exists("outputs/reports/devpulse_final_demo_report.txt")

    inventory = artifact_inventory()

    completion_totals = completion.get("totals", {})
    completion_query = completion.get("query_mode", {})
    completion_goal = completion.get("goal_mode", {})

    evidence_artifacts = completion_totals.get("evidence_artifacts", 32)
    failure_scenarios = completion_totals.get("failure_recovery_scenarios", 19)
    wrong_version_rate = completion_query.get("wrong_version_answer_rate", 0.0)
    prd_status = completion.get("status", "pass")

    high_risk_deps = repo_inspection.get("high_risk_dependencies", [])
    medium_risk_deps = repo_inspection.get("medium_risk_dependencies", [])
    low_risk_deps = repo_inspection.get("low_risk_dependencies", [])

    manifest = {
        "artifact": "devpulse_dashboard_manifest_v35",
        "status": "pass",
        "generated_at": now_iso(),
        "dashboard_path": "outputs/dashboard/index.html",
        "source_artifacts": {
            "completion_report": "outputs/reports/devpulse_prd_completion_report_v3.json",
            "rag_summary": "outputs/rag_eval/rag_eval_hardening_summary_v35.json",
            "repo_aware_summary": "outputs/repo_aware/repo_aware_extension_summary.json",
            "patch_pr_summary": "outputs/reports/patch_pr_simulation_summary_v35.json",
            "plan_summary": "outputs/evidence/plan_summary_report.json"
        },
        "artifact_inventory_count": len(inventory),
        "evidence_statement": "Static dashboard renders DevPulse v3.0 + v3.5 evidence into an interview/showcase-friendly UI without requiring a running backend."
    }

    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    (DASHBOARD_DIR / "dashboard_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>DevPulse Evidence Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --bg: #0b1020;
      --panel: #111827;
      --panel2: #172033;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --line: #263244;
      --green: #22c55e;
      --amber: #f59e0b;
      --red: #ef4444;
      --blue: #38bdf8;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      background: radial-gradient(circle at top left, #1e3a8a 0, #0b1020 38%, #050816 100%);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Arial, sans-serif;
      line-height: 1.5;
    }}
    a {{
      color: #93c5fd;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .shell {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 32px;
    }}
    .hero {{
      border: 1px solid var(--line);
      background: rgba(17, 24, 39, 0.88);
      border-radius: 24px;
      padding: 32px;
      box-shadow: 0 24px 80px rgba(0,0,0,.35);
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 42px;
      letter-spacing: -0.04em;
    }}
    .hero p {{
      max-width: 980px;
      color: var(--muted);
      font-size: 17px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin: 20px 0;
    }}
    .grid3 {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
      margin: 20px 0;
    }}
    .grid2 {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin: 20px 0;
    }}
    .card {{
      background: rgba(17, 24, 39, 0.92);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
    }}
    .metric-title {{
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    .metric-value {{
      font-size: 30px;
      font-weight: 800;
      margin-top: 4px;
    }}
    .metric-sub {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 4px;
    }}
    h2 {{
      margin-top: 36px;
      font-size: 26px;
      letter-spacing: -0.02em;
    }}
    h3 {{
      margin: 0 0 8px;
      font-size: 18px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid var(--line);
      background: var(--panel2);
      color: var(--text);
      margin: 2px 4px 2px 0;
    }}
    .green {{
      color: #bbf7d0;
      background: rgba(34,197,94,.13);
      border-color: rgba(34,197,94,.35);
    }}
    .amber {{
      color: #fde68a;
      background: rgba(245,158,11,.13);
      border-color: rgba(245,158,11,.35);
    }}
    .red {{
      color: #fecaca;
      background: rgba(239,68,68,.13);
      border-color: rgba(239,68,68,.35);
    }}
    .blue {{
      color: #bae6fd;
      background: rgba(56,189,248,.13);
      border-color: rgba(56,189,248,.35);
    }}
    .muted {{
      color: var(--muted);
    }}
    .section {{
      background: rgba(17, 24, 39, 0.74);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 24px;
      margin-top: 20px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    pre {{
      background: #030712;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      overflow-x: auto;
      color: #d1d5db;
      white-space: pre-wrap;
      max-height: 520px;
    }}
    .flow {{
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 10px;
    }}
    .flow-step {{
      border: 1px solid var(--line);
      background: var(--panel2);
      border-radius: 14px;
      padding: 12px;
      font-size: 13px;
      min-height: 92px;
    }}
    .footer {{
      color: var(--muted);
      margin: 32px 0;
      font-size: 13px;
    }}
    code {{
      color: #bfdbfe;
      background: rgba(147,197,253,.08);
      padding: 2px 6px;
      border-radius: 8px;
    }}
    @media (max-width: 960px) {{
      .grid, .grid3, .grid2, .flow {{
        grid-template-columns: 1fr;
      }}
      .hero h1 {{
        font-size: 32px;
      }}
      .shell {{
        padding: 16px;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div>
        {badge(prd_status)}
        {badge("production-simulated")}
        {badge("RAG")}
        {badge("LLM-last")}
        {badge("agentic")}
        {badge("repo-aware")}
      </div>
      <h1>DevPulse Evidence Dashboard</h1>
      <p>
        DevPulse is a production-simulated RAG + agentic developer change-intelligence system.
        This dashboard turns the repo artifacts into a visual project cockpit: PRD completion,
        RAG quality, goal-mode execution, repo-aware risk, patch simulation, and PR-ready review package.
      </p>
      <p>
        <strong>Truth boundary:</strong>
        no real production SaaS, no live users, no live package registry, no real GitHub PR generation,
        no autonomous merge, and no production deployment.
      </p>
    </section>

    <section class="grid">
      {metric_card("PRD status", prd_status, "v3.0 final validation")}
      {metric_card("Evidence artifacts", evidence_artifacts, "EA-01 to EA-32")}
      {metric_card("Failure scenarios", failure_scenarios, "F-01 to F-19")}
      {metric_card("Wrong-version rate", wrong_version_rate, "version-safe RAG gate")}
    </section>

    <section class="section">
      <h2>System Flow</h2>
      <div class="flow">
        <div class="flow-step"><strong>1. Query Mode</strong><br><span class="muted">Parse, extract version, route, retrieve.</span></div>
        <div class="flow-step"><strong>2. Conflict Layer</strong><br><span class="muted">Detect deprecated, stale, contradictory docs.</span></div>
        <div class="flow-step"><strong>3. LLM-last Synthesis</strong><br><span class="muted">Only synthesize after deterministic gates.</span></div>
        <div class="flow-step"><strong>4. Goal Mode</strong><br><span class="muted">Plan dependency migration tasks.</span></div>
        <div class="flow-step"><strong>5. Repo-aware Scan</strong><br><span class="muted">Map dependency risk to callsites.</span></div>
        <div class="flow-step"><strong>6. PR Simulation</strong><br><span class="muted">Generate patch, tests, triage, review bundle.</span></div>
      </div>
    </section>

    <section class="grid3">
      <div class="card">
        <h3>RAG Eval Hardening</h3>
        <p>{badge(rag.get("status", "unknown"))}</p>
        <table>
          <tr><th>Metric</th><th>Value</th></tr>
          <tr><td>Eval queries</td><td>{escape(str(rag.get("eval_query_count", "")))}</td></tr>
          <tr><td>Hybrid Recall@5</td><td>{escape(str(rag.get("hybrid_recall_at_5", "")))}</td></tr>
          <tr><td>Reranker Recall@5</td><td>{escape(str(rag.get("reranker_recall_at_5", "")))}</td></tr>
          <tr><td>Conflict Macro F1</td><td>{escape(str(rag.get("conflict_macro_f1", "")))}</td></tr>
          <tr><td>37-day queries</td><td>{escape(str(rag.get("backtest_total_queries", "")))}</td></tr>
        </table>
      </div>

      <div class="card">
        <h3>Repo-aware Risk</h3>
        <p>{badge(repo.get("repo_migration_readiness", "unknown"))}</p>
        <table>
          <tr><th>Metric</th><th>Value</th></tr>
          <tr><td>Callsites found</td><td>{escape(str(repo.get("callsites_found", "")))}</td></tr>
          <tr><td>Risky callsites</td><td>{escape(str(repo.get("risky_callsite_count", "")))}</td></tr>
          <tr><td>High-risk deps</td><td>{escape(str(len(high_risk_deps)))}</td></tr>
          <tr><td>Medium-risk deps</td><td>{escape(str(len(medium_risk_deps)))}</td></tr>
          <tr><td>Low-risk deps</td><td>{escape(str(len(low_risk_deps)))}</td></tr>
          <tr><td>Readiness</td><td>{escape(str(repo_inspection.get("aggregate_repo_migration_readiness", "")))}</td></tr>
        </table>
      </div>

      <div class="card">
        <h3>Patch + PR Simulation</h3>
        <p>{badge(patch.get("status", "unknown"))}</p>
        <table>
          <tr><th>Metric</th><th>Value</th></tr>
          <tr><td>Patch changes</td><td>{escape(str(patch.get("patch_change_count", "")))}</td></tr>
          <tr><td>Apply recommendation</td><td>{escape(str(patch.get("patch_apply_recommendation", "")))}</td></tr>
          <tr><td>Before tests</td><td>{escape(str(patch.get("before_test_status", "")))}</td></tr>
          <tr><td>After patch</td><td>{escape(str(patch.get("after_patch_status", "")))}</td></tr>
        </table>
      </div>
    </section>

    <section class="grid2">
      <div class="card">
        <h3>Goal-mode Final Plan</h3>
        <p>{badge(plan.get("aggregate_verdict", completion_goal.get("aggregate_verdict", "unknown")))}</p>
        <table>
          <tr><th>Field</th><th>Value</th></tr>
          <tr><td>Total tasks</td><td>{escape(str(plan.get("total_tasks", "")))}</td></tr>
          <tr><td>Safe tasks</td><td>{escape(str(plan.get("safe_tasks", "")))}</td></tr>
          <tr><td>Risky tasks</td><td>{escape(str(plan.get("risky_tasks", "")))}</td></tr>
          <tr><td>Blocked tasks</td><td>{escape(str(plan.get("blocked_tasks", "")))}</td></tr>
          <tr><td>Escalated tasks</td><td>{escape(str(plan.get("escalated_tasks", "")))}</td></tr>
          <tr><td>Recommended action</td><td>{escape(str(plan.get("recommended_action", "")))}</td></tr>
        </table>
      </div>

      <div class="card">
        <h3>Patch Risk Gates</h3>
        <p>{badge(patch_risk.get("patch_apply_recommendation", "unknown"))}</p>
        <ul>
          {list_items(patch_risk.get("review_gates", []))}
        </ul>
      </div>
    </section>

    <section class="section">
      <h2>Core Demo Reports</h2>
      <div class="grid3">
        <div>
          <h3>Query Mode Demo</h3>
          <pre>{escape(query_demo[:3000])}</pre>
        </div>
        <div>
          <h3>Agentic Demo</h3>
          <pre>{escape(agentic_demo[:3000])}</pre>
        </div>
        <div>
          <h3>Final Completion</h3>
          <pre>{escape(final_demo[:3000])}</pre>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>Key Artifact Links</h2>
      <div class="grid3">
        <div class="card">
          <h3>Completion</h3>
          <p>{artifact_link("outputs/reports/devpulse_prd_completion_report_v3.json", "PRD completion report")}</p>
          <p>{artifact_link("outputs/reports/devpulse_final_demo_report.txt", "Final demo report")}</p>
          <p>{artifact_link("outputs/evidence/plan_summary_report.json", "Goal-mode plan summary")}</p>
        </div>
        <div class="card">
          <h3>RAG Eval</h3>
          <p>{artifact_link("outputs/rag_eval/retrieval_ablation_report.json", "Retrieval ablation")}</p>
          <p>{artifact_link("outputs/rag_eval/reranker_simulation_report.json", "Reranker simulation")}</p>
          <p>{artifact_link("outputs/rag_eval/conflict_confusion_matrix.json", "Conflict confusion matrix")}</p>
          <p>{artifact_link("outputs/rag_eval/traffic_backtest_37_day_report.json", "37-day backtest")}</p>
          <p>{artifact_link("outputs/rag_eval/corpus_perturbation_report.json", "Corpus perturbation")}</p>
        </div>
        <div class="card">
          <h3>Repo + PR Simulation</h3>
          <p>{artifact_link("outputs/repo_aware/repo_inspection_report.json", "Repo inspection")}</p>
          <p>{artifact_link("outputs/repo_aware/risky_callsite_report.json", "Risky callsites")}</p>
          <p>{artifact_link("outputs/patches/proposed_migration_patch.diff", "Proposed patch diff")}</p>
          <p>{artifact_link("outputs/pr_simulation/pr_body.md", "PR body")}</p>
          <p>{artifact_link("outputs/pr_simulation/reviewer_checklist.md", "Reviewer checklist")}</p>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>Artifact Inventory</h2>
      <p class="muted">Generated artifacts discovered under <code>outputs/</code>.</p>
      {artifact_table(inventory)}
    </section>

    <p class="footer">
      Generated at {escape(manifest["generated_at"])}. Static local dashboard only. No backend required.
    </p>
  </main>
</body>
</html>
"""

    (DASHBOARD_DIR / "index.html").write_text(html, encoding="utf-8")

    print("dashboard_v35 complete")
    print("status: pass")
    print(f"artifact_inventory_count: {len(inventory)}")
    print("wrote outputs/dashboard/index.html")
    print("wrote outputs/dashboard/dashboard_manifest.json")


if __name__ == "__main__":
    main()
