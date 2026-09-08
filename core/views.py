"""
core/views.py — Core page views.

Provides home, language switching, and static informational pages.
All views are function-based for simplicity and testability.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import translation
from django.views.decorators.http import require_POST

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
    language = request.POST.get("language", "en").strip()

    # Validate against configured LANGUAGES
    valid_codes = {code for code, _label in settings.LANGUAGES}
    if language not in valid_codes:
        language = settings.LANGUAGE_CODE

    # Persist in session (LocaleMiddleware reads django_language key)
    request.session["django_language"] = language

    # Activate for the current response so any rendered content uses the new lang
    translation.activate(language)

    referer = request.META.get("HTTP_REFERER") or "/"
    response = redirect(referer)

    # Also write the language cookie so LocaleMiddleware picks it up on next request
    response.set_cookie(
        key=settings.LANGUAGE_COOKIE_NAME,
        value=language,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response


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
