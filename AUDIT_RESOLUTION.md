# Deep Audit Resolution

**Audit input:** `deep_audit_report.md`  
**Resolved plan:** `IMPLEMENTATION_PLAN.md` v4.3

## Resolution summary

| Audit group | Resolution |
|---|---|
| A. URLs | Removed stale India Code/NBA deep links; use migrated India Code portal, e-Gazette and verified authority links |
| B. Contradictions | Canonical evidence labels, 14-day timeline, version history, terminology, state mapping and routes aligned |
| C. Cross-file | README and USER_GUIDE aligned with v4.3 |
| D. Legal/factual | Corrected Section 3(p) date; added 3(d), 2023 biodiversity amendment, Rule 2(ee), First Schedule, Schedule T, 2024 Patent Rules and NDCT Rules |
| E. Structure | Added navigation, canonical requirements file, `.gitignore`, `.gitattributes` and project description |
| F. Missing content | Defined plain `ai` package, prompt, chunks, Chroma naming, model cache and endpoint controls |
| G. Security | Added concrete limits, DPDP mapping, query HMAC, licence manifest, sensitive-data warning, CSP, same-origin policy and Ollama binding verification |
| H. Environment | Windows remains primary because this workspace is Windows; Linux deployment commands were added |

## Findings requiring correction to the audit itself

1. **Section 3(p):** the audit proposed `2005-01-01`. Verified sources show
   clause 3(p) was inserted by the Patents (Amendment) Act, 2002 with effect
   from **20 May 2003**. The plan uses that date. Section 3(d)'s relevant 2005
   amendment is tracked separately.
2. **Operating system:** the audit referenced a Linux copy under
   `/home/student/Desktop/...`. The actual user workspace is Windows at
   `C:\IP-SAKTI-Sahayak`, so CRLF and PowerShell are not inherently erroneous.
   Cross-platform Linux commands and `.gitattributes` were still added.
3. **Drugs and Cosmetics Act title:** “The Drugs and Cosmetics Act, 1940” was
   already the correct official title. The real issue was provision-specific
   commencement/amendment dates; v4.3 now records those separately.

## Updated-audit delta resolved in v4.3

- Embedded Chroma is read-only at runtime and Django is explicitly
  single-process; Linux Gunicorn uses one worker with four threads.
- Ollama generation uses a precisely defined in-process bounded semaphore,
  not an implied durable queue. SQLite uses WAL plus a busy timeout.
- Qwen is pinned to `qwen2.5:7b-instruct-q4_K_M`; hardware guidance now says
  6 GB minimum and 8 GB recommended.
- IndicTrans2 runs on demand and CPU-first; English is the default pivot.
- The selector includes all 22 Eighth Schedule languages plus English, with
  honest Pilot/Beta labels and low-resource evaluation gates.
- Romanised Hindi, multi-question prompts, future-effective law, expired
  wizard sessions, missing source packs and spurious citations have explicit
  handling.

## Canonical product vocabulary

### Evidence labels

- Strong evidence
- Limited evidence
- Unable to answer from verified sources

### Internal result states

- `grounded`
- `evidence_only`
- `unable_to_answer`
- `out_of_scope`
- `conflict`
- `busy`
- `unavailable`

### Regulatory spelling

Use **Ayurveda Aahara** in user-visible text. Other spellings exist only as
retrieval aliases.

## Remaining deliberate limitations

- No application code exists yet; the Markdown describes the approved MVP.
- URLs must be verified again while acquiring each source and stored in the
  source manifest.
- English/Hindi are release languages. Other selectable languages retain
  Pilot/Beta status until human evaluation.
- Public production scale, foreign domestic-law advice, uploads, voice,
  fine-tuning and autonomous agents remain outside the MVP.
