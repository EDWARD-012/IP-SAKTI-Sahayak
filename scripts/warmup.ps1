#Requires -Version 5.1
<#
.SYNOPSIS
    Warm embeddings + Ollama before a live SIH Ask demo.

.EXAMPLE
    .\scripts\warmup.ps1
    .\scripts\warmup.ps1 -SkipOllama
#>

[CmdletBinding()]
param(
    [switch]$SkipOllama,
    [switch]$NoGenerate
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
    Write-Host "WARNING: .venv not found; using system python" -ForegroundColor Yellow
}

$argsList = @("manage.py", "warmup")
if ($SkipOllama) { $argsList += "--skip-ollama" }
if ($NoGenerate) { $argsList += "--no-generate" }

Write-Host "IP-SAKTI warmup" -ForegroundColor Cyan
& $Python @argsList
if ($LASTEXITCODE -ne 0) { throw "warmup failed (exit $LASTEXITCODE)" }
