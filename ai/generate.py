"""
ai/generate.py — Ollama generation with in-process concurrency control.

Concurrency model (MVP):
  - threading.BoundedSemaphore(1): at most 1 concurrent generation
  - At most 2 waiters; additional requests return state="busy"
  - 5-second wait timeout; returns state="busy" on timeout
  - Cancellation: mark request_id in _cancelled set; generation discards output
  - Process restart discards waiting requests (transient state)
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from typing import Any

logger = logging.getLogger("ai")

# ── Concurrency primitives ────────────────────────────────────
_semaphore = threading.BoundedSemaphore(1)
_waiter_count = 0
_waiter_lock = threading.Lock()
_MAX_WAITERS = 2
_SEMAPHORE_WAIT_TIMEOUT = 5.0  # seconds

# ── Cancellation set ─────────────────────────────────────────
_cancelled: set[str] = set()
_cancelled_lock = threading.Lock()


def cancel_request(request_id: str) -> None:
    """Mark *request_id* as cancelled. Generation will discard output on next check."""
    with _cancelled_lock:
        _cancelled.add(request_id)
    logger.debug("cancel_request: marked %s cancelled", request_id)


def _is_cancelled(request_id: str) -> bool:
    with _cancelled_lock:
        return request_id in _cancelled


def _cleanup_cancelled(request_id: str) -> None:
    with _cancelled_lock:
        _cancelled.discard(request_id)


# ── System prompt template ────────────────────────────────────
_SYSTEM_PROMPT = """\
You are IP-SAKTI Sahayak, an information assistant for Ayurveda-related intellectual property and regulatory topics.

RULES (follow strictly):
1. Answer ONLY from the provided EVIDENCE CHUNKS below.
2. Cite every factual claim with {{"chunk_id": "...", "source_id": "...", "section": "...", "quote": "..."}}.
3. If evidence is insufficient, return state "unable_to_answer" with a brief reason.
4. Never fabricate statutes, section numbers, dates, or treaty articles.
5. End every answer with: "This is general information, not legal advice."
6. Do not include any text outside the JSON response.

JURISDICTION: {jurisdiction}

EVIDENCE CHUNKS:
{evidence_chunks}

QUESTION: {question}

Return JSON only — no preamble, no markdown:
{{
  "state": "grounded" | "evidence_only" | "unable_to_answer" | "out_of_scope" | "conflict",
  "answer": "...",
  "citations": [
    {{"chunk_id": "...", "source_id": "...", "section": "...", "quote": "...", "title": "..."}}
  ],
  "confidence_note": "..."
}}
"""


def build_prompt(question: str, jurisdiction: str, chunks: list[dict[str, Any]]) -> str:
    """Format the system prompt with evidence chunks (capped for CPU latency)."""
    trimmed = chunks[:4]
    parts: list[str] = []
    for c in trimmed:
        text = (c.get("text") or "").strip()
        if len(text) > 450:
            text = text[:450] + "…"
        parts.append(
            f"[{c['chunk_id']}] {c.get('source_id', '')} § {c.get('section_ref', '')}\n"
            f"Effective from: {c.get('effective_from', 'unknown')}\n"
            f"{text}"
        )
    evidence_text = "\n\n".join(parts)
    return _SYSTEM_PROMPT.format(
        jurisdiction=jurisdiction,
        evidence_chunks=evidence_text or "(no chunks retrieved)",
        question=question,
    )


def _call_ollama(prompt: str, model: str, base_url: str, timeout: float) -> str:
    """
    Make a synchronous call to the Ollama /api/chat endpoint.
    Returns the raw assistant message text.
    """
    import urllib.request

    from django.conf import settings

    # Cap tokens so CPU Qwen finishes before the HTTP timeout on Railway.
    num_predict = int(getattr(settings, "OLLAMA_NUM_PREDICT", 256) or 256)
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": max(64, min(num_predict, 512)),
        },
    }).encode()

    req = urllib.request.Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode())
    return body["message"]["content"]


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Extract JSON from raw model output (handles markdown fences)."""
    # Strip ```json ... ``` fences if present
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        # Attempt partial extraction between first { and last }
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
        return {
            "state": "unable_to_answer",
            "answer": "The model returned an unparseable response. Please retry.",
            "citations": [],
            "confidence_note": "Parse error",
        }


def generate(
    prompt: str,
    request_id: str,
    model: str = "qwen2.5:3b-instruct-q4_K_M",
    base_url: str = "http://127.0.0.1:11434",
    timeout: float = 45.0,
) -> dict[str, Any]:
    """
    Acquire semaphore → call Ollama → parse JSON response → release → return.

    Returns a dict with keys: state, answer, citations, confidence_note.
    Returns {"state": "busy"} if semaphore cannot be acquired within timeout.
    Returns {"state": "cancelled"} if request was cancelled while waiting.
    """
    global _waiter_count

    # ── Check waiter limit ────────────────────────────────────
    with _waiter_lock:
        if _waiter_count >= _MAX_WAITERS:
            return {"state": "busy", "answer": "", "citations": [], "confidence_note": ""}
        _waiter_count += 1

    try:
        # ── Acquire semaphore (5s timeout) ────────────────────
        acquired = _semaphore.acquire(timeout=_SEMAPHORE_WAIT_TIMEOUT)
        if not acquired:
            return {"state": "busy", "answer": "", "citations": [], "confidence_note": ""}

        try:
            # ── Check cancellation ────────────────────────────
            if _is_cancelled(request_id):
                _cleanup_cancelled(request_id)
                return {"state": "cancelled", "answer": "", "citations": [], "confidence_note": ""}

            # ── Call Ollama ───────────────────────────────────
            start = time.monotonic()
            raw = _call_ollama(prompt, model, base_url, timeout)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info("Ollama responded in %d ms", elapsed_ms)

            # ── Check cancellation again after generation ─────
            if _is_cancelled(request_id):
                _cleanup_cancelled(request_id)
                return {"state": "cancelled", "answer": "", "citations": [], "confidence_note": ""}

            result = _parse_json_response(raw)
            result["_latency_ms"] = elapsed_ms
            return result

        finally:
            _semaphore.release()

    except TimeoutError as exc:
        logger.error("Ollama generate timed out: %s", exc)
        return {
            "state": "timeout",
            "answer": "",
            "citations": [],
            "confidence_note": "Model generate timed out — caller may fall back to evidence_only.",
        }
    except OSError as exc:
        # urllib raises URLError (OSError subclass); socket timeouts often surface here.
        err_name = type(exc).__name__
        err_low = str(exc).lower()
        if "timed out" in err_low or "timeout" in err_low or err_name == "TimeoutError":
            logger.error("Ollama generate timed out (OSError): %s", exc)
            return {
                "state": "timeout",
                "answer": "",
                "citations": [],
                "confidence_note": "Model generate timed out — caller may fall back to evidence_only.",
            }
        logger.error("Ollama connection error: %s", exc)
        return {
            "state": "unavailable",
            "answer": "Could not connect to the language model. Please check that Ollama is running.",
            "citations": [],
            "confidence_note": "",
        }
    except Exception as exc:
        err_low = str(exc).lower()
        if "timed out" in err_low or "timeout" in err_low:
            logger.error("Ollama generate timed out: %s", exc)
            return {
                "state": "timeout",
                "answer": "",
                "citations": [],
                "confidence_note": "Model generate timed out — caller may fall back to evidence_only.",
            }
        logger.exception("Ollama unexpected error: %s", exc)
        return {
            "state": "unavailable",
            "answer": "An unexpected error occurred while generating the response.",
            "citations": [],
            "confidence_note": "",
        }
    finally:
        with _waiter_lock:
            _waiter_count -= 1
