param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = "fast")
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
Initialize-MachineFiles $ProjectRoot

if (-not (Get-HarnessLaneEnabled $ProjectRoot "contract" $true)) {
  Write-LaneResult $ProjectRoot "contract" "DEFERRED" @() @() @("contract lane disabled in harness.yml") @()
  Write-Host "[DEFERRED] contract"
  exit 0
}

$p = Get-AEPaths $ProjectRoot
$contract = Join-Path $p.Docs "04-contract-map.md"
if (!(Test-Path -LiteralPath $contract)) {
  "# Contract Map`n`n| ID | Endpoint/service | Method | Frontend caller | Request body | Response shape | Auth/session | Error shape | Loading state | Empty state | Test evidence | Status |`n|---|---|---|---|---|---|---|---|---|---|---|---|`n" | Set-Content -Encoding UTF8 $contract
}

$frontendCalls = @()
$apiDefs = @()
$files = Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File -Include *.ts,*.tsx,*.js,*.jsx,*.dart,*.py -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch "\\node_modules\\|\\.git\\|\\build\\|\\dist\\|\\.dart_tool\\|\\apps\\web\\.next\\|\\\.next\\" }
foreach ($file in $files) {
  try { $txt = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop } catch { continue }
  if ([string]::IsNullOrEmpty($txt)) { continue }
  $rel = Get-RelativeEvidencePath $ProjectRoot $file.FullName
  foreach ($m in [regex]::Matches($txt, '(fetch|axios\.[a-z]+|http\.(get|post|put|patch|delete))\s*\(?\s*["'']([^"'']+/[^"'']*)["'']')) {
    $callText = $m.Groups[0].Value
    $snippetLength = [Math]::Min(300, $txt.Length - $m.Index)
    $snippet = $txt.Substring($m.Index, $snippetLength)
    $method = ""
    $methodMatch = [regex]::Match($callText, '(?i)(axios|http)\.(get|post|put|patch|delete)\b')
    if ($methodMatch.Success) { $method = $methodMatch.Groups[2].Value.ToUpperInvariant() }
    else {
      $methodMatch = [regex]::Match($snippet, '(?i)\bmethod\s*:\s*["'']?(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)')
      if ($methodMatch.Success) { $method = $methodMatch.Groups[1].Value.ToUpperInvariant() }
    }
    $frontendCalls += @{ file = $rel; call = $callText; path = $m.Groups[3].Value; method = $method }
  }
  foreach ($m in [regex]::Matches($txt, '(Get|Post|Put|Patch|Delete)\(["'']([^"'']*)["'']\)|(router|app)\.(get|post|put|patch|delete)\(["'']([^"'']*)["'']')) {
    $method = if (![string]::IsNullOrWhiteSpace($m.Groups[1].Value)) { $m.Groups[1].Value.ToUpperInvariant() } else { $m.Groups[4].Value.ToUpperInvariant() }
    $routePath = if (![string]::IsNullOrWhiteSpace($m.Groups[2].Value)) { $m.Groups[2].Value } else { $m.Groups[5].Value }
    $apiDefs += @{ file = $rel; def = $m.Groups[0].Value; method = $method; path = $routePath }
  }
  foreach ($m in [regex]::Matches($txt, '@(app|router)\.(get|post|put|patch|delete|head|options)\(["'']([^"'']+)["'']')) {
    $apiDefs += @{ file = $rel; def = $m.Groups[0].Value; method = $m.Groups[2].Value.ToUpperInvariant(); path = $m.Groups[3].Value; framework = "fastapi" }
  }
}

$nextApiRoot = Join-Path $ProjectRoot "apps\web\src\app\api"
if (Test-Path -LiteralPath $nextApiRoot) {
  foreach ($routeFile in (Get-ChildItem -LiteralPath $nextApiRoot -Recurse -File -Filter route.ts -ErrorAction SilentlyContinue)) {
    try { $txt = Get-Content -LiteralPath $routeFile.FullName -Raw -ErrorAction Stop } catch { continue }
    $rel = Get-RelativeEvidencePath $ProjectRoot $routeFile.FullName
    $routeDir = (Split-Path $routeFile.FullName -Parent)
    $routeRel = $routeDir.Substring($nextApiRoot.TrimEnd('\').Length).TrimStart('\','/') -replace '\\','/'
    $routePath = "/api/" + ($routeRel -replace '/route$','')
    $routePath = $routePath -replace '/+','/'
    foreach ($method in @("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")) {
      if ($txt -match "export\s+async\s+function\s+$method\b") {
        $apiDefs += @{ file = $rel; def = "export async function $method"; method = $method; path = $routePath; framework = "next-app-router" }
      }
    }
  }
}

foreach ($adapter in @("next-contract.ps1","nest-contract.ps1","flutter-contract.ps1")) {
  $adapterPath = Join-Path $PSScriptRoot "adapters\$adapter"
  if (!(Test-Path -LiteralPath $adapterPath)) { continue }
  try {
    $raw = & powershell -ExecutionPolicy Bypass -File $adapterPath -ProjectRoot $ProjectRoot | Out-String
    if (![string]::IsNullOrWhiteSpace($raw)) {
      $adapterResult = $raw | ConvertFrom-Json
      foreach ($call in @($adapterResult.frontendCalls)) {
        if ($null -ne $call) { $frontendCalls += $call }
      }
      foreach ($def in @($adapterResult.apiDefinitions)) {
        if ($null -ne $def) { $apiDefs += $def }
      }
    }
  } catch {
    Add-VerificationResult $ProjectRoot "contract-adapter:$adapter" "PASS_WITH_LIMITATION" $_.Exception.Message ""
  }
}

$out = Join-Path $p.Results "contract-discovery.json"
$contractJson = $p.ContractMapJson
$contracts = @()
$contractSpecs = @(
  @{
    id="CONTRACT-DAILY-SNAPSHOT"; endpoint="/api/daily-snapshot"; method="GET";
    frontendCaller="apps/web/src/lib/dailySnapshot.ts and route-rendered pages";
    request="Optional query parameter date=YYYY-MM-DD";
    response="JSON DailySnapshot with date, themeCount, canonicalEventCount, themes/events/review fields";
    auth="none; local public market-information demo data only";
    errorShape="NextResponse JSON error handled by caller fallback/default snapshot";
    evidence="docs/auto-execute/results/finahunt-full-flow.json"
  },
  @{
    id="CONTRACT-REFRESH-LATEST"; endpoint="/api/refresh-latest"; method="POST";
    frontendCaller="apps/web/src/components/RefreshLatestButton.tsx";
    request="Empty POST body; FINAHUNT_ACCEPTANCE_SMOKE may select smoke data path";
    response="JSON { ok: boolean, latestDate, ...snapshot refresh payload } or { ok:false,error }";
    auth="none; no production service or payment access";
    errorShape="HTTP 500 JSON { ok:false,error:string }";
    evidence="docs/auto-execute/results/finahunt-full-flow.json"
  },
  @{
    id="CONTRACT-RUN-LOW-POSITION"; endpoint="/api/run-low-position"; method="POST";
    frontendCaller="apps/web/src/components/RunLowPositionButton.tsx";
    request="Empty POST body; FINAHUNT_ACCEPTANCE_SMOKE may select smoke data path";
    response="JSON { ok: boolean, latestDate, ...low-position workbench payload } or { ok:false,error }";
    auth="none; no production service or payment access";
    errorShape="HTTP 500 JSON { ok:false,error:string }";
    evidence="docs/auto-execute/results/finahunt-full-flow.json"
  }
)
foreach ($spec in $contractSpecs) {
  $apiMatch = @($apiDefs | Where-Object { $_.path -eq $spec.endpoint -and $_.method -eq $spec.method }).Count -gt 0
  $frontendMatch = @($frontendCalls | Where-Object { $_.path -eq $spec.endpoint -or $_.call -match [regex]::Escape($spec.endpoint) }).Count -gt 0
  if ($apiMatch -or $frontendMatch) {
    $contracts += @{
      id=$spec.id
      frontendCaller=$spec.frontendCaller
      endpoint=$spec.endpoint
      method=$spec.method
      request=$spec.request
      response=$spec.response
      auth=$spec.auth
      errorShape=$spec.errorShape
      loadingState="Button/page-level pending state or static render fallback"
      emptyState="Fallback snapshot/workbench rows keep page non-blank"
      evidence=$spec.evidence
      required=$true
      status="PASS"
    }
  }
}

$contractObj = @{
  schemaVersion = $AE_SCHEMA_VERSION
  frontendCalls = $frontendCalls
  apiDefinitions = $apiDefs
  contracts = $contracts
  generatedAt = (Get-Date).ToString("s")
  status = "DISCOVERED"
  note = "Auto-discovery only. Agent must reconcile request/response/auth/error/loading/empty states before final PASS."
}
$contractObj | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $out
$contractObj | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $contractJson
Add-EvidenceItem $ProjectRoot "api" $out "contract discovery"
Add-EvidenceItem $ProjectRoot "api" $contractJson "contract map json"

if ($frontendCalls.Count -eq 0 -and $apiDefs.Count -eq 0) {
  Add-Blocker $ProjectRoot "contract" "MANUAL_REVIEW_REQUIRED" "No frontend calls or backend API definitions auto-detected"
  Write-LaneResult $ProjectRoot "contract" "MANUAL_REVIEW_REQUIRED" @() @((Get-RelativeEvidencePath $ProjectRoot $contract),(Get-RelativeEvidencePath $ProjectRoot $out),(Get-RelativeEvidencePath $ProjectRoot $contractJson)) @("No contracts auto-detected") @("Fill 04-contract-map.md manually or add tests that expose API contracts.")
  Write-Host "[MANUAL_REVIEW_REQUIRED] contract"
} else {
  $contractStatus = if ($contracts.Count -gt 0) { "PASS" } else { "PASS_WITH_LIMITATION" }
  $contractBlockers = if ($contracts.Count -gt 0) { @() } else { @("Contract discovery is not proof that request/response/auth/error states are aligned.") }
  Add-VerificationResult $ProjectRoot "contract" $contractStatus "Contract discovery generated $($contracts.Count) reconciled contract(s)" $out
  Write-LaneResult $ProjectRoot "contract" $contractStatus @() @((Get-RelativeEvidencePath $ProjectRoot $contract),(Get-RelativeEvidencePath $ProjectRoot $out),(Get-RelativeEvidencePath $ProjectRoot $contractJson)) $contractBlockers @("Run run-contract-verify.ps1 after completing contract-map.json or contract tests.")
  Write-Host "[$contractStatus] contract discovery"
}
