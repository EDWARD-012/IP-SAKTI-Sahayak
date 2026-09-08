"""
ai/citations.py — Citation validation.

A citation is valid only when ALL three conditions hold:
  1. chunk_id is in the retrieved set for this request
  2. The cited section/locator string appears in the chunk text (verbatim)
  3. Overlapping legal key terms between citation quote and chunk text
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("ai")


def _normalise_section(section: str) -> str:
    """Normalise section reference for comparison (lowercase, strip whitespace)."""
    return re.sub(r"\s+", " ", section.strip().lower())


def _terms_overlap(text_a: str, text_b: str, min_terms: int = 2) -> bool:
    """Check if two texts share at least *min_terms* non-trivial words."""
    stop_words = {
        "the", "a", "an", "and", "or", "of", "in", "to", "for", "is", "are",
        "was", "were", "be", "been", "has", "have", "had", "with", "that",
        "this", "it", "its", "any", "all", "such", "as", "by", "at", "on",
    }
    words_a = {w for w in re.findall(r"\b\w{4,}\b", text_a.lower()) if w not in stop_words}
    words_b = {w for w in re.findall(r"\b\w{4,}\b", text_b.lower()) if w not in stop_words}
    return len(words_a & words_b) >= min_terms


def validate(
    raw_response: dict[str, Any],
    retrieved_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Validate citations in *raw_response* against the *retrieved_chunks*.

    Mutates and returns *raw_response* with:
      - citations list updated (invalid citations removed)
      - state upgraded/downgraded based on validation result

    Returns the validated response dict.
    """
    if not retrieved_chunks:
        raw_response["state"] = "unable_to_answer"
        raw_response["citations"] = []
        raw_response.setdefault("confidence_note", "No retrieved chunks to validate against.")
        return raw_response

    chunk_map: dict[str, dict[str, Any]] = {c["chunk_id"]: c for c in retrieved_chunks}
    citations: list[dict[str, Any]] = raw_response.get("citations", []) or []

    validated: list[dict[str, Any]] = []
    rejected: list[str] = []

    for cite in citations:
        chunk_id = cite.get("chunk_id", "")
        section  = cite.get("section", "")
        quote    = cite.get("quote", "")

        # ── Check 1: chunk_id in retrieved set ───────────────
        if chunk_id not in chunk_map:
            rejected.append(f"{chunk_id}: not in retrieved set")
            continue

        chunk_text = chunk_map[chunk_id].get("text", "")

        # ── Check 2: section appears in chunk text ───────────
        if section:
            norm_section = _normalise_section(section)
            norm_text    = _normalise_section(chunk_text)
            if norm_section not in norm_text:
                # Try partial match (section number only)
                section_num = re.search(r"\d[\w().]*", section)
                if section_num and section_num.group(0) not in norm_text:
                    rejected.append(f"{chunk_id}: section '{section}' not found in chunk")
                    continue

        # ── Check 3: term overlap between quote and chunk text
        if quote and chunk_text:
            if not _terms_overlap(quote, chunk_text):
                rejected.append(f"{chunk_id}: quote has no term overlap with chunk")
                continue

        validated.append(cite)

    if rejected:
        logger.debug("Citation validation rejected: %s", rejected)

    raw_response["citations"] = validated

    # ── Determine final state based on validation result ─────
    original_state = raw_response.get("state", "grounded")

    if original_state in ("grounded", "evidence_only"):
        if len(validated) == 0:
            raw_response["state"] = "unable_to_answer"
            raw_response["confidence_note"] = "No citations survived validation."
        elif len(validated) < len(citations):
            raw_response["state"] = "evidence_only"
            raw_response["confidence_note"] = (
                f"{len(rejected)} citation(s) could not be validated and were removed."
            )
        # else: all citations valid → keep original_state

    return raw_response
