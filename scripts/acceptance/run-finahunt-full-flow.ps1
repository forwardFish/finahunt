param([string]$ProjectRoot = (Get-Location).Path, [int]$Port = 3000)
$ErrorActionPreference = 'Stop'
$web = Join-Path $ProjectRoot 'apps\web'
$docs = Join-Path $ProjectRoot 'docs\auto-execute'
$logs = Join-Path $docs 'logs'
$results = Join-Path $docs 'results'
New-Item -ItemType Directory -Force -Path $logs,$results | Out-Null
$base = "http://127.0.0.1:$Port"
$out = Join-Path $results 'finahunt-full-flow.json'
$serverLog = Join-Path $logs 'full-flow-next-start.log'
$proc = $null
try {
  $proc = Start-Process -FilePath 'npm.cmd' -ArgumentList @('run','start','--','-p',"$Port") -WorkingDirectory $web -RedirectStandardOutput $serverLog -RedirectStandardError (Join-Path $logs 'full-flow-next-start.err.log') -PassThru -WindowStyle Hidden
  $ready = $false
  for ($i=0; $i -lt 45; $i++) {
    try { Invoke-WebRequest -Uri $base -UseBasicParsing -TimeoutSec 2 | Out-Null; $ready = $true; break } catch { Start-Sleep -Seconds 1 }
  }
  if (-not $ready) { throw "Next server did not become ready at $base" }
  $routes = @('/','/fermentation','/research','/workbench','/api/daily-snapshot')
  $checks = @()
  $disclaimer = -join ([int[]](19981,26500,25104,25237,36164,24314,35758) | ForEach-Object { [char]$_ })
  foreach ($route in $routes) {
    $url = $base + $route
    $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
    $body = [string]$resp.Content
    $ok = $resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400 -and $body.Length -gt 20
    if ($route -eq '/api/daily-snapshot') { $ok = $ok -and $body.Contains('themeCount') -and $body.Contains('canonicalEventCount') }
    else { $ok = $ok -and $body.Contains('Finahunt') -and $body.Contains($disclaimer) }
    $checks += [pscustomobject]@{ route=$route; statusCode=$resp.StatusCode; bytes=$body.Length; pass=$ok }
  }
  $allPass = (@($checks | Where-Object { -not $_.pass }).Count -eq 0)
  [pscustomobject]@{ lane='e2e-flow'; status=$(if($allPass){'PASS'}else{'HARD_FAIL'}); baseUrl=$base; checks=$checks; serverLog='docs/auto-execute/logs/full-flow-next-start.log'; updatedAt=(Get-Date).ToString('s') } | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $out
  if (-not $allPass) { exit 1 }
  exit 0
} finally {
  if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}
