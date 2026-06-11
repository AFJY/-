#!/usr/bin/env python3
"""
同花顺远航版 桌面桥接代理 — 在 Windows 桌面运行

将本地实时行情转发到 Stock AI 服务，优先使用 akshare 读取 A 股盘面；
若你已打开同花顺远航版，本代理会并行运行，数据以推送形式覆盖云端行情。

用法 (Windows):
  pip install websockets akshare
  python ths_agent.py --server ws://YOUR_SERVER:8765/ws/ths --symbols 600519,000001

同花顺说明:
  同花顺远航版无公开 API。本代理通过 akshare（东方财富源）获取与同花顺一致的 A 股实时价；
  你在桌面看盘用同花顺，交易决策在 Stock AI 云端/本地服务执行。
  后续可扩展 pywinauto 读取同花顺窗口自选列表。
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone

try:
    import akshare as ak
except ImportError:
    raise SystemExit("请安装: pip install akshare websockets")

try:
    import websockets
except ImportError:
    raise SystemExit("请安装: pip install websockets")


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


async def run(server_url: str, symbols: list[str], interval: int) -> None:
    while True:
        try:
            async with websockets.connect(server_url) as ws:
                msg = await ws.recv()
                print("Connected:", msg)
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
    p.add_argument("--symbols", default="600519,000001,399001", help="逗号分隔股票代码")
    p.add_argument("--interval", type=int, default=5, help="推送间隔秒")
    args = p.parse_args()
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    asyncio.run(run(args.server, symbols, args.interval))


if __name__ == "__main__":
    main()
