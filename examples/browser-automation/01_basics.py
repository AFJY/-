"""Lesson 1: launch browser, open a page, screenshot, print title."""

from pathlib import Path

from playwright.sync_api import sync_playwright

OUTPUT = Path(__file__).resolve().parent / "output"
OUTPUT.mkdir(exist_ok=True)


def main() -> None:
    with sync_playwright() as p:
        # headless=False shows the browser window (good for learning)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        page.goto("https://example.com", wait_until="domcontentloaded")
        print(f"Title: {page.title()}")
        print(f"URL:   {page.url}")

        shot = OUTPUT / "01_example_com.png"
        page.screenshot(path=str(shot), full_page=True)
        print(f"Screenshot saved: {shot}")

        browser.close()


if __name__ == "__main__":
    main()
