param([string]$ProjectRoot = (Get-Location).Path)
. "$PSScriptRoot\lib.ps1"
$ProjectRoot = Get-ProjectRoot $ProjectRoot
Initialize-Layout $ProjectRoot
$p = Get-AEPaths $ProjectRoot

$templates = @{
  "00-environment-snapshot.md" = "# Environment Snapshot`n"
  "00-project-intake.md" = "# Project Intake`n`nProject root: $ProjectRoot`n"
  "01-task-decomposition.md" = "# Task Decomposition`n"
  "02-requirement-traceability-matrix.md" = "# Requirement Traceability Matrix`n`n| ID | Requirement | Source | Priority | Target | Acceptance | Evidence | Status | Notes |`n|---|---|---|---|---|---|---|---|---|`n"
  "03-surface-map.md" = "# Surface Map`n"
  "04-visual-acceptance-checklist.md" = "# Visual Acceptance Checklist`n"
  "05-known-gaps-and-assumptions.md" = "# Known Gaps and Assumptions`n"
  "06-test-matrix.md" = "# Test Matrix`n"
  "07-acceptance-test-plan.md" = "# Acceptance Test Plan`n"
  "08-repair-log.md" = "# Repair Log`n"
  "09-code-review.md" = "# Code Review`n"
  "10-agent-mistake-log.md" = "# Agent Mistake Log`n"
  "11-harness-improvement-log.md" = "# Harness Improvement Log`n"
  "FULL_FLOW_ACCEPTANCE.md" = "# Full Flow Acceptance`n"
  "UI_REFERENCE_INVENTORY.md" = "# UI Reference Inventory`n"
  "QUALITY_GATES.md" = "# Quality Gates`n`n- PASS`n- HARD_FAIL`n- DOCUMENTED_BLOCKER`n- DEFERRED`n- MANUAL_REVIEW_REQUIRED`n"
  "GOLDEN_RULES.md" = "# Golden Rules`n`n- Do not fake pass.`n- Do not delete tests.`n- Do not invent undocumented APIs.`n- Do not access production services.`n- Do not run git reset/git clean.`n"
  "AGENT_READABILITY.md" = "# Agent Readability`n`nStart with AGENTS.md, progress.md, feature_list.json, and run-all.ps1.`n"
  "verification-results.md" = "# Verification Results`n"
  "blockers.md" = "# Blockers`n"
  "progress.md" = "# Progress`n`nHarness initialized.`n"
}

foreach ($name in $templates.Keys) {
  $path = Join-Path $p.Docs $name
  if (!(Test-Path $path)) { $templates[$name] | Set-Content -Encoding UTF8 $path }
}

$featureList = Join-Path $p.Features "feature_list.json"
if (!(Test-Path $featureList)) {
  $data = @{
    project = (Split-Path $ProjectRoot -Leaf)
    schemaVersion = "0.1"
    generatedAt = (Get-Date).ToString("s")
    features = @(
      @{
        id = "FE-HARNESS-001"
        category = "harness"
        priority = "P0"
        description = "Harness is initialized and run-all fast mode has been executed"
        source = "docs/auto-execute"
        surface = "harness"
        relatedFiles = @("docs/auto-execute","scripts/acceptance")
        requiredGates = @("init-harness","run-all-fast")
        evidenceRequired = @("verification-results.md","AUTO_EXECUTE_DELIVERY_REPORT.md")
        passes = $false
        evidence = @()
        notes = ""
      }
    )
  }
  $data | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $featureList
}
if (!(Test-Path (Join-Path $p.Features "feature_status.json"))) {
  @{ updatedAt=(Get-Date).ToString("s"); statuses=@{} } | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $p.Features "feature_status.json")
}
if (!(Test-Path (Join-Path $p.Features "current_feature.json"))) {
  @{ current=$null; updatedAt=(Get-Date).ToString("s") } | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $p.Features "current_feature.json")
}

# UI inventory
$inventory = Join-Path $p.Docs "UI_REFERENCE_INVENTORY.md"
"# UI Reference Inventory`n" | Set-Content -Encoding UTF8 $inventory
foreach ($dir in @((Join-Path $ProjectRoot "docs\design\UI"), (Join-Path $ProjectRoot "docs\UI"))) {
  if (Test-Path $dir) {
    Add-Content -Encoding UTF8 $inventory "`n## $dir`n"
    Get-ChildItem $dir -Recurse -File -Include *.png,*.jpg,*.jpeg,*.webp,*.gif,*.html | ForEach-Object {
      Add-Content -Encoding UTF8 $inventory "- $($_.FullName)"
    }
  }
}

Update-State $ProjectRoot "init" "initialized" "Run scripts/acceptance/run-all.ps1 -Mode fast"
Add-VerificationResult $ProjectRoot "init-harness" "PASS" "Harness initialized" ""
Write-Host "[PASS] Harness initialized"
