"""
corpus/views.py — Corpus information views.

Shows the active corpus version metadata and full source manifest.
"""
from __future__ import annotations

import logging

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from corpus.models import CorpusVersion, SourceManifest

logger = logging.getLogger("ip_sakti")


def about_corpus(request: HttpRequest) -> HttpResponse:
    """
    GET /corpus/about/ — active corpus version details and high-level source summary.
    """
    active_version: CorpusVersion | None = (
        CorpusVersion.objects.filter(status="active").first()
    )
    sources: list[SourceManifest] = []
    if active_version is not None:
        sources = list(active_version.sources.order_by("source_id"))

    return render(request, "corpus/about.html", {
        "corpus_version": active_version,
        "sources": sources,
    })


def sources_list(request: HttpRequest) -> HttpResponse:
    """
    GET /corpus/sources/ — full source manifest table for the active corpus version.
    Provides provenance and reuse-basis information for all indexed documents.
    """
    active_version: CorpusVersion | None = (
        CorpusVersion.objects.filter(status="active").first()
    )
    if active_version is not None:
        sources = active_version.sources.order_by("source_id")
    else:
        sources = SourceManifest.objects.none()

    return render(request, "corpus/sources.html", {
        "sources": sources,
        "corpus_version": active_version,
    })
