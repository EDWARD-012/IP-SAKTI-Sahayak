"""
scripts/screenshot_ui.py — Capture UI screenshots for visual verification.
Requires: pip install playwright && playwright install chromium
Usage: python scripts/screenshot_ui.py (server must be running on :8000)
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent.parent / "screenshots"
OUT.mkdir(exist_ok=True)

PAGES = [
    ("home",    "/",           1366),
    ("chat",    "/assistant/", 1366),
    ("wizard",  "/wizard/",    1366),
    ("corpus",  "/corpus/about/", 1366),
    ("home-mobile", "/",       390),   # iPhone-ish width
    ("chat-mobile", "/assistant/", 390),
]


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, path, width in PAGES:
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(800)  # let GSAP entrance finish
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
            print(f"captured {name}.png ({width}px)")
            page.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
