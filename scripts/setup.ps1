#Requires -Version 5.1
<#
.SYNOPSIS
    IP-SAKTI Sahayak — Windows development setup script.
.DESCRIPTION
    Creates the virtual environment, installs dependencies, copies .env if
    absent, runs database migrations, and checks for Ollama.
    Run from the project root (C:\IP-SAKTI-Sahayak\) — administrator rights
    are not required unless your execution policy blocks unsigned scripts.
.EXAMPLE
    Set-Location C:\IP-SAKTI-Sahayak
    .\scripts\setup.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# ── Helpers ───────────────────────────────────────────────────────────────────

function Write-Step { param([string]$M) Write-Host "`n  ▶  $M" -ForegroundColor Cyan    }
function Write-Ok   { param([string]$M) Write-Host "     ✓  $M" -ForegroundColor Green  }
function Write-Warn { param([string]$M) Write-Host "     ⚠  $M" -ForegroundColor Yellow }
function Write-Fail { param([string]$M) Write-Host "     ✗  $M" -ForegroundColor Red    }

# ── 1. Python version check ───────────────────────────────────────────────────

Write-Step "Checking Python version"

try {
    $pyOut = & python --version 2>&1
    if ($pyOut -match 'Python (\d+)\.(\d+)') {
        [int]$major = $Matches[1]; [int]$minor = $Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Fail "Python 3.11+ required. Found: $pyOut"
            exit 1
        }
        Write-Ok $pyOut
    } else {
        Write-Fail "Cannot parse Python version output: $pyOut"
        exit 1
    }
} catch {
    Write-Fail "Python is not installed or not in PATH."
    Write-Host "     Download from https://www.python.org/downloads/" -ForegroundColor White
    exit 1
}

# ── 2. Create virtual environment ─────────────────────────────────────────────

Write-Step "Creating virtual environment (.venv)"

$VenvPath = Join-Path $ProjectRoot '.venv'

if (Test-Path $VenvPath) {
    Write-Warn ".venv already exists — skipping creation"
} else {
    try {
        & python -m venv $VenvPath
        Write-Ok "Virtual environment created at $VenvPath"
    } catch {
        Write-Fail "Failed to create .venv: $_"
        exit 1
    }
}

# ── 3. Activate virtual environment ───────────────────────────────────────────

Write-Step "Activating virtual environment"

$Activate = Join-Path $VenvPath 'Scripts\Activate.ps1'
if (-not (Test-Path $Activate)) {
    Write-Fail "Activate.ps1 not found at $Activate"
    exit 1
}

try {
    . $Activate
    Write-Ok "Virtual environment activated"
} catch {
    Write-Fail "Activation failed: $_"
    exit 1
}

# ── 4. Install requirements ────────────────────────────────────────────────────

Write-Step "Installing Python dependencies from requirements.txt"

$ReqFile = Join-Path $ProjectRoot 'requirements.txt'
if (-not (Test-Path $ReqFile)) {
    Write-Fail "requirements.txt not found at $ReqFile"
    exit 1
}

try {
    & pip install -r $ReqFile --quiet --disable-pip-version-check
    Write-Ok "All dependencies installed"
} catch {
    Write-Fail "pip install failed: $_"
    exit 1
}

# ── 5. Copy .env.example → .env ───────────────────────────────────────────────

Write-Step "Setting up environment file"

$EnvFile    = Join-Path $ProjectRoot '.env'
$EnvExample = Join-Path $ProjectRoot '.env.example'

if (Test-Path $EnvFile) {
    Write-Warn ".env already exists — not overwriting"
} elseif (Test-Path $EnvExample) {
    try {
        Copy-Item $EnvExample $EnvFile
        Write-Ok ".env.example → .env (edit it before running in production)"
    } catch {
        Write-Fail "Could not copy .env.example: $_"
        exit 1
    }
} else {
    Write-Warn ".env.example not found — create .env manually before running"
}

# ── 6. Run database migrations ────────────────────────────────────────────────

Write-Step "Running database migrations"

Push-Location $ProjectRoot
try {
    & python manage.py migrate --no-input
    Write-Ok "Migrations applied"
} catch {
    Write-Fail "Migrations failed: $_"
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

# ── 7 & 8. Ollama check ───────────────────────────────────────────────────────

Write-Step "Checking for Ollama"

$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue

if ($ollamaCmd) {
    Write-Ok "Ollama found at: $($ollamaCmd.Source)"
    Write-Host ""
    Write-Warn "Pull the model if you have not done so yet:"
    Write-Host "         ollama pull qwen2.5:7b-instruct-q4_K_M" -ForegroundColor White
    Write-Host ""
    Write-Warn "Start Ollama before launching the app:"
    Write-Host "         ollama serve" -ForegroundColor White
} else {
    Write-Warn "Ollama not found in PATH. The app will run in DEMO_MODE without it."
    Write-Host "     Install from: https://ollama.com/download" -ForegroundColor White
}

# ── 9. Next steps ──────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "    Setup complete! Next steps:" -ForegroundColor Cyan
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "    1.  Edit .env with your configuration"
Write-Host "    2.  (Optional) ollama serve             — start LLM backend"
Write-Host "    3.  python manage.py runserver          — start dev server"
Write-Host "    4.  Open http://localhost:8000/ in your browser"
Write-Host ""
