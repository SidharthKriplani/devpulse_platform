# Rollback Plan

## Scope

This rollback plan applies to the simulated DevPulse migration package.

## Rollback Steps

1. Revert package.json dependency version bumps.
2. Revert auth-sdk authenticate signature change.
3. Revert profile-sdk getUserProfile replacement.
4. Revert logging payload shape change.
5. Reinstall previous dependency lockfile.
6. Run test suite.
7. Confirm checkout login/profile/logging flows return to baseline behavior.

## Rollback Trigger

Rollback immediately if:

- auth login fails
- profile loading fails
- logging ingestion rejects payloads
- typecheck fails on SDK imports
- any critical checkout path regresses

## Truth Boundary

This is a generated rollback plan for a controlled local simulation, not an executed production rollback.
