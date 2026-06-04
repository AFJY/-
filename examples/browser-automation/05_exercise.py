"""
Exercise: complete the TODOs below, then run this script.

Goal: open example.com, click "Learn more", assert the new page title
contains "IANA", and save a screenshot to output/05_exercise.png.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright, expect

OUTPUT = Path(__file__).resolve().parent / "output"
OUTPUT.mkdir(exist_ok=True)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # TODO 1: navigate to https://example.com

        # TODO 2: click the link whose visible text is "Learn more"
        # Hint: page.get_by_role("link", name="...")

        # TODO 3: wait until URL contains "iana.org"

        # TODO 4: assert page title contains "IANA"
        # Hint: expect(page).to_have_title(...)

        # TODO 5: screenshot to OUTPUT / "05_exercise.png"

        browser.close()
        print("Exercise stub — fill in the TODOs above!")


# --- Solution (uncomment to check your work) ---
# def main() -> None:
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         page = browser.new_page()
#         page.goto("https://example.com")
#         page.get_by_role("link", name="Learn more").click()
#         page.wait_for_url("**iana.org**")
#         expect(page).to_have_title(expect.string_containing("IANA"))
#         page.screenshot(path=str(OUTPUT / "05_exercise.png"))
#         browser.close()
#         print("Exercise done!")


if __name__ == "__main__":
    main()
