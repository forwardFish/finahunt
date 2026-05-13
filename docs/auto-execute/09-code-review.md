# Code Review

Generated: 2026-05-13 19:32:18 +0800

Scope reviewed: `scripts/acceptance`, `tools/full_acceptance_smoke.py`, Python command tools, two API routes, and app route responsibilities.

| Area | Result | Notes |
|---|---|---|
| Destructive operations | PASS | Architecture guard passed; no `git reset`, `git clean`, force push, production DB/payment access in executable acceptance scope. |
| Runtime contract | PASS | `dailySnapshot.ts` and `lowPositionWorkbench.ts` remain the data boundary; acceptance-smoke is opt-in. |
| Search q | PASS | `/workbench?q=????` reflects q and is asserted by smoke. |
| Compatibility routes | PRODUCT_DECISION_REQUIRED | Independent pages are verified; product decision needed against redirect-only wording. |
| Visual taste | MANUAL_REVIEW_REQUIRED | Objective smoke passes; human review needed for exact UI taste. |
| Live/production runtime | DEFERRED | Local seed smoke used by harness. |

Verification: build PASS, compileall PASS, pytest PASS (33 passed), run-all fast/gate/full PASS.
