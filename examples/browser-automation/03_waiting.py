"""Lesson 3: navigation, URL waits, and visibility assertions."""

from playwright.sync_api import sync_playwright, expect


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://playwright.dev/python/")

        page.get_by_role("link", name="Get started", exact=True).click()
        page.wait_for_url("**/docs/intro")
        expect(page).to_have_url("https://playwright.dev/python/docs/intro")

        # expect() auto-retries until timeout (default 5s)
        expect(page.get_by_role("heading", name="Installation")).to_be_visible()

        code_blocks = page.locator("pre code")
        count = code_blocks.count()
        print(f"Intro page loaded; found {count} code block(s).")

        browser.close()


if __name__ == "__main__":
    main()
