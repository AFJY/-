export const CNY = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
  maximumFractionDigits: 2,
});

export const DEFAULT_WATCHLIST = [
  {
    symbol: "600519.SH",
    name: "贵州茅台",
    sector: "消费",
    price: 1468.5,
    previousClose: 1452.88,
    volume: 12800,
  },
  {
    symbol: "300750.SZ",
    name: "宁德时代",
    sector: "新能源",
    price: 207.32,
    previousClose: 204.2,
    volume: 84300,
  },
  {
    symbol: "002594.SZ",
    name: "比亚迪",
    sector: "汽车",
    price: 229.7,
    previousClose: 232.1,
    volume: 56200,
  },
  {
    symbol: "600036.SH",
    name: "招商银行",
    sector: "金融",
    price: 35.41,
    previousClose: 35.02,
    volume: 189600,
  },
  {
    symbol: "688981.SH",
    name: "中芯国际",
    sector: "半导体",
    price: 48.88,
    previousClose: 47.95,
    volume: 97600,
  },
  {
    symbol: "601318.SH",
    name: "中国平安",
    sector: "保险",
    price: 46.26,
    previousClose: 45.82,
    volume: 132400,
  },
  {
    symbol: "000858.SZ",
    name: "五粮液",
    sector: "消费",
    price: 128.66,
    previousClose: 130.1,
    volume: 73400,
  },
  {
    symbol: "000001.SZ",
    name: "平安银行",
    sector: "金融",
    price: 10.48,
    previousClose: 10.39,
    volume: 224500,
  },
  {
    symbol: "600900.SH",
    name: "长江电力",
    sector: "公用事业",
    price: 29.31,
    previousClose: 29.16,
    volume: 168900,
  },
  {
    symbol: "300059.SZ",
    name: "东方财富",
    sector: "金融科技",
    price: 14.52,
    previousClose: 14.19,
    volume: 336800,
  },
];

const MARKET_OPEN_MINUTE = 9 * 60 + 30;
const MARKET_CLOSE_MINUTE = 15 * 60;

export function createInitialState(now = new Date()) {
  return {
    cash: 100000,
    initialCash: 100000,
    holdings: {},
    orders: [],
    journal: [],
    coachMessages: [
      {
        role: "coach",
        text: "欢迎进入新股民模拟盘。先观察，再小仓位试单；每次下单都写下理由和止损线。",
        time: formatTime(now),
      },
    ],
    selectedSymbol: DEFAULT_WATCHLIST[0].symbol,
    searchQuery: "",
    watchlist: DEFAULT_WATCHLIST.map((quote, index) =>
      enrichQuote({ ...quote }, index, 0)
    ),
    tick: 0,
    market: getMarketStatus(now),
  };
}

export function getMarketStatus(now = new Date()) {
  const minutes = now.getHours() * 60 + now.getMinutes();
  const isWeekday = now.getDay() > 0 && now.getDay() < 6;
  const morning = minutes >= MARKET_OPEN_MINUTE && minutes <= 11 * 60 + 30;
  const afternoon = minutes >= 13 * 60 && minutes <= MARKET_CLOSE_MINUTE;
  const isOpen = isWeekday && (morning || afternoon);

  return {
    isOpen,
    label: isOpen ? "A股交易时段" : "模拟盘运行中",
    next: isOpen ? "按实时节奏刷新模拟行情" : "非交易时段使用教学行情",
  };
}

export function applyMarketTick(state, now = new Date()) {
  const tick = state.tick + 1;
  const watchlist = state.watchlist.map((quote, index) =>
    enrichQuote({ ...quote }, index, tick)
  );
  const nextState = {
    ...state,
    tick,
    watchlist,
    market: getMarketStatus(now),
  };

  return fillPendingOrders(nextState, now);
}

export function placeOrder(state, draft, now = new Date()) {
  const quote = findQuote(state, draft.symbol);
  const quantity = Number(draft.quantity);
  const side = draft.side === "sell" ? "sell" : "buy";
  const type = draft.type === "limit" ? "limit" : "market";
  const limitPrice =
    type === "limit" && draft.limitPrice !== "" ? Number(draft.limitPrice) : null;
  const reason = String(draft.reason || "").trim();
  const validationError = validateOrder(state, quote, {
    side,
    quantity,
    type,
    limitPrice,
  });

  if (validationError) {
    return appendOrder(state, buildOrder({
      quote,
      side,
      type,
      limitPrice,
      quantity,
      reason,
      status: "REJECTED",
      message: validationError,
      now,
    }));
  }

  const executable = isExecutable(side, type, limitPrice, quote.price);
  const order = buildOrder({
    quote,
    side,
    type,
    limitPrice,
    quantity,
    reason,
    status: executable ? "FILLED" : "PENDING",
    message: executable ? "已成交" : "限价未触发，等待模拟撮合",
    now,
  });

  if (!executable) {
    return appendOrder(state, order);
  }

  return executeOrder(state, order, quote.price, now);
}

export function getPortfolioSummary(state) {
  const marketValue = Object.values(state.holdings).reduce((sum, holding) => {
    const quote = findQuote(state, holding.symbol);
    return sum + holding.quantity * quote.price;
  }, 0);
  const totalAssets = state.cash + marketValue;
  const totalReturn = totalAssets - state.initialCash;

  return {
    cash: state.cash,
    marketValue,
    totalAssets,
    totalReturn,
    totalReturnPct: totalReturn / state.initialCash,
  };
}

export function getHoldingsRows(state) {
  return Object.values(state.holdings)
    .filter((holding) => holding.quantity > 0)
    .map((holding) => {
      const quote = findQuote(state, holding.symbol);
      const marketValue = holding.quantity * quote.price;
      const cost = holding.quantity * holding.avgCost;
      const pnl = marketValue - cost;

      return {
        ...holding,
        name: quote.name,
        price: quote.price,
        marketValue,
        pnl,
        pnlPct: cost === 0 ? 0 : pnl / cost,
      };
    });
}

export function getOrderEstimate(state, draft) {
  const quote = findQuote(state, draft.symbol);
  const quantity = Number(draft.quantity || 0);
  const side = draft.side === "sell" ? "sell" : "buy";
  const price =
    draft.type === "limit" && Number(draft.limitPrice) > 0
      ? Number(draft.limitPrice)
      : quote.price;

  if (!quantity || quantity <= 0) {
    return {
      price,
      gross: 0,
      fees: 0,
      total: 0,
    };
  }

  const fees = calculateFees(side, price, quantity);
  const gross = price * quantity;

  return {
    price,
    gross,
    fees,
    total: side === "buy" ? gross + fees : gross - fees,
  };
}

export function getSelectedQuote(state) {
  return findQuote(state, state.selectedSymbol) || state.watchlist[0];
}

export function searchStocks(quotes, query) {
  const normalized = String(query || "").trim().toLowerCase();
  if (!normalized) {
    return quotes;
  }

  return quotes.filter((quote) => {
    const code = quote.symbol.toLowerCase();
    const compactCode = code.replace(".", "");
    return (
      quote.name.toLowerCase().includes(normalized) ||
      quote.sector.toLowerCase().includes(normalized) ||
      code.includes(normalized) ||
      compactCode.includes(normalized)
    );
  });
}

export function getQuoteLinks(symbol) {
  const code = toProviderCode(symbol);
  return {
    eastmoney: `https://quote.eastmoney.com/${code}.html`,
    sina: `https://finance.sina.com.cn/realstock/company/${code}/nc.shtml`,
  };
}

export function getIntradaySeries(quote, tick = 0, points = 64) {
  const safePoints = Math.max(8, points);
  const open = quote.previousClose;
  const amplitude = Math.max(open * 0.018, 0.08);

  return Array.from({ length: safePoints }, (_, index) => {
    const progress = index / (safePoints - 1);
    const wave =
      Math.sin((index + tick) * 0.37) * amplitude +
      Math.cos((index + tick) * 0.13) * amplitude * 0.45;
    const trend = (quote.price - open) * progress;
    const price = roundMoney(open + trend + wave * (0.35 + progress * 0.65));

    return {
      time: formatIntradayTime(progress),
      price,
      volume: Math.round(quote.volume * (0.4 + Math.abs(wave / amplitude)) / safePoints),
    };
  });
}

export function addCoachMessage(state, text, now = new Date()) {
  const userText = String(text || "").trim();
  if (!userText) {
    return state;
  }

  const reply = getCoachReply(state, userText);

  return {
    ...state,
    coachMessages: [
      ...state.coachMessages,
      { role: "user", text: userText, time: formatTime(now) },
      { role: "coach", text: reply, time: formatTime(now) },
    ],
  };
}

export function getCoachReply(state, userText) {
  const summary = getPortfolioSummary(state);
  const lastOrder = state.orders[0];
  const lower = userText.toLowerCase();

  if (lower.includes("止损") || userText.includes("亏")) {
    return "新股民先把止损写在买入前：单笔亏损尽量控制在总资产的 1%-2%，到了价格就执行，不临场改规则。";
  }

  if (lower.includes("买") || lower.includes("追")) {
    return "买入前先回答三件事：趋势是否明确、仓位是否小于总资产 20%、如果错了在哪里退出。没有答案就先观察。";
  }

  if (lower.includes("卖") || lower.includes("止盈")) {
    return "卖出可以分批：一部分锁定利润，一部分按移动止损跟随。重点是让规则决定动作，而不是让情绪决定动作。";
  }

  if (lastOrder?.status === "REJECTED") {
    return `刚才订单被拒绝：${lastOrder.message}。先修正数量、资金或持仓，再重新下单。`;
  }

  if (summary.totalReturn < 0) {
    return "当前模拟账户处于回撤。先降低下单频率，复盘最近三笔交易理由，找出是否存在追涨或无计划补仓。";
  }

  return "我会按新股民训练模式陪你复盘。你可以告诉我想买哪只 A 股、买入理由、预期持有时间和能接受的最大亏损。";
}

function fillPendingOrders(state, now) {
  let nextState = { ...state, orders: [] };
  const remainingOrders = [];

  for (const order of state.orders) {
    if (order.status !== "PENDING") {
      remainingOrders.push(order);
      continue;
    }

    const quote = findQuote(state, order.symbol);
    if (isExecutable(order.side, order.type, order.limitPrice, quote.price)) {
      nextState = executeOrder(
        { ...nextState, orders: remainingOrders },
        { ...order, status: "FILLED", message: "模拟行情触发限价成交" },
        quote.price,
        now
      );
      remainingOrders.splice(0, remainingOrders.length, ...nextState.orders);
    } else {
      remainingOrders.push(order);
    }
  }

  return { ...nextState, orders: remainingOrders };
}

function executeOrder(state, order, fillPrice, now) {
  const fees = calculateFees(order.side, fillPrice, order.quantity);
  const gross = fillPrice * order.quantity;
  const filledOrder = {
    ...order,
    fillPrice,
    fees,
    gross,
    total: order.side === "buy" ? gross + fees : gross - fees,
    status: "FILLED",
    message: order.message || "已成交",
    time: formatTime(now),
  };

  if (order.side === "buy") {
    const holding = state.holdings[order.symbol] || {
      symbol: order.symbol,
      quantity: 0,
      avgCost: 0,
    };
    const newQuantity = holding.quantity + order.quantity;
    const newCost = holding.avgCost * holding.quantity + gross + fees;

    return {
      ...state,
      cash: roundMoney(state.cash - gross - fees),
      holdings: {
        ...state.holdings,
        [order.symbol]: {
          ...holding,
          quantity: newQuantity,
          avgCost: roundMoney(newCost / newQuantity),
        },
      },
      orders: [filledOrder, ...state.orders],
      journal: [buildJournalEntry(filledOrder), ...state.journal],
    };
  }

  const holding = state.holdings[order.symbol];
  const remainingQuantity = holding.quantity - order.quantity;
  const realizedPnl = gross - fees - holding.avgCost * order.quantity;
  const holdings = {
    ...state.holdings,
    [order.symbol]: {
      ...holding,
      quantity: remainingQuantity,
    },
  };

  if (remainingQuantity === 0) {
    delete holdings[order.symbol];
  }

  return {
    ...state,
    cash: roundMoney(state.cash + gross - fees),
    holdings,
    orders: [{ ...filledOrder, realizedPnl }, ...state.orders],
    journal: [
      buildJournalEntry({ ...filledOrder, realizedPnl }),
      ...state.journal,
    ],
  };
}

function buildOrder({
  quote,
  side,
  type,
  limitPrice,
  quantity,
  reason,
  status,
  message,
  now,
}) {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    symbol: quote.symbol,
    name: quote.name,
    side,
    type,
    limitPrice,
    quantity,
    reason,
    status,
    message,
    time: formatTime(now),
  };
}

function appendOrder(state, order) {
  return {
    ...state,
    orders: [order, ...state.orders],
  };
}

function buildJournalEntry(order) {
  const sideText = order.side === "buy" ? "买入" : "卖出";
  const reason = order.reason || "未填写交易理由";

  return {
    id: order.id,
    title: `${sideText} ${order.name} ${order.quantity} 股`,
    detail: `${reason}；成交价 ${order.fillPrice.toFixed(2)}，费用 ${CNY.format(order.fees)}。`,
    time: order.time,
  };
}

function validateOrder(state, quote, order) {
  if (!quote) {
    return "未找到股票代码";
  }

  if (!Number.isInteger(order.quantity) || order.quantity <= 0) {
    return "数量必须是正整数";
  }

  if (order.side === "buy" && order.quantity % 100 !== 0) {
    return "A股买入按 100 股一手提交";
  }

  if (order.type === "limit" && (!order.limitPrice || order.limitPrice <= 0)) {
    return "限价单必须填写有效价格";
  }

  const estimate = getOrderEstimate(state, {
    symbol: quote.symbol,
    side: order.side,
    type: order.type,
    limitPrice: order.limitPrice,
    quantity: order.quantity,
  });

  if (order.side === "buy" && estimate.total > state.cash) {
    return "可用现金不足";
  }

  if (order.side === "sell") {
    const holding = state.holdings[quote.symbol];
    if (!holding || holding.quantity < order.quantity) {
      return "持仓不足";
    }
  }

  return "";
}

function calculateFees(side, price, quantity) {
  const gross = price * quantity;
  const commission = Math.max(gross * 0.0003, 5);
  const stampDuty = side === "sell" ? gross * 0.0005 : 0;
  const transferFee = gross * 0.00001;

  return roundMoney(commission + stampDuty + transferFee);
}

function isExecutable(side, type, limitPrice, marketPrice) {
  if (type === "market") {
    return true;
  }

  return side === "buy" ? limitPrice >= marketPrice : limitPrice <= marketPrice;
}

function toProviderCode(symbol) {
  const [code, market] = symbol.split(".");
  return `${market === "SH" ? "sh" : "sz"}${code}`;
}

function formatIntradayTime(progress) {
  const tradingMinutes = 240;
  let minuteOffset = Math.round(progress * tradingMinutes);
  let minutes = 9 * 60 + 30 + minuteOffset;

  if (minuteOffset > 120) {
    minutes = 13 * 60 + (minuteOffset - 120);
  }

  const hour = Math.floor(minutes / 60);
  const minute = minutes % 60;
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function enrichQuote(quote, index, tick) {
  const wave = Math.sin((tick + 1) * (index + 1) * 0.53) * 0.012;
  const drift = Math.cos((tick + index + 2) * 0.31) * 0.004;
  const nextPrice = Math.max(0.01, quote.price * (1 + wave + drift));
  const price = roundMoney(nextPrice);
  const change = price - quote.previousClose;

  return {
    ...quote,
    price,
    change,
    changePct: change / quote.previousClose,
    dayHigh: Math.max(quote.dayHigh || price, price),
    dayLow: Math.min(quote.dayLow || price, price),
    volume: Math.round(quote.volume * (1 + Math.abs(wave) * 3)),
  };
}

function findQuote(state, symbol) {
  return state.watchlist.find((quote) => quote.symbol === symbol);
}

function roundMoney(value) {
  return Math.round(value * 100) / 100;
}

function formatTime(now) {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(now);
}
