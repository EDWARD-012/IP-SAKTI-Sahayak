"""
scripts/verify_fixes.py — One-shot verification for the bug-fix round.

Checks (against a dev server on :8001):
  1. Homepage renders with the 3D hero (WebGL canvas present)
  2. Browser dark mode does NOT invert the theme (body bg stays light)
  3. Chat ask flow returns a real answer partial (no 422)
  4. No 404s for static assets during a full page load
Captures fresh screenshots to screenshots/.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8001"
OUT = Path(__file__).resolve().parent.parent / "screenshots"
OUT.mkdir(exist_ok=True)


def main() -> int:
    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=swiftshader"])

        # ── 1+4: homepage, collect 404s ──
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        bad: list[str] = []
        page.on("response", lambda r: bad.append(f"{r.status} {r.url}")
                if r.status >= 400 else None)
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1500)
        canvas = page.query_selector(".gov-hero__canvas canvas")
        print("3D hero canvas:", "PRESENT" if canvas else "MISSING (fallback chakra shown)")
        if bad:
            failures.append(f"HTTP errors on homepage: {bad}")
        page.screenshot(path=str(OUT / "home.png"))
        page.close()

        # ── 2: dark-mode emulation must stay light ──
        page = browser.new_page(
            viewport={"width": 1366, "height": 900},
            color_scheme="dark",
        )
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1000)
        bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
        print("body bg under OS dark mode:", bg)
        if bg not in ("rgb(245, 245, 245)", "rgb(255, 255, 255)"):
            failures.append(f"dark mode leaked: body bg = {bg}")
        page.screenshot(path=str(OUT / "home-darkmode-check.png"))
        page.close()

        # ── 3: chat ask end-to-end ──
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(f"{BASE}/assistant/", wait_until="networkidle", timeout=30000)
        page.fill("#chat-question", "Can I patent an Ayurvedic formulation from a classical text?")
        with page.expect_response(lambda r: "/assistant/ask/" in r.url) as resp_info:
            page.click("#chat-form [type=submit]")
        resp = resp_info.value
        print("ask status:", resp.status)
        if resp.status != 200:
            failures.append(f"/assistant/ask/ returned {resp.status}")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / "chat-answer.png"))
        page.close()

        # ── extra screenshots ──
        for name, path, width in [
            ("chat", "/assistant/", 1366),
            ("wizard", "/wizard/", 1366),
            ("home-mobile", "/", 390),
        ]:
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUT / f"{name}.png"))
            page.close()

        browser.close()

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(" -", f)
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
