"""
从同花顺远航版读取自选股列表 (Windows)

尝试顺序:
  1. 用户导出 JSON (bridge/watchlist.json)
  2. 同花顺用户目录下的 SelfStock / block 文件
  3. 同花顺导出 CSV/TXT
  4. pywinauto 读取窗口标题 (可选, --ui)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


def normalize_code(code: str) -> str:
    code = code.strip()
    if "." in code:
        return code.upper()
    if len(code) == 6 and code.isdigit():
        return f"{code}.SS" if code.startswith("6") else f"{code}.SZ"
    return code


def from_json_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [normalize_code(str(x)) for x in data]
    if isinstance(data, dict) and "symbols" in data:
        return [normalize_code(str(x)) for x in data["symbols"]]
    return []


def from_csv_or_txt(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    codes = re.findall(r"\b(\d{6})\b", text)
    return [normalize_code(c) for c in dict.fromkeys(codes)]


def from_ini_block(path: Path) -> list[str]:
    """Parse simple INI/block files that contain 6-digit codes."""
    if not path.exists():
        return []
    raw = path.read_bytes()
    # Extract ASCII digit sequences of length 6
    codes = re.findall(rb"\d{6}", raw)
    seen: list[str] = []
    for c in codes:
        sym = normalize_code(c.decode())
        if sym not in seen:
            seen.append(sym)
    return seen


def scan_ths_user_dirs() -> list[str]:
    """Scan common 同花顺远航版 / 同花顺 installation paths on Windows."""
    if os.name != "nt":
        return []

    candidates: list[Path] = []
    home = Path.home()
    appdata = os.environ.get("APPDATA", "")
    localappdata = os.environ.get("LOCALAPPDATA", "")

    for base in [
        Path(appdata) / "同花顺",
        Path(localappdata) / "同花顺",
        Path("C:/同花顺远航版"),
        Path("C:/同花顺"),
        Path("D:/同花顺远航版"),
        Path("D:/同花顺"),
        home / "同花顺远航版",
    ]:
        if base.exists():
            candidates.append(base)

    # Program Files variants
    for drive in ("C", "D"):
        for name in ("同花顺远航版", "hexin", "THS", "同花顺"):
            p = Path(f"{drive}:/{name}")
            if p.exists():
                candidates.append(p)

    symbols: list[str] = []
    patterns = [
        "**/SelfStockInfo.dat",
        "**/SelfStockInfo.json",
        "**/selfstock.json",
        "**/stockblock.ini",
        "**/block.dat",
        "**/Block/*.txt",
        "**/自选股*.txt",
        "**/自选股*.csv",
    ]
    for root in candidates:
        for pat in patterns:
            for fp in root.glob(pat):
                if fp.suffix.lower() == ".json":
                    symbols.extend(from_json_file(fp))
                elif fp.suffix.lower() in (".csv", ".txt"):
                    symbols.extend(from_csv_or_txt(fp))
                else:
                    symbols.extend(from_ini_block(fp))

    return list(dict.fromkeys(symbols))


def from_pywinauto() -> list[str]:
    """Optional: read visible stock codes from 同花顺 main window."""
    try:
        from pywinauto import Desktop
    except ImportError:
        return []

    symbols: list[str] = []
    try:
        windows = Desktop(backend="uia").windows()
        for w in windows:
            title = w.window_text()
            if "同花顺" not in title and "远航" not in title:
                continue
            for ctrl in w.descendants():
                try:
                    text = ctrl.window_text()
                except Exception:
                    continue
                for code in re.findall(r"\b(\d{6})\b", text or ""):
                    sym = normalize_code(code)
                    if sym not in symbols:
                        symbols.append(sym)
    except Exception:
        pass
    return symbols


def load_watchlist(
    json_path: Path | None = None,
    use_ui: bool = False,
) -> list[str]:
    json_path = json_path or Path(__file__).parent / "watchlist.json"
    symbols: list[str] = []

    symbols.extend(from_json_file(json_path))
    if symbols:
        return list(dict.fromkeys(symbols))

    symbols.extend(scan_ths_user_dirs())
    if symbols:
        return list(dict.fromkeys(symbols))

    if use_ui:
        symbols.extend(from_pywinauto())

    return list(dict.fromkeys(symbols))


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="读取同花顺自选股")
    p.add_argument("--ui", action="store_true", help="尝试从同花顺窗口读取")
    p.add_argument("--json", default="", help="自定义 watchlist.json 路径")
    args = p.parse_args()
    jp = Path(args.json) if args.json else None
    result = load_watchlist(jp, use_ui=args.ui)
    print(json.dumps(result, ensure_ascii=False, indent=2))
