"""Capture a live (DEMO_MODE=False) chat answer screenshot."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "screenshots"
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=swiftshader"])
    pg = b.new_page(viewport={"width": 1366, "height": 950})
    pg.goto("http://127.0.0.1:8000/assistant/", wait_until="networkidle", timeout=30000)
    pg.fill("#chat-question", "Can I patent an Ayurvedic formulation based on a classical text?")
    with pg.expect_response(lambda r: "/assistant/ask/" in r.url, timeout=120000) as ri:
        pg.click("#chat-form [type=submit]")
    print("ask status:", ri.value.status)
    pg.wait_for_timeout(2000)
    pg.screenshot(path=str(OUT / "chat-live.png"), full_page=True)
    print("saved chat-live.png")
    b.close()
