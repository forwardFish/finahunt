# 04 Test Matrix - expanded acceptance pass

| Test | Command | Expected | Current result | Blocking | Evidence |
| --- | --- | --- | --- | --- | --- |
| Next build | `cd apps/web && npm run build` | PASS | PASS | yes | terminal run at 2026-05-13 11:18:56 |
| npm lint | package script check | run if exists | NOT PRESENT | no | `apps/web/package.json` has dev/build/start only |
| npm typecheck | package script check | run if exists | NOT PRESENT | no | Next build type check ran |
| npm test | package script check | run if exists | NOT PRESENT | no | no npm test script |
| Python compileall | `python -m compileall -q agents packages graphs workflows tools skills tests` | PASS | PASS | yes | terminal run |
| Pytest | `python -m pytest -q` | PASS | PASS, 33 passed | yes | terminal run; atexit temp cleanup warning after pass |
| Route smoke | `python tools/full_acceptance_smoke.py --routes` | PASS | PASS, 13 cases | yes | `route-smoke.json` |
| API smoke | `python tools/full_acceptance_smoke.py --api` | PASS | PASS, 8 cases over 3 route files | yes | `api-smoke.json` |
| Integration smoke | `python tools/full_acceptance_smoke.py --integration` | PASS | PASS, 8 checks | yes | `integration-smoke.json` |
| Python command smoke | `python tools/full_acceptance_smoke.py --python-commands` | PASS | PASS, 3 commands | yes | `python-command-smoke.json` |
| Screenshot capture | `python tools/full_acceptance_smoke.py --screenshots` | PASS | PASS, 12 screenshots | yes | `screenshots/*.png` |
