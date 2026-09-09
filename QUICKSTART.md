# IP-SAKTI Sahayak — Quick Start Guide

**SIH26045 — Ministry of Ayush / AIIA**  
Version 4.3 | September 2026

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | https://www.python.org/downloads/ |
| Ollama | Latest | https://ollama.ai/download |
| Git | Any | https://git-scm.com/ |

---

## Step 1: Environment Setup (Windows)

```powershell
cd C:\IP-SAKTI-Sahayak

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment config
Copy-Item .env.example .env
```

Edit `.env` with a real `SECRET_KEY` and `AUDIT_HMAC_KEY` before production.

---

## Step 2: Database Setup

```powershell
# Run migrations
python manage.py migrate

# Create admin user (optional)
python manage.py createsuperuser
```

---

## Step 3: Download JS Vendor Files (for offline demo)

```powershell
$base = "core\static\js"
Invoke-WebRequest "https://unpkg.com/htmx.org@2.0.2/dist/htmx.min.js"                              -OutFile "$base\htmx.min.js"
Invoke-WebRequest "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"                 -OutFile "$base\gsap.min.js"
Invoke-WebRequest "https://unpkg.com/@dotlottie/player-component@2.7.12/dist/dotlottie-player.mjs" -OutFile "$base\dotlottie-player.mjs"
```

---

## Step 4: Run in Demo Mode (no Ollama needed)

```powershell
# DEMO_MODE=True is the default — placeholder responses shown
python manage.py runserver
```

Open http://localhost:8000 — you'll see the full UI with demo responses.

---

## Step 5: Enable Live RAG (full pipeline)

### 5a. Pull Ollama model
```powershell
ollama pull qwen2.5:7b-instruct-q4_K_M
# Requires ~5 GB disk, ~6 GB VRAM (or 8 GB recommended)
```

### 5b. Start Ollama (bound to localhost only)
```powershell
$env:OLLAMA_ORIGINS="http://localhost:8000"
$env:OLLAMA_HOST="127.0.0.1:11434"
ollama serve
```

### 5c. Download corpus PDFs
See `.cursor/skills/corpus-management/SKILL.md` for the full source list.  
Download to `data/corpus/` and fill the YAML manifests in `data/manifests/`.

### 5d. Index corpus
```powershell
# Run the ingestion pipeline (takes 15-45 min on first run)
python manage.py build_corpus_version --version 1 --sources data/corpus/
python manage.py validate_corpus_version --version 1
python manage.py activate_corpus_version --version 1
```

### 5e. Disable demo mode
Edit `.env`:
```
DEMO_MODE=False
```
Restart the server.

---

## Step 6: System Check

```powershell
python scripts/check_system.ps1
```

Checks: Python version, Ollama binding, model pulled, Chroma accessible, .env present.

---

## Running Tests

```powershell
pytest tests/ -v --cov=. --cov-report=term-missing
```

Golden set retrieval test (requires live corpus):
```powershell
pytest tests/test_retrieval_golden.py -v
```

---

## Production Deployment (Render.com)

1. Push repo to GitHub
2. Create new Web Service on render.com
3. Connect GitHub repo
4. Render reads `render.yaml` — auto-configures
5. Set environment variables in Render dashboard:
   - `SECRET_KEY` (generate random 50+ chars)
   - `AUDIT_HMAC_KEY` (generate random 32+ chars)
   - `DEMO_MODE=True` (until corpus is indexed)
   - `ALLOWED_HOSTS=your-app.onrender.com`

---

## Project Structure

```
C:\IP-SAKTI-Sahayak\
├── ip_sakti/           Django project (settings, urls, wsgi)
├── core/               Home, static pages, language selection
├── chat/               Ask endpoint, HTMX chat, AnswerAudit model
├── corpus/             Corpus versioning, source manifests
├── wizard/             Formulation wizard (4-step)
├── ai/                 RAG pipeline (retrieve, generate, citations, safety)
├── data/
│   ├── manifests/      YAML source manifests (tracked in git)
│   ├── golden/         Golden question test set
│   ├── raw/            Downloaded PDFs (gitignored)
│   └── corpus/         Processed for ingestion (gitignored)
├── core/static/
│   ├── css/            tokens.css + gov-style.css + chat.css
│   ├── js/             app.js, chat.js, wizard.js + vendor files
│   ├── images/         ashoka-chakra.svg, national-emblem.svg
│   └── animations/     .lottie files
├── scripts/            setup.ps1, check_system.ps1, ingest.ps1
└── tests/              pytest test suite
```

---

## What Needs to Be Provided (after demo)

The following are placeholders and will be needed for full live functionality:

| Item | Status | Action needed |
|---|---|---|
| Ollama + model | Local only | `ollama pull qwen2.5:7b-instruct-q4_K_M` |
| Legal corpus PDFs | Not included | Download per `corpus-management` skill |
| IndicTrans2 model | Stub | `pip install ctranslate2` + download model |
| Lottie animations | Needs download | See `core/static/animations/ASSETS.md` |
| National emblem | Placeholder SVG | Download official from india.gov.in |
| Offline fonts | Needs npm install | See `core/static/fonts/FONTS.md` |

---

## Contacts

- **Problem Statement:** SIH26045 — Ministry of Ayush / AIIA
- **Audit:** `AUDIT_RESOLUTION.md`
