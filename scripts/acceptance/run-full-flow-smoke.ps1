param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = 'fast', [string]$BaseUrl = 'http://127.0.0.1:3021')
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
$server = $null
try {
  $server = Start-FinahuntServerIfNeeded $ProjectRoot $BaseUrl
  $flags = @('--routes','--api','--integration')
  if ($Mode -ne 'fast') { $flags += '--screenshots' }
  $ok = Invoke-LoggedCommand $ProjectRoot "smoke:full-flow-$Mode" { python tools/full_acceptance_smoke.py --base-url $BaseUrl @flags } "smoke-full-flow-$Mode.log" $ProjectRoot
  if (!$ok) { exit 1 }
  if ($Mode -eq 'full') {
    $ok2 = Invoke-LoggedCommand $ProjectRoot 'smoke:python-commands' { python tools/full_acceptance_smoke.py --base-url $BaseUrl --python-commands } 'smoke-python-commands.log' $ProjectRoot
    if (!$ok2) { exit 1 }
  }
} finally { Stop-FinahuntServerIfOwned $ProjectRoot $server }
