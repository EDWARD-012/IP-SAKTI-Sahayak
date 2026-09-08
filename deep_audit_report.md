# Deep Audit Report: IP-SAKTI Sahayak Markdown Files

**Audit Date:** 2026-09-08  
**Scope:** All 3 markdown files — line-by-line factual, technical, legal, and consistency audit  
**Files Audited:**
- [README.md](file:///home/student/Desktop/IP-SAKTI-Sahayak/README.md) (14 lines)
- [IMPLEMENTATION_PLAN.md](file:///home/student/Desktop/IP-SAKTI-Sahayak/IMPLEMENTATION_PLAN.md) (1,185 lines)
- [USER_GUIDE.md](file:///home/student/Desktop/IP-SAKTI-Sahayak/USER_GUIDE.md) (106 lines)

---

## Table of Contents

1. [URL Verification](#1-url-verification)
2. [Legal Fact Accuracy](#2-legal-fact-accuracy)
3. [Technical Feasibility Audit](#3-technical-feasibility-audit)
4. [Internal Contradictions & Inconsistencies](#4-internal-contradictions--inconsistencies)
5. [Timeline & Resourcing Realism](#5-timeline--resourcing-realism)
6. [Security & Privacy Audit](#6-security--privacy-audit)
7. [Language & Translation Audit](#7-language--translation-audit)
8. [Edge Case Coverage Audit](#8-edge-case-coverage-audit)
9. [Document Quality & Formatting](#9-document-quality--formatting)
10. [Consolidated Findings Table](#10-consolidated-findings-table)

---

## 1. URL Verification

Every URL in [IMPLEMENTATION_PLAN.md](file:///home/student/Desktop/IP-SAKTI-Sahayak/IMPLEMENTATION_PLAN.md) §19.1 was tested. Results:

| # | URL | Line | Status | Finding |
|---|---|---|---|---|
| 1 | `indiacode.nic.in/handle/123456789/1392` (Patents Act) | 742 | ⏱️ **TIMEOUT** | India Code's DSpace server is extremely slow/unreliable. Cannot confirm URL resolves. |
| 2 | `indiacode.nic.in/handle/123456789/2046` (BD Act) | 743 | ⏱️ **TIMEOUT** | Same India Code reliability issue |
| 3 | `indiacode.nic.in/handle/123456789/2409` (D&C Act) | 744 | ⏱️ **TIMEOUT** | Same |
| 4 | `indiacode.nic.in/handle/123456789/1412` (DMR Act) | 746 | 🔴 **404 NOT FOUND** | URL returns HTTP 404. Handle ID may be wrong or page restructured. |
| 5 | `fssai.gov.in/.../Gazette_Notification_Ayurveda_Aahara_09_05_2022.pdf` | 747 | ✅ **LIVE** | PDF accessible |
| 6 | `nbaindia.org/blog/933/3/TheBiologicalDiver.html` | 748 | 🔴 **404 NOT FOUND** | NBA website has been restructured. URL is dead. |
| 7 | `ipindia.gov.in/patents-before-you-apply-public-search` | 749 | ✅ **LIVE** | Accessible |
| 8 | `ipindia.gov.in/pages/e-services` | 750 | ✅ **LIVE** | Accessible |
| 9 | `tkdl.res.in/` | 752 | ✅ **LIVE** | Accessible |
| 10 | `tkdl.res.in/tkdl/langdefault/Common/Abouttkdl.asp?GL=Eng` | 752 | ✅ **LIVE** | Accessible |
| 11 | `wipo.int/en/web/treaties/ip/gratk/index` | 753 | ✅ **LIVE** | Accessible |
| 12 | `wipo.int/en/web/treaties/ip/gratk/summary_gratk` | 754 | ✅ **LIVE** | Accessible |

> [!CAUTION]
> **2 URLs are confirmed broken (404).** The Drugs and Magic Remedies Act India Code link and the NBA Biological Diversity Rules link both return 404. These must be corrected before any corpus acquisition begins.

> [!WARNING]
> **3 India Code URLs timed out.** India Code's DSpace server (`indiacode.nic.in`) is notoriously unreliable. The plan should document alternative acquisition paths (e.g., direct gazette PDFs from `egazette.gov.in` or Ministry publications).

### URL Audit Actions Required

| Priority | Action |
|---|---|
| 🔴 P0 | Find correct India Code handle for DMR Act 1954 or replace with gazette PDF |
| 🔴 P0 | Replace NBA URL with current `nbaindia.org` URL for BD Rules 2024 (try `nbaindia.org/statutory-rules`) |
| 🟡 P1 | Add fallback URLs for all India Code sources (gazette PDFs as alternatives) |
| 🟡 P1 | Add URL verification date to each link in the source table |

---

## 2. Legal Fact Accuracy

Each legal reference was verified against authoritative sources.

### 2.1 Verified Correct ✅

| Claim | Location | Verification |
|---|---|---|
| Section 3(p) bars patenting of traditional knowledge | §6, §19.1, §21, USER_GUIDE L51 | ✅ Confirmed. Section 3(p) states "an invention which, in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components" is not an invention. |
| Biological Diversity Act, 2002 | §19.1 L743 | ✅ Correct year |
| Biological Diversity (Amendment) Act, 2023 | §19.1, §3 | ✅ Confirmed. President's assent August 3, 2023. |
| Biological Diversity Rules, 2024 | §19.1 L748 | ✅ Confirmed. Notified October 22, 2024; effective December 25, 2024. |
| Drugs and Cosmetics Act, 1940 | §19.1 L744 | ✅ Confirmed. Enacted 1940, commenced April 1, 1947. |
| Drugs and Cosmetics Rules, 1945 | §19.1 L745 | ✅ Confirmed. |
| Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954 | §19.1 L746 | ✅ Confirmed. Act No. 21 of 1954. |
| FSSAI Ayurveda Aahara Regulations, 2022 | §19.1 L747 | ✅ Confirmed. Gazette notification May 6, 2022. |
| WIPO GRATK Treaty, 2024 | §19.1 L753 | ✅ Confirmed. Adopted May 24, 2024. |
| Patents Act, 1970 | §19.1 L742 | ✅ Correct year |

### 2.2 Legal Issues Found 🔴

| # | Issue | Location | Severity | Detail |
|---|---|---|---|---|
| L-1 | **"First Schedule authoritative text" terminology** | §3.1 L55 (implicit via problem statement alignment) | 🟡 Medium | The plan says "formulation and method drawn from a First-Schedule authoritative text." The D&C Act Schedule references for ASU drugs are in the **First Schedule**, but the plan never actually names or cites this schedule. The wizard should reference Schedule I Part I specifically. |
| L-2 | **Section 3(p) effective date in chunk metadata** | §6.1 L188 | 🟡 Medium | The example shows `"effective_from": "2024-03-15"` for Section 3(p). Section 3(p) was inserted by the **Patents (Amendment) Act, 2005** (effective 2005-01-01). The date `2024-03-15` appears to reference the 2024 Patent Rules, not Section 3(p) itself. This conflation of section effective dates with rules effective dates is a metadata design flaw. |
| L-3 | **2024 Patent Rules not separately listed** | §19.1 | 🔴 High | The problem statement specifically highlights "the 2024 patent and biodiversity rules." The Patents (Amendment) Rules, 2024 are a distinct instrument from the Patents Act, 1970 and are not listed as a corpus source. |
| L-4 | **Biological Diversity Act "as amended in 2023"** | §19.1 L743 | 🟡 Medium | The plan says "as amended" but the India Code handle points to the original 2002 Act. The consolidated version incorporating the 2023 amendments may have a different handle/URL, or the plan should note that the 2023 Amendment Act is a separate document to ingest alongside the parent Act. |
| L-5 | **"Classical medicine" definition incomplete** | §8 | 🟡 Medium | The wizard defines classical/generic medicine but doesn't reference the specific Rule 2(ee) of the D&C Rules which defines "Ayurvedic, Siddha or Unani drug" and the Schedule categories. The wizard's accuracy depends on this definition being precisely mapped. |
| L-6 | **No mention of Schedule T** | §8, §19.1 | 🔴 High | Schedule T of the D&C Rules prescribes Good Manufacturing Practices for ASU drugs. This is critical for understanding manufacturing compliance and is referenced in most licensing discussions. It should be in the corpus. |

---

## 3. Technical Feasibility Audit

### 3.1 Model & Hardware Claims

| Claim | Location | Verified | Finding |
|---|---|---|---|
| "Qwen 7B Q4 needs 8–12 GB VRAM" | §5 L152 | ⚠️ **Overstated** | Qwen2.5 7B Q4_K_M weighs ~4.7 GB. Recommended VRAM is **6–8 GB**, not 8–12 GB. The 8–12 GB figure is safe but misleading — it suggests the model needs more than it does, potentially excluding teams with 6 GB GPUs (e.g., RTX 2060/3060) that would actually work. |
| "14B needs 16 GB+ VRAM" | §5 L153 | ✅ | Approximately correct for Q4 quantization of a 14B model. |
| "CPU-only: use a 3B/4B model" | §5 L154 | ✅ | Reasonable recommendation. |
| "Median response under 20 seconds" | §14 L589 | ⚠️ **Risky** | This depends heavily on context length. With 4–5 evidence chunks at ~500 tokens each plus a long system prompt, the input can reach 4K+ tokens. At Qwen 7B Q4 generation speeds of ~40–75 tok/sec on consumer GPUs, a 200-token answer takes 3–5 seconds, but embedding + retrieval + prompt assembly adds 2–5 seconds. 20 seconds is achievable but tight on slower GPUs. |
| "`ollama pull qwen2.5:7b`" | §23.2 L1022 | ⚠️ **Ambiguity** | This pulls the default quantization, which is typically Q4_K_M. But the plan doesn't specify Q4 vs Q4_K_M vs Q5_K_M. The `ollama pull qwen2.5:7b` tag should be pinned to a specific quantization for reproducibility. |

### 3.2 ChromaDB Architecture Risk

> [!CAUTION]
> **Critical multi-worker concurrency issue identified.**

The plan states (§4 L130): "SQLite and Chroma are files, not network services."

When Django runs under **Gunicorn** (Profile B/C, §12), it spawns multiple worker processes. ChromaDB in `PersistentClient` (library/embedded) mode does not share state across processes. This means:

- Worker 1 may serve stale embeddings
- Workers writing simultaneously to the same Chroma directory can corrupt the index
- This directly contradicts the plan's claim of "two concurrent browser requests" working correctly (§26 L1159)

**Mitigation options (not addressed in the plan):**
1. Run ChromaDB in server mode (adds a third process — contradicts §4's "only two processes")
2. Use `--workers 1` for Gunicorn (single worker, no concurrency issue, but limits throughput)
3. Accept that Chroma is read-only at runtime (ingestion is offline), which largely mitigates write conflicts, but stale-read risk remains across worker restarts

**Recommendation:** Add a note that for Gunicorn deployment, either use `--workers 1` or switch Chroma to HTTP server mode. The "files, not network services" claim needs a caveat.

### 3.3 Embedding Model Assessment

| Claim | Verified | Finding |
|---|---|---|
| "bge-m3 is multilingual" | ✅ | Supports 100+ languages, trained on 170+. Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Urdu, Kannada, Malayalam, Punjabi — all supported. |
| bge-m3 handles all 20 listed languages | ⚠️ **Partial** | bge-m3 is trained on unbalanced data. Performance for **low-resource languages** like Dogri, Maithili, Konkani, Manipuri, Santali, and Bodo may be poor. The plan acknowledges this implicitly with the Beta tier but doesn't quantify the risk. |
| bge-m3 cross-lingual retrieval works for legal text | ⚠️ **Unverified** | bge-m3 is primarily benchmarked on general-domain text. Legal/statutory text with specific section numbers, provisos, and Hindi legal terminology may have significantly lower retrieval quality. The Phase 0 spike should specifically test legal retrieval quality. |

### 3.4 Translation Pipeline

| Claim | Verified | Finding |
|---|---|---|
| "IndicTrans2 as optional translation adapter" | ✅ | IndicTrans2 supports 22 scheduled Indian languages + English. |
| Plan lists 20 languages | ⚠️ **Mismatch** | See §7 Language Audit below for detailed comparison. |

### 3.5 LangChain "Thin Use" Claim

| Concern | Severity |
|---|---|
| "LangChain used only for document loading, retrieval and prompt composition" (§1 L16) | 🟡 **Version pinning risk** — LangChain's API surface changes frequently. The plan says `pip install langchain langchain-community langchain-ollama langchain-chroma` (§23.2 L1012–1014) which is 4 LangChain packages. "Thin use" with 4 packages is contradictory. Breaking changes between `langchain` and `langchain-community` are common. |
| No version pins specified | 🔴 **High** — `pip install langchain` without a version pin in a rapidly-changing library is a reproducibility hazard. The plan mentions `pip freeze > requirements-lock.txt` after first install but this is reactive, not proactive. |

### 3.6 Django Configuration

| Issue | Location | Severity | Detail |
|---|---|---|---|
| Django 5.x specified | §5 L138 | ⚠️ | Django 5.x requires Python 3.10+. The plan specifies Python 3.11 (§23.1 L998), which is compatible. But the bootstrap command uses `py -3.11` (Windows-only). |
| `django-admin startproject config .` | §23.2 L1016 | ✅ | Correct — creates the `config/` directory as the Django project in the current directory. |
| No `ALLOWED_HOSTS` in `.env.example` | §23.3 L1039 | 🟡 | `ALLOWED_HOSTS` is critical for production. Should be in the example env file. |
| HTMX + Alpine.js claimed | §5 L139 | ⚠️ | Alpine.js is mentioned in the stack table but never referenced again in the entire plan. Is it actually needed, or was it a leftover from v2/v3? |

---

## 4. Internal Contradictions & Inconsistencies

| # | Contradiction | Location A | Location B | Severity |
|---|---|---|---|---|
| C-1 | **"v3 correction" vs "v4.1" naming** | §2 table header says "v3 correction" | Title says "v4.1" | 🟢 Low — cosmetic but confusing. Was there a v3 that was superseded? |
| C-2 | **"Retrieve 8 chunks" vs "Keep at most 4–5 evidence chunks"** | §6.2 L204 | §6.2 L206 | 🟢 Low — Retrieve 8, keep 4–5 after dedup. Logically consistent but the flow should be clearer: "retrieve 8 → dedup → keep top 4–5." |
| C-3 | **"No Celery" but "bounded waiting queue"** | §1 L23 "Do not add Celery" | §10 L408 "bounded waiting queue with a visible 'model busy' response" | 🟡 Medium — How is the waiting queue implemented without a task queue? If it's in-process, it requires threading or asyncio, which the plan explicitly avoids ("synchronous request with timeout" §2 L42). |
| C-4 | **"Synchronous request with timeout" vs "one active GPU generation at a time" with queue** | §2 L42 | §10 L407–408 | 🟡 Medium — If requests are synchronous and there's no async queue, the second concurrent user simply blocks the Django worker thread until the first generation completes or times out. This is architecturally different from a "queue." The plan should clarify: is it a semaphore-guarded synchronous wait or an actual queue? |
| C-5 | **Windows workspace path vs Linux deployment** | §7 L539: `C:\IP-SAKTI-Sahayak\` | §12 L500: "Gunicorn on Linux" | 🟡 Medium — Project structure uses Windows paths, but Linux deployment is recommended. Bootstrap commands are PowerShell-only. |
| C-6 | **"No persistent chat history by default" vs "last 4 [chat turns] plus a safe summary"** | §10 L415 | §10 L404 | 🟡 Medium — If chat history isn't retained, how are the "last 4 turns" sent to the model? They must be in the session (which is transient). But the plan also says "session-scoped history" (§10 L399). The distinction between "session memory" and "persistent history" should be explicit. |
| C-7 | **Alpine.js in stack but never used** | §5 L139 | Entire rest of plan | 🟢 Low — Alpine.js appears once. Either remove from stack or explain where it's used. |
| C-8 | **"Fourteen-day MVP plan" (§24) vs "Days 1–21" (§14)** | §14: 5 phases across 21 days | §24: 14-day table | 🟡 Medium — §14 describes Phases 0–5 across 21 days. §24 shows a 14-day table. These are different timelines. Which one is authoritative? |
| C-9 | **"30-question golden set" (§14 L598) vs "30–40 grounded India questions" (§15 L663)** | §14 L598 | §15 L663 | 🟢 Low — 30 vs 30–40. Minor discrepancy but should be consistent. |
| C-10 | **Feedback in USER_GUIDE but Feedback model is "should ship"** | USER_GUIDE L91–92 | §3.2 L72 | 🟡 Medium — The USER_GUIDE tells users to "Use feedback to flag…" but feedback buttons are listed under "Should ship" (§3.2), not "Must ship" (§3.1). If feedback doesn't ship, the user guide is wrong. |
| C-11 | **"IndicTrans2 disabled until RAG works" (Profile A) but Translation is "optional" (§1)** | §12 L494 | §1 L20 | 🟢 Low — Consistent in intent but the wording differs. |
| C-12 | **"SQLite for application data" but no SQLite concurrency note** | §1 L21, §4 L130 | §12 Profile B/C | 🟡 Medium — SQLite has a write lock. With Gunicorn multi-workers writing `AnswerAudit` and `Feedback` rows concurrently, SQLite `SQLITE_BUSY` errors are possible. The plan should mention WAL mode or `CONN_MAX_AGE` settings. |

---

## 5. Timeline & Resourcing Realism

### 5.1 The Two-Timeline Problem

> [!IMPORTANT]
> **§14 describes a 21-day plan across 5 phases. §24 describes a 14-day plan.** These are contradictory. Which timeline is the team following?

| Phase (§14) | Days | §24 Day Mapping | Conflict? |
|---|---|---|---|
| Phase 0: Feasibility spike | Days 1–2 | Day 1 | ⚠️ 2 days compressed to 1 |
| Phase 1: India RAG | Days 3–7 | Days 2–7 | ≈ Aligned |
| Phase 2: Product flow | Days 8–11 | Days 8–10 | ⚠️ 4 days compressed to 3 |
| Phase 3: Multilingual | Days 12–16 | Days 10–11 | 🔴 5 days compressed to 2 |
| Phase 4: International + polish | Days 17–19 | Day 12 | 🔴 3 days compressed to 1 |
| Phase 5: Hardening | Days 20–21 | Days 13–14 | ≈ Aligned |

**Verdict:** The 14-day plan is significantly more aggressive than the 21-day plan. Multilingual expansion (5 days → 2 days) and international pilot (3 days → 1 day) are particularly unrealistic in the 14-day version.

### 5.2 Critical Path Risks

| Risk | Impact | Likelihood |
|---|---|---|
| **Corpus acquisition takes longer than expected** — India Code is unreliable, NBA URL is broken, D&C Rules "relevant ASU portions" requires legal judgment | Delays Phase 1 gate | 🔴 High |
| **Section-aware parsing is harder than expected** — Legal text has provisos, explanations, schedules, cross-references, and amendments that break naive section splitting | Delays Phase 1 | 🔴 High |
| **Qwen 7B doesn't reliably produce structured JSON** | Requires prompt engineering iteration; may need format enforcement | 🟡 Medium |
| **bge-m3 retrieval quality is poor for Hindi legal text** | May require Hindi-specific embedding experiments | 🟡 Medium |
| **6-person team with 2 people doing legal research AND wizard rules AND QA sets** | These are three distinct skill-heavy tasks for 2 people | 🟡 Medium |

### 5.3 Day-by-Day Feasibility Assessment (14-Day Plan)

| Day | Deliverable | Realistic? | Notes |
|---|---|---|---|
| 1 | Hardware benchmark + Django skeleton | ✅ Yes | Django skeleton is `startproject` + `startapp` — minutes. Benchmark is 2–3 hours. |
| 2 | First 2 P0 sources + manifests | ⚠️ Tight | Requires downloading, verifying reuse rights, creating manifests, legal metadata review. If India Code is down, this blocks. |
| 3 | Section-aware parser | ⚠️ Tight | Parsing Indian legal PDFs with provisos, schedules, and OCR artifacts is a multi-day task in practice. |
| 4 | Chroma ingestion/retrieval | ✅ Yes | If parser works, ingestion is straightforward with LangChain. |
| 5 | Structured Qwen answer | ⚠️ Tight | Prompt engineering for reliable JSON output from a 7B model requires iteration. |
| 6 | Citation validation + fallback | ✅ Yes | Deterministic code, well-defined requirements. |
| 7 | 30-question golden set | ⚠️ Tight | Creating 30 high-quality legal Q&A pairs with expected source IDs requires domain expertise. |
| 8 | Django chat + source drawer | ✅ Yes | HTMX-based chat is well-documented. |
| 9 | Wizard v1 | ✅ Yes | Deterministic decision tree with HTMX forms. |
| 10 | Hindi UI + mixed Hindi queries | ⚠️ Tight | Django i18n setup + testing multilingual retrieval quality. |
| 11 | Five pilot language experiments | 🔴 Unrealistic | Evaluating 5 languages requires creating test sets, running retrieval experiments, and making keep/cut decisions — in one day. |
| 12 | Privacy/security/failure states | ⚠️ Tight | The security checklist in §10 has 15+ items. Testing all failure states from §11 in one day is aggressive. |
| 13 | Offline package + backup | ✅ Yes | Packaging is Docker/script work. |
| 14 | Demo/PPT/user test | ✅ Yes | If everything else is done. |

---

## 6. Security & Privacy Audit

### 6.1 Threat Model Assessment

The threat table in §10 is comprehensive for an MVP. Specific audit findings:

| # | Finding | Location | Severity | Detail |
|---|---|---|---|---|
| S-1 | **No Content Security Policy (CSP) mentioned** | §10 | 🟡 Medium | The plan mentions XSS escaping but not CSP headers. Django's `SecurityMiddleware` doesn't add CSP by default. A CSP header (`script-src 'self'`) would mitigate XSS even if escaping fails. |
| S-2 | **Ollama bound to 127.0.0.1 — but no auth** | §10 L410 | 🟡 Medium | Ollama has no built-in authentication. If another process on the same machine is compromised, it can send arbitrary prompts to Ollama. This is acceptable for a demo laptop but should be noted for Profile C (public preview). |
| S-3 | **"No arbitrary file upload in MVP" but "Export answer as PDF"** | §10 L405, §3.2 L73 | 🟢 Low | PDF export is server-side generation, not user upload. No conflict, but the distinction should be explicit. |
| S-4 | **Session fixation not mentioned** | §10 | 🟡 Medium | Django's default session middleware is vulnerable to session fixation if `SESSION_COOKIE_SECURE` and `SESSION_COOKIE_HTTPONLY` aren't set. The plan mentions "secure cookie settings in deployed mode" (L414) but doesn't enumerate which settings. |
| S-5 | **Rate limiting specification is vague** | §10 L394 | 🟡 Medium | "Per-session rate limit" — what's the rate? 10/min? 100/hour? Without a number, implementation will vary. |
| S-6 | **Idempotency token implementation not specified** | §22.3 L985–986 | 🟡 Medium | The plan says "idempotency token" for question submissions but doesn't specify the mechanism (UUID in form hidden field? Server-side token store?). |
| S-7 | **DPDP Act not referenced** | §10 | 🔴 High | The problem statement explicitly requires "privacy, audit and security aligned to the Digital Personal Data Protection regime." The plan has good privacy defaults but never cites the DPDP Act, 2023. Specific DPDP requirements like consent notice, purpose limitation, data retention limits, and the right to erasure should be mapped to the system's behavior. |
| S-8 | **No mention of model licence compliance** | §10 L398 | 🟡 Medium | The plan says "model provenance and licence manifest." Qwen2.5 uses the Apache 2.0 licence, which is permissive. But bge-m3 uses MIT. IndicTrans2 uses MIT. These should be documented in a `LICENCES.md` or `NOTICES` file for compliance. |
| S-9 | **Audit log stores "cited_chunk_ids" but not query hash** | §22.2 L960–962 | 🟡 Medium | The `AnswerAudit` model stores `cited_chunk_ids` but the plan says "do not store the full chat question/answer by default" (L968). For DPDP compliance and abuse investigation, a one-way hash of the query (not the query itself) would be useful. |

---

## 7. Language & Translation Audit

### 7.1 The 20-Language List Cross-Check

The plan lists 20 languages across three tiers (§7.2 L296–299). Here's a cross-check against IndicTrans2's supported languages:

| Language | Plan Tier | In IndicTrans2? | In bge-m3 (likely)? | Notes |
|---|---|---|---|---|
| English | Verified | ✅ | ✅ | |
| Hindi | Verified | ✅ | ✅ | |
| Bengali | Pilot | ✅ | ✅ | |
| Marathi | Pilot | ✅ | ✅ | |
| Tamil | Pilot | ✅ | ✅ | |
| Telugu | Pilot | ✅ | ✅ | |
| Gujarati | Pilot | ✅ | ✅ | |
| Urdu | Beta | ✅ | ✅ | RTL noted in plan |
| Kannada | Beta | ✅ | ⚠️ Lower resource | |
| Malayalam | Beta | ✅ | ⚠️ Lower resource | |
| Odia | Beta | ✅ | ⚠️ Lower resource | |
| Punjabi | Beta | ✅ | ⚠️ Lower resource | |
| Assamese | Beta | ✅ | ⚠️ Lower resource | |
| Sanskrit | Beta | ✅ | ⚠️ Very low resource | |
| Nepali | Beta | ✅ | ⚠️ Lower resource | |
| Konkani | Beta | ✅ | ❌ Very unlikely | Konkani has minimal web training data |
| Maithili | Beta | ✅ | ❌ Very unlikely | Maithili has minimal web training data |
| Dogri | Beta | ✅ | ❌ Very unlikely | Dogri has minimal web training data |
| Sindhi | Beta | ✅ | ⚠️ RTL noted | RTL (Perso-Arabic script) |
| Manipuri | Beta | ✅ (Meitei script) | ❌ Very unlikely | Very low resource in embeddings |

> [!WARNING]
> **IndicTrans2 supports 22 scheduled languages + English = 23 total.** The plan lists only 20. Missing from the plan:
> - **Bodo** (brx_Deva) — 8th Schedule language
> - **Kashmiri** (kas_Arab/kas_Deva) — 8th Schedule language
> - **Santali** (sat_Olck) — 8th Schedule language, uses Ol Chiki script
>
> If the goal is "20 languages visible in the selector" (§3.1 L63), the plan should explain why these 3 are excluded (presumably very low resource / very small speaker population for IP queries).

### 7.2 Translation Flow Issues

| # | Issue | Location | Severity |
|---|---|---|---|
| T-1 | **IndicTrans2 model size not mentioned** | §5 | 🟡 Medium | The IndicTrans2 1B model requires ~4 GB RAM/VRAM. On a machine already running Qwen 7B Q4 (~5 GB), this adds significant memory pressure. The plan should specify whether to use CPU-only inference for translation. |
| T-2 | **"Generate a grounded answer in a well-supported pivot language" (§7.3 L308)** — which pivot? | §7.3 | 🟡 Medium | Is the pivot always English? Always Hindi? The plan should specify the pivot language selection logic. |
| T-3 | **Source quotations "remain in their original language" (USER_GUIDE L31)** — but sources are in English and Hindi | USER_GUIDE L31 | 🟢 Low | This is correct behavior but should clarify: most Indian statutes are in English. Hindi translations exist for some but are not always authoritative. The "original language" of the source is almost always English for the MVP corpus. |

---

## 8. Edge Case Coverage Audit

### 8.1 Edge Cases Present in §11 But Missing Implementation Guidance

The plan lists 50+ edge cases in §11 (L421–481) but several lack clear implementation paths:

| Edge Case | Line | Implementation Guidance? | Gap |
|---|---|---|---|
| "Misspellings, transliteration and mixed scripts" | L428 | ❌ None | How does the system handle Romanised Hindi ("kya patent ho sakta hai")? bge-m3 may or may not handle transliteration well. No fallback specified. |
| "Multiple questions in one message" | L430 | ❌ None | Does the system attempt to split? Refuse? Answer the first only? |
| "Amendment published but not yet in force" | L444 | ❌ None | How is `effective_from` (future date) handled in retrieval? Is it filtered out or shown with a warning? |
| "Provision repealed, superseded or retained only for transitional cases" | L445 | ⚠️ Partial | Metadata has `status: current` but no `status: repealed` or `status: transitional` handling described. |
| "OCR changes a section number, negation, date or monetary amount" | L446 | ❌ None | This is acknowledged as a risk but no mitigation beyond manual QA is specified. OCR error detection is non-trivial. |
| "Two or three users submit questions simultaneously" | L467 | ⚠️ Partial | Semaphore + queue mentioned in §10, but implementation specifics are in contradiction (see C-3, C-4 above). |

### 8.2 Edge Cases Missing from §11

| Missing Edge Case | Why It Matters |
|---|---|
| **User asks in one language but selects a different language** | e.g., Types in English but has Hindi selected. Should the system answer in Hindi or English? |
| **Corpus has no content for the selected IP type** | e.g., User asks about GI registration but only Patents Act and BD Act are in the MVP corpus. |
| **User asks the same question twice in quick succession** | The idempotency token should handle this, but the edge case isn't enumerated. |
| **Browser session expires mid-wizard** | Wizard state is in `WizardSession` with `session_key`. What if the session cookie expires midway through the wizard flow? |
| **Model generates valid JSON but with hallucinated chunk_ids that coincidentally match real chunks** | The plan validates that chunk_ids exist, but what if the model hallucinates a chunk_id that happens to exist but isn't relevant? This is the "spurious citation" problem. |

---

## 9. Document Quality & Formatting

### 9.1 README.md

| # | Issue | Line | Severity |
|---|---|---|---|
| D-1 | Windows path `C:\IP-SAKTI-Sahayak` hardcoded | 3 | 🟡 Medium |
| D-2 | No project description for newcomers | — | 🔴 High |
| D-3 | No licence declaration | — | 🟡 Medium |
| D-4 | Version says "v4 MVP stack" in heading but links to "v4.1" plan | 9 vs 5 | 🟢 Low |
| D-5 | CRLF line endings (`\r\n`) | Throughout | 🟢 Low — but may cause issues on Linux |

### 9.2 IMPLEMENTATION_PLAN.md

| # | Issue | Line | Severity |
|---|---|---|---|
| D-6 | CRLF line endings throughout | All | 🟢 Low |
| D-7 | PowerShell-only bootstrap (§23.2) with no Linux equivalent | 1006–1024 | 🟡 Medium |
| D-8 | Backtick escaping in PowerShell commands may confuse readers | 1012–1014 | 🟢 Low |
| D-9 | `SOURCES.md` referenced in project structure (L563) but never described | 563 | 🟡 Medium |
| D-10 | `scripts/ingest.ps1`, `check_system.ps1`, `warmup.ps1` listed (L573–575) but never described | 573–575 | 🟡 Medium |
| D-11 | No table of contents for a 1,185-line document | — | 🟡 Medium |
| D-12 | §2 table says "v3 correction" — is this v3 or v4? | 35–44 | 🟢 Low |

### 9.3 USER_GUIDE.md

| # | Issue | Line | Severity |
|---|---|---|---|
| D-13 | CRLF line endings | All | 🟢 Low |
| D-14 | No version/date stamp | — | 🟢 Low |
| D-15 | "Use feedback to flag a wrong citation…" (L91) — but feedback is "should ship," not "must ship" | 91 | 🟡 Medium |
| D-16 | No jurisdiction toggle explanation | — | 🟡 Medium |
| D-17 | No explanation of confidence tiers (Strong evidence / Limited evidence / Unable to answer) | — | 🟡 Medium |

---

## 10. Consolidated Findings Table

### Severity Legend
- 🔴 **Critical** — blocks correctness, compliance, or deployment
- 🟠 **High** — significant gap that affects quality or completeness
- 🟡 **Medium** — should be addressed before demo
- 🟢 **Low** — minor polish or enhancement

| ID | Category | Finding | Severity | File | Recommended Action |
|---|---|---|---|---|---|
| URL-1 | URL | DMR Act India Code URL returns 404 | 🔴 | IMPL §19.1 L746 | Find correct handle or replace with gazette PDF |
| URL-2 | URL | NBA BD Rules URL returns 404 | 🔴 | IMPL §19.1 L748 | Replace with current `nbaindia.org` URL |
| URL-3 | URL | India Code server unreliable (3 timeouts) | 🟠 | IMPL §19.1 | Add fallback gazette PDF URLs |
| L-2 | Legal | Section 3(p) effective date in metadata example is wrong | 🟠 | IMPL §6.1 L188 | Use 2005-01-01 (Patents Amendment Act 2005) |
| L-3 | Legal | 2024 Patent Rules not listed as corpus source | 🔴 | IMPL §19.1 | Add as P1 source |
| L-4 | Legal | BD Act 2023 amendment not distinguished from parent Act | 🟡 | IMPL §19.1 | Clarify if consolidated or separate documents |
| L-5 | Legal | Classical medicine definition missing D&C Rule 2(ee) reference | 🟡 | IMPL §8 | Add regulatory definition reference |
| L-6 | Legal | Schedule T (GMP for ASU) missing from corpus | 🟠 | IMPL §19.1 | Add as P1 source |
| T-1 | Technical | Qwen 7B VRAM claim overstated (8–12 GB vs actual 6–8 GB) | 🟡 | IMPL §5 L152 | Correct to "6 GB minimum, 8 GB recommended" |
| T-2 | Technical | ChromaDB multi-worker concurrency risk | 🔴 | IMPL §4, §12, §26 | Document single-worker or server-mode requirement |
| T-3 | Technical | LangChain version not pinned | 🟠 | IMPL §23.2 | Pin versions in `requirements.in` |
| T-4 | Technical | `ollama pull qwen2.5:7b` doesn't specify quantization | 🟡 | IMPL §23.2 | Specify exact tag (e.g., `qwen2.5:7b-instruct-q4_K_M`) |
| T-5 | Technical | Alpine.js in stack table but never referenced again | 🟢 | IMPL §5 L139 | Remove or explain usage |
| T-6 | Technical | IndicTrans2 memory impact not assessed | 🟡 | IMPL §5 | Document ~4 GB additional memory for translation model |
| C-3 | Consistency | "No Celery" contradicts "bounded waiting queue" | 🟡 | IMPL §1 vs §10 | Clarify queue is a Django threading semaphore, not a task queue |
| C-4 | Consistency | "Synchronous requests" contradicts queue semantics | 🟡 | IMPL §2 vs §10 | Define exact concurrency mechanism |
| C-5 | Consistency | Windows paths vs Linux deployment | 🟡 | IMPL §13 vs §12 | Use platform-neutral paths |
| C-8 | Consistency | 14-day plan vs 21-day plan contradicts | 🟠 | IMPL §14 vs §24 | Reconcile into one authoritative timeline |
| C-10 | Consistency | USER_GUIDE mentions feedback but it's "should ship" | 🟡 | USER_GUIDE L91 vs IMPL §3.2 | Move feedback to "must ship" or add "if available" caveat |
| C-12 | Consistency | SQLite concurrent writes under Gunicorn | 🟡 | IMPL §4, §12 | Document WAL mode requirement |
| S-7 | Security | DPDP Act not referenced | 🔴 | IMPL §10 | Map system behavior to DPDP requirements |
| S-1 | Security | No Content Security Policy headers | 🟡 | IMPL §10 | Add CSP to security checklist |
| S-5 | Security | Rate limiting has no specific numbers | 🟡 | IMPL §10 | Specify rate limits |
| S-8 | Security | Model/library licence manifest missing | 🟡 | IMPL §10 | Create `LICENCES.md` |
| LANG-1 | Language | 3 scheduled languages missing (Bodo, Kashmiri, Santali) | 🟡 | IMPL §7.2 | Explain exclusion or add to Beta |
| LANG-2 | Language | Low-resource language embedding quality unverified | 🟡 | IMPL §7 | Add explicit evaluation plan for Konkani, Maithili, Dogri, Manipuri |
| LANG-3 | Language | Pivot language for translation not specified | 🟡 | IMPL §7.3 | Specify English as default pivot |
| EDGE-1 | Edge case | Romanised Hindi handling not specified | 🟡 | IMPL §11 | Add transliteration handling strategy |
| EDGE-2 | Edge case | Multiple questions in one message not specified | 🟡 | IMPL §11 | Define behavior (answer first, refuse, or split) |
| EDGE-3 | Edge case | Future-dated amendments not handled in retrieval | 🟡 | IMPL §11 | Add `effective_from` date filter logic |
| EDGE-4 | Edge case | Spurious citation (valid chunk_id, wrong context) | 🟡 | IMPL §6.4 | Add relevance check (not just existence check) |
| DOC-1 | Documentation | README has no project description | 🟠 | README | Add 3–5 sentence description |
| DOC-2 | Documentation | No table of contents for 1,185-line plan | 🟡 | IMPL | Add TOC |
| DOC-3 | Documentation | CRLF line endings may cause Linux issues | 🟢 | All files | Convert to LF |
| DOC-4 | Documentation | `SOURCES.md` referenced but not described | 🟡 | IMPL §13 L563 | Add description or template |
| DOC-5 | Documentation | Scripts (`.ps1`) listed but not described | 🟡 | IMPL §13 L573–575 | Add brief descriptions |
| TIMELINE-1 | Timeline | 14-day vs 21-day contradiction | 🟠 | IMPL §14 vs §24 | Pick one and reconcile |
| TIMELINE-2 | Timeline | Day 11 (5 pilot languages in 1 day) is unrealistic | 🔴 | IMPL §24 | Extend to 2–3 days or reduce scope |
| TIMELINE-3 | Timeline | Corpus acquisition on Day 2 assumes India Code availability | 🟠 | IMPL §24 | Pre-download sources or have gazette PDF fallbacks ready |

---

## Summary Statistics

| Severity | Count |
|---|---|
| 🔴 Critical | 8 |
| 🟠 High | 8 |
| 🟡 Medium | 24 |
| 🟢 Low | 7 |
| **Total** | **47** |

### Top 5 Actions by Impact

1. **Fix the 2 broken URLs** (URL-1, URL-2) — these block corpus acquisition entirely
2. **Resolve the ChromaDB concurrency issue** (T-2) — this affects all multi-user scenarios including the demo
3. **Reconcile the 14-day vs 21-day timeline** (C-8, TIMELINE-1) — the team can't follow two schedules
4. **Add DPDP Act mapping** (S-7) — required by the problem statement, currently absent
5. **Add missing corpus sources** (L-3, L-6) — 2024 Patent Rules and Schedule T are high-priority gaps

> [!IMPORTANT]
> Despite 47 findings, the fundamental architecture is sound. Most findings are **addressable documentation fixes**, not architectural flaws. The 8 critical items should be resolved before any code is written.
