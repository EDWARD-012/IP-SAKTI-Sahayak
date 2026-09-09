# Deploy Ollama for IP-SAKTI (Railway cloud)

**Production path:** Ollama runs as its own Railway service in the same project as Django.
No laptop tunnel required. Cloudflare Workers cannot host full Ollama; use Railway (or similar).

## Architecture (live)

```text
User browser
  → https://ip-sakti-sahayak-production-4c21.up.railway.app
  → Django (DEMO_MODE=False)
  → OLLAMA_BASE_URL=http://ollama.railway.internal:11434
  → Railway service "ollama" (qwen2.5:3b-instruct-q4_K_M on volume)
```

## What is already deployed

| Piece | Detail |
|---|---|
| Service | `ollama` (custom image from `deploy/ollama/`) |
| Volume | `ollama-volume` → `/root/.ollama` (model cache) |
| Model | `qwen2.5:3b-instruct-q4_K_M` (~1.9 GB, pulled at boot) |
| Django var | `OLLAMA_BASE_URL=http://ollama.railway.internal:11434` |
| Flag | `DEMO_MODE=False` |

## Redeploy / update Ollama

From the repo root:

```powershell
cd C:\IP-SAKTI-Sahayak
railway up .\deploy\ollama -s ollama -d -y --path-as-root --ci
```

Entrypoint starts `ollama serve`, then `ollama pull` for `OLLAMA_MODEL` (skipped if already on the volume).

Service variables (on `ollama`):

```text
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_ORIGINS=*
OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
```

Web service variables (on `ip-sakti-sahayak`):

```powershell
railway service link ip-sakti-sahayak
railway variables set OLLAMA_BASE_URL=http://ollama.railway.internal:11434
railway variables set DEMO_MODE=False
railway variables set OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
railway service restart -y
```

## Verify

```powershell
Invoke-RestMethod https://ip-sakti-sahayak-production-4c21.up.railway.app/health/
```

Expect:

| Field | Target |
|---|---|
| `demo_mode` | `false` |
| `ollama_reachable` | `true` |

CPU inference on Railway is slow (often 30–120s per answer). Scale memory if the service OOMs.

## Fallback — laptop + tunnel (optional)

Only if the cloud Ollama service is down:

```powershell
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:11434 --http-host-header="localhost:11434"
railway variables set OLLAMA_BASE_URL=https://YOUR-TUNNEL-HOST
```

Ollama rejects non-local `Host` headers with **403** unless the tunnel rewrites Host (flag above) or `OLLAMA_HOST=0.0.0.0:11434`.

## Local Docker (optional)

`docker-compose.yml` profile `ollama` runs Ollama beside `web` on a laptop. Production still uses the Railway `ollama` service.

## Limits

- Cloud Ollama enables **LLM generation** without a laptop.
- Full **cited RAG** also needs a Chroma index + bge-m3 in the Django process.
  `seed_cloud_db` only seeds statute **metadata** (`0.3-cloud`) — it does **not**
  build vectors. See **[RAG.md](RAG.md)** for the pipeline and how to sync Chroma
  to the Railway `/data` volume.
