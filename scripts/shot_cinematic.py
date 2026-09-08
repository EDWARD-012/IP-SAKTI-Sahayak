"""Capture cinematic 3D hero + chat empty-state screenshots."""
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent.parent / "screenshots"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader"])
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        page.goto(f"{BASE}/", wait_until="networkidle", timeout=40000)
        page.wait_for_timeout(2500)
        canvas = page.query_selector("#hero3d canvas")
        print("hero canvas:", "YES" if canvas else "NO")
        print("hero3d-active:", page.locator(".hero3d-active").count())
        page.screenshot(path=str(OUT / "cinematic-home.png"))

        page.goto(f"{BASE}/assistant/", wait_until="networkidle", timeout=40000)
        page.wait_for_timeout(2200)
        chat_c = page.query_selector("#chat3d canvas")
        print("chat canvas:", "YES" if chat_c else "NO")
        page.screenshot(path=str(OUT / "cinematic-chat.png"))

        if errors:
            print("JS errors:")
            for e in errors[:12]:
                print(" -", e)
        browser.close()
    return 0 if canvas else 1


if __name__ == "__main__":
    raise SystemExit(main())
