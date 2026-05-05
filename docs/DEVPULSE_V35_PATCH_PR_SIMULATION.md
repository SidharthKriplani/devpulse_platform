# DevPulse v3.5 Patch + PR Simulation Extension

## Purpose

This extension turns repo-aware migration analysis into a reviewer-safe migration execution simulation.

It does not mutate the sample repository. It generates patch proposals, test simulation reports, failure triage, and a PR-ready review bundle.

## New Artifacts

```text
outputs/patches/proposed_file_changes.json
outputs/patches/proposed_migration_patch.diff
outputs/reports/patch_risk_report.json
outputs/test_simulation/before_tests_report.json
outputs/test_simulation/after_patch_tests_report.json
outputs/test_simulation/test_failure_triage_report.json
outputs/pr_simulation/pr_title.txt
outputs/pr_simulation/pr_body.md
outputs/pr_simulation/pr_diff.patch
outputs/pr_simulation/reviewer_checklist.md
outputs/pr_simulation/rollback_plan.md
outputs/reports/patch_pr_simulation_summary_v35.json
outputs/validation/patch_pr_simulation_validation_v35.json
