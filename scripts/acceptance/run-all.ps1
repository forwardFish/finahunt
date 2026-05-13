param([string]$ProjectRoot = (Get-Location).Path, [ValidateSet('fast','gate','full')] [string]$Mode = 'fast')
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
$p = Get-AEPaths $ProjectRoot
Update-State $ProjectRoot 'run-all' 'running' "Mode=$Mode"
Add-VerificationResult $ProjectRoot "run-all:${Mode}:start" 'PASS' "Started Auto Execute Acceptance First mode $Mode" ''
Write-Host "auto-execute-acceptance-first run-all | Mode=$Mode | ProjectRoot=$ProjectRoot"
$failures = 0

function Run-Stage($Name, [scriptblock]$Block) {
  Write-Host "`n---- stage: $Name ----"
  & $Block
  $code = $LASTEXITCODE
  if ($null -eq $code) { $code = 0 }
  if ($code -ne 0) { $script:failures++ }
}

Run-Stage 'collect-env' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'collect-env.ps1') -ProjectRoot $ProjectRoot -Mode $Mode }
Run-Stage 'collect-git-status' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'collect-git-status.ps1') -ProjectRoot $ProjectRoot -Mode $Mode }
Run-Stage 'architecture-guard' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run-architecture-guard.ps1') -ProjectRoot $ProjectRoot -Mode $Mode }
Run-Stage 'frontend-build' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run-frontend.ps1') -ProjectRoot $ProjectRoot -Mode $Mode }
Run-Stage 'backend-tests' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run-backend.ps1') -ProjectRoot $ProjectRoot -Mode $Mode }
Run-Stage 'db-e2e' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run-db-e2e.ps1') -ProjectRoot $ProjectRoot -Mode $Mode }
Run-Stage 'full-flow-smoke' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run-full-flow-smoke.ps1') -ProjectRoot $ProjectRoot -Mode $Mode -BaseUrl 'http://127.0.0.1:3021' }

if ($Mode -eq 'gate' -or $Mode -eq 'full') {
  Run-Stage 'api-smoke-wrapper' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run-api-smoke.ps1') -ProjectRoot $ProjectRoot -Mode $Mode -BaseUrl 'http://127.0.0.1:3021' }
  Run-Stage 'visual-smoke-wrapper' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'run-visual-smoke.ps1') -ProjectRoot $ProjectRoot -Mode $Mode -BaseUrl 'http://127.0.0.1:3021' }
}

Run-Stage 'summarize-errors' { powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'summarize-errors.ps1') -ProjectRoot $ProjectRoot -Mode $Mode }

$summaryPath = Join-Path $p.QaResults 'full-acceptance-smoke-summary.json'
$reportStatus = if ($failures -eq 0) { 'PASS' } else { 'HARD_FAIL' }
$report = @"
# AUTO EXECUTE DELIVERY REPORT

Generated: $(Get-Date)

## Run summary

- Project root: $ProjectRoot
- Mode: $Mode
- Status: $reportStatus
- Failures: $failures
- Base URL: http://127.0.0.1:3021

## Evidence

- Verification results: `docs/auto-execute/verification-results.md`
- Blockers: `docs/auto-execute/blockers.md`
- Logs: `docs/auto-execute/logs/`
- Smoke JSON: `docs/qa/full-acceptance/test-results/`
- Screenshots: `docs/qa/full-acceptance/screenshots/`
- Smoke summary: $summaryPath

## Classification reminders

- UI editorial taste remains `MANUAL_REVIEW_REQUIRED` where noted in traceability.
- `/low-position` and `/sprint-2` remain independent compatibility pages and are classified as `PRODUCT_DECISION_REQUIRED` against the original redirect-only Sprint 6/6B wording.
- DB E2E is `DEFERRED` because Sprint 6/6B acceptance is local web/UI/API-surface oriented and production DB access is forbidden.
"@
$report | Set-Content -Encoding UTF8 $p.FinalReport

if ($failures -eq 0) {
  Add-VerificationResult $ProjectRoot "run-all:$Mode" 'PASS' 'All required stages for this mode passed or were explicitly classified' $p.FinalReport
  Update-State $ProjectRoot 'run-all' 'complete' "Mode=$Mode PASS"
  Write-Host "[PASS] run-all $Mode. Report: $($p.FinalReport)"
  exit 0
}
Add-VerificationResult $ProjectRoot "run-all:$Mode" 'HARD_FAIL' "$failures stage failure(s)" $p.FinalReport
Add-Blocker $ProjectRoot "run-all:$Mode" 'HARD_FAIL' "$failures stage failure(s)" $p.FinalReport
Update-State $ProjectRoot 'run-all' 'failed' "Mode=$Mode HARD_FAIL"
Write-Host "[HARD_FAIL] run-all $Mode. Report: $($p.FinalReport)"
exit 1
