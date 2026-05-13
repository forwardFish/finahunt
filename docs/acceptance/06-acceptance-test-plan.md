# 06 Acceptance Test Plan - expanded acceptance pass

## Reused and extended tests

- Keep `python -m pytest -q` as the Python contract gate.
- Keep `npm run build` as the Next.js build/type gate.
- Use `tools/full_acceptance_smoke.py` as the broadened acceptance gate.

## Full local acceptance command sequence

```powershell
cd D:\lyh\agent\agent-frame\finahunt\apps\web
npm run build
cd D:\lyh\agent\agent-frame\finahunt
python -m compileall -q agents packages graphs workflows tools skills tests
python -m pytest -q
python tools/full_acceptance_smoke.py --base-url http://127.0.0.1:3021
```

## Evidence outputs

- `docs/qa/full-acceptance/test-results/route-smoke.json`
- `docs/qa/full-acceptance/test-results/api-smoke.json`
- `docs/qa/full-acceptance/test-results/integration-smoke.json`
- `docs/qa/full-acceptance/test-results/python-command-smoke.json`
- `docs/qa/full-acceptance/test-results/screenshot-capture.json`
- `docs/qa/full-acceptance/test-results/surface-inventory.json`
- `docs/qa/full-acceptance/screenshots/*.png`

## Manual review still useful

- Visual taste polish against all UI reference images.
- Decide whether to add new domain-specific API routes beyond the current 3 actual Next API routes.
