# IP-SAKTI Sahayak — Quick start

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/download) (only if `DEMO_MODE=False`)
- Windows PowerShell or macOS/Linux shell

## Setup

```powershell
cd C:\IP-SAKTI-Sahayak
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

Default `.env` uses `DEMO_MODE=True` so the UI works without Ollama.

## Live answers (local)

```powershell
ollama pull qwen2.5:3b-instruct-q4_K_M
```

In `.env`:

```env
DEMO_MODE=False
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
```

Index / activate a corpus version (see `data/CORPUS_SOURCES.md` and management commands), then restart the server.

## Cloud demo

Public app: https://ip-sakti-sahayak-production-4c21.up.railway.app  

Ollama on Railway: [docs/DEPLOY_OLLAMA.md](docs/DEPLOY_OLLAMA.md)

## Health check

```text
GET /health/
```

Expect `status=ok`. For live LLM: `demo_mode=false`, `ollama_reachable=true`.

## More

- [USER_GUIDE.md](USER_GUIDE.md) — end-user guide  
- [docs/RAG.md](docs/RAG.md) — RAG pipeline and deploy status  
- [docs/SIH26045_Technical_Documentation.md](docs/SIH26045_Technical_Documentation.md) — SIH technical doc  
- [LICENCES.md](LICENCES.md) — corpus licence notes  

**Problem statement:** SIH26045 — Ministry of Ayush / AIIA
