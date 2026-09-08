"""
core/context_processors.py
Site-wide context available in every template.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from django.http import HttpRequest


def site_context(request: "HttpRequest") -> dict:
    """
    Inject into every template:
      - LANGUAGES            list of (code, label) tuples
      - LANGUAGE_CODE        current active language code
      - active_corpus_version string or None
      - DEMO_MODE            bool — true when RAG is stubbed
    """
    # Active corpus version (lazy import to avoid circular)
    active_corpus_version: str | None = None
    try:
        from corpus.models import CorpusVersion

        cv = CorpusVersion.objects.filter(status="active").first()
        active_corpus_version = cv.version if cv else None
    except Exception:
        pass

    language_code = request.LANGUAGE_CODE if hasattr(request, "LANGUAGE_CODE") else "en"

    return {
        "LANGUAGES": settings.LANGUAGES,
        "LANGUAGE_CODE": language_code,
        "active_corpus_version": active_corpus_version,
        "DEMO_MODE": getattr(settings, "DEMO_MODE", True),
        "debug": settings.DEBUG,
    }
