"""
Ensure active CorpusVersion + SourceManifest rows exist (cloud / fresh DB).

Activates 0.3-demo / ip_sakti_v0_3-demo so Railway can use an uploaded Chroma index.
Does not build Chroma vectors — upload chroma_db to the volume separately.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date

# Must match local build_corpus_version naming for the jury demo index.
_CLOUD_RAG_VERSION = "0.3-demo"
_CLOUD_RAG_COLLECTION = "ip_sakti_v0_3-demo"


def _probe_chroma_count(collection_name: str) -> int | None:
    """Best-effort chunk count from CHROMA_PERSIST_DIR; None if unavailable."""
    try:
        import chromadb

        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        col = client.get_collection(collection_name)
        return int(col.count())
    except Exception:
        return None


class Command(BaseCommand):
    help = "Seed/activate 0.3-demo corpus metadata for cloud RAG (+ manifests)."

    def handle(self, *args, **options):
        from corpus.models import CorpusVersion, SourceManifest

        active = CorpusVersion.objects.filter(status="active").first()

        # Retire legacy metadata-only cloud stub if it is still active.
        if active and active.version == "0.3-cloud":
            active.status = "retired"
            active.save(update_fields=["status"])
            self.stdout.write(self.style.WARNING("Retired legacy active corpus: 0.3-cloud"))
            active = None

        if active and active.version != _CLOUD_RAG_VERSION:
            # Keep a non-demo active version if operators set one deliberately,
            # but ensure chroma_collection is coherent when it is 0.3-demo elsewhere.
            self.stdout.write(
                self.style.SUCCESS(f"Active corpus already set: {active.version}")
            )
        elif active and active.version == _CLOUD_RAG_VERSION:
            if active.chroma_collection != _CLOUD_RAG_COLLECTION:
                active.chroma_collection = _CLOUD_RAG_COLLECTION
                active.save(update_fields=["chroma_collection"])
            if active.notes and "Cloud metadata stub" in active.notes:
                active.notes = ""
                active.save(update_fields=["notes"])
            self.stdout.write(self.style.SUCCESS(f"Active corpus already set: {active.version}"))
        else:
            demo = CorpusVersion.objects.filter(version=_CLOUD_RAG_VERSION).first()
            if demo:
                CorpusVersion.objects.filter(status="active").exclude(
                    pk=demo.pk
                ).update(status="retired")
                demo.status = "active"
                demo.chroma_collection = _CLOUD_RAG_COLLECTION
                demo.activated_at = timezone.now()
                if demo.notes and "Cloud metadata stub" in demo.notes:
                    demo.notes = ""
                demo.save()
                active = demo
                self.stdout.write(
                    self.style.SUCCESS(f"Re-activated corpus: {active.version}")
                )
            else:
                CorpusVersion.objects.filter(status="active").update(status="retired")
                active = CorpusVersion.objects.create(
                    version=_CLOUD_RAG_VERSION,
                    status="active",
                    chroma_collection=_CLOUD_RAG_COLLECTION,
                    sources_count=0,
                    chunks_count=0,
                    notes="",
                    activated_at=timezone.now(),
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Seeded active corpus: {active.version}")
                )

        assert active is not None

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
                "effective_from": parse_date(str(data.get("effective_from") or "")),
                "effective_status": data.get("effective_status") or "current",
                "reuse_basis": data.get("reuse_basis") or "public-statute",
                "retrieved_at": parse_date(str(data.get("retrieved_at") or "")),
                "notes": (data.get("notes") or "").strip(),
                "corpus_version": active,
            }
            _obj, was_created = SourceManifest.objects.update_or_create(
                source_id=source_id,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                linked += 1

        count = SourceManifest.objects.filter(corpus_version=active).count()
        update_fields = ["sources_count"]
        active.sources_count = count

        probed = _probe_chroma_count(active.chroma_collection)
        if probed is not None:
            active.chunks_count = probed
            update_fields.append("chunks_count")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Chroma probe: {active.chroma_collection} → {probed} chunks"
                )
            )
        elif not active.chunks_count:
            active.chunks_count = 0
            update_fields.append("chunks_count")

        active.save(update_fields=update_fields)

        self.stdout.write(
            self.style.SUCCESS(
                f"Sources ready: {count} linked to {active.version} "
                f"(created={created}, updated={linked}, "
                f"collection={active.chroma_collection})"
            )
        )
