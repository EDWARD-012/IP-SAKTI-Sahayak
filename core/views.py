"""
core/views.py — Core page views.

Provides home, language switching, health, and static informational pages.
All views are function-based for simplicity and testability.
"""
from __future__ import annotations

import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import translation
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger("ip_sakti")


def home(request: HttpRequest) -> HttpResponse:
    """Landing page — renders core/home.html."""
    return render(request, "core/home.html")


@require_POST
def set_language(request: HttpRequest) -> HttpResponse:
    """
    POST /language/set/ — store preferred language in session and cookie,
    then redirect back to the referring page (or home).

    Expects POST field: ``language`` (BCP-47 code, e.g. "hi", "ta").
    """
    from django.contrib import messages

    # Django 5.x: LANGUAGE_SESSION_KEY lives on settings (default "django_language"),
    # not django.utils.translation.
    session_key = getattr(settings, "LANGUAGE_SESSION_KEY", "django_language")

    language = request.POST.get("language", "en").strip()

    valid_codes = {code for code, _label in settings.LANGUAGES}
    if language not in valid_codes:
        language = settings.LANGUAGE_CODE

    request.session[session_key] = language
    request.session.modified = True
    translation.activate(language)

    if language not in ("en", "hi"):
        messages.warning(
            request,
            "Language preference saved, but full UI translation is not available yet "
            f"for this Pilot language ({language}). The interface stays in English — "
            "see GAPS.md.",
        )
    elif language == "hi":
        messages.success(
            request,
            "भाषा हिंदी पर सेट हो गई। मुख्य नेविगेशन और होम हीरो हिंदी में दिखेंगे।",
        )

    referer = request.META.get("HTTP_REFERER") or "/"
    response = redirect(referer)
    response.set_cookie(
        key=settings.LANGUAGE_COOKIE_NAME,
        value=language,
        max_age=getattr(settings, "LANGUAGE_COOKIE_AGE", 60 * 60 * 24 * 365),
        path=getattr(settings, "LANGUAGE_COOKIE_PATH", "/"),
        domain=getattr(settings, "LANGUAGE_COOKIE_DOMAIN", None),
        secure=bool(getattr(settings, "LANGUAGE_COOKIE_SECURE", False)),
        httponly=bool(getattr(settings, "LANGUAGE_COOKIE_HTTPONLY", False)),
        samesite=getattr(settings, "LANGUAGE_COOKIE_SAMESITE", "Lax") or "Lax",
    )
    return response


def _ollama_reachable() -> bool:
    """Probe Ollama /api/tags (allow tunnel RTT to laptop)."""
    base = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    url = f"{base}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        # 2s is fine for localhost; tunneled Railway→laptop needs more headroom.
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.debug("Ollama health probe failed: %s", exc)
        return False


def _active_corpus_version() -> str:
    try:
        from corpus.models import CorpusVersion
        cv = CorpusVersion.objects.filter(status="active").first()
        return cv.version if cv else "none"
    except Exception:
        return "none"


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    """GET /health/ — lightweight readiness JSON for SIH laptop demo."""
    payload = {
        "status": "ok",
        "demo_mode": bool(getattr(settings, "DEMO_MODE", True)),
        "ollama_reachable": _ollama_reachable(),
        "active_corpus_version": _active_corpus_version(),
        "debug": bool(settings.DEBUG),
    }
    return JsonResponse(payload)


def screen_reader(request: HttpRequest) -> HttpResponse:
    """Screen-reader and accessibility guide."""
    return render(request, "core/screen_reader.html")


def privacy(request: HttpRequest) -> HttpResponse:
    """Privacy notice (DPDP-aligned)."""
    return render(request, "core/privacy.html")


def terms(request: HttpRequest) -> HttpResponse:
    """Terms of use."""
    return render(request, "core/terms.html")


def help_page(request: HttpRequest) -> HttpResponse:
    """Help and FAQ page."""
    return render(request, "core/help.html")


def contact(request: HttpRequest) -> HttpResponse:
    """Contact information."""
    return render(request, "core/contact.html")
