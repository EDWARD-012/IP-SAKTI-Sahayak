# IP-SAKTI Sahayak — SIH Jury Demo Script

**URL:** http://127.0.0.1:8000/  
**Stack:** Waitress · `DEMO_MODE=False` · corpus **`0.3-demo`** (8 sources) · Ollama `qwen2.5:3b-instruct-q4_K_M`

---

## T−15 min (before jury enters)

```powershell
cd C:\IP-SAKTI-Sahayak
.\scripts\warmup.ps1
.\scripts\serve_demo.ps1          # if not already running — ONE process only
.\scripts\demo_checklist.ps1
```

Confirm `/health/` → `status=ok`, `demo_mode=false`, `debug=false`, `ollama_reachable=true`, `active_corpus_version=0.3-demo`.

---

## Live flow (~8–10 min)

| # | Action | Say / show |
|---|---|---|
| 1 | Home (optional: switch **हिन्दी**) | GOI chrome, source-cited positioning |
| 2 | **Ask IP-SAKTI** → chip **Section 3(p) TK** or type patent/TK question | Pending “You asked” + finding animation → **grounded** + Patents Act §3(p) |
| 3 | Chip **Ayurveda Aahara** or **NBA / ABS** | Second grounded path (FSSAI / BDA) |
| 4 | Ask foreign USPTO / “cryptocurrency investments” | **Refusal** / out-of-scope — no hallucinated law |
| 5 | **Clear Session** (confirm) | History wipe + reload |
| 6 | Top bar **Screen Reader Access** + dark theme toggle | GIGW a11y + visible Ashoka mark |
| 7 | Optional: Formulation Wizard header | Pathway finder — not deep Rule 2(ee) |

---

## If Ask is slow

- Say: *“CPU laptop — evidence card may appear first; full generate can take ~1–2 minutes when warm.”*
- Do **not** open a second server on `:8000`.
- Fallback: evidence_only card with citations is still a valid demo outcome.

---

## Do **not** claim

- Full Pilot-language UI (Telugu etc.) — preference only  
- Full India Code PDFs / production HTTPS  
- Instant answers on cold start  

---

## Backup

If Ollama dies mid-demo: flip `.env` `DEMO_MODE=True`, restart Waitress, show illustrative stub + explain live path was demonstrated earlier / in video.
