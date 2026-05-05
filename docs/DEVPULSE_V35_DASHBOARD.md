# DevPulse v3.5 Static Evidence Dashboard

## Purpose

The dashboard converts DevPulse evidence artifacts into a visual local showcase.

It is intentionally static and local. It does not require a backend, frontend framework, hosted service, or paid infrastructure.

## Run

```bash
PYTHONPATH=. python3 scripts/build_dashboard_v35.py
PYTHONPATH=. python3 scripts/validate_dashboard_v35.py
open outputs/dashboard/index.html
eof
