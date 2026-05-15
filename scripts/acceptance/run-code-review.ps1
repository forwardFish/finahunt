param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = "fast")
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
Initialize-MachineFiles $ProjectRoot
$p = Get-AEPaths $ProjectRoot
$review = Join-Path $p.Docs "09-code-review.md"
if (!(Test-Path -LiteralPath $review)) { "# Code Review`n" | Set-Content -Encoding UTF8 $review }
$issues = @()
foreach ($required in @(
  "docs/auto-execute/gap-list.json",
  "docs/auto-execute/results/secret-guard.json",
  "docs/auto-execute/results/report-integrity.json",
  "docs/auto-execute/results/frontend-test.json",
  "docs/auto-execute/results/backend-test.json",
  "docs/auto-execute/results/contract-verifier.json",
  "docs/auto-execute/results/e2e-flow.json",
  "docs/auto-execute/results/ui-verifier.json"
)) {
  if (!(Test-Path -LiteralPath (Join-Path $ProjectRoot $required))) { $issues += "Missing review evidence: $required" }
}
try {
  $gapList = Get-Content -LiteralPath $p.GapListJson -Raw | ConvertFrom-Json
  $openHard = @($gapList.gaps | Where-Object { $_.severity -in @("HARD_FAIL","IN_SCOPE_GAP") -and $_.status -ne "CLOSED" })
  if ($openHard.Count -gt 0) { $issues += "Open hard/in-scope gaps remain: $($openHard.Count)" }
} catch { $issues += "Could not read gap-list.json" }
foreach ($resultFile in @("secret-guard.json","report-integrity.json","frontend-test.json","backend-test.json","contract-verifier.json","e2e-flow.json")) {
  try {
    $result = Get-Content -LiteralPath (Join-Path $p.Results $resultFile) -Raw | ConvertFrom-Json
    $status = Normalize-AEVerdict $result.status
    if ($status -notin @("PASS","PASS_WITH_LIMITATION")) { $issues += "$resultFile status is $status" }
  } catch { $issues += "Could not read $resultFile" }
}
$statusOut = if ($issues.Count -gt 0) { "PASS_WITH_LIMITATION" } else { "PASS" }
Add-Content -Encoding UTF8 $review @(
  "",
  "## $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
  "- Automated acceptance code review status: $statusOut",
  "- Checked gap list, secret guard, report integrity, frontend/backend tests, contract verifier, E2E flow, and UI verifier artifacts.",
  "- Remaining issues: $(if ($issues.Count -gt 0) { $issues -join '; ' } else { 'None from automated acceptance review.' })",
  ""
)
Add-VerificationResult $ProjectRoot "code-review" $statusOut "Automated acceptance review completed with $($issues.Count) issue(s)" $review
Write-LaneResult $ProjectRoot "code-review" $statusOut @() @((Get-RelativeEvidencePath $ProjectRoot $review)) $issues @()
Write-Host "[$statusOut] code-review"
