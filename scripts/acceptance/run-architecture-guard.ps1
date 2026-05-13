param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = 'fast')
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
$p = Get-AEPaths $ProjectRoot
$out = Join-Path $p.Summaries 'architecture-guard.md'
"# Architecture Guard`nGenerated: $(Get-Date)`n" | Set-Content -Encoding UTF8 $out
$issues = 0
$scanRoots = @('scripts\acceptance','tools','apps\web\src')
$destructiveCommandPattern = '(^|\s|[;&|])(?:git|git\.exe)\s+(?:reset|clean)\b|(^|\s|[;&|])(?:git|git\.exe)\s+push\b[^\r\n]*--force\b|push\s+--force\b|force\s+push\b'
$externalProductionPattern = 'supabase\.co|stripe|payment|prod(?:uction)?\s+database'
foreach ($root in $scanRoots) {
  $dir = Join-Path $ProjectRoot $root
  if (!(Test-Path $dir)) { continue }
  Get-ChildItem $dir -Recurse -File -Include *.ps1,*.cmd,*.bat,*.sh,*.ts,*.tsx,*.py -ErrorAction SilentlyContinue | ForEach-Object {
    $txt = Get-Content -Raw -LiteralPath $_.FullName -ErrorAction SilentlyContinue
    $destructiveLines = @()
    ($txt -split "`r?`n") | ForEach-Object {
      $line = $_
      if ($line -match $destructiveCommandPattern -and $line -notmatch '(?i)do not|never|forbidden|golden rules') {
        $destructiveLines += $line.Trim()
      }
    }
    if ($destructiveLines.Count -gt 0) { Add-Content -Encoding UTF8 $out "HARD_FAIL destructive command pattern: $($_.FullName)"; $issues++ }
    if ((Split-Path $_.FullName -Leaf) -ne 'run-architecture-guard.ps1' -and $txt -match $externalProductionPattern) { Add-Content -Encoding UTF8 $out "MANUAL_REVIEW_REQUIRED external-production keyword: $($_.FullName)" }
  }
}
if ($issues -gt 0) { Add-VerificationResult $ProjectRoot 'architecture-guard' 'HARD_FAIL' "$issues destructive pattern(s)" $out; Add-Blocker $ProjectRoot 'architecture-guard' 'HARD_FAIL' "$issues destructive pattern(s)" $out; exit 1 }
Add-VerificationResult $ProjectRoot 'architecture-guard' 'PASS' 'No destructive git or production access patterns in executable acceptance scope' $out
Write-Host '[PASS] architecture-guard'
