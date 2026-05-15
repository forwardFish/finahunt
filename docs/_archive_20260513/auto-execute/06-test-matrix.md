# Test Matrix

Generated: 2026-05-13 19:31:02 +0800

| Gate | Command | Final status | Evidence |
|---|---|---|---|
| Init | `powershell -ExecutionPolicy Bypass -File .\scripts\acceptance\init-harness.ps1` | PASS | `verification-results.md` |
| Build | `cd apps/web && npm run build` | PASS | `logs/frontend-build.log` |
| Compile | `python -m compileall -q agents packages graphs workflows tools skills tests` | PASS | `logs/backend-compileall.log` |
| Pytest | `python -m pytest -q` | PASS, 33 passed | `logs/backend-pytest.log` |
| Fast | `run-all.ps1 -Mode fast` | PASS | `logs/smoke-full-flow-fast.log` |
| Gate | `run-all.ps1 -Mode gate` | PASS | `logs/smoke-full-flow-gate.log`, screenshots |
| Full | `run-all.ps1 -Mode full` | PASS | `logs/smoke-full-flow-full.log`, `logs/smoke-python-commands.log` |
| Search | `/workbench?q=????` route case | PASS | `workbench-search-smoke.json` |
| Compatibility routes | `/low-position`, `/sprint-2` route cases | PRODUCT_DECISION_REQUIRED | `redirect-final-url.json` |
| Visual taste | screenshot objective smoke | PASS objective, MANUAL_REVIEW_REQUIRED taste | `screenshot-capture.json`, `visual-smoke.md` |
