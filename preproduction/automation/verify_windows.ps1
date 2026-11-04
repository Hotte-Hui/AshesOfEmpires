# Read-only local verification; runs no Unreal Engine commands and installs nothing.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
Write-Host "Ashes of Empires v0.4: Python checks" -ForegroundColor Cyan
py -3 tools/validate_v3.py
if ($LASTEXITCODE -ne 0) { throw 'Canonical v3 validation failed' }
py -3 tools/validate_integrity_v4.py
if ($LASTEXITCODE -ne 0) { throw 'Deep integrity validation failed' }
py -3 tools/story_engine_v4.py
if ($LASTEXITCODE -ne 0) { throw 'v4 reference story route failed' }
py -3 tools/build_preview_v4.py
if ($LASTEXITCODE -ne 0) { throw 'Preview generation failed' }
py -3 -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Regression tests failed' }
Write-Host "Offline checks passed. UE5 still needs an independent compile and playtest." -ForegroundColor Green
