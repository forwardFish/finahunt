# 01 Task Decomposition - expanded acceptance pass

| Work ID | Work unit | Type | Target files/areas | Dependency | Acceptance check | Status |
| --- | --- | --- | --- | --- | --- | --- |
| W2-001 | Re-scan actual routes/API/integration surfaces | audit | app router, API routes, client fetches, forms, Python commands | git status | surface inventory | done |
| W2-002 | Expand route/API acceptance coverage | test | `tools/full_acceptance_smoke.py` | W2-001 | 12 route cases, 8 API cases | done |
| W2-003 | Add integration and Python command smoke | test | smoke script | W2-001 | fetch target + command results | done |
| W2-004 | Fix mojibake hardcoded UI text | implementation | FinancialUI, buttons, webView | expanded smoke failure | no mojibake in route/screenshot smoke | done |
| W2-005 | Re-run build/Python/pytest/smoke/screenshots | verification | all gates | W2-002/W2-004 | all pass | done |
| W2-006 | Update docs/report/review | docs/review | docs/acceptance, docs/qa, final report | verification | report evidence | done |
