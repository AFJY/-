# 浏览器自动化入门（Playwright + Python）

用 [Playwright](https://playwright.dev/python/) 学习浏览器自动化：打开页面、定位元素、点击、填表、等待、截图。所有示例都针对**公开演示站点**，不涉及刷课或绕过平台检测。

## 快速开始

```bash
cd examples/browser-automation
bash setup.sh
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 按顺序运行
python 01_basics.py
python 02_locators.py
python 03_waiting.py
python 04_forms.py
python 05_exercise.py
```

截图会保存到 `output/` 目录。

## 核心概念

| 概念 | 说明 |
|------|------|
| **Browser** | 浏览器进程（Chromium / Firefox / WebKit） |
| **Context** | 独立会话：Cookie、本地存储互不干扰 |
| **Page** | 单个标签页，大部分操作在 `page` 上完成 |
| **Locator** | 定位元素的方式，推荐用 `get_by_role`、`get_by_text` |
| **Auto-wait** | Playwright 在点击、填表前会自动等元素可操作 |

## 示例目录

| 文件 | 学什么 |
|------|--------|
| `01_basics.py` | 启动浏览器、打开 URL、截图、打印标题 |
| `02_locators.py` | 多种定位方式、点击链接 |
| `03_waiting.py` | 显式等待、导航、断言 |
| `04_forms.py` | TodoMVC 演示站：输入、勾选、删除 |
| `05_exercise.py` | 练习题：自己补全脚本 |

## 常用 API 速查

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # headless=True 无界面
    page = browser.new_page()
    page.goto("https://example.com")

    page.get_by_role("link", name="More information").click()
    page.get_by_label("用户名").fill("alice")
    page.get_by_placeholder("搜索").fill("Playwright")
    page.locator("#submit").click()

    page.wait_for_url("**/success")
    assert page.get_by_text("欢迎").is_visible()

    page.screenshot(path="output/shot.png", full_page=True)
    browser.close()
```

## 调试技巧

1. **有界面模式**：`launch(headless=False)`，亲眼看到浏览器在做什么。
2. **慢动作**：`launch(slow_mo=500)`，每步延迟 500ms。
3. **Codegen 录制**：安装后运行 `playwright codegen https://example.com`，操作浏览器会自动生成代码。
4. **Inspector**：设置 `PWDEBUG=1 python 01_basics.py` 进入逐步调试。

## 与 Selenium 对比（了解即可）

| | Playwright | Selenium |
|---|------------|----------|
| 维护方 | Microsoft | 社区 + 各浏览器厂商 |
| 等待 | 内置 auto-wait | 常需手写 WebDriverWait |
| 多标签/上下文 | 原生支持 | 需额外管理 |
| 安装 | `pip install playwright && playwright install` | 需单独下载 WebDriver |

本教程选用 Playwright，因为 API 现代、文档好、与 Hermes 完整安装脚本中的 Playwright 一致。

## 合法使用提醒

浏览器自动化适合：**自己的网站测试**、**公开 Demo 练习**、**重复性办公流程（经授权）**。请勿用于伪造学习进度、批量注册、爬取受保护数据或违反网站服务条款的行为。

## 下一步

- 官方文档：[Playwright Python](https://playwright.dev/python/docs/intro)
- 录制脚本：`playwright codegen`
- 无头 CI：把 `headless=True` 放进 GitHub Actions 做回归测试
- Hermes Agent：`hermes doctor` 检查 Playwright 是否已安装（需先跑 `scripts/install-hermes-full.sh`）
