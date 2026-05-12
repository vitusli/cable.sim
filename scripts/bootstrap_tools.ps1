# Bootstrap the tools/ folder (packman + repoman) by copying from a reference Kit extension repo.
# This avoids vendoring NVIDIA's bootstrap files in our git history.
#
# Usage:
#   .\scripts\bootstrap_tools.ps1 -Reference "A:\isaac-sim-exts\cable-extension"

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Reference
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$srcTools = Join-Path $Reference "tools"
$dstTools = Join-Path $repoRoot "tools"

if (-not (Test-Path -LiteralPath $srcTools)) {
    throw "Reference tools dir not found: $srcTools"
}

Write-Host "Copying tools/ from $srcTools -> $dstTools"
Copy-Item -LiteralPath $srcTools -Destination $repoRoot -Recurse -Force

Write-Host "Done. Run '.\repo.bat build' next." -ForegroundColor Green
