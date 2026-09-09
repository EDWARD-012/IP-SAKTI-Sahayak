from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "IP-SAKTI Core"

    def ready(self) -> None:
        """Activate SQLite WAL; warm embeddings in background when live."""
        from django.db.models.signals import post_migrate

        def _activate_wal(sender: object, **kwargs: object) -> None:
            try:
                from django.db import connection
                connection.cursor().execute("PRAGMA journal_mode=WAL;")
                connection.cursor().execute("PRAGMA synchronous=NORMAL;")
            except Exception:
                pass

        post_migrate.connect(_activate_wal, weak=False)

        # Avoid double-start under Django autoreload parent process.
        import os
        if os.environ.get("RUN_MAIN") == "false":
            return

        from django.conf import settings
        if getattr(settings, "DEMO_MODE", True):
            return

        def _warm_embeddings() -> None:
            try:
                from ai.retrieve import _get_embed_model
                model = _get_embed_model()
                if model is not None:
                    model.encode(["warmup"], normalize_embeddings=True)
            except Exception:
                pass

        import threading
        threading.Thread(target=_warm_embeddings, name="embed-warmup", daemon=True).start()
