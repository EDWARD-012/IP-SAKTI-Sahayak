from django.core.management.base import BaseCommand, CommandError

from corpus.models import CorpusVersion


class Command(BaseCommand):
    help = "Activate a corpus version by its version string."

    def add_arguments(self, parser):
        parser.add_argument(
            "version",
            help="The corpus version string to activate (e.g. '1.0').",
        )

    def handle(self, *args, **options):
        version_str = options["version"]

        try:
            cv = CorpusVersion.objects.get(version=version_str)
        except CorpusVersion.DoesNotExist:
            raise CommandError(
                f"CorpusVersion with version='{version_str}' does not exist."
            )

        if cv.status == "active":
            self.stdout.write(
                self.style.WARNING(
                    f"CorpusVersion '{version_str}' is already active."
                )
            )
            return

        if cv.status not in ("validated", "building", "failed", "retired"):
            raise CommandError(
                f"Cannot activate version '{version_str}' with status='{cv.status}'."
            )

        try:
            cv.activate()
        except Exception as exc:
            raise CommandError(
                f"Failed to activate version '{version_str}': {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"CorpusVersion '{version_str}' activated successfully."
            )
        )
