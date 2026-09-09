"""
chat/views.py — Chat / RAG assistant views.

Endpoints:
  GET  /assistant/         → chat_view  (renders full page)
  POST /assistant/ask/     → ask        (HTMX partial, runs RAG pipeline)
  DELETE /assistant/cancel/→ cancel     (HTMX, marks request cancelled)
  POST /assistant/session-clear/ → session_clear
  POST /assistant/feedback/ → feedback
"""
from __future__ import annotations

import hashlib
import hmac as _hmac
import logging
import time
import uuid
from typing import Any
from urllib.parse import parse_qs

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from ai import generate as ai_generate
from ai import pipeline as ai_pipeline
from chat.forms import ChatForm
from chat.models import AnswerAudit, Feedback

logger = logging.getLogger("ip_sakti")

# ── Session keys ──────────────────────────────────────────────────────────────
_HISTORY_KEY = "chat_history"
_RL_KEY = "rl_ask"
_MAX_HISTORY = 4


# ── Private helpers ───────────────────────────────────────────────────────────

def _hmac_query(query: str) -> str:
    """Return HMAC-SHA256 hex fingerprint of *query*. Never store raw text in DB."""
    return _hmac.new(
        settings.AUDIT_HMAC_KEY.encode(),
        query.encode(),
        hashlib.sha256,
    ).hexdigest()


def _get_history(request: HttpRequest) -> list[dict[str, Any]]:
    """Return the current session chat history (up to _MAX_HISTORY turns)."""
    return list(request.session.get(_HISTORY_KEY, []))


def _push_turn(request: HttpRequest, turn: dict[str, Any]) -> None:
    """Append a turn to session history, rotating oldest when > _MAX_HISTORY."""
    history = _get_history(request)
    history.append(turn)
    if len(history) > _MAX_HISTORY:
        history = history[-_MAX_HISTORY:]
    request.session[_HISTORY_KEY] = history


def _check_rate_limit(request: HttpRequest) -> bool:
    """
    Session-based sliding-window rate limiter.
    Returns True (under limit) or False (over limit, do not process).
    """
    now = time.time()
    rl: dict[str, Any] = request.session.get(_RL_KEY) or {
        "count": 0,
        "window_start": now,
    }
    # Reset window if more than 60 s have passed
    if now - rl["window_start"] >= 60.0:
        rl = {"count": 0, "window_start": now}
    if rl["count"] >= settings.RATE_LIMIT_ASK_PER_MIN:
        return False
    rl["count"] += 1
    request.session[_RL_KEY] = rl
    return True


def _active_corpus_version() -> str:
    """Return the version string of the currently active CorpusVersion, or 'none'."""
    try:
        from corpus.models import CorpusVersion  # avoid circular import at module level
        cv = CorpusVersion.objects.filter(status="active").first()
        return cv.version if cv else "none"
    except Exception as exc:
        logger.warning("Could not determine active corpus version: %s", exc)
        return "none"


# ── Views ─────────────────────────────────────────────────────────────────────

def chat_view(request: HttpRequest) -> HttpResponse:
    """
    GET /assistant/ — main chat interface.

    Template context:
      form            – ChatForm (optionally prefilled from ?q=)
      session_history – last _MAX_HISTORY turns from session
      request_id      – fresh UUID for the next question
    """
    initial = {}
    q = request.GET.get("q", "").strip()
    if q:
        initial["question"] = q

    return render(request, "chat/chat.html", {
        "form": ChatForm(initial=initial),
        "session_history": _get_history(request),
        "request_id": str(uuid.uuid4()),
        "prefilled_query": q,
    })


def ask(request: HttpRequest) -> HttpResponse:
    """
    POST /assistant/ask/ (HTMX only) — run the RAG pipeline and return a partial.

    Returns:
      chat/partials/_answer.html  — normal result
      chat/partials/_busy.html    — service busy / rate-limited
      chat/partials/_error.html   — validation or pipeline error
    """
    if request.method != "POST" or not getattr(request, "htmx", None):
        return HttpResponse(status=405)

    # ── Rate limiting ─────────────────────────────────────────────
    if not _check_rate_limit(request):
        return render(request, "chat/partials/_busy.html", {
            "reason": "rate_limited",
            "retry_after": 60,
        }, status=429)

    # ── Form validation ───────────────────────────────────────────
    form = ChatForm(request.POST)
    if not form.is_valid():
        return render(request, "chat/partials/_error.html", {
            "errors": form.errors,
            "error": "Please correct the highlighted fields.",
        }, status=422)

    question: str = form.cleaned_data["question"]
    # Template sends lowercase slugs; pipeline + audit use short codes.
    _juri_map = {"india": "IN", "international": "INT", "both": "BOTH"}
    jurisdiction: str = _juri_map.get(form.cleaned_data["jurisdiction"], "IN")
    language_code: str = request.session.get("django_language", "en")
    corpus_version: str = _active_corpus_version()

    # ── Pipeline call ─────────────────────────────────────────────
    try:
        result = ai_pipeline.process_question(
            question=question,
            jurisdiction=jurisdiction,
            language_code=language_code,
            corpus_version=corpus_version,
        )
    except Exception as exc:
        logger.exception("Pipeline unhandled error: %s", exc)
        return render(request, "chat/partials/_error.html", {
            "error": "An unexpected error occurred. Please try again shortly.",
        }, status=500)

    if result.state == "busy":
        return render(request, "chat/partials/_busy.html", {
            "reason": "service_busy",
        }, status=503)

    # ── Audit record (DPDP-aligned — HMAC only, no raw query text) ─
    try:
        AnswerAudit.objects.create(
            request_id=result.request_id,
            query_hmac=_hmac_query(question),
            query_hmac_key_id=settings.AUDIT_HMAC_KEY_ID,
            corpus_version=corpus_version,
            jurisdiction=jurisdiction,
            language_code=language_code,
            outcome=result.state,
            cited_chunk_ids=[c.get("chunk_id", "") for c in result.citations],
            latency_ms=result.latency_ms,
            demo_mode=result.demo_mode,
        )
    except Exception as exc:
        # Audit failure is non-fatal; log and continue
        logger.warning("AnswerAudit write failed: %s", exc)

    # ── Update session history ────────────────────────────────────
    # Question text is stored only in the ephemeral session (not in the
    # immutable audit DB record above) so the user can see their history
    # in the current browser session.
    _push_turn(request, {
        "request_id": result.request_id,
        "question": question,
        "answer": result.answer,
        "citations": result.citations,
        "state": result.state,
        "confidence_note": result.confidence_note,
        "demo_mode": result.demo_mode,
    })

    response = render(request, "chat/partials/_answer.html", {
        "result": result,
        "question": question,
    })
    # Refresh sidebar history without a full page reload (HTMX OOB).
    history_html = render(request, "chat/partials/_history_panel.html", {
        "session_history": _get_history(request),
    }).content.decode("utf-8")
    # Inject hx-swap-oob onto the panel root.
    history_html = history_html.replace(
        'id="chat-history-panel"',
        'id="chat-history-panel" hx-swap-oob="true"',
        1,
    )
    response.content = response.content + history_html.encode("utf-8")
    return response


@require_GET
def history_turn(request: HttpRequest, index: int) -> HttpResponse:
    """
    GET /assistant/history/<index>/ — re-open a prior turn from this session.

    Index is into the chronological session list (0 = oldest retained turn).
    """
    history = _get_history(request)
    if index < 0 or index >= len(history):
        return HttpResponseBadRequest("Unknown history item.")

    turn = history[index]
    from types import SimpleNamespace

    result = SimpleNamespace(
        request_id=turn.get("request_id") or "",
        state=turn.get("state") or "unable_to_answer",
        answer=turn.get("answer") or "",
        citations=turn.get("citations") or [],
        confidence_note=turn.get("confidence_note") or "",
        demo_mode=bool(turn.get("demo_mode")),
        latency_ms=0,
    )
    return render(request, "chat/partials/_answer.html", {
        "result": result,
        "question": turn.get("question") or "",
    })


def cancel(request: HttpRequest) -> HttpResponse:
    """
    DELETE /assistant/cancel/ (HTMX) — cancel an in-flight generation request.

    Reads request_id from query params or form-encoded body.
    Marks the AnswerAudit row cancelled and signals the generate module.
    Returns 204 No Content on success.
    """
    if request.method not in ("DELETE", "POST"):
        return HttpResponse(status=405)

    # Django does not populate request.POST for DELETE, so parse body manually
    request_id_str: str = request.GET.get("request_id", "")
    if not request_id_str:
        try:
            body = request.body.decode("utf-8", errors="replace")
            params = parse_qs(body)
            request_id_str = params.get("request_id", [""])[0]
        except Exception as exc:
            logger.debug("cancel: body parse failed: %s", exc)

    if request_id_str:
        try:
            rid = uuid.UUID(request_id_str)
            AnswerAudit.objects.filter(request_id=rid).update(cancelled=True)
            ai_generate.cancel_request(str(rid))
            logger.debug("Cancelled request %s", rid)
        except (ValueError, Exception) as exc:
            logger.warning("cancel: failed for id=%s — %s", request_id_str, exc)

    return HttpResponse(status=204)


def session_clear(request: HttpRequest) -> HttpResponse:
    """
    POST /assistant/session-clear/ — wipe chat history from the current session.

    HTMX: 204 + HX-Redirect to chat page.
    Non-HTMX: redirect to chat page.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    request.session.pop(_HISTORY_KEY, None)
    request.session.pop(_RL_KEY, None)
    request.session.modified = True

    is_htmx = bool(getattr(request, "htmx", False)) or (
        request.headers.get("HX-Request", "").lower() == "true"
    )
    if is_htmx:
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("chat:chat")
        return response
    return redirect("chat:chat")


@require_POST
def feedback(request: HttpRequest) -> HttpResponse:
    """
    POST /assistant/feedback/ (HTMX only) — record thumbs up/down on an answer.
    """
    if not getattr(request, "htmx", None):
        return HttpResponse(status=405)

    rating = (request.POST.get("rating") or "").strip().lower()
    if rating not in ("up", "down"):
        return HttpResponse("Invalid rating.", status=422)

    request_id_str = (request.POST.get("request_id") or "").strip()
    try:
        rid = uuid.UUID(request_id_str)
    except (ValueError, TypeError):
        return HttpResponse("Invalid request_id.", status=422)

    category = (request.POST.get("category") or "").strip()[:64]
    comment = (request.POST.get("comment") or "").strip()[:2000]

    Feedback.objects.create(
        request_id=rid,
        rating=rating,
        category=category,
        comment=comment,
    )
    return HttpResponse(status=204)
