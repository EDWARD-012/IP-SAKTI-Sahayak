---
name: rag-pipeline
description: Build, debug and extend the IP-SAKTI RAG pipeline — chunking legal PDFs, embedding with bge-m3, retrieval from Chroma, prompt assembly and Qwen generation. Use when working on ai/ingest.py, ai/retrieve.py, ai/generate.py, ai/citations.py, or when the user mentions RAG, chunking, embeddings, Chroma, Ollama, retrieval quality, citation validation or evidence grounding.
disable-model-invocation: true
---

# IP-SAKTI RAG Pipeline

## Stack
- Embeddings: `BAAI/bge-m3` via `sentence-transformers`
- Vector store: Chroma `PersistentClient` (read-only at runtime)
- LLM: `qwen2.5:7b-instruct-q4_K_M` via `ollama` Python client
- Orchestration: thin LangChain (`langchain-chroma`, `langchain-ollama`) behind adapter modules

## Module layout
```
ai/
  __init__.py
  ingest.py      # parse → chunk → embed → publish to Chroma
  retrieve.py    # query embed → Chroma top-k → dedup → evidence threshold
  generate.py    # semaphore → Ollama chat → parse JSON answer
  citations.py   # validate chunk IDs + relevance check
  safety.py      # scope/privacy/output deterministic checks
  translate.py   # optional IndicTrans2 adapter
```

## Chunking rules
- Use section-aware splitting: split on regex `r'^\s*(Section|Rule|Article|Clause)\s+\d+'`
- Target 400–500 tokens per chunk; overlap 50 tokens
- Preserve: `source_id`, `section_ref`, `effective_from`, `effective_to`, `status`, `page`
- Store full verbatim text in metadata — citations quote this, not LLM output

## Retrieval
```python
# retrieve.py pattern
def retrieve(query: str, jurisdiction: str, k: int = 8) -> list[dict]:
    """Embed query → Chroma similarity search → dedup → keep top 4-5."""
    results = chroma_collection.query(
        query_texts=[query],
        n_results=k,
        where={"jurisdiction": jurisdiction}  # metadata filter
    )
    return deduplicate_and_rank(results)  # keep top 4-5
```

## Prompt template (system)
```
You are IP-SAKTI Sahayak, an information assistant for Ayurveda-related intellectual property.
RULES:
1. Answer ONLY from the provided evidence chunks.
2. Cite every factual claim with {"chunk_id": "...", "section": "...", "quote": "..."}.
3. If evidence is insufficient, return {"state": "unable_to_answer", "reason": "..."}.
4. Never fabricate statutes, sections, dates or treaty articles.
5. End every answer with: "This is general information, not legal advice."

JURISDICTION: {jurisdiction}
EVIDENCE:
{evidence_chunks}
QUESTION: {question}

Return JSON: {"state": "grounded"|"evidence_only"|"unable_to_answer"|"out_of_scope"|"conflict",
              "answer": "...", "citations": [...], "confidence_note": "..."}
```

## Citation validation (ai/citations.py)
A citation is valid only when ALL three hold:
1. `chunk_id` exists in the retrieved set for this request
2. Cited `section` or locator appears verbatim in the chunk text
3. Overlapping legal key terms between citation quote and answer claim

If any check fails: downgrade to `evidence_only` or `unable_to_answer`.

## Evidence threshold
- < 2 relevant chunks after dedup → `unable_to_answer`
- All citations pass check → `grounded`
- Some citations pass → `evidence_only`
- Two chunks contradict on same point → `conflict`

## Chroma collection naming
- Active collection: `ip_sakti_v{corpus_version}` e.g. `ip_sakti_v1`
- Never overwrite an active collection; create new version, then swap in `CorpusVersion`
- Index is built offline by `scripts/ingest.ps1`; app never writes to Chroma

## Debugging retrieval quality
1. Run 30-question golden set: `pytest tests/test_retrieval_golden.py`
2. Inspect chunk text: `python scripts/inspect_chunk.py <chunk_id>`
3. Check cosine similarity scores in Chroma result metadata
4. If Hindi queries underperform, test `translate query → English → retrieve` path

## See also
- [corpus-management skill](../corpus-management/SKILL.md)
- `IMPLEMENTATION_PLAN.md` §§6, 14, 22
