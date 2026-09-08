from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "IP-SAKTI Core"

    def ready(self) -> None:
        """Activate SQLite WAL mode after migrations via a post-migrate signal."""
        from django.db.models.signals import post_migrate

        def _activate_wal(sender: object, **kwargs: object) -> None:
            try:
                from django.db import connection
                connection.cursor().execute("PRAGMA journal_mode=WAL;")
                connection.cursor().execute("PRAGMA synchronous=NORMAL;")
            except Exception:
                pass

        post_migrate.connect(_activate_wal, weak=False)
