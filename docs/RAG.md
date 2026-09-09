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

## Deploy status (Railway production)

| Layer | Status |
|---|---|
| Django UI | Live |
| Postgres metadata | Active corpus **`0.3-demo`** (seeded by `seed_cloud_db`) |
| Ollama / Qwen | Live — private service `ollama` |
| Chroma vectors | Live — volume `/data/chroma_db` · collection `ip_sakti_v0_3-demo` (~43 chunks / 8 sources) |
| Embedding cache | `/data/hf` (`HF_HOME` / `TRANSFORMERS_CACHE`) |
| Full cited RAG | **Yes** — after warmup / first Ask loads bge-m3 |

Health check:

```text
GET /health/
→ demo_mode=false, ollama_reachable=true, chroma_reachable=true,
  active_corpus_version=0.3-demo
```

## Local full RAG

```powershell
python manage.py build_corpus_version 0.3-demo
python manage.py validate_corpus_version 0.3-demo
python manage.py activate_corpus_version 0.3-demo

# .env: DEMO_MODE=False, OLLAMA_BASE_URL=http://127.0.0.1:11434, CHROMA_PERSIST_DIR=./chroma_db
ollama pull qwen2.5:3b-instruct-q4_K_M
python manage.py runserver
```

## Refreshing the cloud index

1. Rebuild locally (`build_corpus_version`).
2. Upload: `railway volume files -v ip-sakti-sahayak-volume upload ./chroma_db /chroma_db --overwrite`
3. Redeploy / restart web; `seed_cloud_db` keeps `0.3-demo` / `ip_sakti_v0_3-demo` active.
4. Optional: `railway run python manage.py warmup --no-generate`

Do **not** run full embedding builds inside every container boot.

## Edge cases (pipeline)

| Situation | State |
|---|---|
| Fewer than 2 retrieved chunks | `unable_to_answer` |
| Safety blocks foreign / unsafe input | `out_of_scope` |
| Invented citation `chunk_id` | citations stripped → often `unable_to_answer` |
| Ollama generate timeout | `evidence_only` (quotes still shown) |
| Ollama down | `unavailable` |
| Generate queue full | `busy` |
| `DEMO_MODE=True` | stub demo card |

Automated coverage: `tests/test_pipeline.py` (mocked).

## Related docs

- [README.md](../README.md)
- [QUICKSTART.md](../QUICKSTART.md)
- [DEPLOY_OLLAMA.md](DEPLOY_OLLAMA.md)
- [data/CORPUS_SOURCES.md](../data/CORPUS_SOURCES.md)
- [SIH26045_Technical_Documentation.md](SIH26045_Technical_Documentation.md)
