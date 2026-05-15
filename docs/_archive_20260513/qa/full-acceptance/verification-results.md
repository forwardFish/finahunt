# Full Acceptance Verification Results - Ralph continuation

Generated: 2026-05-13 16:27:40 +0800

## Summary

- Next page routes discovered: 6
- Next API route files discovered: 3
- Route smoke: PASS, 13 cases (6 routes default + date query, plus workbench search query)
- API smoke: PASS, 8 cases over 3 actual API route files
- Integration smoke: PASS, 8 checks
- Python command smoke: PASS, 3 commands
- Screenshot capture: PASS, 12 screenshots (desktop + mobile for 6 routes)

## Fresh verification evidence

- `npm run build` in `apps/web`: PASS
- `python -m compileall -q agents packages graphs workflows tools skills tests`: PASS
- `python -m pytest -q`: PASS, 33 passed in 9.40s
- `python tools/full_acceptance_smoke.py --base-url http://127.0.0.1:3021 --routes --api --integration --screenshots`: PASS
- `python tools/full_acceptance_smoke.py --base-url http://127.0.0.1:3021 --python-commands`: PASS

## Evidence files

- `docs/qa/full-acceptance/test-results/full-acceptance-smoke-summary.json`
- `docs/qa/full-acceptance/test-results/surface-inventory.json`
- `docs/qa/full-acceptance/test-results/route-smoke.json`
- `docs/qa/full-acceptance/test-results/api-smoke.json`
- `docs/qa/full-acceptance/test-results/integration-smoke.json`
- `docs/qa/full-acceptance/test-results/python-command-smoke.json`
- `docs/qa/full-acceptance/test-results/screenshot-capture.json`
- `docs/qa/full-acceptance/test-results/workbench-search-smoke.json`
- `docs/qa/full-acceptance/screenshots/desktop-*.png`
- `docs/qa/full-acceptance/screenshots/mobile-*.png`

## Ralph continuation fixes validated

- Restored `/low-position` and `/sprint-2` as independent accessible pages rather than redirect-only paths.
- Repaired `workbench` visible copy and search state text.
- Added smoke helpers for final URL and H1 extraction.
- Tightened smoke assertions to check visible route identity text.
- Fixed mobile grid/card overflow by allowing grid children and cards to shrink inside viewport.

## Remaining non-blocking risks

- Manual product taste review remains separate from automated acceptance.
- Adding more granular API routes remains a product/API design decision, not an acceptance patch.
