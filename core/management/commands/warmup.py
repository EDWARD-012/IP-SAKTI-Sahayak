"""
warmup — Pre-load embedding model and optionally ping Ollama before a live demo.

Usage:
    python manage.py warmup
    python manage.py warmup --skip-ollama
    python manage.py warmup --no-generate
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Warm SentenceTransformer cache and optionally ping Ollama for SIH demo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-ollama",
            action="store_true",
            help="Only load embeddings; do not contact Ollama.",
        )
        parser.add_argument(
            "--no-generate",
            action="store_true",
            help="Ping /api/tags only; skip the tiny /api/chat generate.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("IP-SAKTI warmup"))
        self.stdout.write(f"  EMBED_MODEL={settings.EMBED_MODEL} ({settings.EMBED_DEVICE})")
        self.stdout.write(f"  OLLAMA_MODEL={settings.OLLAMA_MODEL}")
        self.stdout.write(f"  DEMO_MODE={getattr(settings, 'DEMO_MODE', True)}")
        self.stdout.write(f"  CHROMA_PERSIST_DIR={settings.CHROMA_PERSIST_DIR}")
        self.stdout.write("")

        # ── Chroma active collection ──────────────────────────
        try:
            from corpus.models import CorpusVersion
            import chromadb

            cv = CorpusVersion.objects.filter(status="active").first()
            if not cv:
                self.stdout.write(self.style.WARNING("[WARN] No active CorpusVersion"))
            else:
                client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
                col = client.get_collection(cv.chroma_collection)
                n = int(col.count())
                self.stdout.write(self.style.SUCCESS(
                    f"[OK]   Chroma {cv.chroma_collection} → {n} chunks "
                    f"(corpus {cv.version})"
                ))
                if n > 0 and cv.chunks_count != n:
                    cv.chunks_count = n
                    cv.save(update_fields=["chunks_count"])
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"[FAIL] Chroma probe: {exc}"))

        # ── Embeddings ────────────────────────────────────────
        t0 = time.monotonic()
        try:
            from ai.retrieve import _get_embed_model

            embed = _get_embed_model()
            if embed is None:
                self.stdout.write(self.style.ERROR(
                    f"[FAIL] Embedding model not loaded ({time.monotonic() - t0:.1f}s)"
                ))
            else:
                # One tiny encode to force weights onto the device.
                embed.encode(["warmup"], normalize_embeddings=True)
                self.stdout.write(self.style.SUCCESS(
                    f"[OK]   Embeddings ready in {time.monotonic() - t0:.1f}s "
                    f"({settings.EMBED_MODEL})"
                ))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(
                f"[FAIL] Embeddings error after {time.monotonic() - t0:.1f}s: {exc}"
            ))

        if options["skip_ollama"]:
            self.stdout.write("")
            self.stdout.write("Skipped Ollama (--skip-ollama).")
            return

        # ── Ollama /api/tags ──────────────────────────────────
        base = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        t1 = time.monotonic()
        try:
            req = urllib.request.Request(f"{base}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                tags_body = json.loads(resp.read().decode())
            models = [m.get("name", "") for m in tags_body.get("models", [])]
            self.stdout.write(self.style.SUCCESS(
                f"[OK]   Ollama /api/tags in {time.monotonic() - t1:.1f}s "
                f"({len(models)} model(s))"
            ))
            if settings.OLLAMA_MODEL and settings.OLLAMA_MODEL not in models:
                # Allow tag without exact quant suffix match noise
                approx = any(settings.OLLAMA_MODEL.split(":")[0] in m for m in models)
                if not approx:
                    self.stdout.write(self.style.WARNING(
                        f"       Model '{settings.OLLAMA_MODEL}' not listed in /api/tags"
                    ))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            self.stdout.write(self.style.ERROR(
                f"[FAIL] Ollama /api/tags after {time.monotonic() - t1:.1f}s: {exc}"
            ))
            self.stdout.write("       Start Ollama before live Ask, or keep DEMO_MODE=True.")
            return

        if options["no_generate"]:
            self.stdout.write("")
            self.stdout.write("Skipped generate (--no-generate).")
            return

        # ── Tiny /api/chat generate ───────────────────────────
        t2 = time.monotonic()
        try:
            payload = json.dumps({
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "user", "content": "Reply READY only"},
                ],
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 8},
            }).encode()
            req = urllib.request.Request(
                f"{base}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            timeout = min(float(getattr(settings, "OLLAMA_TIMEOUT", 180)), 120.0)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode())
            text = (body.get("message") or {}).get("content", "").strip()
            self.stdout.write(self.style.SUCCESS(
                f"[OK]   Ollama generate in {time.monotonic() - t2:.1f}s "
                f"→ {text[:80]!r}"
            ))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            self.stdout.write(self.style.ERROR(
                f"[FAIL] Ollama generate after {time.monotonic() - t2:.1f}s: {exc}"
            ))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Warmup finished."))
