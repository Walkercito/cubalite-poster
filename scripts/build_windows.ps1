# Build a lean Windows distribution of Cubalite Poster.
#
# Prerequisites (run on Windows):
#   - uv  https://docs.astral.sh/uv/
#   - Python 3.12+ (uv will manage it)
#
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
#
# Output:
#   dist/CubalitePoster/CubalitePoster.exe   (+ sibling DLLs — ship the whole folder)
#   dist/CubalitePoster.zip                 (ready to hand to operators)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "==> Sync packaging dependencies" -ForegroundColor Cyan
# Prefer the lockfile so CI and local builds resolve the same wheels.
uv sync --group packaging --frozen
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frozen sync failed; falling back to uv sync --group packaging" -ForegroundColor Yellow
    uv sync --group packaging
}

Write-Host "==> Clean previous build artefacts" -ForegroundColor Cyan
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist\CubalitePoster) { Remove-Item -Recurse -Force dist\CubalitePoster }
if (Test-Path dist\CubalitePoster.zip) { Remove-Item -Force dist\CubalitePoster.zip }

Write-Host "==> PyInstaller (onedir, no UPX)" -ForegroundColor Cyan
uv run pyinstaller --noconfirm --clean packaging/cubalite_poster.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

$distDir = "dist\CubalitePoster"
$exePath = Join-Path $distDir "CubalitePoster.exe"
if (-not (Test-Path $exePath)) {
    throw "Expected $exePath was not produced"
}

Write-Host "==> Zip for distribution" -ForegroundColor Cyan
Compress-Archive -Path $distDir -DestinationPath "dist\CubalitePoster.zip" -Force

$size = (Get-ChildItem -Recurse $distDir | Measure-Object -Property Length -Sum).Sum
$sizeMb = [math]::Round($size / 1MB, 1)
$zipMb = [math]::Round((Get-Item "dist\CubalitePoster.zip").Length / 1MB, 1)

Write-Host ""
Write-Host "Build OK" -ForegroundColor Green
Write-Host "  Folder : $distDir  (~${sizeMb} MB)"
Write-Host "  Zip    : dist\CubalitePoster.zip  (~${zipMb} MB)"
Write-Host "  Launch : $exePath"
Write-Host ""
Write-Host "Ship the whole CubalitePoster folder (or the zip), not just the .exe."
Write-Host "Optional: Authenticode-sign CubalitePoster.exe to minimise SmartScreen prompts."
