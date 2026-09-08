"""Capture light + dark screenshots and confirm the theme toggle persists."""
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent.parent / "screenshots"
OUT.mkdir(exist_ok=True)


def main() -> int:
    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=swiftshader"])
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(f"{BASE}/", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1200)

        theme = page.get_attribute("html", "data-theme")
        print("initial theme:", theme)
        page.screenshot(path=str(OUT / "home-light.png"))

        toggle = page.locator("#theme-toggle")
        if toggle.count() == 0:
            failures.append("theme toggle missing")
        else:
            toggle.click()
            page.wait_for_timeout(400)
            theme = page.get_attribute("html", "data-theme")
            print("after click:", theme)
            if theme != "dark":
                failures.append(f"toggle did not switch to dark (got {theme})")
            bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
            print("dark body bg:", bg)
            page.screenshot(path=str(OUT / "home-dark.png"))

            # persist across reload
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(800)
            theme = page.get_attribute("html", "data-theme")
            print("after reload:", theme)
            if theme != "dark":
                failures.append(f"theme did not persist (got {theme})")
            page.screenshot(path=str(OUT / "home-dark-reload.png"))

            page.goto(f"{BASE}/assistant/", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(800)
            page.screenshot(path=str(OUT / "chat-dark.png"))

            toggle.click()
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT / "chat-light.png"))

        browser.close()

    if failures:
        print("FAILURES:")
        for f in failures:
            print(" -", f)
        return 1
    print("All theme checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
