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

Railway hosts Django + Postgres, a dedicated **Ollama** service, and a **Chroma**
index (`0.3-demo`) on the web volume for full cited RAG. Details:
[docs/RAG.md](docs/RAG.md) · [docs/DEPLOY_OLLAMA.md](docs/DEPLOY_OLLAMA.md).
With `DEMO_MODE=True`, the app serves illustrative answers only.

---

## Stack (MVP — no OpenAI / Gemini)

| Layer | Choice |
|---|---|
| Web | Django 5 + HTMX + GOI-style UI |
| RAG | LangChain-thin · Chroma · **bge-m3** |
| LLM | **Ollama** on Railway · `qwen2.5:3b-instruct-q4_K_M` (CPU) |
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

## Railway + Ollama (cloud — laptop optional)

```text
Browser → Railway Django → http://ollama.railway.internal:11434 → Railway Ollama (Qwen 3B)
```

Image + entrypoint: [`deploy/ollama/`](deploy/ollama/). Full ops: **[docs/DEPLOY_OLLAMA.md](docs/DEPLOY_OLLAMA.md)**

```powershell
railway up .\deploy\ollama -s ollama -d -y --path-as-root --ci
# Web already uses:
#   OLLAMA_BASE_URL=http://ollama.railway.internal:11434
#   DEMO_MODE=False
```

Check `/health/` → `demo_mode: false`, `ollama_reachable: true`,
`chroma_reachable: true`, `active_corpus_version: 0.3-demo`.

**RAG on Railway:** Ollama (generation) + Chroma `0.3-demo` on `/data/chroma_db`
+ bge-m3 cache under `/data/hf`. See **[docs/RAG.md](docs/RAG.md)**. First Ask after
a cold cache may be slow while embeddings download; then CPU answers often take 30–120s.

---

## Docs

| Doc | Purpose |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | Local setup detail |
| [USER_GUIDE.md](USER_GUIDE.md) | End-user walkthrough |
| [docs/RAG.md](docs/RAG.md) | How RAG works · what is / isn’t deployed |
| [docs/DEPLOY_OLLAMA.md](docs/DEPLOY_OLLAMA.md) | Railway Ollama |
| [docs/SIH26045_Technical_Documentation.md](docs/SIH26045_Technical_Documentation.md) | Full SIH tech doc |
| [LICENCES.md](LICENCES.md) | Corpus licence notes |

---

## Security / hygiene

- Never commit `.env` (only `.env.example`).
- Rotate `SECRET_KEY` and `AUDIT_HMAC_KEY` per environment.
- Demo answers are illustrative; always verify with official GOI sources.

---

## Licence

See repository licence files and [LICENCES.md](LICENCES.md) for corpus reuse basis.
