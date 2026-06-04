"""Lesson 4: interact with a demo todo app (add, complete, filter)."""

from pathlib import Path

from playwright.sync_api import sync_playwright, expect

OUTPUT = Path(__file__).resolve().parent / "output"
OUTPUT.mkdir(exist_ok=True)

TODO_URL = "https://demo.playwright.dev/todomvc"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(TODO_URL)

        input_box = page.get_by_placeholder("What needs to be done?")
        tasks = ["学习 Playwright 定位元素", "运行 04_forms.py", "阅读 README"]

        for task in tasks:
            input_box.fill(task)
            input_box.press("Enter")

        items = page.locator(".todo-list li")
        expect(items).to_have_count(3)

        # Mark first task done
        page.locator(".todo-list li").first.locator('input[type="checkbox"]').check()
        expect(page.locator(".todo-list li.completed")).to_have_count(1)

        # Filter: Active only
        page.get_by_role("link", name="Active").click()
        expect(page.locator(".todo-list li")).to_have_count(2)

        page.screenshot(path=str(OUTPUT / "04_todomvc_active.png"))
        print("Todo demo completed: 3 added, 1 completed, Active filter applied.")

        browser.close()


if __name__ == "__main__":
    main()
