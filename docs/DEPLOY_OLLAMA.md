# Deploy Ollama for IP-SAKTI (Railway)

Railway hosts the Django app. Ollama runs on a **laptop (or other GPU/CPU host)** and is reached over an HTTPS tunnel.

Do **not** set `OLLAMA_BASE_URL=http://127.0.0.1:11434` on Railway — that loopback is the container itself.

## Architecture

```text
User browser
    → https://ip-sakti-sahayak-production-4c21.up.railway.app
    → Django (DEMO_MODE=False)
    → OLLAMA_BASE_URL=https://<tunnel>
    → Laptop Ollama :11434 (qwen2.5:3b-instruct-q4_K_M)
```

## Prerequisites

- Ollama installed and model pulled:

```powershell
ollama pull qwen2.5:3b-instruct-q4_K_M
ollama list
# Optional check:
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

- Railway CLI linked to project `ip-sakti-sahayak`.
- Tunnel client: [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/) **or** [ngrok](https://ngrok.com/download).

## 1. Allow tunnel Host headers (Ollama)

Ollama rejects non-local `Host` headers with bare **403** (DNS-rebinding guard). Either:

```powershell
# Preferred with tunnels: rewrite Host at the tunnel (see commands below), OR
# Bind openly + allow origins (Windows User env, then restart Ollama):
[System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0:11434", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_ORIGINS", "*", "User")
# Then restart Ollama / `ollama serve`
```

## 2. Start the tunnel

### Option A — Cloudflare quick tunnel

```powershell
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:11434 --http-host-header="localhost:11434"
```

Copy the printed `https://….trycloudflare.com` URL (no trailing slash).

### Option B — ngrok

```powershell
ngrok http 11434 --host-header="localhost:11434"
```

Copy the `https://….ngrok-free.app` (or similar) forwarding URL.

Leave the tunnel process running for the whole demo.

## 3. Point Railway at the tunnel

```powershell
cd C:\IP-SAKTI-Sahayak
railway variables set OLLAMA_BASE_URL=https://YOUR-TUNNEL-HOST
railway variables set DEMO_MODE=False
railway variables set OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
```

Redeploy or restart the web service so workers pick up env:

```powershell
railway up -y -d --ci
# or: railway redeploy
```

## 4. Verify

```powershell
Invoke-RestMethod https://ip-sakti-sahayak-production-4c21.up.railway.app/health/
```

Expect:

| Field | Target |
|---|---|
| `ok` | `true` |
| `demo_mode` | `false` |
| `ollama_reachable` | `true` |

Then ask a patent/GI question on the live site. If Ollama is slow on CPU, allow 30–120s.

## 5. Rollback to stub demo

```powershell
railway variables set DEMO_MODE=True
```

## Local Docker (optional)

`docker-compose.yml` can start an `ollama` service beside `web` for local stacks. Railway production still uses the tunnel pattern above.

## Jury day checklist

- [ ] Laptop plugged in, sleep disabled
- [ ] `ollama list` shows the Qwen model
- [ ] Tunnel process alive; URL matches Railway `OLLAMA_BASE_URL`
- [ ] `/health/` shows `demo_mode=false` and `ollama_reachable=true`
- [ ] One warm-up Ask completed before the demo

## Limits

- Tunneled Ollama enables **LLM generation** from the cloud app.
- Full **cited RAG** also needs a Chroma index visible to the Django process. Cloud `seed_cloud_db` seeds statute metadata (`0.3-cloud`). For full retrieval, use the laptop-indexed corpus profile or sync vectors to the Railway volume in a later step.
