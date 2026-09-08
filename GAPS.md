# IP-SAKTI Sahayak — Open gaps vs IMPLEMENTATION_PLAN v4.3

Last updated: 2026-09-08 (**JURY READY** — final audit green)  
Target for “prod” in this repo: **SIH laptop demo** (Waitress). Public internet scale is deferred (§3.3).

---

## Final audit snapshot (green)

| Check | Result |
|---|---|
| `/health/` | `ok` · `demo_mode=false` · `debug=false` · `ollama_reachable=true` · **`0.3-demo`** |
| pytest | **43 passed** |
| Corpus | **8 sources / 43 chunks**; golden source hit-rate **100%** on validate |
| Warmup | Embeddings + Ollama generate `READY` |
| Chat CSRF / Clear Session | Live HTML has `X-CSRFToken` on session-clear |
| Screen Reader | `/screen-reader/` lists NVDA/JAWS; chat `#sr-live` present |
| Hindi chrome | Home, nav, chat, help headings, footer, wizard header/steps, corpus about title |
| Ops docs | `DEMO_SCRIPT.md` · `scripts/demo_checklist.ps1` · `warmup.ps1` · `serve_demo.ps1` |

---

## Closed this pass

| Item | Result |
|---|---|
| Clear Session 403 | CSRF on HTMX + global `setupCsrfForHtmx` |
| Screen Reader Access | GIGW page + a11y `nav` + `#sr-live` |
| Dark Ashoka mark | Visible under `html[data-theme=dark]` |
| Pending Ask UX | Question bubble + finding animation |
| Corpus | **`0.3-demo`** (Patents, GI, BDA, Aahara, D&C, Nagoya, TKDL, TRIPS) |
| Hindi chrome | Home/nav/chat/help/footer/wizard/corpus titles |
| `DEBUG` | `.env` **`DEBUG=False`** |
| Jury script | **`DEMO_SCRIPT.md`** |

---

## Remaining (non-blocking for laptop demo)

| Gap | Notes |
|---|---|
| Live Ask CPU latency | Warm ~50–120s; evidence_only on timeout — scripted in `DEMO_SCRIPT.md` |
| Wizard step body / full FAQ Hindi | Header + steps done; long prose still EN |
| IndicTrans2 Q&A | Answers stay model language |
| Full statute PDFs | Demo TXT excerpts only |
| Network-off backup video | Not recorded — optional |
| Public HTTPS / lockfile | Deferred §3.3 |

---

## Deployed now (Profile B — SIH laptop)

| Item | State |
|---|---|
| Waitress | **one** process → `http://127.0.0.1:8000/` |
| `/health/` | `ok` · `demo_mode=false` · `debug=false` · `ollama_reachable=true` · **`0.3-demo`** |
| Warmup | Embeddings + Ollama generate `READY` |
| pytest | **43 passed** |
| Env | `DEMO_MODE=False`, `DEBUG=False`, `TRANSLATE_BACKEND=ollama`, `OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M` |
| `check --deploy` | HSTS/SSL warnings only (expected for localhost HTTP) |

`0.4-pdf` rebuild: large `drugs-cosmetics-act-1940.pdf` extract hangs on this laptop; PDF staged under `data/staging/`. **Jury stays on `0.3-demo`.**
