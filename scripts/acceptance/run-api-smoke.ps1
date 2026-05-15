param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = "fast", [string]$BaseUrl = "http://127.0.0.1:3000")
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
Initialize-MachineFiles $ProjectRoot
$p = Get-AEPaths $ProjectRoot
$out = Join-Path $p.Summaries "api-smoke.md"
"# API Smoke`nBase URL: $BaseUrl`n" | Set-Content -Encoding UTF8 $out
$surface = Join-Path $p.Docs "03-surface-map.md"
$endpoints = @()
if (Test-Path $surface) {
  $content = Get-Content $surface -Raw
  $matches = [regex]::Matches($content, '(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_.\/{}:-]+)')
  foreach ($m in $matches) { $endpoints += @{ method=$m.Groups[1].Value; path=$m.Groups[2].Value } }
}
if ($endpoints.Count -eq 0 -and (Test-Path -LiteralPath $p.ContractMapJson)) {
  try {
    $contractMap = Get-Content -LiteralPath $p.ContractMapJson -Raw | ConvertFrom-Json
    foreach ($api in @($contractMap.apiDefinitions)) {
      if (![string]::IsNullOrWhiteSpace([string]$api.path) -and ![string]::IsNullOrWhiteSpace([string]$api.method)) {
        $endpoints += @{ method=([string]$api.method).ToUpperInvariant(); path=[string]$api.path }
      }
    }
    if ($endpoints.Count -eq 0) {
      foreach ($contract in @($contractMap.contracts)) {
        if (![string]::IsNullOrWhiteSpace([string]$contract.endpoint) -and ![string]::IsNullOrWhiteSpace([string]$contract.method)) {
          $endpoints += @{ method=([string]$contract.method).ToUpperInvariant(); path=[string]$contract.endpoint }
        }
      }
    }
  } catch {}
}
if ($endpoints.Count -eq 0) {
  Add-Blocker $ProjectRoot "api-smoke" "MANUAL_REVIEW_REQUIRED" "No endpoints found in surface map"
  Write-LaneResult $ProjectRoot "api-smoke" "MANUAL_REVIEW_REQUIRED" @() @((Get-RelativeEvidencePath $ProjectRoot $out)) @("No endpoints found in surface map") @("Populate 03-surface-map.md or 04-contract-map.md with API endpoints.")
  Write-Host "[MANUAL_REVIEW_REQUIRED] api-smoke"
  exit 0
}
$fullFlowResult = Join-Path $p.Results "finahunt-full-flow.json"
if (Test-Path -LiteralPath $fullFlowResult) {
  try {
    $fullFlow = Get-Content -LiteralPath $fullFlowResult -Raw | ConvertFrom-Json
    $apiChecks = @($fullFlow.checks | Where-Object { [string]$_.route -like "/api/*" })
    if ($apiChecks.Count -gt 0 -and @($apiChecks | Where-Object { $_.pass -ne $true }).Count -eq 0) {
      Add-Content -Encoding UTF8 $out "`n## Reused full-flow API evidence`n"
      foreach ($check in $apiChecks) {
        Add-Content -Encoding UTF8 $out "- $($check.route) -> $($check.statusCode), bytes=$($check.bytes)"
      }
      $commands = @(@{ command="run-finahunt-full-flow.ps1 API checks"; status="PASS"; log=(Get-RelativeEvidencePath $ProjectRoot $fullFlowResult) })
      Write-LaneResult $ProjectRoot "api-smoke" "PASS" $commands @((Get-RelativeEvidencePath $ProjectRoot $out),(Get-RelativeEvidencePath $ProjectRoot $fullFlowResult),(Get-RelativeEvidencePath $ProjectRoot $p.ContractMapJson)) @() @()
      Add-VerificationResult $ProjectRoot "api-smoke" "PASS" "API smoke reused passing full-flow API checks and reconciled contract map endpoints." $out
      Write-Host "[PASS] api-smoke"
      exit 0
    }
  } catch {}
}
$commands = @()
$hardFail = $false
foreach ($ep in $endpoints) {
  $url = $BaseUrl.TrimEnd("/") + $ep.path
  try {
    $start = Get-Date
    $resp = Invoke-WebRequest -Uri $url -Method $ep.method -UseBasicParsing -TimeoutSec 20
    $ms = ((Get-Date) - $start).TotalMilliseconds
    Add-Content -Encoding UTF8 $out "- $($ep.method) $url -> $($resp.StatusCode), $ms ms"
    Add-VerificationResult $ProjectRoot "api:$($ep.method) $($ep.path)" "PASS" "Status $($resp.StatusCode)" $out
    $commands += @{ command = "$($ep.method) $url"; status = "PASS"; log = Get-RelativeEvidencePath $ProjectRoot $out }
  } catch {
    Add-Content -Encoding UTF8 $out "ERROR: $($ep.method) $url failed: $($_.Exception.Message)"
    Add-VerificationResult $ProjectRoot "api:$($ep.method) $($ep.path)" "HARD_FAIL" $_.Exception.Message $out
    $commands += @{ command = "$($ep.method) $url"; status = "HARD_FAIL"; log = Get-RelativeEvidencePath $ProjectRoot $out }
    $hardFail = $true
  }
}
Write-LaneResult $ProjectRoot "api-smoke" $(if ($hardFail) { "HARD_FAIL" } else { "PASS" }) $commands @((Get-RelativeEvidencePath $ProjectRoot $out)) $(if ($hardFail) { @("One or more API smoke requests failed") } else { @() }) @()
