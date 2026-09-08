#Requires -Version 5.1
<#
.SYNOPSIS
    IP-SAKTI Sahayak — System readiness checker.
.DESCRIPTION
    Runs PASS/FAIL checks for all runtime dependencies and prints a summary
    table. Exits with code 0 when everything passes, or 1 when any check fails.
.EXAMPLE
    Set-Location C:\IP-SAKTI-Sahayak
    .\scripts\check_system.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'SilentlyContinue'
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Passed  = 0
$Failed  = 0
$Results = [System.Collections.Generic.List[PSCustomObject]]::new()

# ── Helper ─────────────────────────────────────────────────────────────────────

function Add-Check {
    param(
        [string]$Name,
        [bool]  $Ok,
        [string]$Detail = ''
    )
    $Results.Add([PSCustomObject]@{ Name = $Name; Ok = $Ok; Detail = $Detail })
    if ($Ok) { $script:Passed++ } else { $script:Failed++ }
}

# ── 1. Python version ──────────────────────────────────────────────────────────

try {
    $pyOut = & python --version 2>&1
    if ($pyOut -match 'Python (\d+)\.(\d+)') {
        [int]$maj = $Matches[1]; [int]$min = $Matches[2]
        $ok = ($maj -gt 3) -or ($maj -eq 3 -and $min -ge 11)
        Add-Check 'Python 3.11+' $ok $pyOut
    } else {
        Add-Check 'Python 3.11+' $false "Unparseable: $pyOut"
    }
} catch {
    Add-Check 'Python 3.11+' $false 'python not found in PATH'
}

# ── 2. Key pip packages ────────────────────────────────────────────────────────

$PkgList = @('django', 'django_htmx', 'gunicorn', 'chromadb', 'ollama', 'langchain_chroma', 'whitenoise')
foreach ($pkg in $PkgList) {
    try {
        $out = & pip show $pkg 2>&1
        $ok  = ($out | Select-String -Pattern 'Name:' -Quiet)
        Add-Check "pip: $pkg" ([bool]$ok) ($(if ($ok) { 'installed' } else { 'not found — run pip install' }))
    } catch {
        Add-Check "pip: $pkg" $false 'pip error'
    }
}

# ── 3. Ollama service reachable ────────────────────────────────────────────────

try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:11434/api/tags' `
                              -UseBasicParsing -TimeoutSec 4
    Add-Check 'Ollama: service running' ($resp.StatusCode -eq 200) "HTTP $($resp.StatusCode)"
} catch {
    Add-Check 'Ollama: service running' $false 'Not reachable at 127.0.0.1:11434 — run: ollama serve'
}

# ── 4. Ollama bound to 127.0.0.1 (not 0.0.0.0) ───────────────────────────────

try {
    $lines  = & netstat -an 2>&1
    $bound  = @($lines | Where-Object { $_ -match '127\.0\.0\.1:11434' -and $_ -match 'LISTEN' })
    $public = @($lines | Where-Object { $_ -match '0\.0\.0\.0:11434'   -and $_ -match 'LISTEN' })
    if ($bound.Count -gt 0) {
        Add-Check 'Ollama: bound to loopback' $true 'LISTENING on 127.0.0.1:11434'
    } elseif ($public.Count -gt 0) {
        Add-Check 'Ollama: bound to loopback' $false 'Listening on 0.0.0.0 — restrict to 127.0.0.1 in production'
    } else {
        Add-Check 'Ollama: bound to loopback' $false 'Port 11434 not found in netstat'
    }
} catch {
    Add-Check 'Ollama: bound to loopback' $false "netstat error: $_"
}

# ── 5. Ollama model pulled ────────────────────────────────────────────────────

$TargetModel = 'qwen2.5:7b-instruct-q4_K_M'
try {
    $list    = & ollama list 2>&1
    $present = $list | Where-Object { $_ -match [regex]::Escape($TargetModel) }
    Add-Check "Ollama: model present" ([bool]$present) (
        $(if ($present) { $TargetModel } else { "Not found — run: ollama pull $TargetModel" })
    )
} catch {
    Add-Check 'Ollama: model present' $false 'ollama CLI not in PATH'
}

# ── 6. CHROMA_PERSIST_DIR accessible ─────────────────────────────────────────

$ChromaDir = if ($env:CHROMA_PERSIST_DIR) { $env:CHROMA_PERSIST_DIR } else {
    Join-Path $ProjectRoot 'chroma_db'
}

$chromaOk = Test-Path $ChromaDir -PathType Container
if (-not $chromaOk) {
    try { New-Item -ItemType Directory -Path $ChromaDir -Force | Out-Null; $chromaOk = $true } catch {}
}
Add-Check 'CHROMA_PERSIST_DIR accessible' $chromaOk $ChromaDir

# ── 7. .env file exists ────────────────────────────────────────────────────────

$envPath = Join-Path $ProjectRoot '.env'
Add-Check '.env file exists' (Test-Path $envPath -PathType Leaf) $envPath

# ── 8. SQLite WAL mode ────────────────────────────────────────────────────────

$DbPath = Join-Path $ProjectRoot 'db.sqlite3'
if (Test-Path $DbPath -PathType Leaf) {
    $sqlite3 = Get-Command sqlite3 -ErrorAction SilentlyContinue
    if ($sqlite3) {
        try {
            $mode = (& sqlite3 $DbPath 'PRAGMA journal_mode;' 2>&1) -join ''
            Add-Check 'SQLite WAL mode' ($mode -match 'wal') "journal_mode=$mode"
        } catch {
            Add-Check 'SQLite WAL mode' $false "sqlite3 error: $_"
        }
    } else {
        # Heuristic: WAL sidecar file present → WAL was active at some point
        $walFile = "${DbPath}-wal"
        Add-Check 'SQLite WAL mode' (Test-Path $walFile) (
            $(if (Test-Path $walFile) { 'WAL sidecar found' } else { 'sqlite3 CLI absent — install sqlite3 for a definitive check' })
        )
    }
} else {
    Add-Check 'SQLite WAL mode' $false 'db.sqlite3 not found — run: python manage.py migrate'
}

# ── Print results ──────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "    IP-SAKTI Sahayak — System Check" -ForegroundColor Cyan
Write-Host "  ════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

foreach ($r in $Results) {
    $colour = if ($r.Ok) { 'Green' } else { 'Red' }
    $tag    = if ($r.Ok) { 'PASS' }  else { 'FAIL' }
    $sym    = if ($r.Ok) { '✓' }     else { '✗' }
    $detail = if ($r.Detail) { "  ($($r.Detail))" } else { '' }
    Write-Host "    [$tag] $sym  $($r.Name)$detail" -ForegroundColor $colour
}

Write-Host ""
$summColour = if ($Failed -eq 0) { 'Green' } else { 'Yellow' }
Write-Host "    Passed: $Passed   Failed: $Failed" -ForegroundColor $summColour
Write-Host ""

exit $(if ($Failed -eq 0) { 0 } else { 1 })
