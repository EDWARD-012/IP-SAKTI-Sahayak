"""
Ensure active CorpusVersion + SourceManifest rows exist (cloud / fresh DB).

Does not build Chroma vectors — metadata so About Corpus and health stay useful.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date


class Command(BaseCommand):
    help = "Seed active corpus version and source manifests from data/manifests/."

    def handle(self, *args, **options):
        from corpus.models import CorpusVersion, SourceManifest

        active = CorpusVersion.objects.filter(status="active").first()
        if not active:
            active = CorpusVersion.objects.create(
                version="0.3-cloud",
                status="active",
                chroma_collection="ip_sakti_v03_cloud",
                sources_count=0,
                chunks_count=0,
                notes="",  # UI shows translated demo hint; avoid English DB notes
                activated_at=timezone.now(),
            )
            self.stdout.write(self.style.SUCCESS(f"Seeded active corpus: {active.version}"))
        else:
            # Clear legacy English stub notes so Hindi UI stays monolingual.
            if active.notes and "Cloud metadata stub" in active.notes:
                active.notes = ""
                active.save(update_fields=["notes"])
            self.stdout.write(self.style.SUCCESS(f"Active corpus already set: {active.version}"))

        manifest_dir = Path(settings.BASE_DIR) / "data" / "manifests"
        if not manifest_dir.is_dir():
            self.stdout.write(self.style.WARNING(f"No manifests at {manifest_dir}"))
            return

        created = 0
        linked = 0
        for path in sorted(manifest_dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"Skip {path.name}: {exc}"))
                continue

            source_id = (data.get("source_id") or path.stem).strip()
            if not source_id:
                continue

            defaults = {
                "title": data.get("title") or source_id,
                "authority": data.get("authority") or "",
                "jurisdiction": data.get("jurisdiction") or "IN",
                "ip_types": data.get("ip_types") or [],
                "landing_url": data.get("landing_url") or "",
                "sha256": data.get("sha256") or "",
                "effective_from": parse_date(str(data.get("effective_from") or "")) ,
                "effective_status": data.get("effective_status") or "current",
                "reuse_basis": data.get("reuse_basis") or "public-statute",
                "retrieved_at": parse_date(str(data.get("retrieved_at") or "")),
                "notes": (data.get("notes") or "").strip(),
                "corpus_version": active,
            }
            obj, was_created = SourceManifest.objects.update_or_create(
                source_id=source_id,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                linked += 1

        count = SourceManifest.objects.filter(corpus_version=active).count()
        if active.sources_count != count:
            active.sources_count = count
            # Keep existing chunk count if already set from a real index.
            if not active.chunks_count:
                active.chunks_count = 0
            active.save(update_fields=["sources_count", "chunks_count"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Sources ready: {count} linked to {active.version} "
                f"(created={created}, updated={linked})"
            )
        )
