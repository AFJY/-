#!/usr/bin/env python3
"""Stock AI — paper trading CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console

from stock_ai.config import load_config
from stock_ai.data.fetcher import MarketDataFetcher
from stock_ai.analysis.learner import SignalLearner
from stock_ai.config import resolve_path
from stock_ai.runner import print_status, run_paper_trading, train_all
from stock_ai.trading.backtest import run_backtest

console = Console()


def cmd_train(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    console.print("[bold]训练模型（历史行情学习）...[/]")
    train_all(config)


def cmd_run(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    console.print("[bold]执行模拟盘自动交易...[/]")
    summary = run_paper_trading(config)
    print_status(summary, config)


def cmd_backtest(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    fetcher = MarketDataFetcher()
    learner = SignalLearner(resolve_path(config["runtime"]["model_dir"], config))
    symbol = args.symbol
    days = config["learning"]["lookback_days"]
    df = fetcher.fetch_history(symbol, days=days)
    console.print(f"[bold]回测 {symbol}...[/]")
    result = run_backtest(
        symbol,
        df,
        learner,
        initial_capital=config["trading"]["initial_capital"],
        min_confidence=config["trading"]["min_confidence"],
    )
    console.print(f"初始资金: {result.initial_capital:,.2f}")
    console.print(f"最终权益: {result.final_equity:,.2f}")
    console.print(f"收益率:   {result.return_pct:+.2f}%")
    console.print(f"交易次数: {result.trade_count}")
    console.print(f"最大回撤: {result.max_drawdown_pct:.2f}%")


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn
    from stock_ai.web.server import create_app

    config = load_config(args.config)
    host = config.get("runtime", {}).get("web_host", "0.0.0.0")
    port = int(config.get("runtime", {}).get("web_port", 8765))
    app = create_app(args.config)
    console.print(f"[bold green]Stock AI 仪表盘:[/] http://{host}:{port}")
    console.print(f"同花顺桥接: python bridge/ths_agent.py --server ws://HOST:{port}/ws/ths")
    uvicorn.run(app, host=host, port=port, log_level="info")


def cmd_target(args: argparse.Namespace) -> None:
    from stock_ai.config_manager import set_monthly_target
    pct = set_monthly_target(args.pct, args.config)
    console.print(f"[green]月目标收益率已设为 {pct}%[/]")


def cmd_status(args: argparse.Namespace) -> None:
    import json
    config = load_config(args.config)
    state_file = resolve_path(config["runtime"]["state_file"], config)
    if not state_file.exists():
        console.print("[yellow]尚无模拟盘状态，请先运行: python main.py run[/]")
        return
    data = json.loads(state_file.read_text(encoding="utf-8"))
    console.print_json(data=data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stock AI — 基于公开行情与新闻的模拟盘自动交易"
    )
    parser.add_argument("-c", "--config", default="config.yaml", help="配置文件路径")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("train", help="用历史数据训练/更新 ML 模型").set_defaults(func=cmd_train)
    sub.add_parser("run", help="拉取最新行情并执行一轮模拟交易").set_defaults(func=cmd_run)
    sub.add_parser("status", help="查看当前模拟盘持仓").set_defaults(func=cmd_status)
    sub.add_parser("serve", help="启动实时盯盘 Web 仪表盘 + 自动交易").set_defaults(func=cmd_serve)

    tgt = sub.add_parser("target", help="设置月目标收益率 (%)")
    tgt.add_argument("pct", type=float, help="月目标，例如 8 表示 8%")
    tgt.set_defaults(func=cmd_target)

    bt = sub.add_parser("backtest", help="对单个标的做历史回测")
    bt.add_argument("-s", "--symbol", default="SPY", help="标的代码")
    bt.set_defaults(func=cmd_backtest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
