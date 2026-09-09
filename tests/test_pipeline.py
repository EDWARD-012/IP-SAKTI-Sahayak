"""Mocked live-path RAG pipeline edge cases (no HF / Ollama required)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from ai.pipeline import process_question


def _chunk(cid: str, text: str = "Section 3(p) traditional knowledge exclusion.") -> dict:
    return {
        "chunk_id": cid,
        "source_id": "patents-act-1970",
        "section_ref": "Section 3(p)",
        "text": text,
        "title": "The Patents Act, 1970",
        "effective_from": "1970-09-19",
        "score": 0.9,
    }


@pytest.mark.django_db
def test_demo_mode_stub(settings):
    settings.DEMO_MODE = True
    result = process_question("Explain Section 3(p)", jurisdiction="IN")
    assert result.demo_mode is True
    assert "demonstration" in result.answer.lower() or result.state == "demo"


@pytest.mark.django_db
def test_live_unable_when_too_few_chunks(settings):
    settings.DEMO_MODE = False
    with (
        patch("ai.safety.check_input", return_value=(True, "")),
        patch("ai.retrieve.retrieve", return_value=[_chunk("only-one")]),
        patch("ai.translate.translate", return_value=None),
    ):
        result = process_question(
            "What is Section 3(p) of the Patents Act?",
            jurisdiction="IN",
            language_code="en",
            corpus_version="0.3-demo",
        )
    assert result.state == "unable_to_answer"
    assert result.demo_mode is False


@pytest.mark.django_db
def test_live_empty_retrieve_unable(settings):
    settings.DEMO_MODE = False
    with (
        patch("ai.safety.check_input", return_value=(True, "")),
        patch("ai.retrieve.retrieve", return_value=[]),
        patch("ai.translate.translate", return_value=None),
    ):
        result = process_question(
            "What is TKDL used for in patent examination?",
            jurisdiction="IN",
            corpus_version="0.3-demo",
        )
    assert result.state == "unable_to_answer"


@pytest.mark.django_db
def test_live_out_of_scope_from_safety(settings):
    settings.DEMO_MODE = False
    with patch("ai.safety.check_input", return_value=(False, "foreign_law_probe")):
        result = process_question(
            "How do I file a USPTO patent for my crypto token?",
            jurisdiction="IN",
            corpus_version="0.3-demo",
        )
    assert result.state == "out_of_scope"


@pytest.mark.django_db
def test_live_busy_from_generate(settings):
    settings.DEMO_MODE = False
    chunks = [_chunk("c1"), _chunk("c2", "Section 3(p) known properties.")]
    with (
        patch("ai.safety.check_input", return_value=(True, "")),
        patch("ai.retrieve.retrieve", return_value=chunks),
        patch("ai.translate.translate", return_value=None),
        patch(
            "ai.generate.generate",
            return_value={"state": "busy", "answer": "", "citations": []},
        ),
        patch("ai.generate.build_prompt", return_value="prompt"),
    ):
        result = process_question(
            "Explain Section 3(p) for classical Ayurveda formulations.",
            jurisdiction="IN",
            corpus_version="0.3-demo",
        )
    assert result.state == "busy"


@pytest.mark.django_db
def test_live_timeout_becomes_evidence_only(settings):
    settings.DEMO_MODE = False
    chunks = [_chunk("c1"), _chunk("c2", "Section 3(p) traditional knowledge.")]
    with (
        patch("ai.safety.check_input", return_value=(True, "")),
        patch("ai.retrieve.retrieve", return_value=chunks),
        patch("ai.translate.translate", return_value=None),
        patch(
            "ai.generate.generate",
            return_value={"state": "timeout", "answer": "", "citations": []},
        ),
        patch("ai.generate.build_prompt", return_value="prompt"),
    ):
        result = process_question(
            "Explain Section 3(p) traditional knowledge exclusion.",
            jurisdiction="IN",
            corpus_version="0.3-demo",
        )
    assert result.state == "evidence_only"
    assert len(result.citations) >= 1


@pytest.mark.django_db
def test_live_unavailable_from_generate(settings):
    settings.DEMO_MODE = False
    chunks = [_chunk("c1"), _chunk("c2")]
    with (
        patch("ai.safety.check_input", return_value=(True, "")),
        patch("ai.retrieve.retrieve", return_value=chunks),
        patch("ai.translate.translate", return_value=None),
        patch(
            "ai.generate.generate",
            return_value={"state": "unavailable", "answer": "down", "citations": []},
        ),
        patch("ai.generate.build_prompt", return_value="prompt"),
    ):
        result = process_question(
            "Explain Ayurveda Aahara labelling rules briefly.",
            jurisdiction="IN",
            corpus_version="0.3-demo",
        )
    assert result.state == "unavailable"


@pytest.mark.django_db
def test_citation_unknown_chunk_becomes_unable(settings):
    settings.DEMO_MODE = False
    chunks = [
        _chunk("real-1", "Section 3(p) traditional knowledge or aggregation."),
        _chunk("real-2", "Section 3(p) traditionally known components."),
    ]
    fake_gen = {
        "state": "grounded",
        "answer": "Section 3(p) excludes traditional knowledge inventions.",
        "citations": [
            {
                "chunk_id": "invented-id",
                "section": "Section 3(p)",
                "quote": "traditional knowledge",
            }
        ],
        "confidence_note": "",
    }
    with (
        patch("ai.safety.check_input", return_value=(True, "")),
        patch("ai.retrieve.retrieve", return_value=chunks),
        patch("ai.translate.translate", return_value=None),
        patch("ai.generate.generate", return_value=fake_gen),
        patch("ai.generate.build_prompt", return_value="prompt"),
        patch("ai.safety.check_output", return_value=(True, "")),
    ):
        result = process_question(
            "Explain Section 3(p) of the Patents Act 1970.",
            jurisdiction="IN",
            corpus_version="0.3-demo",
        )
    assert result.state == "unable_to_answer"
    assert result.citations == []
