param([string]$ProjectRoot = (Get-Location).Path, [string]$Mode = "fast", [string]$BackendDir = "")
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
Initialize-MachineFiles $ProjectRoot
$p = Get-AEPaths $ProjectRoot

if ($Mode -eq "fast") {
  Add-VerificationResult $ProjectRoot "db-e2e" "DEFERRED" "Skipped in fast mode" ""
  Write-LaneResult $ProjectRoot "db-e2e" "DEFERRED" @() @() @("Skipped in fast mode") @("Run -Mode gate or -Mode full with safe local Postgres.")
  Write-Host "[DEFERRED] db-e2e fast mode"
  exit 0
}

$commands = @()
$blockers = @()
$nextActions = @()
$hardFail = $false
$environmentBlocked = $false

if ($env:DATABASE_BACKEND -and $env:DATABASE_BACKEND -ne "postgres") {
  $hardFail = $true
  $blockers += "DATABASE_BACKEND=$env:DATABASE_BACKEND; structured warehouse lane requires postgres."
}
$env:DATABASE_BACKEND = "postgres"
if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
  $env:DATABASE_URL = "postgresql+psycopg://finahunt:finahunt_local@127.0.0.1:54329/finahunt"
}
if (Test-UnsafeDatabaseUrl $env:DATABASE_URL) {
  Add-Blocker $ProjectRoot "db-e2e" "DOCUMENTED_BLOCKER" "DATABASE_URL looks unsafe"
  Write-LaneResult $ProjectRoot "db-e2e" "DOCUMENTED_BLOCKER" @() @() @("DATABASE_URL looks unsafe") @()
  Write-Host "[DOCUMENTED_BLOCKER] db-e2e unsafe DATABASE_URL"
  exit 0
}

$compose = Join-Path $ProjectRoot "docker\docker-compose.yml"
$usesLocalComposePostgres = $env:DATABASE_URL -match "(@127\.0\.0\.1:54329|@localhost:54329|//127\.0\.0\.1:54329|//localhost:54329)"
if ($usesLocalComposePostgres -and !(Test-Path -LiteralPath $compose)) {
  $hardFail = $true
  $environmentBlocked = $true
  $blockers += "docker/docker-compose.yml not found; local Postgres service cannot be verified."
} elseif ($usesLocalComposePostgres -and !(Test-CommandExists "docker")) {
  $hardFail = $true
  $environmentBlocked = $true
  $blockers += "Docker unavailable; cannot verify local Postgres service."
} elseif ($usesLocalComposePostgres) {
  Push-Location $ProjectRoot
  try {
    $ok = Invoke-Gate $ProjectRoot "db:postgres-up" { docker compose -f $compose up -d postgres } "db-postgres-up.log"
    $commands += @{ command = "docker compose -f docker/docker-compose.yml up -d postgres"; status = $(if ($ok) { "PASS" } else { "HARD_FAIL" }); log = "docs/auto-execute/logs/db-postgres-up.log" }
    if (-not $ok) {
      $hardFail = $true
      $environmentBlocked = $true
      $blockers += "Docker Postgres service failed to start; see docs/auto-execute/logs/db-postgres-up.log."
    }
    $ok = Invoke-Gate $ProjectRoot "db:postgres-ps" { docker compose -f $compose ps postgres } "db-postgres-ps.log"
    $commands += @{ command = "docker compose -f docker/docker-compose.yml ps postgres"; status = $(if ($ok) { "PASS" } else { "HARD_FAIL" }); log = "docs/auto-execute/logs/db-postgres-ps.log" }
    if (-not $ok) {
      $hardFail = $true
      $environmentBlocked = $true
      $blockers += "Docker Postgres service is not running; see docs/auto-execute/logs/db-postgres-ps.log."
    }
  } finally {
    Pop-Location
  }
}

if (-not $environmentBlocked) {
  Push-Location $ProjectRoot
  try {
    $ok = Invoke-Gate $ProjectRoot "db:schema-bootstrap" { python -m packages.storage.migrations.bootstrap } "db-schema-bootstrap.log"
    $commands += @{ command = "python -m packages.storage.migrations.bootstrap"; status = $(if ($ok) { "PASS" } else { "HARD_FAIL" }); log = "docs/auto-execute/logs/db-schema-bootstrap.log" }
    if (-not $ok) { $hardFail = $true }

    $ok = Invoke-Gate $ProjectRoot "db:runtime-write-snapshot" { python tools/run_latest_snapshot.py --acceptance-smoke } "db-runtime-write-snapshot.log"
    $commands += @{ command = "python tools/run_latest_snapshot.py --acceptance-smoke"; status = $(if ($ok) { "PASS" } else { "HARD_FAIL" }); log = "docs/auto-execute/logs/db-runtime-write-snapshot.log" }
    if (-not $ok) { $hardFail = $true }

    $ok = Invoke-Gate $ProjectRoot "db:runtime-write-low-position" { python tools/run_low_position_workbench.py --acceptance-smoke } "db-runtime-write-low-position.log"
    $commands += @{ command = "python tools/run_low_position_workbench.py --acceptance-smoke"; status = $(if ($ok) { "PASS" } else { "HARD_FAIL" }); log = "docs/auto-execute/logs/db-runtime-write-low-position.log" }
    if (-not $ok) { $hardFail = $true }

    $ok = Invoke-Gate $ProjectRoot "db:repository-read-snapshot" { python tools/query_web_data.py daily-snapshot } "db-repository-read-snapshot.log"
    $commands += @{ command = "python tools/query_web_data.py daily-snapshot"; status = $(if ($ok) { "PASS" } else { "HARD_FAIL" }); log = "docs/auto-execute/logs/db-repository-read-snapshot.log" }
    if (-not $ok) { $hardFail = $true }

    $ok = Invoke-Gate $ProjectRoot "db:repository-read-low-position" { python tools/query_web_data.py low-position-workbench } "db-repository-read-low-position.log"
    $commands += @{ command = "python tools/query_web_data.py low-position-workbench"; status = $(if ($ok) { "PASS" } else { "HARD_FAIL" }); log = "docs/auto-execute/logs/db-repository-read-low-position.log" }
    if (-not $ok) { $hardFail = $true }
  } finally {
    Pop-Location
  }
}

$status = if ($environmentBlocked) { "BLOCKED_BY_ENVIRONMENT" } elseif ($hardFail) { "HARD_FAIL" } else { "PASS" }
if ($hardFail) {
  $nextActions += "Bring up local Docker Postgres, keep DATABASE_BACKEND=postgres, rerun schema bootstrap, runtime write, and repository/API read checks."
} else {
  $nextActions += "DB lane is ready; run integrated API/UI smoke to prove Next routes render the same dataset."
}
Write-LaneResult $ProjectRoot "db-e2e" $status $commands @("docs/auto-execute/logs/db-schema-bootstrap.log","docs/auto-execute/logs/db-runtime-write-snapshot.log","docs/auto-execute/logs/db-repository-read-snapshot.log") $blockers $nextActions
Add-VerificationResult $ProjectRoot "db-e2e" $status "Postgres service/schema/runtime write/repository read completed with status $status" (Join-Path $p.Results "db-e2e.json")
Write-Host "[$status] db-e2e"
exit (Get-AEExitCode $status)
