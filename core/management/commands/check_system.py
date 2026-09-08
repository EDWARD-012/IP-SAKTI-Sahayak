"""
Print OK/FAIL readiness checks for SIH laptop demo.

Usage:
    python manage.py check_system
"""
from __future__ import annotations

import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Print OK/FAIL for DEMO_MODE, Ollama reachability, active corpus, DEBUG."

    def handle(self, *args, **options):
        demo = bool(getattr(settings, "DEMO_MODE", True))
        debug = bool(settings.DEBUG)
        ollama_ok = self._ollama_ok()
        corpus = self._active_corpus()

        rows = [
            ("DEMO_MODE", True, f"DEMO_MODE={demo}"),
            ("OLLAMA", ollama_ok or demo, f"reachable={ollama_ok}"),
            ("ACTIVE_CORPUS", corpus != "none" or demo, f"version={corpus}"),
            ("DEBUG", True, f"DEBUG={debug}"),
        ]

        fails = 0
        for name, ok, detail in rows:
            mark = "OK" if ok else "FAIL"
            if not ok:
                fails += 1
            self.stdout.write(f"[{mark}] {name}: {detail}")

        if fails:
            self.stderr.write(self.style.ERROR(f"{fails} check(s) failed"))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("All checks OK (demo-tolerant)"))

    def _ollama_ok(self) -> bool:
        base = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        try:
            req = urllib.request.Request(f"{base}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return 200 <= resp.status < 300
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return False

    def _active_corpus(self) -> str:
        try:
            from corpus.models import CorpusVersion
            cv = CorpusVersion.objects.filter(status="active").first()
            return cv.version if cv else "none"
        except Exception:
            return "none"
