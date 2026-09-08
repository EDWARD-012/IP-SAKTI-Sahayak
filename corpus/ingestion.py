"""
corpus/ingestion.py — Real corpus ingestion pipeline.

Flow:
    source files (PDF / TXT)  →  extract text  →  section-aware chunking
    →  bge-m3 embeddings  →  Chroma upsert  →  CorpusVersion / SourceManifest rows

Heavy dependencies (pypdf, sentence-transformers, chromadb, PyYAML) are imported
lazily inside functions so that importing this module never fails in DEMO_MODE
or during test collection. Callers get a clear IngestionError if a dependency
is missing.

The chunk metadata written to Chroma MUST match the keys ai/retrieve.py reads:
    chunk_id, source_id, section_ref, title, jurisdiction,
    effective_from, effective_status
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from django.conf import settings

logger = logging.getLogger("ai")


class IngestionError(RuntimeError):
    """Raised when a required ingestion dependency or input is missing."""


# ── Chunk container ───────────────────────────────────────────

@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Section / article heading detection ───────────────────────
# Matches lines such as:  "3. Short title", "Section 3A.", "Article 27", "27B."
_SECTION_RE = re.compile(r"^\s*(?:section\s+)?(\d+[A-Z]{0,2})\.\s", re.IGNORECASE)
_ARTICLE_RE = re.compile(r"^\s*article\s+(\d+[A-Z]{0,2})\b", re.IGNORECASE)


def _detect_section(paragraph: str) -> str:
    """Return a section/article label if *paragraph* starts like a heading, else ''."""
    head = paragraph.lstrip()[:80]
    m = _ARTICLE_RE.match(head)
    if m:
        return f"Article {m.group(1)}"
    m = _SECTION_RE.match(head)
    if m:
        return f"Section {m.group(1)}"
    return ""


# ── Text extraction ───────────────────────────────────────────

def extract_text(path: Path) -> str:
    """
    Extract plain text from a .pdf or .txt file.

    PDFs: pypdf first, pdfminer.six as fallback. Plain .txt read directly.
    Raises IngestionError when a PDF parser is unavailable.
    """
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")

    if suffix != ".pdf":
        raise IngestionError(f"Unsupported source file type: {path.name}")

    # ── pypdf ──
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "") for page in reader.pages]
        text = "\n".join(pages).strip()
        if text:
            return text
        logger.warning("pypdf extracted no text from %s — trying pdfminer.", path.name)
    except ImportError:
        logger.info("pypdf not installed — trying pdfminer.")
    except Exception as exc:
        logger.warning("pypdf failed on %s: %s — trying pdfminer.", path.name, exc)

    # ── pdfminer.six fallback ──
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
        return (pdfminer_extract(str(path)) or "").strip()
    except ImportError as exc:
        raise IngestionError(
            "No PDF parser available. Install with: pip install pypdf pdfminer.six"
        ) from exc


# ── Chunking ──────────────────────────────────────────────────

def chunk_text(
    text: str,
    *,
    source_id: str,
    title: str,
    jurisdiction: str,
    effective_from: str,
    effective_status: str,
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> list[Chunk]:
    """
    Split *text* into overlapping, section-aware chunks.

    Paragraphs are accumulated up to ``max_chars``; when the limit is reached a
    chunk is emitted and a ``overlap_chars`` tail is carried into the next chunk
    to preserve context across boundaries. The most recently seen section/article
    heading is recorded as ``section_ref`` metadata for every chunk.
    """
    # Normalise whitespace, split into paragraphs on blank lines.
    text = re.sub(r"[ \t]+", " ", text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_len = 0
    current_section = ""
    idx = 0

    def _emit() -> str:
        nonlocal idx
        body = "\n\n".join(buf).strip()
        if not body:
            return ""
        chunk_id = f"{source_id}::{idx:04d}"
        chunks.append(Chunk(
            chunk_id=chunk_id,
            text=body,
            metadata={
                "chunk_id":         chunk_id,
                "source_id":        source_id,
                "section_ref":      current_section or "",
                "title":            title,
                "jurisdiction":     jurisdiction,
                "effective_from":   effective_from or "",
                "effective_status": effective_status or "current",
            },
        ))
        idx += 1
        return body

    for para in paragraphs:
        sec = _detect_section(para)
        if sec:
            current_section = sec

        if buf and buf_len + len(para) > max_chars:
            body = _emit()
            tail = body[-overlap_chars:] if overlap_chars else ""
            buf = [tail, para] if tail else [para]
            buf_len = len(tail) + len(para)
        else:
            buf.append(para)
            buf_len += len(para) + 2

    _emit()
    return chunks


# ── Manifest loading ──────────────────────────────────────────

def _load_manifests(manifests_dir: Path) -> dict[str, dict[str, Any]]:
    """Load every *.yaml manifest keyed by source_id. Empty dict if dir missing."""
    if not manifests_dir.is_dir():
        return {}
    try:
        import yaml
    except ImportError as exc:
        raise IngestionError(
            "PyYAML required to read manifests. Install with: pip install PyYAML"
        ) from exc

    out: dict[str, dict[str, Any]] = {}
    for yml in sorted(manifests_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
            sid = data.get("source_id") or yml.stem
            out[sid] = data
        except Exception as exc:
            logger.warning("Skipping manifest %s: %s", yml.name, exc)
    return out


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


# ── Public build entrypoint ───────────────────────────────────

@dataclass
class BuildResult:
    version: str
    collection: str
    sources_count: int
    chunks_count: int
    per_source: dict[str, int] = field(default_factory=dict)


def build_corpus(
    *,
    version: str,
    sources_dir: Path,
    manifests_dir: Path | None = None,
    max_chars: int = 1200,
    overlap_chars: int = 150,
    batch_size: int = 16,
    on_progress: Callable[[str], None] | None = None,
) -> BuildResult:
    """
    Build a Chroma collection from all PDF/TXT files in *sources_dir*.

    Returns a BuildResult. Raises IngestionError on missing deps / no sources.
    Does NOT touch CorpusVersion status — the management command owns lifecycle.
    """
    def log(msg: str) -> None:
        logger.info(msg)
        if on_progress:
            on_progress(msg)

    if not sources_dir.is_dir():
        raise IngestionError(f"Sources directory not found: {sources_dir}")

    source_files = sorted(
        p for p in sources_dir.iterdir()
        if p.suffix.lower() in (".pdf", ".txt")
    )
    if not source_files:
        raise IngestionError(
            f"No .pdf or .txt files found in {sources_dir}. "
            "Place source documents there first."
        )

    # ── Lazy heavy imports ──
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise IngestionError(
            "sentence-transformers required. Install: pip install sentence-transformers"
        ) from exc
    try:
        import chromadb
    except ImportError as exc:
        raise IngestionError(
            "chromadb required. Install: pip install chromadb"
        ) from exc

    manifests = _load_manifests(manifests_dir) if manifests_dir else {}

    log(f"Loading embedding model {settings.EMBED_MODEL} on {settings.EMBED_DEVICE} …")
    model = SentenceTransformer(settings.EMBED_MODEL, device=settings.EMBED_DEVICE)

    collection_name = f"ip_sakti_v{version.replace('.', '_')}"
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

    # Fresh collection: drop any stale one with the same name.
    try:
        client.delete_collection(collection_name)
        log(f"Removed existing collection {collection_name}.")
    except Exception:
        pass
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine", "corpus_version": version},
    )

    all_chunks: list[Chunk] = []
    per_source: dict[str, int] = {}
    manifest_rows: dict[str, dict[str, Any]] = {}

    for src in source_files:
        source_id = src.stem
        meta = manifests.get(source_id, {})
        title = meta.get("title", source_id.replace("-", " ").title())
        jurisdiction = str(meta.get("jurisdiction", "IN"))
        effective_from = str(meta.get("effective_from", "") or "")
        effective_status = str(meta.get("effective_status", "current") or "current")

        log(f"Extracting {src.name} …")
        text = extract_text(src)
        if not text.strip():
            log(f"  ! {src.name} produced no text — skipping.")
            continue

        chunks = chunk_text(
            text,
            source_id=source_id,
            title=title,
            jurisdiction=jurisdiction,
            effective_from=effective_from,
            effective_status=effective_status,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
        per_source[source_id] = len(chunks)
        all_chunks.extend(chunks)
        log(f"  {source_id}: {len(chunks)} chunks")

        manifest_rows[source_id] = {
            "meta": meta,
            "sha256": _sha256(src),
            "title": title,
            "jurisdiction": jurisdiction,
            "effective_from": effective_from,
            "effective_status": effective_status,
        }

    if not all_chunks:
        raise IngestionError("No chunks produced from any source file.")

    # ── Embed + upsert in batches ──
    log(f"Embedding {len(all_chunks)} chunks (batch={batch_size}) …")
    texts = [c.text for c in all_chunks]
    ids = [c.chunk_id for c in all_chunks]
    metas = [c.metadata for c in all_chunks]

    for start in range(0, len(all_chunks), batch_size):
        end = start + batch_size
        embeddings = model.encode(
            texts[start:end],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        collection.upsert(
            ids=ids[start:end],
            documents=texts[start:end],
            embeddings=[e.tolist() for e in embeddings],
            metadatas=metas[start:end],
        )
        log(f"  upserted {min(end, len(all_chunks))}/{len(all_chunks)}")

    # ── Persist SourceManifest + CorpusVersion rows ──
    _persist_rows(version, collection_name, per_source, manifest_rows, len(all_chunks))

    return BuildResult(
        version=version,
        collection=collection_name,
        sources_count=len(per_source),
        chunks_count=len(all_chunks),
        per_source=per_source,
    )


def _persist_rows(
    version: str,
    collection_name: str,
    per_source: dict[str, int],
    manifest_rows: dict[str, dict[str, Any]],
    chunks_count: int,
) -> None:
    """Create/update CorpusVersion (status=building) and SourceManifest rows."""
    from datetime import date

    from corpus.models import CorpusVersion, SourceManifest

    cv, _ = CorpusVersion.objects.update_or_create(
        version=version,
        defaults={
            "status": "building",
            "chroma_collection": collection_name,
            "sources_count": len(per_source),
            "chunks_count": chunks_count,
        },
    )

    for source_id, info in manifest_rows.items():
        meta = info["meta"]
        eff_from = info["effective_from"] or None
        retrieved = meta.get("retrieved_at") or None
        SourceManifest.objects.update_or_create(
            source_id=source_id,
            defaults={
                "title":            info["title"],
                "authority":        meta.get("authority", ""),
                "jurisdiction":     info["jurisdiction"],
                "ip_types":         meta.get("ip_types", []) or [],
                "landing_url":      meta.get("landing_url", "") or "",
                "sha256":           info["sha256"],
                "effective_from":   eff_from if _is_date(eff_from) else None,
                "effective_status": info["effective_status"],
                "reuse_basis":      meta.get("reuse_basis", "public-statute"),
                "retrieved_at":     retrieved if _is_date(retrieved) else date.today(),
                "notes":            str(meta.get("notes", "") or ""),
                "corpus_version":   cv,
            },
        )


def _is_date(value: Any) -> bool:
    """True if *value* looks like an ISO date string 'YYYY-MM-DD'."""
    if not value or not isinstance(value, str):
        return False
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", value.strip()))
