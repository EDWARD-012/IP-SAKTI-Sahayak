"""
corpus/views.py — Corpus information views.

Shows the active corpus version metadata and full source manifest.
"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from corpus.models import CorpusVersion, SourceManifest

logger = logging.getLogger("ip_sakti")

# Fallback labels when DB rows exist without rich fields.
_P0_IDS = {
    "patents-act-1970",
    "gi-act-1999",
    "biological-diversity-act-2002",
    "drugs-cosmetics-act-1940",
}


def _source_row(src: SourceManifest) -> dict[str, Any]:
    from corpus.i18n_labels import (
        bilingual_subtitle,
        localize_authority,
        localize_ip_types,
        localize_title,
    )

    english_title = src.title or src.source_id
    return {
        "name": localize_title(src.source_id, english_title),
        "name_en": bilingual_subtitle(src.source_id, english_title),
        "authority": localize_authority(src.authority or ""),
        "ip_types": localize_ip_types(src.ip_types),
        "is_active": True,
        "source_id": src.source_id,
        "tier": "P0" if src.source_id in _P0_IDS else "P1",
    }


def about_corpus(request: HttpRequest) -> HttpResponse:
    """
    GET /corpus/about/ — active corpus version details and high-level source summary.
    """
    active_version: CorpusVersion | None = (
        CorpusVersion.objects.filter(status="active").first()
    )
    sources: list[SourceManifest] = []
    if active_version is not None:
        sources = list(
            SourceManifest.objects.filter(corpus_version=active_version).order_by("source_id")
        )
        if not sources:
            # Older rows may not be FK-linked yet — still show global manifests.
            sources = list(SourceManifest.objects.order_by("source_id")[:40])

    rows = [_source_row(s) for s in sources]
    p0_sources = [r for r in rows if r["tier"] == "P0"]
    p1_sources = [r for r in rows if r["tier"] == "P1"]

    corpus_stats = {
        "chunks_count": getattr(active_version, "chunks_count", None) if active_version else None,
        "source_count": len(sources) or getattr(active_version, "sources_count", None),
        "last_updated": (
            (active_version.activated_at or active_version.created_at).date().isoformat()
            if active_version and (active_version.activated_at or active_version.created_at)
            else None
        ),
        "notes": getattr(active_version, "notes", "") if active_version else "",
        "chroma_collection": getattr(active_version, "chroma_collection", "") if active_version else "",
    }

    return render(request, "corpus/about.html", {
        "corpus_version": active_version,
        "active_corpus_version": active_version.version if active_version else None,
        "sources": sources,
        "corpus_stats": corpus_stats,
        "p0_sources": p0_sources,
        "p1_sources": p1_sources,
        "demo_mode": bool(getattr(settings, "DEMO_MODE", True)),
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
        sources = SourceManifest.objects.filter(corpus_version=active_version).order_by("source_id")
        if not sources.exists():
            sources = SourceManifest.objects.order_by("source_id")
    else:
        sources = SourceManifest.objects.none()

    return render(request, "corpus/sources.html", {
        "sources": sources,
        "corpus_version": active_version,
    })
