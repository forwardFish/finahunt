# Verification Results

Generated: 2026-05-13 19:32:18 +0800

## Direct commands

| Command | Status | Evidence |
|---|---|---|
| `init-harness.ps1` | PASS | harness initialized |
| `cd apps/web && npm run build` | PASS | `logs/frontend-build.log` |
| `python -m compileall -q agents packages graphs workflows tools skills tests` | PASS | `logs/backend-compileall.log` |
| `python -m pytest -q` | PASS, 33 passed | `logs/backend-pytest.log` |

## run-all gates

| Gate | Status | Evidence |
|---|---|---|
| fast | PASS | `logs/smoke-full-flow-fast.log` |
| gate | PASS | `logs/smoke-full-flow-gate.log` |
| full | PASS | `logs/smoke-full-flow-full.log`, `logs/smoke-python-commands.log` |

## Smoke summary

| Evidence | Status |
|---|---|
| Routes | 13/13 PASS |
| APIs | 8/8 PASS |
| Integration | 8/8 PASS |
| Screenshots | 12/12 PASS |
| Python commands | 3/3 PASS |
| `/workbench?q=????` | 1/1 PASS |
| Compatibility URL records | 5/5 PASS |

Final HARD_FAIL: none. DOCUMENTED_BLOCKER: none. Remaining classifications: PRODUCT_DECISION_REQUIRED for `/low-position` and `/sprint-2`, MANUAL_REVIEW_REQUIRED for visual taste, DEFERRED for production/live source E2E.
