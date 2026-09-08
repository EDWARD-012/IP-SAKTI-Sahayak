"""
Stub management command: validate a built corpus version.

Checks that the CorpusVersion has at least --min-chunks chunks recorded,
then sets its status to 'validated'.

For testing, creates the CorpusVersion if it does not yet exist.
"""
from django.core.management.base import BaseCommand, CommandError

from corpus.models import CorpusVersion


class Command(BaseCommand):
    help = (
        "Validate a built corpus version. "
        "Sets status to 'validated' when chunks_count >= --min-chunks. "
        "Creates the record if it does not exist (useful for testing)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--version",
            required=True,
            help="The corpus version string to validate.",
        )
        parser.add_argument(
            "--min-chunks",
            type=int,
            default=1,
            dest="min_chunks",
            help="Minimum chunk count required to pass validation (default: 1).",
        )

    def handle(self, *args, **options):
        version_str = options["version"]
        min_chunks = options["min_chunks"]

        collection_name = f"ip_sakti_v{version_str.replace('.', '_')}"
        cv, created = CorpusVersion.objects.get_or_create(
            version=version_str,
            defaults={
                "status": "building",
                "chroma_collection": collection_name,
            },
        )

        if created:
            self.stdout.write(
                self.style.WARNING(
                    f"CorpusVersion '{version_str}' did not exist — "
                    "created a placeholder record for testing."
                )
            )

        if cv.chunks_count < min_chunks:
            raise CommandError(
                f"Validation failed for '{version_str}': "
                f"chunks_count={cv.chunks_count} is below min_chunks={min_chunks}. "
                "Run the build pipeline and update chunks_count before validating."
            )

        cv.status = "validated"
        cv.save(update_fields=["status"])

        self.stdout.write(
            self.style.SUCCESS(
                f"CorpusVersion '{version_str}' validated "
                f"({cv.chunks_count} chunks \u2265 {min_chunks})."
            )
        )
