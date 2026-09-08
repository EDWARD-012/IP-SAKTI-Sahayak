"""
ai/retrieve.py — Chroma vector store retrieval.

Returns [] immediately when DEMO_MODE=True or when Chroma/embeddings are unavailable.
In live mode: embed query with bge-m3 → Chroma similarity search → dedup → top 4-5 chunks.
"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger("ai")

# ── Module-level lazy singletons ──────────────────────────────
_embed_model: Any = None
_chroma_client: Any = None
_embed_lock = None  # threading.Lock, initialised on first use


def _get_embed_model() -> Any:
    """Lazy-load sentence_transformers embedding model (bge-m3)."""
    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s on %s", settings.EMBED_MODEL, settings.EMBED_DEVICE)
            _embed_model = SentenceTransformer(
                settings.EMBED_MODEL,
                device=settings.EMBED_DEVICE,
            )
            logger.info("Embedding model loaded.")
        except ImportError:
            logger.warning("sentence_transformers not available — retrieval disabled.")
        except Exception as exc:
            logger.error("Failed to load embedding model: %s", exc)
    return _embed_model


def _get_chroma_client() -> Any:
    """Lazy-load Chroma persistent client."""
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            logger.info("Chroma client connected at %s", settings.CHROMA_PERSIST_DIR)
        except ImportError:
            logger.warning("chromadb not available — retrieval disabled.")
        except Exception as exc:
            logger.error("Failed to connect to Chroma: %s", exc)
    return _chroma_client


def _get_active_collection(client: Any) -> Any | None:
    """Return the Chroma collection for the active corpus version."""
    try:
        from corpus.models import CorpusVersion
        cv = CorpusVersion.objects.filter(status="active").first()
        if not cv:
            logger.warning("No active corpus version found.")
            return None
        return client.get_collection(cv.chroma_collection)
    except Exception as exc:
        logger.error("Failed to get active Chroma collection: %s", exc)
        return None


def _deduplicate(results: list[dict[str, Any]], k: int = 5) -> list[dict[str, Any]]:
    """Remove duplicate chunks (same source + section) and return top k."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for r in results:
        key = f"{r.get('source_id', '')}::{r.get('section_ref', '')}"
        if key not in seen:
            seen.add(key)
            unique.append(r)
        if len(unique) >= k:
            break
    return unique


def _query_collection(
    collection: Any,
    query: str,
    jurisdiction: str,
    k: int,
) -> list[dict[str, Any]]:
    """Embed *query* and run a similarity search against *collection*."""
    embed = _get_embed_model()
    if embed is None:
        return []

    query_embedding = embed.encode([query], normalize_embeddings=True)[0].tolist()

    where: dict[str, Any] = {}
    if jurisdiction in ("IN", "INT"):
        where["jurisdiction"] = jurisdiction
    # For "BOTH", no jurisdiction filter

    query_kwargs: dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where

    results = collection.query(**query_kwargs)

    chunks: list[dict[str, Any]] = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, distances):
        chunks.append({
            "chunk_id":       meta.get("chunk_id", ""),
            "source_id":      meta.get("source_id", ""),
            "section_ref":    meta.get("section_ref", ""),
            "text":           doc,
            "effective_from": meta.get("effective_from", ""),
            "effective_status": meta.get("effective_status", "current"),
            "title":          meta.get("title", ""),
            "score":          float(1 - dist),  # cosine distance → similarity
        })
    return chunks


def retrieve_from_collection(
    query: str,
    collection_name: str,
    jurisdiction: str = "IN",
    k: int = 8,
) -> list[dict[str, Any]]:
    """
    Retrieve against a NAMED collection, ignoring DEMO_MODE and active-version
    gating. Used by validate_corpus_version to test a freshly built (not-yet-
    active) index. Returns [] on any failure.
    """
    client = _get_chroma_client()
    if client is None:
        return []
    try:
        collection = client.get_collection(collection_name)
    except Exception as exc:
        logger.error("Could not open collection %s: %s", collection_name, exc)
        return []
    try:
        return _deduplicate(_query_collection(collection, query, jurisdiction, k), k=5)
    except Exception as exc:
        logger.error("Chroma query error on %s: %s", collection_name, exc)
        return []


def retrieve(
    query: str,
    jurisdiction: str = "IN",
    k: int = 8,
) -> list[dict[str, Any]]:
    """
    Embed query → Chroma similarity search → dedup → return top 4-5 chunks.

    Each chunk dict contains:
      chunk_id, source_id, section_ref, text, effective_from, effective_status, score

    Returns [] when DEMO_MODE=True, Chroma unavailable, or no relevant chunks found.
    """
    if getattr(settings, "DEMO_MODE", True):
        return []

    embed = _get_embed_model()
    if embed is None:
        return []

    client = _get_chroma_client()
    if client is None:
        return []

    collection = _get_active_collection(client)
    if collection is None:
        return []

    try:
        return _deduplicate(_query_collection(collection, query, jurisdiction, k), k=5)
    except Exception as exc:
        logger.error("Chroma query error: %s", exc)
        return []
