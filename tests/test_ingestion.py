"""
tests/test_ingestion.py — Unit tests for the pure-Python ingestion logic.

These cover text extraction (.txt), section-aware chunking, and metadata shape
WITHOUT requiring the heavy AI stack (sentence-transformers / chromadb / torch).
The embed+upsert path is exercised separately once those deps are installed.
"""
from __future__ import annotations

from pathlib import Path

from corpus.ingestion import (
    Chunk,
    _detect_section,
    chunk_text,
    extract_text,
)


def test_detect_section_variants():
    assert _detect_section("3. Short title and commencement.") == "Section 3"
    assert _detect_section("Section 3A. Inventions not patentable.") == "Section 3A"
    assert _detect_section("Article 27 Patentable subject matter") == "Article 27"
    assert _detect_section("This is an ordinary paragraph.") == ""


def test_extract_text_from_txt(tmp_path: Path):
    p = tmp_path / "sample.txt"
    p.write_text("Hello statute.\n\nSecond paragraph.", encoding="utf-8")
    assert "Hello statute." in extract_text(p)


def test_chunk_text_basic_metadata():
    text = (
        "3. Definitions.\n\n"
        "In this Act, unless the context otherwise requires, the following "
        "definitions apply to all provisions herein described in detail.\n\n"
        "Section 3(p). An invention which, in effect, is traditional knowledge "
        "or an aggregation of known properties of traditionally known components.\n\n"
        "Article 27. Patentable subject matter under the international framework."
    )
    chunks = chunk_text(
        text,
        source_id="patents-act-1970",
        title="The Patents Act, 1970",
        jurisdiction="IN",
        effective_from="1970-09-19",
        effective_status="current",
        max_chars=200,
        overlap_chars=40,
    )
    assert chunks, "expected at least one chunk"
    assert all(isinstance(c, Chunk) for c in chunks)

    first = chunks[0]
    # chunk_id format: <source_id>::<4-digit index>
    assert first.chunk_id == "patents-act-1970::0000"
    # Metadata keys must match what ai/retrieve.py reads
    for key in (
        "chunk_id", "source_id", "section_ref", "title",
        "jurisdiction", "effective_from", "effective_status",
    ):
        assert key in first.metadata, f"missing metadata key: {key}"
    assert first.metadata["source_id"] == "patents-act-1970"
    assert first.metadata["jurisdiction"] == "IN"
    # No metadata value may be None (Chroma rejects None)
    for c in chunks:
        assert all(v is not None for v in c.metadata.values())


def test_chunk_text_splits_long_input():
    # 12 paragraphs of ~100 chars with a small max should yield multiple chunks
    para = "This is a reasonably long paragraph of legal text used for testing. "
    text = "\n\n".join(f"{i}. {para}" for i in range(1, 13))
    chunks = chunk_text(
        text,
        source_id="gi-act-1999",
        title="GI Act 1999",
        jurisdiction="IN",
        effective_from="1999-12-30",
        effective_status="current",
        max_chars=250,
        overlap_chars=50,
    )
    assert len(chunks) >= 3
    # ids are sequential and unique
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
    assert ids == [f"gi-act-1999::{i:04d}" for i in range(len(ids))]


def test_chunk_text_empty_input():
    assert chunk_text(
        "   \n\n   ",
        source_id="x", title="X", jurisdiction="IN",
        effective_from="", effective_status="current",
    ) == []
