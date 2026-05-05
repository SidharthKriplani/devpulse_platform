# DevPulse Platform

**Production-simulated RAG + agentic migration intelligence platform for version-safe developer change decisions.**

<p>
  <a href="https://sidharthkriplani.github.io/devpulse_platform/">
    <img alt="Live Dashboard" src="https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-2ea44f?style=for-the-badge&logo=githubpages&logoColor=white">
  </a>
  <img alt="PRD Status" src="https://img.shields.io/badge/PRD%20v3.5-PASS-brightgreen?style=for-the-badge">
  <img alt="RAG" src="https://img.shields.io/badge/RAG-Version%20Safe-2563eb?style=for-the-badge">
  <img alt="Agentic" src="https://img.shields.io/badge/Agentic-Orchestration-7c3aed?style=for-the-badge">
  <img alt="Evidence" src="https://img.shields.io/badge/Evidence-70%20Artifacts-f59e0b?style=for-the-badge">
</p>

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-3776ab?style=flat-square&logo=python&logoColor=white">
  <img alt="Static Dashboard" src="https://img.shields.io/badge/Dashboard-Static%20HTML-orange?style=flat-square">
  <img alt="Wrong Version Rate" src="https://img.shields.io/badge/Wrong--Version%20Rate-0.0-brightgreen?style=flat-square">
  <img alt="Hybrid Recall" src="https://img.shields.io/badge/Hybrid%20Recall%405-0.94-blue?style=flat-square">
  <img alt="Conflict Macro F1" src="https://img.shields.io/badge/Conflict%20Macro%20F1-0.966-purple?style=flat-square">
  <img alt="Backtest" src="https://img.shields.io/badge/37--Day%20Backtest-2479%20Queries-teal?style=flat-square">
</p>

---

## At a Glance

| Layer | What it proves |
|---|---|
| **Version-safe RAG** | Hard version filtering, zero wrong-version answer rate, citation-backed synthesis |
| **Deterministic conflict detection** | Stale, contradictory, deprecated, and cross-source conflict handling |
| **Agentic Goal Mode** | Bounded task planning, recovery, escalation, and final migration decisioning |
| **Repo-aware analysis** | Local repository scan, dependency usage mapping, risky callsite detection |
| **Patch + PR simulation** | Reviewer-safe patch diff, test simulation, triage, checklist, rollback plan |
| **Evidence dashboard** | Public visual dashboard summarizing 70 generated artifacts |

---

DevPulse helps engineering teams reason about dependency migrations by combining version-aware retrieval, deterministic conflict detection, LLM-last synthesis boundaries, agentic migration planning, repo-aware callsite analysis, patch proposal simulation, test/triage simulation, and a static evidence dashboard.

## Live Dashboard

**Open the visual showcase:**  
https://sidharthkriplani.github.io/devpulse_platform/

The dashboard gives a fast view of:

- PRD completion status
- Query Mode and Goal Mode flow
- RAG evaluation metrics
- repo-aware migration risk
- patch and PR simulation
- final validation artifacts
- truth boundary and evidence inventory

## What DevPulse Solves

Dependency migrations often fail because teams rely on stale docs, ambiguous version references, contradictory changelogs, or incomplete migration notes.

DevPulse is designed to answer questions like:

- “How should I migrate this dependency from v2 to v3?”
- “Are these docs stale or contradictory?”
- “Which source-code callsites are risky?”
- “Can this migration proceed safely, or should it be blocked?”
- “What evidence supports the recommendation?”

The system intentionally avoids blind LLM output. It uses deterministic gates first, then allows synthesis only when evidence is sufficiently grounded.

## Core Architecture

```text
User Query / Migration Goal
        |
        v
Query Mode
- query parsing
- version extraction
- route selection
- version-aware retrieval
- conflict detection
- citation assembly
- SAFE / RISKY / BLOCKED migration report
        |
        v
Goal Mode
- goal parsing
- dependency delta detection
- task planning
- task execution through Query Mode
- bounded recovery
- plan summary reporting
        |
        v
Repo-Aware Extension
- local sample repo scan
- dependency usage mapping
- risky callsite detection
        |
        v
Patch + PR Simulation
- proposed patch diff
- before/after test simulation
- failure triage
- reviewer checklist
- rollback plan
        |
        v
Evidence Dashboard
```

## Key Results

| Area | Result |
|---|---:|
| PRD v3.0 status | pass |
| Query Mode artifacts | 24 |
| Goal Mode artifacts | 8 |
| Total evidence artifacts | 32 |
| Failure/recovery scenarios | 19 |
| Wrong-version answer rate | 0.0 |
| RAG eval query count | 180 |
| Hybrid Recall@5 | 0.94 |
| Reranker simulated Recall@5 | 0.97 |
| Conflict Macro F1 | 0.966 |
| 37-day backtest queries | 2,479 |
| Repo-aware callsites found | 10 |
| Risky callsites found | 10 |
| Patch recommendation | DO_NOT_APPLY_WITHOUT_REVIEW |
| Dashboard artifact inventory | 70 artifacts |

## What Is Implemented

### Query Mode

DevPulse Query Mode includes:

- deterministic query parsing
- version extraction
- complexity routing
- version-filtered retrieval simulation
- deterministic conflict detection
- SAFE / RISKY / BLOCKED migration reports
- LLM-last synthesis boundary
- programmatic citation assembly
- fallback and audit artifacts
- 24 evidence artifacts
- 10 failure/recovery scenarios

### Goal Mode

DevPulse Goal Mode includes:

- `GoalParser`
- `DependencyDeltaDetector`
- `TaskPlanner`
- `TaskExecutor`
- `RecoveryDecider`
- `PlanSummaryReporter`
- controlled dependency target registry
- bounded retry cap
- staged migration recommendation
- 8 evidence artifacts
- 9 failure/recovery scenarios

### Repo-Aware Extension

The repo-aware extension scans a local sample repository and maps dependency risk to source-code callsites.

Artifacts include:

```text
outputs/repo_aware/repo_inspection_report.json
outputs/repo_aware/dependency_usage_map.json
outputs/repo_aware/risky_callsite_report.json
outputs/repo_aware/repo_aware_extension_summary.json
```

### Patch + PR Simulation

DevPulse generates reviewer-safe migration proposal artifacts:

```text
outputs/patches/proposed_file_changes.json
outputs/patches/proposed_migration_patch.diff
outputs/reports/patch_risk_report.json
outputs/test_simulation/before_tests_report.json
outputs/test_simulation/after_patch_tests_report.json
outputs/test_simulation/test_failure_triage_report.json
outputs/pr_simulation/pr_body.md
outputs/pr_simulation/pr_diff.patch
outputs/pr_simulation/reviewer_checklist.md
outputs/pr_simulation/rollback_plan.md
```

### RAG Evaluation Hardening

DevPulse includes deeper RAG evaluation artifacts:

```text
outputs/rag_eval/retrieval_ablation_report.json
outputs/rag_eval/reranker_simulation_report.json
outputs/rag_eval/conflict_confusion_matrix.json
outputs/rag_eval/traffic_backtest_37_day_report.json
outputs/rag_eval/corpus_perturbation_report.json
outputs/rag_eval/rag_eval_hardening_summary_v35.json
```

## Run Locally

Run the full PRD validation bundle:

```bash
PYTHONPATH=. python3 scripts/run_devpulse_complete_v3.py
PYTHONPATH=. python3 scripts/show_final_demo_report.py
```

Run the v3.5 extensions:

```bash
PYTHONPATH=. python3 scripts/run_repo_aware_scan_v35.py
PYTHONPATH=. python3 scripts/validate_repo_aware_extension_v35.py

PYTHONPATH=. python3 scripts/run_patch_pr_simulation_v35.py
PYTHONPATH=. python3 scripts/validate_patch_pr_simulation_v35.py

PYTHONPATH=. python3 scripts/run_rag_eval_hardening_v35.py
PYTHONPATH=. python3 scripts/validate_rag_eval_hardening_v35.py

PYTHONPATH=. python3 scripts/build_dashboard_v35.py
PYTHONPATH=. python3 scripts/validate_dashboard_v35.py
open outputs/dashboard/index.html
```

## Important Artifacts

| Artifact | Path |
|---|---|
| Final PRD completion report | `outputs/reports/devpulse_prd_completion_report_v3.json` |
| Final demo report | `outputs/reports/devpulse_final_demo_report.txt` |
| Query Mode demo | `outputs/evidence/devpulse_demo_report.txt` |
| Agentic demo | `outputs/evidence/agentic_demo_report.txt` |
| Goal plan summary | `outputs/evidence/plan_summary_report.json` |
| RAG hardening summary | `outputs/rag_eval/rag_eval_hardening_summary_v35.json` |
| Repo inspection report | `outputs/repo_aware/repo_inspection_report.json` |
| Risky callsite report | `outputs/repo_aware/risky_callsite_report.json` |
| Patch risk report | `outputs/reports/patch_risk_report.json` |
| PR simulation body | `outputs/pr_simulation/pr_body.md` |
| Static dashboard | `docs/index.html` |

## Truth Boundary

DevPulse is a **solo-built, non-production, production-simulated system**.

It does **not** claim:

- real production SaaS usage
- real production traffic
- real users
- live npm/PyPI/Maven registry integration
- real GitHub PR creation
- real CI execution
- autonomous production code mutation
- autonomous merge safety
- production deployment

The project is intentionally evidence-backed and simulation-bounded. Every major claim is supported by executable scripts, generated artifacts, validation reports, and a dashboard.

## Resume-Safe Claim

Built DevPulse, a production-simulated RAG + agentic migration intelligence platform with version-aware retrieval, deterministic conflict detection, LLM-last grounded synthesis, SAFE/RISKY/BLOCKED decisioning, repo-aware callsite risk analysis, patch/PR simulation, 37-day RAG backtesting, and a static evidence dashboard covering 70 generated artifacts.

## Repository Structure

```text
configs/                  controlled registries and scope config
src/devpulse/             core Query Mode and Goal Mode modules
scripts/                  executable demo, validation, and artifact builders
sample_repos/             controlled local repo used for repo-aware simulation
outputs/evidence/         core evidence artifacts
outputs/validation/       validation reports
outputs/repo_aware/       repo-aware migration scan artifacts
outputs/patches/          patch proposal artifacts
outputs/pr_simulation/    PR-ready simulation package
outputs/rag_eval/         RAG evaluation hardening artifacts
outputs/dashboard/        local static dashboard
docs/                     public GitHub Pages dashboard and documentation
```

## Status

DevPulse is complete at the production-simulated repo-evidence level and is publicly showcaseable through GitHub Pages.
