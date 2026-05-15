# Acceptance Test Plan

Generated: 2026-05-13 19:31:02 +0800

```powershell
cd D:\lyh\agent\agent-frame\finahunt
powershell -ExecutionPolicy Bypass -File .\scripts\acceptance\init-harness.ps1
cd D:\lyh\agent\agent-frame\finahunt\apps\web
npm run build
cd D:\lyh\agent\agent-frame\finahunt
python -m compileall -q agents packages graphs workflows tools skills tests
python -m pytest -q
powershell -ExecutionPolicy Bypass -File .\scripts\acceptance\run-all.ps1 -Mode fast
powershell -ExecutionPolicy Bypass -File .\scripts\acceptance\run-all.ps1 -Mode gate
powershell -ExecutionPolicy Bypass -File .\scripts\acceptance\run-all.ps1 -Mode full
```

Fast includes build, compileall, pytest, route/API/integration smoke. Gate includes fast plus explicit API and desktop/mobile screenshots. Full includes gate plus Python command smoke and final evidence/report updates. The harness only uses `http://127.0.0.1:3021`, records its PID, and stops only harness-owned processes. Acceptance API/Python smoke uses seed documents via `--acceptance-smoke` / `FINAHUNT_ACCEPTANCE_SMOKE=1` to avoid production/live dependency.
