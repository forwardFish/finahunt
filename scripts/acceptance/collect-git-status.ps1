param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = 'fast')
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
$p = Get-AEPaths $ProjectRoot
$out = Join-Path $p.Summaries 'git-status.md'
Push-Location $ProjectRoot
try {
  "# Git Status`n`nGenerated: $(Get-Date)`n`n```text" | Set-Content -Encoding UTF8 $out
  git branch --show-current 2>&1 | Add-Content -Encoding UTF8 $out
  git status --short 2>&1 | Add-Content -Encoding UTF8 $out
  git log --oneline --decorate -5 2>&1 | Add-Content -Encoding UTF8 $out
  Add-Content -Encoding UTF8 $out '```'
  Add-VerificationResult $ProjectRoot 'collect-git-status' 'PASS' 'Git status collected' $out
  Write-Host '[PASS] collect-git-status'
} finally { Pop-Location }
