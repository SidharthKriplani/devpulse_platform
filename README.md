# DevPulse Platform

DevPulse is a solo-built, non-production, production-simulated agentic developer change-intelligence and migration decision system.

It is designed to help engineering teams reason safely about external dependency changes by combining:

- version-aware retrieval
- deterministic conflict detection
- LLM-last grounded synthesis
- SAFE / RISKY / BLOCKED migration reports
- bounded goal-level agentic orchestration
- evidence artifacts and audit traces

## Truth Boundary

DevPulse is not a production SaaS, not connected to live package registries, not serving real users, and not generating real GitHub PRs.

The project is production-simulated: every claimed behavior must be backed by executable scripts and generated artifacts.

## Target PRD Completion

The implementation target is DevPulse PRD v3.0:

- 11-layer Query Mode
- 6-component Goal Mode
- 37-day simulated operating lifecycle
- 32 evidence artifacts
- 19 failure/recovery scenarios
- final validation bundle

## Planned Run Commands

```bash
PYTHONPATH=. python3 scripts/seed_devpulse.py
PYTHONPATH=. python3 scripts/seed_devpulse_v3.py
PYTHONPATH=. python3 scripts/run_devpulse_complete_v3.py
