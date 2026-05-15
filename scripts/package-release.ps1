param(
  [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$OutputDir = "",
  [string]$Version = "2.0"
)

$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$Path) {
  if (!(Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Copy-RequiredFile([string]$SourceRoot, [string]$StageRoot, [string]$RelativePath) {
  $source = Join-Path $SourceRoot $RelativePath
  if (!(Test-Path -LiteralPath $source)) {
    throw "Required release file missing: $RelativePath"
  }
  $target = Join-Path $StageRoot $RelativePath
  Ensure-Dir (Split-Path -Parent $target)
  Copy-Item -LiteralPath $source -Destination $target -Force
}

function Copy-GlobFiles([string]$SourceRoot, [string]$StageRoot, [string]$RelativeDir, [string[]]$Extensions) {
  $sourceDir = Join-Path $SourceRoot $RelativeDir
  if (!(Test-Path -LiteralPath $sourceDir)) {
    throw "Required release directory missing: $RelativeDir"
  }
  $targetDir = Join-Path $StageRoot $RelativeDir
  Ensure-Dir $targetDir
  foreach ($ext in $Extensions) {
    Get-ChildItem -LiteralPath $sourceDir -File -Filter "*.$ext" | ForEach-Object {
      Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $targetDir $_.Name) -Force
    }
  }
}

function Copy-TreeFiles([string]$SourceRoot, [string]$StageRoot, [string]$SourceRelativeDir, [string]$TargetRelativeDir) {
  $sourceDir = Join-Path $SourceRoot $SourceRelativeDir
  if (!(Test-Path -LiteralPath $sourceDir)) { return }
  $sourceFull = (Resolve-Path -LiteralPath $sourceDir).Path.TrimEnd('\') + '\'
  Get-ChildItem -LiteralPath $sourceDir -File -Recurse | ForEach-Object {
    $itemFull = [System.IO.Path]::GetFullPath($_.FullName)
    if (-not $itemFull.StartsWith($sourceFull, [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Refusing to package file outside source tree: $itemFull"
    }
    $rel = $itemFull.Substring($sourceFull.Length)
    $target = Join-Path (Join-Path $StageRoot $TargetRelativeDir) $rel
    Ensure-Dir (Split-Path -Parent $target)
    Copy-Item -LiteralPath $_.FullName -Destination $target -Force
  }
}

function Get-ZipEntries([string]$ZipPath) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
  try {
    return @($zip.Entries | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Name) } | ForEach-Object { $_.FullName.Replace("\", "/") })
  } finally {
    $zip.Dispose()
  }
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
  $OutputDir = Join-Path $ProjectRoot "dist"
}
Ensure-Dir $OutputDir
$OutputDir = (Resolve-Path -LiteralPath $OutputDir).Path

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zipName = "auto-execute-v$Version-clean-$timestamp.zip"
$zipPath = Join-Path $OutputDir $zipName
$stageRoot = Join-Path ([System.IO.Path]::GetTempPath()) "auto-execute-release-$([guid]::NewGuid().ToString('N'))"
Ensure-Dir $stageRoot

try {
  foreach ($file in @("SKILL.md", "README.md", "USAGE.md", "harness.yml.template")) {
    Copy-RequiredFile $ProjectRoot $stageRoot $file
  }

  Copy-GlobFiles $ProjectRoot $stageRoot "scripts\acceptance" @("ps1", "mjs")
  Copy-TreeFiles $ProjectRoot $stageRoot "templates\docs\auto-execute" "templates\docs\auto-execute"
  Copy-TreeFiles $ProjectRoot $stageRoot "docs\auto-execute\meta-tests\fixtures" "meta-tests\fixtures"

  Compress-Archive -Path (Join-Path $stageRoot "*") -DestinationPath $zipPath -Force

  $entries = Get-ZipEntries $zipPath
  $forbidden = @(
    "docs/auto-execute/results",
    "docs/auto-execute/logs",
    "docs/auto-execute/comparison",
    "docs/auto-execute/meta-tests/workspaces",
    "docs/auto-execute/evidence-manifest.json",
    "docs/auto-execute/machine-summary.json",
    "docs/AUTO_EXECUTE_DELIVERY_REPORT.md",
    "AUTO_EXECUTE_DELIVERY_REPORT.md"
  )
  $badEntries = @()
  foreach ($entry in $entries) {
    foreach ($pattern in $forbidden) {
      if ($entry.StartsWith($pattern, [System.StringComparison]::OrdinalIgnoreCase) -or $entry.Equals($pattern, [System.StringComparison]::OrdinalIgnoreCase)) {
        $badEntries += $entry
      }
    }
    if ($entry -match "(?i)(delivery[-_ ]?report|old[-_ ]?project[-_ ]?run|machine-summary\.json|evidence-manifest\.json)") {
      $badEntries += $entry
    }
  }
  $badEntries = @($badEntries | Select-Object -Unique)
  if ($badEntries.Count -gt 0) {
    throw "Release zip contains forbidden old run artifact(s): $($badEntries -join ', ')"
  }

  $manifestPath = Join-Path $OutputDir "auto-execute-v$Version-clean-$timestamp.manifest.json"
  @{
    schemaVersion = $Version
    zipPath = $zipPath
    entryCount = $entries.Count
    entries = $entries
    generatedAt = (Get-Date).ToString("s")
  } | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $manifestPath

  Write-Host "[PASS] clean release package created: $zipPath"
  Write-Host "[PASS] release entries: $($entries.Count)"
  Write-Host "[PASS] manifest: $manifestPath"
  exit 0
} finally {
  try {
    $resolvedStage = (Resolve-Path -LiteralPath $stageRoot -ErrorAction Stop).Path
    $tempRoot = [System.IO.Path]::GetTempPath()
    if ($resolvedStage.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolvedStage).StartsWith("auto-execute-release-", [System.StringComparison]::OrdinalIgnoreCase)) {
      Remove-Item -LiteralPath $resolvedStage -Recurse -Force
    }
  } catch {}
}
