#Requires -Version 5.1
<#
.SYNOPSIS
    IP-SAKTI Sahayak — Corpus ingestion script.
.DESCRIPTION
    Checks that Ollama is running, builds a corpus version, validates it,
    and activates it. Run this AFTER placing source PDFs in data/corpus/ and
    starting `ollama serve`.
.PARAMETER Version
    Corpus version number to build and activate. Defaults to 1.
.EXAMPLE
    Set-Location C:\IP-SAKTI-Sahayak
    .\scripts\ingest.ps1
    .\scripts\ingest.ps1 -Version 2
#>

[CmdletBinding()]
param(
    [int]$Version = 1
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# ── Helpers ───────────────────────────────────────────────────────────────────

function Write-Step { param([string]$M) Write-Host "`n  ▶  $M" -ForegroundColor Cyan    }
function Write-Ok   { param([string]$M) Write-Host "     ✓  $M" -ForegroundColor Green  }
function Write-Warn { param([string]$M) Write-Host "     ⚠  $M" -ForegroundColor Yellow }
function Write-Fail { param([string]$M) Write-Host "     ✗  $M" -ForegroundColor Red    }

# ── 1. Verify Ollama is reachable ────────────────────────────────────────────

Write-Step "Verifying Ollama is running"

try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:11434/api/tags' `
                              -UseBasicParsing -TimeoutSec 5
    if ($resp.StatusCode -ne 200) { throw "Unexpected HTTP $($resp.StatusCode)" }
    Write-Ok "Ollama is up at 127.0.0.1:11434"
} catch {
    Write-Fail "Ollama is not reachable: $_"
    Write-Warn "Start it with:  ollama serve"
    exit 1
}

Push-Location $ProjectRoot

# ── 2. Build corpus version ───────────────────────────────────────────────────

Write-Step "Building corpus version $Version"

try {
    & python manage.py build_corpus_version --version $Version
    Write-Ok "Corpus version $Version built"
} catch {
    Write-Fail "build_corpus_version failed: $_"
    Pop-Location
    exit 1
}

# ── 3. Validate corpus version ────────────────────────────────────────────────

Write-Step "Validating corpus version $Version"

try {
    & python manage.py validate_corpus_version --version $Version
    Write-Ok "Corpus version $Version validation passed"
} catch {
    Write-Fail "validate_corpus_version failed: $_"
    Write-Warn "Resolve validation errors before activating."
    Pop-Location
    exit 1
}

# ── 4. Activate corpus version ────────────────────────────────────────────────

Write-Step "Activating corpus version $Version"

try {
    & python manage.py activate_corpus_version --version $Version
    Write-Ok "Corpus version $Version is now active"
} catch {
    Write-Fail "activate_corpus_version failed: $_"
    Pop-Location
    exit 1
}

# ── 5. Print corpus statistics ────────────────────────────────────────────────

Write-Step "Fetching corpus statistics"

$statsScript = @"
from corpus.models import CorpusVersion, CorpusDocument
active = CorpusVersion.objects.filter(is_active=True).order_by('-id').first()
if active:
    docs = CorpusDocument.objects.filter(version=active).count()
    print(f'  Active version : {active.version}')
    print(f'  Documents      : {docs}')
    print(f'  Created at     : {active.created_at}')
else:
    print('  No active corpus version found.')
"@

try {
    & python manage.py shell -c $statsScript
} catch {
    Write-Warn "Could not retrieve corpus stats (model may not exist yet): $_"
}

Pop-Location

Write-Host ""
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "    Corpus ingestion complete! Version $Version is now active." -ForegroundColor Green
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
