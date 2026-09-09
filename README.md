# IP-SAKTI Sahayak

**SIH26045** — Multilingual IPR assistant for Ayurveda & traditional knowledge  
**Ministry of Ayush / All India Institute of Ayurveda (AIIA)**

IP-SAKTI Sahayak answers patents, GI, biodiversity/ABS, TKDL, and Ayush regulatory questions from a **versioned, cited corpus** of Indian statutes and treaties. It refuses questions outside the corpus. It is **not** legal, medical, or regulatory advice.

---

## Live demo

| | |
|---|---|
| **App** | https://ip-sakti-sahayak-production-4c21.up.railway.app |
| **Health** | https://ip-sakti-sahayak-production-4c21.up.railway.app/health/ |
| **Repo** | https://github.com/EDWARD-012/IP-SAKTI-Sahayak |

Railway runs the Django UI + Postgres. **Live LLM answers** need a reachable Ollama endpoint (see [docs/DEPLOY_OLLAMA.md](docs/DEPLOY_OLLAMA.md)). With `DEMO_MODE=True`, the cloud app serves illustrative answers only.

---

## Stack (MVP — no OpenAI / Gemini)

| Layer | Choice |
|---|---|
| Web | Django 5 + HTMX + GOI-style UI |
| RAG | LangChain-thin · Chroma · **bge-m3** |
| LLM | **Ollama** · `qwen2.5:3b-instruct-q4_K_M` (CPU-friendly) |
| Cloud DB | Railway Postgres (`DATABASE_URL`) |
| Local DB | SQLite under `DATA_DIR` |

---

## Quick start (Windows)

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

Default `.env` has `DEMO_MODE=True` (UI works without Ollama).

### Live local RAG

1. Install [Ollama](https://ollama.ai/download) and pull the model:

```powershell
ollama pull qwen2.5:3b-instruct-q4_K_M
```

2. In `.env`:

```env
DEMO_MODE=False
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
```

3. Index / activate corpus (see [QUICKSTART.md](QUICKSTART.md)), then restart the server.

---

## Railway + Ollama (jury / public demo)

Railway **cannot** use `http://127.0.0.1:11434` (that is inside the container). Expose laptop Ollama with a tunnel and point Railway at it:

```text
Browser → Railway Django → HTTPS tunnel → Laptop Ollama (Qwen 3B)
```

Full steps: **[docs/DEPLOY_OLLAMA.md](docs/DEPLOY_OLLAMA.md)**

Summary:

1. Keep Ollama running on the laptop.
2. Start Cloudflare Tunnel or ngrok to port `11434`.
3. Set Railway variables: `OLLAMA_BASE_URL=https://<tunnel-host>`, `DEMO_MODE=False`.
4. Check `/health/` → `demo_mode: false`, `ollama_reachable: true`.

**Note:** Cloud seed (`seed_cloud_db`) loads statute **metadata**. Full vector RAG needs a Chroma index on the process that answers (typically the laptop profile). Generation via tunneled Ollama can be enabled first; corpus volume sync is a follow-up.

---

## Docs

| Doc | Purpose |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | Local setup detail |
| [USER_GUIDE.md](USER_GUIDE.md) | End-user walkthrough |
| [docs/DEPLOY_OLLAMA.md](docs/DEPLOY_OLLAMA.md) | Tunnel + Railway Ollama |
| [docs/SIH26045_Technical_Documentation.md](docs/SIH26045_Technical_Documentation.md) | Full SIH tech doc |
| [GAPS.md](GAPS.md) | Known gaps |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Build plan |
| [LICENCES.md](LICENCES.md) | Corpus licence notes |

---

## Security / hygiene

- Never commit `.env` (only `.env.example`).
- Rotate `SECRET_KEY` and `AUDIT_HMAC_KEY` per environment.
- Demo answers are illustrative; always verify with official GOI sources.

---

## Licence

See repository licence files and [LICENCES.md](LICENCES.md) for corpus reuse basis.
