#!/usr/bin/env python3
"""
同花顺远航版 桌面桥接代理 — 在 Windows 桌面运行

功能:
  - 自动读取同花顺自选股 (或 bridge/watchlist.json)
  - 推送实时行情到 Stock AI 服务
  - 同步自选股列表到服务端 config

用法 (Windows):
  pip install websockets akshare
  python ths_agent.py --server ws://127.0.0.1:8765/ws/ths
  python ths_agent.py --server ws://127.0.0.1:8765/ws/ths --sync-watchlist --ui
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    import akshare as ak
except ImportError:
    raise SystemExit("请安装: pip install akshare websockets")

try:
    import websockets
except ImportError:
    raise SystemExit("请安装: pip install websockets")

from ths_watchlist import load_watchlist


def fetch_quotes(symbols: list[str]) -> list[dict]:
    out = []
    for sym in symbols:
        code = sym.split(".")[0]
        try:
            df = ak.stock_bid_ask_em(symbol=code)
            price_row = df[df["item"] == "最新"]
            if price_row.empty:
                continue
            price = float(price_row.iloc[0]["value"])
            chg_row = df[df["item"] == "涨幅"]
            chg = float(chg_row.iloc[0]["value"]) if not chg_row.empty else 0.0
            out.append({
                "type": "quote",
                "symbol": sym if "." in sym else f"{code}.SS" if code.startswith("6") else f"{code}.SZ",
                "name": code,
                "price": price,
                "change_pct": chg,
                "volume": 0.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            continue
    return out


def http_sync_watchlist(server_ws_url: str, symbols: list[str]) -> bool:
    """POST watchlist to HTTP API derived from WebSocket URL."""
    parsed = urlparse(server_ws_url.replace("ws://", "http://").replace("wss://", "https://"))
    base = f"{parsed.scheme}://{parsed.netloc}"
    url = f"{base}/api/watchlist/sync"
    body = json.dumps({"symbols": symbols}).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Watchlist sync failed: {e}")
        return False


async def run(
    server_url: str,
    symbols: list[str],
    interval: int,
    sync_watchlist: bool,
) -> None:
    if sync_watchlist and symbols:
        ok = http_sync_watchlist(server_url, symbols)
        print(f"Watchlist sync ({len(symbols)} symbols):", "OK" if ok else "FAILED")

    while True:
        try:
            async with websockets.connect(server_url) as ws:
                msg = await ws.recv()
                print("Connected:", msg)
                # Send watchlist over WS as well
                if symbols:
                    await ws.send(json.dumps({"type": "watchlist", "symbols": symbols}))
                while True:
                    for q in fetch_quotes(symbols):
                        await ws.send(json.dumps(q))
                    await asyncio.sleep(interval)
        except Exception as e:
            print(f"Reconnect in 5s: {e}")
            await asyncio.sleep(5)


def main() -> None:
    p = argparse.ArgumentParser(description="同花顺/桌面行情桥接")
    p.add_argument("--server", default="ws://127.0.0.1:8765/ws/ths", help="Stock AI WebSocket 地址")
    p.add_argument("--symbols", default="", help="逗号分隔股票代码 (留空则自动读自选股)")
    p.add_argument("--interval", type=int, default=5, help="推送间隔秒")
    p.add_argument("--sync-watchlist", action="store_true", help="同步自选股到服务端 config")
    p.add_argument("--ui", action="store_true", help="尝试从同花顺窗口 UI 读取自选股")
    p.add_argument("--watchlist-json", default="", help="自定义 watchlist.json 路径")
    args = p.parse_args()

    if args.symbols.strip():
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        jp = Path(args.watchlist_json) if args.watchlist_json else None
        symbols = load_watchlist(jp, use_ui=args.ui)
        print(f"Loaded {len(symbols)} symbols from 同花顺/本地配置:", symbols[:10], "...")

    if not symbols:
        raise SystemExit(
            "未找到自选股。请: 1) 在同花顺导出到 bridge/watchlist.json "
            '格式 ["600519.SS","000001.SZ"]  2) 或使用 --symbols 600519,000001'
        )

    asyncio.run(run(args.server, symbols, args.interval, args.sync_watchlist))


if __name__ == "__main__":
    main()
