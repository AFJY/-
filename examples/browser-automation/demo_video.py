"""Short visual demo for screen recording — runs key automation steps with visible browser."""

import time
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

OUTPUT = Path(__file__).resolve().parent / "output"
OUTPUT.mkdir(exist_ok=True)


def pause(seconds: float = 1.2) -> None:
    time.sleep(seconds)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        print("=== 1. 打开网页并截图 ===")
        page.goto("https://example.com")
        pause()
        page.screenshot(path=str(OUTPUT / "demo_01.png"))
        print(f"标题: {page.title()}")

        print("=== 2. 点击链接跳转 ===")
        page.get_by_role("link", name="Learn more").click()
        page.wait_for_url("**iana.org**")
        pause()
        print(f"当前 URL: {page.url}")

        print("=== 3. TodoMVC 表单操作 ===")
        page.goto("https://demo.playwright.dev/todomvc")
        box = page.get_by_placeholder("What needs to be done?")
        for task in ["学习 Playwright", "录制演示视频"]:
            box.fill(task)
            box.press("Enter")
            pause(0.6)
        expect(page.locator(".todo-list li")).to_have_count(2)
        page.locator(".todo-list li").first.locator('input[type="checkbox"]').check()
        pause()
        page.screenshot(path=str(OUTPUT / "demo_todo.png"))
        print("已添加 2 条任务并完成 1 条")

        pause(1.5)
        browser.close()
        print("演示结束 ✓")


if __name__ == "__main__":
    main()
