# RAG in IP-SAKTI Sahayak

Retrieval-Augmented Generation (RAG) means: **search verified corpus first**, then
ask the LLM to answer **only from those passages**, with citations checked on the server.

## Pipeline (live mode · `DEMO_MODE=False`)

```text
Question
  → safety check (ai/safety.py)
  → optional translate to English (ai/translate.py)
  → embed query with bge-m3 (ai/retrieve.py)
  → Chroma similarity search (top chunks)
  → evidence gate (≥ 2 chunks required)
  → Ollama / Qwen generate (ai/generate.py)
  → citation validation (ai/citations.py)
  → output safety
  → answer + evidence label
```

| Piece | Role | Code / config |
|---|---|---|
| Embeddings | Query ↔ chunk vectors | `BAAI/bge-m3` · `EMBED_MODEL` |
| Vector store | Persistent index | Chroma · `CHROMA_PERSIST_DIR` |
| LLM | Grounded answer text | Ollama · `OLLAMA_BASE_URL` / `OLLAMA_MODEL` |
| Corpus | Versioned statutes | `CorpusVersion` + manifests · `data/manifests/` |

Evidence labels (UI): **Strong evidence** / **Limited evidence** /
**Unable to answer from verified sources**.

Internal states: `grounded` · `evidence_only` · `unable_to_answer` · `out_of_scope` ·
`conflict` · `busy` · `unavailable`.

With `DEMO_MODE=True`, retrieval and generation are skipped; the app returns an
illustrative stub (safe for UI-only demos).

## What must exist for full cited RAG

1. **Indexed Chroma collection** for the active corpus version  
   (built by `build_corpus_version` / activate — not by `seed_cloud_db`).
2. **Embedding model** loadable in the Django process (`sentence-transformers` + bge-m3).
3. **Reachable Ollama** with the project model tag.
4. **`DEMO_MODE=False`**.

If Chroma has no usable chunks, the pipeline returns `unable_to_answer` even when
Ollama is healthy (generation never invents law without evidence).

## Deploy status (honest)

| Layer | Local laptop | Railway (public demo) |
|---|---|---|
| Django UI | Yes | Yes |
| Postgres / SQLite metadata | SQLite | Postgres · corpus **`0.3-cloud`** |
| Statute list (About corpus) | Yes | Yes (`seed_cloud_db`) |
| Ollama / Qwen | Local install | **Yes** — service `ollama` on private network |
| Chroma vector index | Yes, if you built/activated a version | **Not deployed yet** |
| Full cited RAG | Yes, with indexed corpus | **No** — metadata + LLM only |

### Railway today

- `DEMO_MODE=False`
- `OLLAMA_BASE_URL=http://ollama.railway.internal:11434`
- Active corpus: **`0.3-cloud`** (manifests / About page metadata)
- `seed_cloud_db` **does not** write Chroma vectors
- Without a synced `chroma_db` (or `CHROMA_PERSIST_DIR` on `/data`), Ask cannot
  retrieve passages → answers stay in the **unable / under-evidenced** path, not
  full grounded citations

### Local full RAG

```powershell
# 1. Corpus files under data/raw/ (see data/CORPUS_SOURCES.md)
python manage.py build_corpus_version 0.3-demo
python manage.py validate_corpus_version 0.3-demo
python manage.py activate_corpus_version 0.3-demo

# 2. .env
# DEMO_MODE=False
# OLLAMA_BASE_URL=http://127.0.0.1:11434
# CHROMA_PERSIST_DIR=./chroma_db

ollama pull qwen2.5:3b-instruct-q4_K_M
python manage.py runserver
```

### How to bring full RAG to Railway (follow-up)

1. Build and validate the corpus **locally** (Chroma under `chroma_db/` or `DATA_DIR`).
2. Copy the Chroma persist directory onto the Railway volume (e.g. `/data/chroma_db`).
3. Set `CHROMA_PERSIST_DIR=/data/chroma_db` on the web service.
4. Ensure the active `CorpusVersion.chroma_collection` name matches the uploaded collection.
5. Confirm embedding deps are in the web image (`sentence-transformers`, model download on first Ask — cold start can be large/slow on CPU).
6. Re-check `/health/` and run a Section 3(p) Ask — expect `grounded` + citations.

Until that sync is done, treat Railway as: **UI + corpus metadata + cloud Ollama**;
treat **full RAG** as the laptop-indexed profile (or the post-sync cloud profile).

## Related docs

- [README.md](../README.md) — entry + live URLs  
- [QUICKSTART.md](../QUICKSTART.md) — local setup  
- [DEPLOY_OLLAMA.md](DEPLOY_OLLAMA.md) — Railway Ollama service  
- [data/CORPUS_SOURCES.md](../data/CORPUS_SOURCES.md) — source acquisition  
- [SIH26045_Technical_Documentation.md](SIH26045_Technical_Documentation.md) — full SIH write-up  
