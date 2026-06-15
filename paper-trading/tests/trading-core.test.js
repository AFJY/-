import assert from "node:assert/strict";
import test from "node:test";

import {
  addCoachMessage,
  applyMarketTick,
  createInitialState,
  getHoldingsRows,
  getOrderEstimate,
  getPortfolioSummary,
  placeOrder,
} from "../src/trading-core.js";

test("buy orders update cash, holdings, and journal", () => {
  const state = createInitialState(new Date("2026-06-15T10:00:00"));
  const next = placeOrder(
    state,
    {
      symbol: "600036.SH",
      side: "buy",
      type: "market",
      quantity: 100,
      reason: "小仓位练习，跌破 34.80 止损",
    },
    new Date("2026-06-15T10:01:00")
  );

  assert.equal(next.orders[0].status, "FILLED");
  assert.equal(next.holdings["600036.SH"].quantity, 100);
  assert.equal(next.journal.length, 1);
  assert.ok(next.cash < state.cash);
});

test("A-share buy orders reject non-lot quantities", () => {
  const state = createInitialState();
  const next = placeOrder(state, {
    symbol: "600036.SH",
    side: "buy",
    type: "market",
    quantity: 99,
    reason: "测试不是一手",
  });

  assert.equal(next.orders[0].status, "REJECTED");
  assert.match(next.orders[0].message, /100 股一手/);
});

test("sell orders realize position changes and cash", () => {
  const state = createInitialState();
  const bought = placeOrder(state, {
    symbol: "600036.SH",
    side: "buy",
    type: "market",
    quantity: 200,
    reason: "建立观察仓",
  });
  const sold = placeOrder(bought, {
    symbol: "600036.SH",
    side: "sell",
    type: "market",
    quantity: 100,
    reason: "卖出一半复盘",
  });
  const rows = getHoldingsRows(sold);

  assert.equal(sold.orders[0].status, "FILLED");
  assert.equal(rows[0].quantity, 100);
  assert.ok(sold.cash > bought.cash);
});

test("limit orders can wait for simulated matching", () => {
  const state = createInitialState();
  const quote = state.watchlist.find((item) => item.symbol === "600036.SH");
  const next = placeOrder(state, {
    symbol: "600036.SH",
    side: "buy",
    type: "limit",
    limitPrice: quote.price - 1,
    quantity: 100,
    reason: "只在回落时买入",
  });

  assert.equal(next.orders[0].status, "PENDING");
  assert.equal(applyMarketTick(next).watchlist.length, state.watchlist.length);
});

test("portfolio estimate includes trading fees", () => {
  const state = createInitialState();
  const estimate = getOrderEstimate(state, {
    symbol: "600036.SH",
    side: "buy",
    type: "market",
    quantity: 100,
  });

  assert.ok(estimate.fees >= 5);
  assert.ok(estimate.total > estimate.gross);
});

test("coach keeps novice risk guidance in the workflow", () => {
  const state = createInitialState();
  const next = addCoachMessage(state, "我想追高买入，可以吗？");

  assert.equal(next.coachMessages.length, 3);
  assert.match(next.coachMessages.at(-1).text, /仓位|退出|观察/);
});

test("summary reflects initial virtual account", () => {
  const state = createInitialState();
  const summary = getPortfolioSummary(state);

  assert.equal(summary.cash, 100000);
  assert.equal(summary.totalAssets, 100000);
  assert.equal(summary.totalReturn, 0);
});
