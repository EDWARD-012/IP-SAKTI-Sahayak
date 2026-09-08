#Requires -Version 5.1
<#
.SYNOPSIS
  Pre-jury checklist for IP-SAKTI Sahayak SIH laptop demo.
#>
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py = Join-Path $Root '.venv\Scripts\python.exe'

Write-Host "`n=== IP-SAKTI demo checklist ===" -ForegroundColor Cyan

Write-Host "`n[1] Health"
try {
  $h = Invoke-RestMethod 'http://127.0.0.1:8000/health/'
  Write-Host ("  status={0} demo_mode={1} ollama={2} corpus={3} debug={4}" -f $h.status, $h.demo_mode, $h.ollama_reachable, $h.active_corpus_version, $h.debug)
  if ($h.demo_mode) { Write-Host '  WARN: DEMO_MODE is true — live RAG off' -ForegroundColor Yellow }
  if (-not $h.ollama_reachable) { Write-Host '  WARN: Ollama not reachable' -ForegroundColor Yellow }
  if ($h.debug) { Write-Host '  WARN: DEBUG=true — set DEBUG=False in .env for jury' -ForegroundColor Yellow }
  if ($h.active_corpus_version -notlike '*0.3*') { Write-Host '  WARN: expected corpus 0.3-demo for full chip coverage' -ForegroundColor Yellow }
} catch {
  Write-Host '  FAIL: server not reachable on :8000 — run .\scripts\serve_demo.ps1' -ForegroundColor Red
}

Write-Host "`n[2] Warmup (embeddings + Ollama)"
& $Py manage.py warmup
if ($LASTEXITCODE -ne 0) { Write-Host '  WARN: warmup reported issues' -ForegroundColor Yellow }

Write-Host "`n[3] Pytest smoke"
& $Py -m pytest -q --tb=line
if ($LASTEXITCODE -ne 0) { throw 'pytest failed' }

Write-Host "`n[4] Jury script reminders" -ForegroundColor Green
Write-Host '  - Keep ONE Waitress process (no second runserver on :8000)'
Write-Host '  - Demo Hindi for Home + nav + chat chrome; Pilot langs = preference only'
Write-Host '  - Ask: Section 3(p) TK patent question (India)'
Write-Host '  - Ask: Ayurveda Aahara labelling / Nagoya ABS / TKDL bio-piracy'
Write-Host '  - Show refusal: foreign USPTO / out-of-scope crypto'
Write-Host '  - Show Clear Session + Screen Reader Access + dark theme chakra'
Write-Host "`nDone.`n"
