from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from stock_ai.realtime.monitor import get_monitor

STATIC_DIR = Path(__file__).parent / "static"


class CommandRequest(BaseModel):
    command: str


class ThsQuotePayload(BaseModel):
    symbol: str
    name: str = ""
    price: float
    change_pct: float = 0.0
    volume: float = 0.0
    timestamp: str = ""


class WatchlistSync(BaseModel):
    symbols: list[str]


class MonthlyTarget(BaseModel):
    target_return_pct: float


def create_app(config_path: str = "config.yaml") -> FastAPI:
    app = FastAPI(title="Stock AI Dashboard", version="0.2.0")
    monitor = get_monitor(config_path)
    ws_clients: list[WebSocket] = []

    def on_tick(event: dict) -> None:
        if app.state.loop and ws_clients:
            asyncio.run_coroutine_threadsafe(_broadcast(event), app.state.loop)

    async def _broadcast(data: dict) -> None:
        dead: list[WebSocket] = []
        for ws in ws_clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in ws_clients:
                ws_clients.remove(ws)

    @app.on_event("startup")
    async def startup() -> None:
        app.state.loop = asyncio.get_event_loop()
        monitor.subscribe(on_tick)
        monitor.start()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        monitor.stop()

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    @app.get("/api/status")
    async def api_status() -> dict[str, Any]:
        """Lightweight status from cache; use POST /api/tick for full refresh."""
        prices = {q.symbol: q.price for q in monitor.quote_store.all_quotes()}
        equity = monitor.portfolio.total_equity(prices) if prices else monitor.portfolio.cash
        cycle = monitor.monthly.ensure_cycle(equity)
        return {
            "equity": equity,
            "cash": monitor.portfolio.cash,
            "monthly": cycle.to_dict(),
            "quotes": [
                {"symbol": q.symbol, "name": q.name, "price": q.price, "change_pct": q.change_pct, "source": q.source}
                for q in monitor.quote_store.all_quotes()
            ],
            "signals": monitor._last_signals,
            "paused": monitor._paused,
            "ths_connected": monitor.quote_store.ths_connected,
            "equity_curve": monitor.equity_log.get_curve(200),
        }

    @app.get("/api/equity-curve")
    async def equity_curve() -> dict[str, Any]:
        return {"curve": monitor.equity_log.get_curve(500)}

    @app.post("/api/watchlist/sync")
    async def watchlist_sync(body: WatchlistSync) -> dict[str, Any]:
        symbols = monitor.sync_watchlist(body.symbols)
        return {"ok": True, "watchlist": symbols, "count": len(symbols)}

    @app.post("/api/monthly/target")
    async def monthly_target(body: MonthlyTarget) -> dict[str, Any]:
        pct = monitor.set_monthly_target(body.target_return_pct)
        return {"ok": True, "target_return_pct": pct}

    @app.post("/api/tick")
    async def api_tick() -> dict[str, Any]:
        return monitor.tick()

    @app.post("/api/command")
    async def api_command(req: CommandRequest) -> dict[str, Any]:
        return monitor.handle_command(req.command)

    @app.post("/api/ths/quote")
    async def ths_quote(payload: ThsQuotePayload) -> dict[str, Any]:
        """Receive real-time quote from 同花顺 desktop bridge."""
        quote = monitor.ingest_ths_quote(payload.model_dump())
        event = {"type": "ths_quote", "quote": payload.model_dump(), "source": "ths_bridge"}
        await _broadcast(event)
        return {"ok": True, "symbol": quote.symbol, "price": quote.price}

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        ws_clients.append(ws)
        try:
            await ws.send_json({"type": "welcome", "message": "Stock AI 实时连接已建立"})
            await ws.send_json(monitor.tick())
            while True:
                raw = await ws.receive_text()
                try:
                    msg = json.loads(raw)
                    if msg.get("type") == "command":
                        result = monitor.handle_command(msg.get("command", ""))
                        await ws.send_json({"type": "command_result", **result})
                    elif msg.get("type") == "ths_quote":
                        monitor.ingest_ths_quote(msg)
                except json.JSONDecodeError:
                    result = monitor.handle_command(raw)
                    await ws.send_json({"type": "command_result", **result})
        except WebSocketDisconnect:
            pass
        finally:
            if ws in ws_clients:
                ws_clients.remove(ws)

    @app.websocket("/ws/ths")
    async def ths_bridge(ws: WebSocket) -> None:
        await ws.accept()
        await ws.send_json({"type": "welcome", "message": "同花顺桥接已连接"})
        try:
            while True:
                raw = await ws.receive_text()
                msg = json.loads(raw)
                if msg.get("type") == "quote":
                    monitor.ingest_ths_quote(msg)
                    await _broadcast({"type": "tick_partial", "quote": msg})
                elif msg.get("type") == "watchlist":
                    symbols = monitor.sync_watchlist(msg.get("symbols", []))
                    await ws.send_json({"type": "watchlist_synced", "symbols": symbols})
                elif msg.get("type") == "ping":
                    await ws.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass

    return app
