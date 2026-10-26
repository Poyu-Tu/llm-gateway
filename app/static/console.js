// Demo Console：歡迎頁 → 登入 → 問與答＋調度明細（路由、成本、額度）
// 安全規則（決策書 4.4）：模型的回答是不可信的輸入，一律用 textContent 填字；API Key 只放 sessionStorage
"use strict";

// ---------- 設定 ----------

const KEY_NAME = "llm-gateway-api-key";
const WELCOMED_NAME = "llm-gateway-welcomed";
const GREETING_NAME = "llm-gateway-greeting";

// 問候語停多久進操作頁（毫秒）；歡迎頁不自動跳，等使用者點一下或按任意鍵
const GREETING_MS = 1900;

// 台幣只是讓人有感覺的參考值：匯率寫死、註明日期，不從網路抓（跟 D8 單價不下載同一個原則）
// 2026-10-20 台北外匯收盤 1 美元 = 32.617 新台幣
const TWD_PER_USD = 32.6;

const MAX_CHARS = 4000;

// 路由理由的中文說明（對應 app/router.py 的 reason）
const ROUTE_REASONS = {
  default: "簡單題 → 便宜模型",
  length: "題目超過 300 字 → 強模型",
  keyword: "含分析類關鍵字 → 強模型",
};

// 個資類別的中文（對應 app/audit.py 的 mask_and_detect）
const PII_NAMES = {
  EMAIL: "Email",
  CARD: "信用卡號",
  PHONE: "電話",
  TW_ID: "身分證字號",
};

// 問候語五種，輪流出現（{name} 會換成使用者名稱）
const GREETINGS = [
  "{time}，{name}！今天想問什麼？",
  "歡迎回來，{name}。日月都在軌道上了。",
  "嗨 {name}，今天也讓每一分錢花在刀口上。",
  "{name}，登入成功。問題交給我，帳本我來記。",
  "{name}，準備好了！簡單的交給月亮，難的交給太陽。",
];

// ---------- 狀態（只放記憶體，關掉分頁就沒了） ----------

const state = {
  userId: "",
  limit: 0,
  used: 0,
  replies: [], // 每一則成功回答的明細，點回答就能在右邊再看一次
  session: { count: 0, luna: 0, sol: 0, cost: 0 },
  busy: false,
};

// ---------- 小工具 ----------

function $(id) {
  return document.getElementById(id);
}

// 建一個元素並填好文字；文字一律走 textContent（不會被當成 HTML 執行）
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text !== undefined) {
    node.textContent = text;
  }
  return node;
}

// 建一個 <svg><use href="#i-xxx"></svg> 圖示
function icon(name) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("class", "ic");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS(ns, "use");
  use.setAttribute("href", "#i-" + name);
  svg.appendChild(use);
  return svg;
}

// micro-USD → "US$0.000011"、"US$0.001"、"US$1"：最多 6 位小數，尾巴的 0 拿掉
function usd(microUsd) {
  const text = (microUsd / 1_000_000).toFixed(6).replace(/\.?0+$/, "");
  return "US$" + text;
}

// micro-USD → "≈ NT$0.00036"、"≈ NT$0.29"、"≈ NT$32.6"：不到 1 元留兩位有效數字，看得出差幾倍
function ntd(microUsd) {
  const value = (microUsd / 1_000_000) * TWD_PER_USD;
  if (value === 0) {
    return "≈ NT$0";
  }
  if (value >= 1) {
    return "≈ NT$" + Number(value.toFixed(1)).toString();
  }
  return "≈ NT$" + Number(value.toPrecision(2)).toString();
}

// 依使用者電腦的時區寫出「11/1（日）08:00」
function formatResetTime(date) {
  const days = "日一二三四五六";
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return date.getMonth() + 1 + "/" + date.getDate() + "（" + days[date.getDay()] + "）" + hh + ":" + mm;
}

// 額度在台北時間每月 1 號 00:00 換月（app/quota.py 的 period_of）：有 Retry-After 用伺服器給的秒數，沒有就自己算
const TAIPEI_OFFSET_MS = 8 * 3600 * 1000;

function resetDate(retryAfterSeconds) {
  const seconds = Number(retryAfterSeconds);
  if (seconds > 0) {
    const ms = Date.now() + seconds * 1000;
    return new Date(Math.round(ms / 60000) * 60000);
  }
  // 先把現在換成台北的年月，再算「台北下個月 1 號 00:00」是 UTC 的哪一刻
  const taipei = new Date(Date.now() + TAIPEI_OFFSET_MS);
  return new Date(Date.UTC(taipei.getUTCFullYear(), taipei.getUTCMonth() + 1, 1) - TAIPEI_OFFSET_MS);
}

function timeOfDay() {
  const hour = new Date().getHours();
  if (hour < 11) {
    return "早安";
  }
  if (hour < 18) {
    return "午安";
  }
  return "晚安";
}

// ---------- 換頁 ----------

let currentView = null;

function showView(id) {
  const next = $(id);
  if (currentView === next) {
    return;
  }
  const previous = currentView;
  currentView = next;
  if (!previous) {
    next.hidden = false;
    return;
  }
  previous.classList.add("leaving");
  setTimeout(() => {
    previous.hidden = true;
    previous.classList.remove("leaving");
    next.hidden = false;
  }, 420);
}

// ---------- 第 1 頁：歡迎頁（點一下或按任意鍵才進登入頁） ----------

function startWelcome() {
  showView("view-welcome");
  $("view-welcome").addEventListener("click", leaveWelcome);
  document.addEventListener("keydown", leaveWelcome);
}

function leaveWelcome() {
  $("view-welcome").removeEventListener("click", leaveWelcome);
  document.removeEventListener("keydown", leaveWelcome);
  sessionStorage.setItem(WELCOMED_NAME, "1");
  goToLogin("");
}

// ---------- 第 2 頁：登入 ----------

function goToLogin(message) {
  $("login-form").hidden = false;
  $("greeting").hidden = true;
  $("login-error").textContent = message;
  $("login-button").disabled = false;
  $("login-button").textContent = "驗證並登入";
  showView("view-login");
  setTimeout(() => $("api-key").focus(), 450);
}

// 問 Gateway「我是誰」：只驗 Key、讀額度，不呼叫模型、不花錢
async function fetchMe(key) {
  const response = await fetch("/v1/me", { headers: { Authorization: "Bearer " + key } });
  if (!response.ok) {
    return { ok: false, status: response.status };
  }
  return { ok: true, body: await response.json() };
}

async function login(event) {
  event.preventDefault();
  const key = $("api-key").value.trim();
  if (!key) {
    loginFailed("請先輸入 API Key");
    return;
  }
  $("login-button").disabled = true;
  $("login-button").textContent = "驗證中…";
  let result;
  try {
    result = await fetchMe(key);
  } catch (err) {
    loginFailed("連不到 Gateway，請確認網路");
    return;
  }
  if (!result.ok) {
    loginFailed(result.status === 401 ? "API Key 不正確或已停用" : "服務暫時忙碌，請稍後再試");
    return;
  }
  // 驗證通過才存 Key；輸入框清空，畫面上不再看得到
  sessionStorage.setItem(KEY_NAME, key);
  $("api-key").value = "";
  enterApp(result.body);
  showGreeting();
}

function loginFailed(message) {
  $("login-error").textContent = message;
  $("login-button").disabled = false;
  $("login-button").textContent = "驗證並登入";
  const card = $("login-form");
  card.classList.remove("shake");
  void card.offsetWidth; // 讓搖晃動畫可以重播
  card.classList.add("shake");
}

// 問候語：五種輪流，跟上一次不同
function showGreeting() {
  const last = Number(sessionStorage.getItem(GREETING_NAME) || "-1");
  let index = Math.floor(Math.random() * GREETINGS.length);
  if (index === last) {
    index = (index + 1) % GREETINGS.length;
  }
  sessionStorage.setItem(GREETING_NAME, String(index));
  const text = GREETINGS[index].replace("{time}", timeOfDay()).replace("{name}", state.userId);
  $("greeting-text").textContent = text;
  $("login-form").hidden = true;
  $("greeting").hidden = false;
  setTimeout(() => {
    showView("view-app");
    setTimeout(() => $("message").focus(), 450);
  }, GREETING_MS);
}

function logout() {
  sessionStorage.removeItem(KEY_NAME);
  resetApp();
  goToLogin("已登出");
}

// ---------- 第 3 頁：操作頁 ----------

// 登入成功：角落寫名稱、畫額度條；上一個人的對話與明細全部清掉
function enterApp(me) {
  resetApp();
  state.userId = me.user_id;
  $("user-name").textContent = me.user_id;
  $("user-avatar").textContent = me.user_id.charAt(0).toUpperCase();
  showQuota(me.quota.limit_micro_usd, me.quota.used_micro_usd);
}

// 換人登入：問答、明細、這次登入的累計全部歸零
function resetApp() {
  state.session = { count: 0, luna: 0, sol: 0, cost: 0 };
  showSession();
  clearChat();
}

// 新對話：只清掉畫面上的問答和明細，回到三個範例題；累計和額度不動（錢已經花了）
// 每題本來就各自獨立，清掉畫面不會影響 Gateway 的任何紀錄
function clearChat() {
  state.replies = [];
  const messages = $("messages");
  for (const node of Array.from(messages.children)) {
    if (node.id !== "empty") {
      node.remove();
    }
  }
  $("empty").hidden = false;
  clearDetail();
}

// 等回答的時候不清畫面，不然回答回來會找不到位置
function newChat() {
  if (state.busy) {
    return;
  }
  clearChat();
  $("message").focus();
}

// 額度：剩多少（大字）、條（銀 → 金 → 紅）、已用 / 上限
function showQuota(limit, used) {
  state.limit = limit;
  state.used = used;
  const ratio = limit > 0 ? Math.min(used / limit, 1) : 1;
  const left = Math.max(limit - used, 0);
  const fill = $("quota-fill");
  fill.style.width = (ratio * 100).toFixed(1) + "%";
  fill.classList.toggle("warn", ratio >= 0.8 && ratio < 1);
  fill.classList.toggle("bad", ratio >= 1);
  $("quota-left").textContent = usd(left);
  $("quota-left-ntd").textContent = ntd(left);
  $("quota-left-ntd").hidden = false;
  $("quota-left").parentElement.classList.toggle("bad", ratio >= 1);
  const text = $("quota-text");
  text.classList.toggle("bad", ratio >= 1);
  if (ratio >= 1) {
    text.textContent = "額度已用完，" + formatResetTime(resetDate(null)) + " 恢復（下個月 1 號）";
  } else {
    const percent = used > 0 && ratio < 0.01 ? "不到 1%" : Math.round(ratio * 100) + "%";
    text.textContent = "已用 " + usd(used) + " / 上限 " + usd(limit) + "（" + percent + "）";
  }
}

// 被 429 擋下：條變紅，寫出哪一天幾點恢復、還要多久
function showQuotaExceeded(retryAfterSeconds) {
  showQuota(state.limit, Math.max(state.used, state.limit));
  const reset = resetDate(retryAfterSeconds);
  const hours = Math.max(Math.round((reset.getTime() - Date.now()) / 3600000), 1);
  $("quota-text").textContent = "額度已用完，" + formatResetTime(reset) + " 恢復（下個月 1 號，約 " + hours + " 小時後）";
}

function showSession() {
  const s = state.session;
  $("session-count").textContent = String(s.count);
  $("session-luna").textContent = String(s.luna);
  $("session-sol").textContent = String(s.sol);
  $("session-usd").textContent = usd(s.cost);
  $("session-ntd").textContent = ntd(s.cost);
}

// 調度明細回到「還沒有題目」
function clearDetail() {
  const box = $("route-box");
  box.className = "route idle";
  $("route-icon").setAttribute("href", "#i-orbit");
  $("route-model").textContent = state.session.count > 0 ? "等待下一題" : "等待第一題";
  $("route-reason").textContent = "送出後，這裡會顯示分給哪一顆模型、為什麼";
  $("route-flags").replaceChildren();
  $("usage-of").textContent = "";
  for (const id of ["tok-in", "tok-out", "tok-think", "cost-usd"]) {
    $(id).textContent = "—";
  }
  $("cost-ntd").hidden = true;
}

// 便宜模型＝月亮、強模型＝太陽（降級時實際回答的是便宜模型）
function tierOf(body) {
  return body.route.reason === "default" || body.route.fallback ? "luna" : "sol";
}

// 右邊的調度明細：路由、用量、成本
function showDetail(item) {
  const body = item.body;
  const tier = tierOf(body);
  const box = $("route-box");
  box.className = "route " + tier;
  void box.offsetWidth;
  box.classList.add("flip");
  $("route-icon").setAttribute("href", tier === "luna" ? "#i-moon" : "#i-sun");
  $("route-model").textContent = (tier === "luna" ? "便宜模型 " : "強模型 ") + body.model;
  $("route-reason").textContent = ROUTE_REASONS[body.route.reason] || body.route.reason;

  const flags = $("route-flags");
  flags.replaceChildren();
  if (body.route.fallback) {
    const tag = el("span", "tag warn");
    tag.append(icon("bolt"), el("span", "", "強模型被限流，已降級到便宜模型"));
    flags.appendChild(tag);
  }
  if (body.pii_types && body.pii_types.length > 0) {
    flags.appendChild(piiTag(body.pii_types));
  }

  $("usage-of").textContent = "第 " + item.number + " 題";
  $("tok-in").textContent = body.usage.input_tokens.toLocaleString();
  $("tok-out").textContent = body.usage.output_tokens.toLocaleString();
  $("tok-think").textContent = body.usage.reasoning_tokens.toLocaleString();
  $("cost-usd").textContent = usd(body.cost_micro_usd);
  $("cost-ntd").textContent = ntd(body.cost_micro_usd);
  $("cost-ntd").hidden = false;

  for (const node of document.querySelectorAll(".msg.selected")) {
    node.classList.remove("selected");
  }
  item.node.classList.add("selected");
}

function piiTag(types) {
  const names = types.map((t) => PII_NAMES[t] || t).join("、");
  const tag = el("span", "tag pii");
  tag.append(icon("shield"), el("span", "", "已遮罩 " + names + " 才送出"));
  return tag;
}

// ---------- 對話 ----------

function scrollToBottom() {
  const messages = $("messages");
  messages.scrollTop = messages.scrollHeight;
}

function addUserMessage(text) {
  $("empty").hidden = true;
  const row = el("div", "msg user");
  row.appendChild(el("div", "bubble", text));
  $("messages").appendChild(row);
  scrollToBottom();
}

// 等待中的那一則：轉圈＋已經等了幾秒（強模型可能要 30 秒）
function addPending() {
  const row = el("div", "msg bot pending");
  const avatar = el("span", "bot-avatar");
  avatar.appendChild(icon("orbit"));
  const bubble = el("div", "bubble");
  const dots = el("span", "dots");
  dots.append(el("i"), el("i"), el("i"));
  const label = el("span", "", "Gateway 調度中… 0 秒");
  bubble.append(dots, label);
  row.append(avatar, bubble);
  $("messages").appendChild(row);
  scrollToBottom();
  const started = Date.now();
  const timer = setInterval(() => {
    label.textContent = "Gateway 調度中… " + Math.floor((Date.now() - started) / 1000) + " 秒";
  }, 1000);
  return {
    remove() {
      clearInterval(timer);
      row.remove();
    },
  };
}

function addBotReply(body) {
  const tier = tierOf(body);
  const row = el("div", "msg bot " + tier);
  const avatar = el("span", "bot-avatar");
  avatar.appendChild(icon(tier === "luna" ? "moon" : "sun"));
  const bubble = el("div", "bubble", body.reply === "" ? "（模型這次沒有給出文字）" : body.reply);

  const meta = el("div", "meta");
  const model = el("span", "tag " + tier);
  model.append(icon(tier === "luna" ? "moon" : "sun"), el("span", "", body.model));
  meta.appendChild(model);
  const cost = el("span", "tag");
  cost.append(el("span", "num money", usd(body.cost_micro_usd)), el("span", "muted", ntd(body.cost_micro_usd)));
  meta.appendChild(cost);
  if (body.pii_types && body.pii_types.length > 0) {
    meta.appendChild(piiTag(body.pii_types));
  }
  bubble.appendChild(meta);

  row.append(avatar, bubble);
  $("messages").appendChild(row);

  // 題號跟著「這次登入」數，按了新對話也不會重新從 1 開始
  const item = { number: state.session.count + 1, body: body, node: row };
  state.replies.push(item);
  bubble.addEventListener("click", () => showDetail(item));
  scrollToBottom();
  return item;
}

function addErrorMessage(text) {
  const row = el("div", "msg bot err");
  const avatar = el("span", "bot-avatar");
  avatar.appendChild(icon("bolt"));
  row.append(avatar, el("div", "bubble", text));
  $("messages").appendChild(row);
  scrollToBottom();
}

// 狀態碼 → 使用者看得懂的中文（不顯示伺服器內部細節）
function errorText(status, retryAfter) {
  if (status === 429) {
    return "這個月的額度用完了，" + formatResetTime(resetDate(retryAfter)) + " 恢復（下個月 1 號）。";
  }
  if (status === 503) {
    const seconds = Number(retryAfter);
    return seconds > 0 ? "服務暫時忙碌，約 " + seconds + " 秒後再試。" : "服務暫時忙碌，請稍後再試。";
  }
  if (status === 502) {
    return "模型暫時無法回答，請稍後再試。";
  }
  if (status === 422) {
    return "問題的格式不對（要 1～" + MAX_CHARS + " 字）。";
  }
  return "發生錯誤（HTTP " + status + "），請聯絡管理員。";
}

async function send() {
  const input = $("message");
  const message = input.value.trim();
  const key = sessionStorage.getItem(KEY_NAME);
  if (!message || state.busy) {
    return;
  }
  if (!key) {
    goToLogin("請重新登入");
    return;
  }
  // 送出就清空輸入框，問題留在對話裡；等回答時不能重複送出
  state.busy = true;
  $("send").disabled = true;
  input.value = "";
  updateComposer();
  addUserMessage(message);
  const pending = addPending();
  try {
    const response = await fetch("/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + key },
      body: JSON.stringify({ message: message }),
    });
    pending.remove();
    if (response.status === 401) {
      sessionStorage.removeItem(KEY_NAME);
      resetApp();
      goToLogin("API Key 已失效，請重新登入");
      return;
    }
    if (!response.ok) {
      const retryAfter = response.headers.get("Retry-After");
      addErrorMessage(errorText(response.status, retryAfter));
      if (response.status === 429) {
        showQuotaExceeded(retryAfter);
      }
      return;
    }
    const body = await response.json();
    const item = addBotReply(body);
    showDetail(item);
    showQuota(body.quota.limit_micro_usd, body.quota.used_micro_usd);
    state.session.count += 1;
    state.session[tierOf(body)] += 1;
    state.session.cost += body.cost_micro_usd;
    showSession();
  } catch (err) {
    pending.remove();
    addErrorMessage("連不到 Gateway，請確認網路後再試。");
  } finally {
    state.busy = false;
    $("send").disabled = false;
    input.focus();
  }
}

// 輸入框跟著內容長高；字數快滿時變色
function updateComposer() {
  const input = $("message");
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 180) + "px";
  // 還沒長到上限就不顯示捲軸（不然一行字也會出現上下箭頭）
  input.style.overflowY = input.scrollHeight > 180 ? "auto" : "hidden";
  const count = $("char-count");
  count.textContent = input.value.length + " / " + MAX_CHARS;
  count.classList.toggle("near", input.value.length >= MAX_CHARS * 0.9);
}

// Enter 送出、Shift+Enter 換行；注音選字時按的 Enter 不算（isComposing）
function onMessageKey(event) {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    send();
  }
}

// 範例題：點了只填進輸入框，讓使用者看過再送
function useExample(event) {
  const input = $("message");
  input.value = event.currentTarget.dataset.text;
  updateComposer();
  input.focus();
}

// ---------- 啟動 ----------

// 分頁裡已經有 Key（例如按了重新整理）：直接驗證進操作頁，不再播歡迎頁和問候
async function resume(key) {
  try {
    const result = await fetchMe(key);
    if (result.ok) {
      enterApp(result.body);
      showView("view-app");
      return;
    }
    sessionStorage.removeItem(KEY_NAME);
    goToLogin(result.status === 401 ? "API Key 已失效，請重新登入" : "服務暫時忙碌，請稍後再試");
  } catch (err) {
    goToLogin("連不到 Gateway，請確認網路");
  }
}

// 網頁載入完成後才綁按鈕（HTML 裡不寫 onclick，CSP 才能禁止內嵌程式）
document.addEventListener("DOMContentLoaded", () => {
  $("login-form").addEventListener("submit", login);
  $("logout").addEventListener("click", logout);
  $("home").addEventListener("click", newChat);
  $("new-chat").addEventListener("click", newChat);
  $("send").addEventListener("click", send);
  $("message").addEventListener("keydown", onMessageKey);
  $("message").addEventListener("input", updateComposer);
  for (const button of document.querySelectorAll(".example")) {
    button.addEventListener("click", useExample);
  }

  const key = sessionStorage.getItem(KEY_NAME);
  if (key) {
    resume(key);
  } else if (sessionStorage.getItem(WELCOMED_NAME)) {
    goToLogin("");
  } else {
    startWelcome();
  }
});
