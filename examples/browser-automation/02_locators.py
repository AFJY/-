"""Lesson 2: locate elements with role, text, and CSS selectors."""

from pathlib import Path

from playwright.sync_api import sync_playwright

OUTPUT = Path(__file__).resolve().parent / "output"
OUTPUT.mkdir(exist_ok=True)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://playwright.dev/python/")

        # Prefer accessible locators (stable across layout changes)
        docs_link = page.get_by_role("link", name="Docs")
        print(f"Docs link visible: {docs_link.is_visible()}")

        get_started = page.get_by_role("link", name="Get started", exact=True)
        get_started.click()
        page.wait_for_url("**/docs/intro")
        print(f"After click, URL: {page.url}")

        # CSS / text fallbacks
        heading = page.locator("h1").first
        print(f"Page heading: {heading.inner_text()}")

        page.screenshot(path=str(OUTPUT / "02_playwright_docs.png"))
        browser.close()


if __name__ == "__main__":
    main()
