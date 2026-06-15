import {
  CNY,
  addCoachMessage,
  applyMarketTick,
  createInitialState,
  getHoldingsRows,
  getOrderEstimate,
  getPortfolioSummary,
  placeOrder,
} from "./trading-core.js";

const STORAGE_KEY = "ashare-paper-trading-state-v1";
const state = loadState();
const elements = {};

document.addEventListener("DOMContentLoaded", () => {
  bindElements();
  bindEvents();
  render();
  window.setInterval(() => {
    Object.assign(state, applyMarketTick(state));
    persist();
    renderMarketOnly();
  }, 2800);
});

function bindElements() {
  for (const element of document.querySelectorAll("[data-ref]")) {
    elements[element.dataset.ref] = element;
  }
}

function bindEvents() {
  elements.resetButton.addEventListener("click", () => {
    const fresh = createInitialState();
    Object.keys(state).forEach((key) => delete state[key]);
    Object.assign(state, fresh);
    persist();
    render();
  });

  elements.orderForm.addEventListener("input", renderEstimate);
  elements.symbol.addEventListener("change", () => {
    state.selectedSymbol = elements.symbol.value;
    persist();
    renderMarketOnly();
  });
  elements.orderForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(elements.orderForm);
    const symbol = form.get("symbol");
    const next = placeOrder(state, {
      symbol,
      side: form.get("side"),
      type: form.get("type"),
      limitPrice: form.get("limitPrice"),
      quantity: form.get("quantity"),
      reason: form.get("reason"),
    });

    Object.assign(state, next, { selectedSymbol: symbol });
    persist();
    elements.reason.value = "";
    render();
  });

  elements.coachForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(elements.coachForm);
    Object.assign(state, addCoachMessage(state, form.get("coachInput")));
    persist();
    elements.coachInput.value = "";
    renderCoach();
  });

  for (const button of document.querySelectorAll("[data-nav-target]")) {
    button.addEventListener("click", () => {
      document
        .querySelector(button.dataset.navTarget)
        .scrollIntoView({ behavior: "smooth", block: "start" });
      document
        .querySelectorAll("[data-nav-target]")
        .forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
    });
  }
}

function render() {
  renderMarketOnly();
  renderOrderSymbols();
  renderHoldings();
  renderOrders();
  renderJournal();
  renderCoach();
  renderEstimate();
}

function renderMarketOnly() {
  renderSummary();
  renderWatchlist();
  renderMarketStatus();
}

function renderSummary() {
  const summary = getPortfolioSummary(state);
  elements.totalAssets.textContent = CNY.format(summary.totalAssets);
  elements.cash.textContent = CNY.format(summary.cash);
  elements.marketValue.textContent = CNY.format(summary.marketValue);
  elements.totalReturn.textContent = `${CNY.format(summary.totalReturn)} (${formatPct(
    summary.totalReturnPct
  )})`;
  setTone(elements.totalReturn, summary.totalReturn);
}

function renderMarketStatus() {
  elements.marketStatus.textContent = state.market.label;
  elements.marketHint.textContent = state.market.next;
  elements.marketTime.textContent = new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date());
}

function renderWatchlist() {
  elements.watchlist.innerHTML = state.watchlist
    .map(
      (quote) => `
        <button class="quote-card ${quote.symbol === state.selectedSymbol ? "selected" : ""}" data-symbol="${quote.symbol}">
          <span>
            <strong>${quote.name}</strong>
            <small>${quote.symbol} · ${quote.sector}</small>
          </span>
          <span class="quote-price ${quote.change >= 0 ? "up" : "down"}">
            ${quote.price.toFixed(2)}
            <small>${formatPct(quote.changePct)}</small>
          </span>
        </button>
      `
    )
    .join("");

  for (const card of elements.watchlist.querySelectorAll("[data-symbol]")) {
    card.addEventListener("click", () => {
      state.selectedSymbol = card.dataset.symbol;
      elements.symbol.value = state.selectedSymbol;
      persist();
      render();
    });
  }
}

function renderOrderSymbols() {
  const selected = state.selectedSymbol;
  elements.symbol.innerHTML = state.watchlist
    .map(
      (quote) =>
        `<option value="${quote.symbol}" ${quote.symbol === selected ? "selected" : ""}>${quote.name} ${quote.symbol}</option>`
    )
    .join("");
}

function renderEstimate() {
  const form = new FormData(elements.orderForm);
  const estimate = getOrderEstimate(state, {
    symbol: form.get("symbol"),
    side: form.get("side"),
    type: form.get("type"),
    limitPrice: form.get("limitPrice"),
    quantity: form.get("quantity"),
  });

  elements.estimate.innerHTML = `
    <span>参考价：${estimate.price.toFixed(2)}</span>
    <span>成交额：${CNY.format(estimate.gross)}</span>
    <span>费用：${CNY.format(estimate.fees)}</span>
    <strong>预计${form.get("side") === "sell" ? "到账" : "占用"}：${CNY.format(estimate.total)}</strong>
  `;
}

function renderHoldings() {
  const rows = getHoldingsRows(state);
  elements.holdings.innerHTML = rows.length
    ? rows
        .map(
          (row) => `
            <tr>
              <td>${row.name}<small>${row.symbol}</small></td>
              <td>${row.quantity}</td>
              <td>${row.avgCost.toFixed(2)}</td>
              <td>${row.price.toFixed(2)}</td>
              <td>${CNY.format(row.marketValue)}</td>
              <td class="${row.pnl >= 0 ? "up" : "down"}">${CNY.format(row.pnl)}<small>${formatPct(row.pnlPct)}</small></td>
            </tr>
          `
        )
        .join("")
    : `<tr><td colspan="6" class="empty">暂无持仓，先用小仓位练习第一笔模拟交易。</td></tr>`;
}

function renderOrders() {
  elements.orders.innerHTML = state.orders.length
    ? state.orders
        .slice(0, 8)
        .map(
          (order) => `
            <li>
              <span>
                <strong>${order.side === "buy" ? "买入" : "卖出"} ${order.name}</strong>
                <small>${order.time} · ${order.type === "market" ? "市价" : `限价 ${order.limitPrice}`}</small>
              </span>
              <em class="${order.status.toLowerCase()}">${statusText(order.status)}</em>
            </li>
          `
        )
        .join("")
    : `<li class="empty">订单列表为空。</li>`;
}

function renderJournal() {
  elements.journal.innerHTML = state.journal.length
    ? state.journal
        .map(
          (entry) => `
            <article class="journal-entry">
              <time>${entry.time}</time>
              <h4>${entry.title}</h4>
              <p>${entry.detail}</p>
            </article>
          `
        )
        .join("")
    : `<p class="empty">交易日志会自动记录每笔成交理由，帮助你复盘习惯。</p>`;
}

function renderCoach() {
  elements.coachMessages.innerHTML = state.coachMessages
    .map(
      (message) => `
        <div class="message ${message.role === "coach" ? "coach-message" : "user-message"}">
          <small>${message.role === "coach" ? "交易教练" : "我"} · ${message.time}</small>
          <p>${message.text}</p>
        </div>
      `
    )
    .join("");
  elements.coachMessages.scrollTop = elements.coachMessages.scrollHeight;
}

function loadState() {
  const fresh = createInitialState();
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (!saved) {
      return fresh;
    }

    return {
      ...fresh,
      ...JSON.parse(saved),
    };
  } catch {
    return fresh;
  }
}

function persist() {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function formatPct(value) {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${(value * 100).toFixed(2)}%`;
}

function statusText(status) {
  return {
    FILLED: "已成交",
    PENDING: "待成交",
    REJECTED: "已拒绝",
  }[status];
}

function setTone(element, value) {
  element.classList.toggle("up", value >= 0);
  element.classList.toggle("down", value < 0);
}
