# Repair Log

Generated: 2026-05-13 19:32:18 +0800

| Repair | Files | Reason | Verification |
|---|---|---|---|
| Project-local acceptance harness | `scripts/acceptance/*.ps1`, `docs/auto-execute/*` | Required fast/gate/full Auto Execute loop | final fast/gate/full PASS |
| Full acceptance smoke coverage | `tools/full_acceptance_smoke.py` | Route/date/search/API/integration/screenshot/python evidence and aggregate summary | smoke JSON PASS |
| Compatibility route evidence | `tools/full_acceptance_smoke.py`, docs | Avoid silently passing redirect-vs-independent-page conflict | `redirect-final-url.json` |
| Bounded acceptance command/API runtime | Python tools, API routes, `lib.ps1` | Full mode must be local/repeatable and avoid live/production dependencies | `python-command-smoke.json`, `api-smoke.json` PASS |
| Architecture guard false positive | `run-architecture-guard.ps1` | Safety docs mentioning forbidden commands are not executable destructive commands | architecture guard PASS |
| run-all evidence readability | `run-all.ps1` | Correct gate name interpolation and smoke summary path | final fast/gate/full PASS |
