"""
build_corpus_version — Ingest legal source documents into a Chroma vector index.

Pipeline: PDF/TXT → text extraction → section-aware chunking → bge-m3 embeddings
→ Chroma upsert → CorpusVersion (status='building') + SourceManifest rows.

Usage:
    python manage.py build_corpus_version 1.0
    python manage.py build_corpus_version 1.0 --sources data/raw --manifests data/manifests
    python manage.py build_corpus_version 1.0 --force

Requires: pypdf (or pdfminer.six), sentence-transformers, chromadb, PyYAML.
After building:
    python manage.py validate_corpus_version 1.0
    python manage.py activate_corpus_version 1.0
"""
from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from corpus.ingestion import IngestionError, build_corpus
from corpus.models import CorpusVersion


class Command(BaseCommand):
    help = "Ingest legal source documents (PDF/TXT) into a Chroma vector index."

    def add_arguments(self, parser):
        parser.add_argument("version", help="Corpus version string, e.g. '1.0'.")
        parser.add_argument(
            "--sources",
            default="data/raw",
            help="Directory containing source PDF/TXT files (default: data/raw).",
        )
        parser.add_argument(
            "--manifests",
            default="data/manifests",
            help="Directory containing *.yaml source manifests (default: data/manifests).",
        )
        parser.add_argument("--max-chars", type=int, default=1200, dest="max_chars")
        parser.add_argument("--overlap-chars", type=int, default=150, dest="overlap_chars")
        parser.add_argument("--batch-size", type=int, default=16, dest="batch_size")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Rebuild even if this version already exists (overwrites the collection).",
        )

    def handle(self, *args, **options):
        version = options["version"]
        sources_dir = Path(options["sources"]).resolve()
        manifests_dir = Path(options["manifests"]).resolve()

        existing = CorpusVersion.objects.filter(version=version).first()
        if existing and not options["force"]:
            raise CommandError(
                f"CorpusVersion '{version}' already exists (status={existing.status}). "
                "Use --force to rebuild, or choose a new version string."
            )

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Building corpus v{version}"
        ))
        self.stdout.write(f"  sources:   {sources_dir}")
        self.stdout.write(f"  manifests: {manifests_dir}")
        self.stdout.write(f"  embed:     {settings.EMBED_MODEL} ({settings.EMBED_DEVICE})")
        self.stdout.write(f"  chroma:    {settings.CHROMA_PERSIST_DIR}")
        self.stdout.write("")

        try:
            result = build_corpus(
                version=version,
                sources_dir=sources_dir,
                manifests_dir=manifests_dir,
                max_chars=options["max_chars"],
                overlap_chars=options["overlap_chars"],
                batch_size=options["batch_size"],
                on_progress=lambda m: self.stdout.write(f"  {m}"),
            )
        except IngestionError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Built v{result.version}: {result.chunks_count} chunks "
            f"from {result.sources_count} sources → collection '{result.collection}'."
        ))
        for sid, n in sorted(result.per_source.items()):
            self.stdout.write(f"    {sid}: {n} chunks")
        self.stdout.write("")
        self.stdout.write("Next:")
        self.stdout.write(f"  python manage.py validate_corpus_version {version}")
        self.stdout.write(f"  python manage.py activate_corpus_version {version}")
