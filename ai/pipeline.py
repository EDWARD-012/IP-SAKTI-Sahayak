"""
ai/pipeline.py — Main RAG pipeline coordinator.

Entry point: process_question(question, jurisdiction, language_code, corpus_version)

Flow (DEMO_MODE=False):
  1. Safety check (ai.safety.check_input)
  2. Translate query to English if needed (ai.translate)
  3. Retrieve relevant chunks (ai.retrieve)
  4. Evidence threshold check (< 2 chunks → unable_to_answer)
  5. Build prompt and call Ollama (ai.generate)
  6. Validate citations (ai.citations)
  7. Output safety check (ai.safety.check_output)
  8. Return PipelineResult

Flow (DEMO_MODE=True):
  - Skip steps 2-7, return rich placeholder PipelineResult immediately.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings

logger = logging.getLogger("ai")


@dataclass
class PipelineResult:
    """Structured result from process_question."""
    request_id: str
    state: str          # grounded/evidence_only/unable_to_answer/out_of_scope/conflict/busy/unavailable/demo/cancelled
    answer: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    confidence_note: str = ""
    latency_ms: int = 0
    corpus_version: str = "none"
    demo_mode: bool = False
    error: str = ""


# ── Demo mode placeholder ─────────────────────────────────────
_DEMO_ANSWER = """\
This is a demonstration response from IP-SAKTI Sahayak.

What IP-SAKTI Sahayak does —
In live mode, this system retrieves relevant sections from verified Indian statutes (Patents Act 1970, \
Geographical Indications Act 1999, Biological Diversity Act 2002, Drugs & Cosmetics Act 1940, etc.) \
and generates source-cited answers using the local Qwen2.5-7B model via Ollama.

How to enable live responses —
1. Install Ollama: winget install Ollama.Ollama (Windows) or https://ollama.ai
2. Pull the model: ollama pull qwen2.5:7b-instruct-q4_K_M
3. Download and index the legal corpus (see QUICKSTART.md, section 5)
4. Set DEMO_MODE=False in your .env file

Example of what a live answer looks like —
For a question about patenting an Ayurvedic formulation based on classical texts, \
the system would cite Section 3(p) of the Patents Act 1970 which excludes inventions \
that are traditional knowledge or aggregation of known properties of traditionally known components.

This is general information, not legal advice.
"""

_DEMO_CITATIONS = [
    {
        "chunk_id":       "demo-patents-act-3p",
        "source_id":      "patents-act-1970",
        "title":          "The Patents Act, 1970",
        "section":        "Section 3(p)",
        "effective_from": "1970-09-19",
        "quote": (
            "An invention which, in effect, is traditional knowledge or which is an aggregation or "
            "duplication of known properties of traditionally known component or components."
        ),
    },
    {
        "chunk_id":       "demo-gi-act-s11",
        "source_id":      "gi-act-1999",
        "title":          "The Geographical Indications of Goods (Registration and Protection) Act, 1999",
        "section":        "Section 11",
        "effective_from": "2003-09-15",
        "quote": (
            "Any association of persons or producers or any organisation or authority established by "
            "or under any law for the time being in force representing the interest of the producers "
            "of the concerned goods... may apply in writing to the Registrar for the registration of "
            "the geographical indication."
        ),
    },
]


def _demo_result(corpus_version: str) -> PipelineResult:
    """Return a rich placeholder result for demo mode."""
    return PipelineResult(
        request_id=str(uuid.uuid4()),
        state="demo",
        answer=_DEMO_ANSWER,
        citations=_DEMO_CITATIONS,
        confidence_note="Demo mode — connect Ollama and index corpus for live responses.",
        latency_ms=42,
        corpus_version=corpus_version,
        demo_mode=True,
    )


# ── Live pipeline ─────────────────────────────────────────────

def process_question(
    question: str,
    jurisdiction: str = "IN",
    language_code: str = "en",
    corpus_version: str = "none",
) -> PipelineResult:
    """
    Run the full RAG pipeline for a given question.

    Parameters:
        question        – user's question text
        jurisdiction    – "IN" | "INT" | "BOTH"
        language_code   – BCP-47 code of the UI language (e.g. "en", "hi")
        corpus_version  – active corpus version string

    Returns:
        PipelineResult
    """
    if getattr(settings, "DEMO_MODE", True):
        return _demo_result(corpus_version)

    start = time.monotonic()
    request_id = str(uuid.uuid4())

    # ── Import sub-modules ────────────────────────────────────
    from ai import citations as ai_citations
    from ai import generate as ai_generate
    from ai import retrieve as ai_retrieve
    from ai import safety as ai_safety
    from ai import translate as ai_translate

    # ── 1. Input safety ───────────────────────────────────────
    safe, reason = ai_safety.check_input(question)
    if not safe:
        return PipelineResult(
            request_id=request_id,
            state="out_of_scope",
            answer=f"This question cannot be processed: {reason}",
            corpus_version=corpus_version,
            latency_ms=int((time.monotonic() - start) * 1000),
        )

    # ── 2. Translate query to English (retrieval pivot) ───────
    query_for_retrieval = question
    if language_code != "en":
        translated = ai_translate.translate(question, source_lang=language_code, target_lang="en")
        if translated and translated != question:
            query_for_retrieval = translated
            logger.debug("Query translated %s→en for retrieval.", language_code)

    # ── 3. Retrieve relevant chunks ───────────────────────────
    chunks = ai_retrieve.retrieve(query_for_retrieval, jurisdiction=jurisdiction, k=8)

    # ── 4. Evidence threshold ─────────────────────────────────
    if len(chunks) < 2:
        return PipelineResult(
            request_id=request_id,
            state="unable_to_answer",
            answer=(
                "The active corpus does not have enough relevant text to answer this question "
                "reliably. Please check the corpus coverage or rephrase your question."
            ),
            corpus_version=corpus_version,
            latency_ms=int((time.monotonic() - start) * 1000),
        )

    # ── 5. Build prompt and generate ─────────────────────────
    prompt = ai_generate.build_prompt(
        question=question,
        jurisdiction=jurisdiction,
        chunks=chunks,
    )
    raw = ai_generate.generate(
        prompt=prompt,
        request_id=request_id,
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        timeout=settings.OLLAMA_TIMEOUT,
    )

    if raw.get("state") in ("busy", "unavailable", "cancelled"):
        return PipelineResult(
            request_id=request_id,
            state=raw["state"],
            answer=raw.get("answer", ""),
            corpus_version=corpus_version,
            latency_ms=int((time.monotonic() - start) * 1000),
        )

    # ── 6. Validate citations ─────────────────────────────────
    raw = ai_citations.validate(raw, chunks)

    # ── 7. Output safety ──────────────────────────────────────
    answer_text = raw.get("answer", "")
    output_safe, output_reason = ai_safety.check_output(answer_text)
    if not output_safe:
        logger.warning("Output safety check failed: %s", output_reason)
        raw["state"] = "unable_to_answer"
        raw["answer"] = "The response could not be verified. Please rephrase and try again."
        raw["citations"] = []

    latency_ms = raw.pop("_latency_ms", None) or int((time.monotonic() - start) * 1000)

    return PipelineResult(
        request_id=request_id,
        state=raw.get("state", "unable_to_answer"),
        answer=raw.get("answer", ""),
        citations=raw.get("citations", []),
        confidence_note=raw.get("confidence_note", ""),
        latency_ms=latency_ms,
        corpus_version=corpus_version,
        demo_mode=False,
    )
