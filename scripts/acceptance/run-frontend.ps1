param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = 'fast')
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
$web = Join-Path $ProjectRoot 'apps\web'
$ok = Invoke-LoggedCommand $ProjectRoot 'frontend:build' { npm run build } 'frontend-build.log' $web
if (!$ok) { exit 1 }
