"""
validate_corpus_version — Retrieval-quality gate for a built corpus version.

Runs every golden question (data/golden/golden_questions.json) against the
version's Chroma collection and checks that the expected source(s) appear in
the retrieved top-k. Passes (status → 'validated') when:
    - chunks_count >= --min-chunks, AND
    - source hit-rate >= --min-hit-rate (over questions that expect sources).

Questions whose expected_outcome is out_of_scope / unable_to_answer expect NO
sources and are scored on correctly retrieving little/nothing relevant.

Usage:
    python manage.py validate_corpus_version 1.0
    python manage.py validate_corpus_version 1.0 --min-hit-rate 0.7 --k 8
"""
from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from corpus.models import CorpusVersion


class Command(BaseCommand):
    help = "Validate a built corpus version against golden questions."

    def add_arguments(self, parser):
        parser.add_argument("version", help="Corpus version to validate.")
        parser.add_argument("--min-chunks", type=int, default=10, dest="min_chunks")
        parser.add_argument("--min-hit-rate", type=float, default=0.6, dest="min_hit_rate")
        parser.add_argument("--k", type=int, default=8, help="Top-k retrieved per question.")
        parser.add_argument(
            "--golden",
            default="data/golden/golden_questions.json",
            help="Path to golden questions JSON.",
        )

    def handle(self, *args, **options):
        version = options["version"]
        cv = CorpusVersion.objects.filter(version=version).first()
        if not cv:
            raise CommandError(
                f"CorpusVersion '{version}' not found. Run build_corpus_version first."
            )

        if cv.chunks_count < options["min_chunks"]:
            raise CommandError(
                f"chunks_count={cv.chunks_count} < min_chunks={options['min_chunks']}. "
                "Ingest more sources before validating."
            )

        golden_path = Path(options["golden"]).resolve()
        if not golden_path.is_file():
            raise CommandError(f"Golden questions file not found: {golden_path}")
        questions = json.loads(golden_path.read_text(encoding="utf-8"))

        # Import here so module import never requires the AI stack.
        try:
            from ai.retrieve import retrieve_from_collection
        except Exception as exc:  # pragma: no cover
            raise CommandError(f"Could not import retrieval layer: {exc}") from exc

        k = options["k"]
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Validating v{version} (collection={cv.chroma_collection}, "
            f"embed={settings.EMBED_MODEL})"
        ))

        scored = 0
        hits = 0
        rows: list[tuple[str, str, str]] = []

        for q in questions:
            qid = q.get("id", "?")
            expected = set(q.get("expected_sources", []) or [])
            outcome = q.get("expected_outcome", "grounded")
            juri = q.get("jurisdiction", "IN")

            results = retrieve_from_collection(
                q["question"], cv.chroma_collection, jurisdiction=juri, k=k,
            )
            got_sources = {r["source_id"] for r in results if r.get("source_id")}

            if expected:
                scored += 1
                hit = bool(expected & got_sources)
                hits += int(hit)
                mark = self.style.SUCCESS("PASS") if hit else self.style.ERROR("MISS")
                detail = f"expected {sorted(expected)}, got {sorted(got_sources)[:3]}"
            else:
                # out_of_scope / unable → expect nothing strongly relevant
                mark = self.style.WARNING("N/A ")
                detail = f"({outcome}) top: {sorted(got_sources)[:3]}"

            rows.append((qid, str(mark), detail))

        for qid, mark, detail in rows:
            self.stdout.write(f"  [{mark}] {qid:8s} {detail}")

        hit_rate = (hits / scored) if scored else 0.0
        self.stdout.write("")
        self.stdout.write(
            f"Source hit-rate: {hits}/{scored} = {hit_rate:.0%} "
            f"(threshold {options['min_hit_rate']:.0%})"
        )

        if hit_rate < options["min_hit_rate"]:
            raise CommandError(
                f"Validation FAILED: hit-rate {hit_rate:.0%} below "
                f"{options['min_hit_rate']:.0%}. Check corpus coverage / chunking."
            )

        cv.status = "validated"
        cv.notes = f"Validated: {hits}/{scored} golden sources hit ({hit_rate:.0%})."
        cv.save(update_fields=["status", "notes"])

        self.stdout.write(self.style.SUCCESS(
            f"\nCorpusVersion '{version}' → validated. "
            f"Activate with: python manage.py activate_corpus_version {version}"
        ))
