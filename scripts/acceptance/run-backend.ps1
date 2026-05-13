param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = 'fast')
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
$ok = Invoke-LoggedCommand $ProjectRoot 'backend:compileall' { python -m compileall -q agents packages graphs workflows tools skills tests } 'backend-compileall.log' $ProjectRoot
if (!$ok) { exit 1 }
$ok = Invoke-LoggedCommand $ProjectRoot 'backend:pytest' { python -m pytest -q } 'backend-pytest.log' $ProjectRoot
if (!$ok) { exit 1 }
