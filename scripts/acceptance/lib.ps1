param()

$script:AllowedStatuses = @('PASS','HARD_FAIL','DOCUMENTED_BLOCKER','DEFERRED','MANUAL_REVIEW_REQUIRED','PRODUCT_DECISION_REQUIRED')

function Ensure-Dir($Path) {
  if (!(Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}

function Get-ProjectRoot($ProjectRoot) {
  if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { return (Resolve-Path '.').Path }
  return (Resolve-Path -LiteralPath $ProjectRoot).Path
}

function Get-AEPaths($ProjectRoot) {
  $ProjectRoot = Get-ProjectRoot $ProjectRoot
  $Docs = Join-Path $ProjectRoot 'docs\auto-execute'
  return @{
    ProjectRoot = $ProjectRoot
    Docs = $Docs
    Features = Join-Path $Docs 'features'
    Tasks = Join-Path $Docs 'tasks'
    Logs = Join-Path $Docs 'logs'
    Screenshots = Join-Path $Docs 'screenshots'
    Summaries = Join-Path $Docs 'summaries'
    Verification = Join-Path $Docs 'verification-results.md'
    Blockers = Join-Path $Docs 'blockers.md'
    State = Join-Path $Docs 'state.json'
    Progress = Join-Path $Docs 'progress.md'
    FinalReport = Join-Path $ProjectRoot 'docs\AUTO_EXECUTE_DELIVERY_REPORT.md'
    QaRoot = Join-Path $ProjectRoot 'docs\qa\full-acceptance'
    QaResults = Join-Path $ProjectRoot 'docs\qa\full-acceptance\test-results'
    QaScreenshots = Join-Path $ProjectRoot 'docs\qa\full-acceptance\screenshots'
  }
}

function Initialize-Layout($ProjectRoot) {
  $p = Get-AEPaths $ProjectRoot
  @(
    $p.Docs, $p.Features, $p.Logs, $p.Screenshots, $p.Summaries,
    $p.QaRoot, $p.QaResults, $p.QaScreenshots,
    (Join-Path $p.Tasks 'available'),
    (Join-Path $p.Tasks 'current'),
    (Join-Path $p.Tasks 'completed'),
    (Join-Path $p.Tasks 'blocked')
  ) | ForEach-Object { Ensure-Dir $_ }
}

function Assert-AEStatus($Status) {
  if ($script:AllowedStatuses -notcontains $Status) { throw "Unsupported Auto Execute status: $Status" }
}

function Add-VerificationResult($ProjectRoot, $Gate, $Status, $Details, $Evidence = '') {
  Assert-AEStatus $Status
  $p = Get-AEPaths $ProjectRoot
  Ensure-Dir (Split-Path $p.Verification)
  $time = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  Add-Content -Encoding UTF8 $p.Verification "`n## $Gate`n- Time: $time`n- Status: $Status`n- Details: $Details`n- Evidence: $Evidence`n"
}

function Add-Blocker($ProjectRoot, $Gate, $Type, $Details, $Evidence = '') {
  Assert-AEStatus $Type
  $p = Get-AEPaths $ProjectRoot
  Ensure-Dir (Split-Path $p.Blockers)
  $time = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  Add-Content -Encoding UTF8 $p.Blockers "`n## $Gate`n- Time: $time`n- Type: $Type`n- Details: $Details`n- Evidence: $Evidence`n"
}

function Add-RepairLog($ProjectRoot, $Gate, $Details) {
  $p = Get-AEPaths $ProjectRoot
  $file = Join-Path $p.Docs '08-repair-log.md'
  Ensure-Dir (Split-Path $file)
  Add-Content -Encoding UTF8 $file "`n## $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Gate`n$Details`n"
}

function Update-State($ProjectRoot, $Phase, $Status, $NextAction = '') {
  $p = Get-AEPaths $ProjectRoot
  $obj = @{ projectRoot=$p.ProjectRoot; lastRunAt=(Get-Date).ToString('s'); phase=$Phase; status=$Status; nextAction=$NextAction }
  $obj | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $p.State
}

function Invoke-LoggedCommand($ProjectRoot, $Gate, [scriptblock]$Command, $LogName, [string]$WorkingDirectory = '') {
  $p = Get-AEPaths $ProjectRoot
  Ensure-Dir $p.Logs
  $log = Join-Path $p.Logs $LogName
  if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) { $WorkingDirectory = $ProjectRoot }
  Write-Host "==== $Gate ===="
  Push-Location $WorkingDirectory
  try {
    & $Command *>&1 | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 0 }
    if ($code -eq 0) {
      Add-VerificationResult $ProjectRoot $Gate 'PASS' 'Exit code 0' $log
      Write-Host "[PASS] $Gate"
      return $true
    }
    Add-VerificationResult $ProjectRoot $Gate 'HARD_FAIL' "Exit code $code" $log
    Add-Blocker $ProjectRoot $Gate 'HARD_FAIL' "Exit code $code" $log
    Write-Host "[HARD_FAIL] $Gate exit code $code"
    return $false
  } catch {
    Add-VerificationResult $ProjectRoot $Gate 'HARD_FAIL' $_.Exception.Message $log
    Add-Blocker $ProjectRoot $Gate 'HARD_FAIL' $_.Exception.Message $log
    Write-Host "[HARD_FAIL] $Gate $($_.Exception.Message)"
    return $false
  } finally { Pop-Location }
}

function Test-UrlAlive($Url) {
  try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
    return ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500)
  } catch { return $false }
}

function Start-FinahuntServerIfNeeded($ProjectRoot, $BaseUrl = 'http://127.0.0.1:3021') {
  $p = Get-AEPaths $ProjectRoot
  Ensure-Dir $p.Logs
  Ensure-Dir $p.QaRoot
  if (Test-UrlAlive $BaseUrl) {
    Add-VerificationResult $ProjectRoot 'server:reuse' 'PASS' "Existing local server reachable at $BaseUrl; not owned by harness" ''
    return @{ started=$false; pid=$null; baseUrl=$BaseUrl }
  }
  $npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
  if ([string]::IsNullOrWhiteSpace($npm)) { $npm = (Get-Command npm -ErrorAction Stop).Source }
  $out = Join-Path $p.Logs 'next-start-3021.out.log'
  $err = Join-Path $p.Logs 'next-start-3021.err.log'
  $pidFile = Join-Path $p.QaRoot 'next-start-3021.pid'
  $previousSmokeEnv = $env:FINAHUNT_ACCEPTANCE_SMOKE
  $env:FINAHUNT_ACCEPTANCE_SMOKE = '1'
  try {
    $proc = Start-Process -FilePath $npm -ArgumentList @('run','start','--','-p','3021') -WorkingDirectory (Join-Path $ProjectRoot 'apps\web') -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
  } finally {
    if ($null -eq $previousSmokeEnv) { Remove-Item Env:\FINAHUNT_ACCEPTANCE_SMOKE -ErrorAction SilentlyContinue } else { $env:FINAHUNT_ACCEPTANCE_SMOKE = $previousSmokeEnv }
  }
  Set-Content -Encoding UTF8 -Path $pidFile -Value $proc.Id
  Add-VerificationResult $ProjectRoot 'server:start' 'PASS' "Started local Next server PID $($proc.Id) at $BaseUrl" $pidFile
  Start-Sleep -Seconds 8
  if (!(Test-UrlAlive $BaseUrl)) { throw "Local server did not become reachable at $BaseUrl. See $out / $err" }
  return @{ started=$true; pid=$proc.Id; baseUrl=$BaseUrl }
}

function Stop-FinahuntServerIfOwned($ProjectRoot, $ServerInfo) {
  if ($null -eq $ServerInfo -or -not $ServerInfo.started -or $null -eq $ServerInfo.pid) { return }
  $proc = Get-Process -Id $ServerInfo.pid -ErrorAction SilentlyContinue
  if ($proc) {
    taskkill /PID $ServerInfo.pid /T /F | Out-Null
    Add-VerificationResult $ProjectRoot 'server:stop' 'PASS' "Stopped harness-owned local server PID $($ServerInfo.pid)" ''
  }
}

function Write-AutoExecuteMarkdown($Path, $Content) {
  Ensure-Dir (Split-Path $Path)
  $Content | Set-Content -Encoding UTF8 $Path
}
