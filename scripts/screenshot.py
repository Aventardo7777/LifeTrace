"""Generate project screenshots by driving a headless browser.

This script requires Playwright (``pip install playwright`` and
``playwright install chromium``). If Playwright is unavailable, it exits
gracefully with a message. Screenshots are written to ``screenshots/`` and are
referenced from the README.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

HOST = "http://127.0.0.1:8000"
OUT = ROOT / "screenshots"

PAGES = {
    "dashboard": "/",
    "analysis": "/analysis",
    "record": "/record",
    "data": "/data",
}


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright 未安装，跳过截图生成。")
        return

    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for name, path in PAGES.items():
            try:
                page.goto(f"{HOST}{path}", wait_until="networkidle")
                page.wait_for_timeout(2500)
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
                print(f"已生成 {name}.png")
            except Exception as exc:  # noqa: BLE001
                print(f"{name}.png 生成失败: {exc}")
        browser.close()


if __name__ == "__main__":
    main()
