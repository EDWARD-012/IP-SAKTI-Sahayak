"""
corpus/management/commands/list_corpus_versions.py

Usage:
    python manage.py list_corpus_versions
    python manage.py list_corpus_versions --status active
    python manage.py list_corpus_versions --status building,validated

Lists all CorpusVersion objects in a formatted table.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from corpus.models import CorpusVersion

_STATUS_SYMBOLS: dict[str, str] = {
    "active":    "●",
    "validated": "✓",
    "building":  "⧗",
    "retired":   "○",
    "failed":    "✗",
}

_COL_WIDTHS = {
    "version":    10,
    "status":     12,
    "collection": 28,
    "chunks":      8,
    "sources":     8,
    "created":    20,
    "activated":  20,
}


class Command(BaseCommand):
    help = "List all CorpusVersion objects with key metadata."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--status",
            default="",
            metavar="STATUS[,STATUS...]",
            help=(
                "Filter by status (comma-separated). "
                "Choices: building, validated, active, retired, failed. "
                "Omit to show all."
            ),
        )

    def handle(self, *args, **options) -> None:
        status_filter_raw: str = options.get("status", "").strip()
        status_filter = [s.strip() for s in status_filter_raw.split(",") if s.strip()]

        qs = CorpusVersion.objects.order_by("-created_at")
        if status_filter:
            qs = qs.filter(status__in=status_filter)

        versions = list(qs)

        if not versions:
            if status_filter:
                self.stdout.write(
                    self.style.WARNING(
                        f"No corpus versions found with status in {status_filter}."
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "No corpus versions exist yet. "
                        "Run corpus indexing to create one."
                    )
                )
            return

        # ── Header ─────────────────────────────────────────────────
        header = (
            f"{'  Version':<{_COL_WIDTHS['version']}}"
            f"{'Status':<{_COL_WIDTHS['status']}}"
            f"{'Collection':<{_COL_WIDTHS['collection']}}"
            f"{'Chunks':>{_COL_WIDTHS['chunks']}}"
            f"{'Sources':>{_COL_WIDTHS['sources']}}"
            f"  {'Created':<{_COL_WIDTHS['created']}}"
            f"  {'Activated':<{_COL_WIDTHS['activated']}}"
        )
        separator = "─" * len(header)

        self.stdout.write(separator)
        self.stdout.write(self.style.HTTP_INFO(header))
        self.stdout.write(separator)

        for cv in versions:
            sym = _STATUS_SYMBOLS.get(cv.status, "?")
            created_str = cv.created_at.strftime("%Y-%m-%d %H:%M") if cv.created_at else "—"
            activated_str = cv.activated_at.strftime("%Y-%m-%d %H:%M") if cv.activated_at else "—"

            row = (
                f"{sym} v{cv.version:<{_COL_WIDTHS['version'] - 3}}"
                f"{cv.status:<{_COL_WIDTHS['status']}}"
                f"{cv.chroma_collection:<{_COL_WIDTHS['collection']}}"
                f"{cv.chunks_count:>{_COL_WIDTHS['chunks']}}"
                f"{cv.sources_count:>{_COL_WIDTHS['sources']}}"
                f"  {created_str:<{_COL_WIDTHS['created']}}"
                f"  {activated_str:<{_COL_WIDTHS['activated']}}"
            )

            if cv.status == "active":
                self.stdout.write(self.style.SUCCESS(row))
            elif cv.status == "failed":
                self.stdout.write(self.style.ERROR(row))
            elif cv.status == "retired":
                self.stdout.write(self.style.WARNING(row))
            else:
                self.stdout.write(row)

        self.stdout.write(separator)
        self.stdout.write(f"  {len(versions)} version(s) listed.")
