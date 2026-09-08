"""
STUB management command for corpus ingestion.

Full implementation requires:
  - pypdf               (PDF text extraction)
  - sentence-transformers  (embedding model — BAAI/bge-m3 by default)
  - chromadb            (vector store)

Usage:
  python manage.py build_corpus_version --version 1.0
  python manage.py build_corpus_version --version 1.0 --sources path/to/pdfs/
"""
import os

from django.core.management.base import BaseCommand, CommandError

from corpus.models import CorpusVersion


class Command(BaseCommand):
    help = (
        "STUB: Create a CorpusVersion record and print ingestion instructions. "
        "Real PDF ingestion requires pypdf, sentence-transformers, and chromadb."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--version",
            required=True,
            help="Version string for this corpus build (e.g. '1.0').",
        )
        parser.add_argument(
            "--sources",
            default="data/corpus/",
            help="Path to directory containing source PDFs (default: data/corpus/).",
        )

    def handle(self, *args, **options):
        version_str = options["version"]
        sources_dir = options["sources"]

        if CorpusVersion.objects.filter(version=version_str).exists():
            raise CommandError(
                f"CorpusVersion '{version_str}' already exists. "
                "Choose a different version string or delete the existing record."
            )

        sources_abs = os.path.abspath(sources_dir)
        self.stdout.write(f"[STUB] Would ingest PDFs from: {sources_abs}")

        collection_name = f"ip_sakti_v{version_str.replace('.', '_')}"
        self.stdout.write(
            f"[STUB] Creating CorpusVersion record: version='{version_str}', "
            f"collection='{collection_name}', status='building' …"
        )

        cv = CorpusVersion.objects.create(
            version=version_str,
            status="building",
            chroma_collection=collection_name,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"CorpusVersion '{version_str}' (pk={cv.pk}) created with status='building'."
            )
        )
        self.stdout.write("")
        self.stdout.write("Next steps for full implementation:")
        self.stdout.write("  1. pip install pypdf sentence-transformers chromadb")
        self.stdout.write(f"  2. Place source PDFs in:  {sources_abs}")
        self.stdout.write("  3. Implement the ingestion pipeline (chunk, embed, upsert to Chroma).")
        self.stdout.write(
            f"  4. After ingestion, validate: python manage.py validate_corpus_version --version {version_str}"
        )
        self.stdout.write(
            f"  5. After validation, activate: python manage.py activate_corpus_version --version {version_str}"
        )
