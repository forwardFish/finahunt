param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = "fast")
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
Initialize-MachineFiles $ProjectRoot
$p = Get-AEPaths $ProjectRoot
$commands = @()
$hardFail = $false
$compileTargets = @('agents','packages','graphs','workflows','tools','skills','tests')
$compileArgs = @('-m','compileall','-q') + $compileTargets
$compileLog = Join-Path $p.Logs 'backend-python-compileall.log'
Push-Location $ProjectRoot
try {
  & python @compileArgs *>&1 | Tee-Object -FilePath $compileLog
  $compileCode = $LASTEXITCODE
  $commands += @{ command = "python $($compileArgs -join ' ')"; status = $(if ($compileCode -eq 0) { 'PASS' } else { 'HARD_FAIL' }); log = Get-RelativeEvidencePath $ProjectRoot $compileLog }
  if ($compileCode -ne 0) { $hardFail = $true }
  $pytestLog = Join-Path $p.Logs 'backend-pytest.log'
  & python -m pytest -q *>&1 | Tee-Object -FilePath $pytestLog
  $pytestCode = $LASTEXITCODE
  $commands += @{ command = 'python -m pytest -q'; status = $(if ($pytestCode -eq 0) { 'PASS' } else { 'HARD_FAIL' }); log = Get-RelativeEvidencePath $ProjectRoot $pytestLog }
  if ($pytestCode -ne 0) { $hardFail = $true }
} finally { Pop-Location }
$status = if ($hardFail) { 'HARD_FAIL' } else { 'PASS' }
Write-LaneResult $ProjectRoot 'backend-test' $status $commands @((Get-RelativeEvidencePath $ProjectRoot $compileLog),(Get-RelativeEvidencePath $ProjectRoot $pytestLog)) $(if ($hardFail) { @('Python backend compile/test gate failed') } else { @() }) @('Repair Python backend tests and rerun run-backend-test.ps1.')
Add-VerificationResult $ProjectRoot 'backend-test' $status 'Python compileall and pytest backend verifier completed.' (Join-Path $p.Results 'backend-test.json')
Write-Host "[$status] backend-test"
exit (Get-AEExitCode $status)
