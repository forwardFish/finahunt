param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = 'fast', [string]$BaseUrl = 'http://127.0.0.1:3021')
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
$server = $null
try {
  $server = Start-FinahuntServerIfNeeded $ProjectRoot $BaseUrl
  $ok = Invoke-LoggedCommand $ProjectRoot 'smoke:api' { python tools/full_acceptance_smoke.py --base-url $BaseUrl --api } 'smoke-api.log' $ProjectRoot
  if (!$ok) { exit 1 }
} finally { Stop-FinahuntServerIfOwned $ProjectRoot $server }
