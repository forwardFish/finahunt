param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = 'fast')
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
$p = Get-AEPaths $ProjectRoot
$out = Join-Path $p.Docs '00-environment-snapshot.md'
"# Environment Snapshot`n`nGenerated: $(Get-Date)`n`nMode: $Mode`n" | Set-Content -Encoding UTF8 $out
foreach ($cmd in @('git --version','node -v','npm -v','python --version')) {
  Add-Content -Encoding UTF8 $out "`n## $cmd`n```text"
  try { Invoke-Expression $cmd 2>&1 | Out-String | Add-Content -Encoding UTF8 $out } catch { Add-Content -Encoding UTF8 $out "ERROR: $($_.Exception.Message)" }
  Add-Content -Encoding UTF8 $out '```'
}
Add-VerificationResult $ProjectRoot 'collect-env' 'PASS' 'Environment snapshot generated' $out
Write-Host '[PASS] collect-env'
