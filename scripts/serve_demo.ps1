#Requires -Version 5.1
<#
.SYNOPSIS
    Serve IP-SAKTI Sahayak for SIH laptop jury demo (Waitress on localhost).

.DESCRIPTION
    Collects static files, runs migrations, then starts Waitress on 127.0.0.1:8000.

    Set DEMO_MODE=True in .env for the jury stub (no Ollama required).
    Set DEMO_MODE=False only if Ollama is running AND an active corpus is indexed.

.EXAMPLE
    .\scripts\serve_demo.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "IP-SAKTI Sahayak — SIH demo server" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host ""
Write-Host "Activate the venv first if needed:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
    Write-Host "WARNING: .venv not found; using system python" -ForegroundColor Yellow
}

Write-Host "collectstatic..."
& $Python manage.py collectstatic --noinput
if ($LASTEXITCODE -ne 0) { throw "collectstatic failed" }

Write-Host "migrate..."
& $Python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { throw "migrate failed" }

Write-Host ""
Write-Host "Starting Waitress on http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop."
Write-Host ""

$Waitress = Join-Path $ProjectRoot ".venv\Scripts\waitress-serve.exe"
if (Test-Path $Waitress) {
    & $Waitress --listen=127.0.0.1:8000 ip_sakti.wsgi:application
} else {
    & $Python -m waitress --listen=127.0.0.1:8000 ip_sakti.wsgi:application
}