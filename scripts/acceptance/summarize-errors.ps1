param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = 'fast')
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
$p = Get-AEPaths $ProjectRoot
$out = Join-Path $p.Summaries 'error-summary.md'
"# Error Summary`nGenerated: $(Get-Date)`nMode: $Mode`n" | Set-Content -Encoding UTF8 $out
$hits = 0
if (Test-Path $p.Logs) {
  Get-ChildItem $p.Logs -File | ForEach-Object {
    $m = Select-String -Path $_.FullName -Pattern 'HARD_FAIL|Traceback|Error:|ERROR|failed|Exception' -ErrorAction SilentlyContinue
    if ($m) { $hits += $m.Count; Add-Content -Encoding UTF8 $out "`n## $($_.Name)"; $m | Select-Object -First 20 | ForEach-Object { Add-Content -Encoding UTF8 $out "- Line $($_.LineNumber): $($_.Line.Trim())" } }
  }
}
$status = if ($hits -eq 0) { 'PASS' } else { 'MANUAL_REVIEW_REQUIRED' }
Add-VerificationResult $ProjectRoot 'summarize-errors' $status "$hits error-like log line(s) summarized" $out
Write-Host "[$status] summarize-errors"
