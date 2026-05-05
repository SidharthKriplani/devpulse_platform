# DevPulse v3.5 Repo-Aware Migration Simulation Extension

## Purpose

This extension makes DevPulse codebase-aware.

DevPulse v3.0 already produces version-aware migration decisions from controlled documentation evidence. The v3.5 extension adds a local sample repository scanner that maps dependency migration risk to actual source-code callsites.

## New Capabilities

- sample repository inspection
- package manifest parsing
- dependency usage mapping
- risky source callsite detection
- repo-level migration readiness verdict
- explicit non-claims around real GitHub integration and autonomous code mutation

## New Artifacts

```text
outputs/repo_aware/repo_inspection_report.json
outputs/repo_aware/dependency_usage_map.json
outputs/repo_aware/risky_callsite_report.json
outputs/repo_aware/repo_aware_extension_summary.json
outputs/validation/repo_aware_extension_validation_v35.json
