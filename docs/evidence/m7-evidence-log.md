# M7 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID；個人帳號名稱（含終端機提示字元與路徑中的使用者資料夾名稱，一律寫成 `<user>`）；API Key 本身。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`（檔名以 `m7-` 開頭），日誌另存於 `docs/logs/`。
> E 編號接續 `m6-evidence-log.md`（E145～E154），從 E155 開始。M6 的上雲那一段若在 M7 之後做，照樣記回 `m6-evidence-log.md`，編號繼續往下排。
> 紀錄日期：2026-10-27 建立（E155～E156）

---

## 紀錄規則（沿用 M6）

| # | 東西 | 規則 |
|---|---|---|
| 1 | 證據紀錄 | 本檔；每完成一組步驟就更新 |
| 2 | 里程碑報告 | 整關驗證通過後寫 `docs/milestones/m7-report.md`，格式同 M5；只向本人確認花費時間與實際花費 |
| 3 | 決策書 | M6、M7 結案時一起出新版；期間的新定案先記在本檔 |
| 4 | 截圖、日誌、錄影 | 收到就改名、遮蔽；API Key 不能出現在畫面（agent 用 `getpass` 問 Key） |
| 5 | 存放 | 所有文字檔也存一份到 Project |
| 6 | 收錄範圍 | 只收與專題本身有關的內容 |
| 7 | 推送 | 一律開分支、開 PR、三個必要檢查（`Tests`、`Image scan`、`Config scan`）綠了才合併；commit 英文、PR 中文，都不附署名 |

---

## E155. M7 開工定案：五項（2026-10-27 15:39～15:50，公司電腦，只有定案）

**依據：** 決策書 v2.11.1 的 8.1、8.2 的 M7、7.9「原生工具呼叫」、D38、D42、D66；`app/router.py`、`app/config.toml`、`app/audit.py`、`app/main.py`、`scripts/seed.py`、`compose.yaml`（`main` = `305fe54`）。

**開工時機（本人 10/27 15:39）：** M6 剩上雲一次（本人當晚做），**M7 先開工**。D66 的「M7 最後再做」改為「M6 上雲與 M7 交錯」；8.2 的開工條件「M6 在 10/30 前完成」預期成立。

| # | 題目 | 定案 | 沒選的 | 為什麼 |
|---|---|---|---|---|
| 1 | 工具與任務 | **A+**：三個本機工具 `route(問題)`（用 Gateway 自己的 `choose_model()`，先 `mask()`）、`price(模型)`（讀 `config.toml`）、`calc(算式)`（不用 `eval`，`ast` 只准數字與加減乘除、括號、負號）；任務「『幫我設計一個備份架構』這題會走哪個模型？50 輸入、800 輸出 token 要花多少美元？改走便宜模型貴幾倍？」約 6 步 | A（只有 price＋calc，約 4 步）；B（匯率換算，跟治理無關）；C（呼叫 `/v1/me` 查自己的額度，答案不穩、驗收難寫） | 本人要「更複雜一點」；跟專案的節費故事接得上；數字最多 8 碼不會被遮罩；只讀本機檔案。代價：粗估 6～7 小時，超過 D42 的 6 小時上限 |
| 2 | 兩層煞車 | agent 自己：**最多 8 步、預算 30,000 micro-USD（US$0.03）**，0 代表不限；送出前檢查，累計回應的 `cost_micro_usd`。Gateway：月額度用完 429。停止理由四種：`final`、`max_steps`、`budget`、`quota`（其他錯誤 `http_<狀態碼>`） | 6 步、US$0.02 | 任務約 6 步＋2 步讓模型修正；每步走 sol 粗估 2,000～4,000 micro-USD。弱點：跟 Gateway 一樣「呼叫前檢查、不預扣」，最後一步可能超出預算 |
| 3 | 驗收②的帳號 | **新增 carol，月額度 10,000**（`scripts/seed.py` 的 `DEMO_USERS` 加一行） | alice（1,000，一步就超、第二步 429） | 看得到「跑了幾步才被擋」；Console 的額度那章仍用 alice |
| 4 | 檔案怎麼切 | **`scripts/agent_tools.py`**（`tool_route()`、`tool_price()`、`evaluate()`、`safe_calc()`、`run_tool()`）＋**`scripts/agent_demo.py`**（`parse_reply()`、`build_message()`、`post_chat()`、`run_agent()`、`main()`）；`run_agent()` 的「送出」由參數傳入，測試換成照劇本回答的假 Gateway | 資料夾 `scripts/agent_demo/` 拆三個檔 | 跟現有 `scripts/` 單檔風格一致；工具和迴圈分開，測迴圈不用真的打 Gateway |
| 5 | HTTP 用什麼 | **Python 內建 `urllib`**；網址寫死 `http://127.0.0.1:8000/v1/chat`；Key 用 `getpass` 問 | `httpx` | `httpx` 只是 `openai` 間接帶進來的，正式依賴清單沒有；網址寫死避免被指到別處；Key 不進命令歷史、錄影拍不到 |

**讀程式時發現、會影響設計的事：**
- Gateway 沒有上下文記憶（E149 的取捨）→ agent 每一輪重送「規則＋任務＋做過的每一步」；用假 Gateway 實跑 6 步，`message` 從 244 字長到 518 字，離 4,000 字上限很遠
- 路由看遮罩後的字數（≥ 300 字）與關鍵字：預設任務含「設計」→ **每一步都走強模型 sol**（單價是 luna 的 20 倍）。這是要誠實寫的成本，也是簡報的重點：「agent 比聊天貴，因為每輪重送全部內容」
- 工具結果也經過 `mask()`：10 碼 09 開頭會被當手機、13～19 碼會被當卡號 → 工具回傳的數字要短
- 本機 DynamoDB 是 `-inMemory`：容器重開、重跑 `seed` 後額度歸零（Claude 一度講成「alice 這個月已用完」，已更正）

**沒做：** 原生工具呼叫（7.9 升級路線，要改 D38、遮罩與稽核要處理工具回傳）；agent 不連外部服務；不改 Gateway 一行。

---

## E156. 程式與測試（2026-10-27 15:50～16:51，公司電腦；分支 `feat/m7-agent`，進行中）

**Claude 的驗證複本（不推 GitHub）：**
- 新測試 **29 個**：`tests/test_agent_tools.py` 17 個、`tests/test_agent_demo.py` 12 個；整套 non-integration 360 passed、integration 84 個（合計 444 = 415＋29）
- 破壞實驗：拿掉 `tool_route()` 的 `mask()` → 1 個失敗（`test_route_masks_the_question_first_like_the_gateway`）；`safe_calc()` 改用 `eval` → 5 個失敗（`test_calc_rejects_anything_but_arithmetic` 的五種寫法）；拿掉預算那道煞車 → 1 個失敗（`test_run_agent_stops_when_its_own_budget_is_spent`）
- 本機假 Gateway（`http.server` 照劇本回）實跑：`route` → `price` ×2 → `calc` ×2 → `FINAL`，6 步、`final`；錯的 Key 回 `GatewayReply(status=401)`

**本人進度（公司電腦）：**
- `scripts/agent_tools.py` 打完；Claude 逐行比對抓到一處：`evaluate()` 最後一行 `raise ToolError(...)` 打成 **`return ToolError(...)`** → 錯誤被當成普通的值交回去，`2 ** 10`、`True + 1` 這些該擋的沒擋（「拒絕」那組測試紅）；改回 `raise` 後與驗證版一致（只差檔尾換行）
- 兩個測試檔由 Claude 放進 repo（大小核對過）
- 還沒做：`scripts/agent_demo.py`、`seed.py` 加 carol、整套 `pytest`；實跑與兩條驗收（要在個人電腦，本機 Gateway 讀 `.env` 的金鑰）

---

## E157. 程式打完、實跑兩條驗收（2026-10-27 18:55～19:47，個人電腦；分支 `feat/m7-agent`）

**程式：**
- 本人打 `scripts/agent_demo.py`、`seed.py` 加 carol。Claude 逐行比對第一次抓到 3 處會壞的：`AgentRun` 的 `stop_reason: str` 少了 `= ""`（一建就 `TypeError`）；`"Bearer" + api_key` 少一個空白（實跑每步 401，**測試抓不到**，因為測試用假 Gateway）；`reply.bosy` 打錯字＋半形 `|`、`micro_USD`。改完後只剩 `step = step + 1`、`x = x + cost` 兩行寫法不同（意思同 `+=`）
- `uv run pytest -q`：**444 passed**（32 秒）

**起本機 Gateway 撞到的（都不用改程式）：**
1. `KeyError: 'CHARGE_QUEUE_URL'`：`.env` 沒有這個設定（M5 加的；`compose.yaml` 的 gateway 容器有寫 `disabled`，直接跑 `uvicorn` 讀不到）。改成只在當下 PowerShell 設 `$env:CHARGE_QUEUE_URL="disabled"`，`.env` 不動
2. `[WinError 10048]`：8000 埠已被佔用；本人關掉佔用的程式後正常啟動（log 有 `"mode": "disabled"`）
- 錄影前把 PowerShell 提示字元改成 `PS> `（`function prompt { "PS> " }`），路徑裡的使用者資料夾名稱不入鏡；Key 用 `getpass`，畫面沒有 Key

**實跑結果（三段錄影，存本人電腦；最後一格截圖在 `docs/screenshots/`）：**

| 段 | 帳號、參數 | 步數 | 停止理由 | 花費（micro-USD） | 檔名 |
|---|---|---|---|---|---|
| ① | bob，預設（8 步、30,000） | 8 | `final`（剛好在第 8 步、上限的最後一步） | 8,326 | `m7-agent-1-bob-final` |
| ②-1 | carol，`--max-steps 0 --budget 0` | 8 | `final`（**沒被擋**） | 8,122 | `m7-agent-2-carol-self-correct` |
| ②-2 | carol，同上，再跑一次 | 3＋第 4 步 429 | `quota` ✅ | 2,384 | `m7-agent-3-carol-quota-429` |

- 答案三次都對：sol 約 US$0.0081、luna 約 US$0.000405、貴 20 倍
- 每步都走 `gpt-6-sol`（理由 `keyword`），跟 E155 預期一樣
- **對帳（`/metrics`）：** `llm_cost_usd_total` bob 0.008326、carol 0.010506（= 8,122＋2,384，與畫面加總一致，超過 carol 的 10,000 才被擋）；`llm_requests` 有 carol `status="quota_exceeded"`；`llm_rate_limit_rejected_total{reason="quota"} 1.0`
- 被擋的那一筆 Gateway 不回單號（429 沒有 body 內容），所以用監控計數器對帳，不用 `show_audit`

**跟預估不一樣的（誠實記錄）：**
1. **一步只花 626～1,460 micro-USD，E155 估 2,000～4,000，高估 2～3 倍。** 模型每次只回一行，輸出很短。所以 carol 的 10,000 第一次跑不完、整題做完；第二次才在第 3 步後被擋。驗收照樣成立，故事改成「第一次做完、第二次做到一半額度用完」。`seed.py` 註解的「大約跑 3 步」已改
2. **多花的 2 步都在找便宜模型的名字：** ① 的第 4 步 `route(便宜模型)`；②-1 的第 4 步自己編出 `gpt-6-mini`，工具回「沒有這個模型（有：gpt-6-luna、gpt-6-sol）」，第 5 步就改問對的（agent 自己修正的證據）。剛好吻合 E155 的「6 步＋2 步讓模型修正」，但 bob 在上限的最後一步才完成，**8 步沒有餘裕**。不改 `RULES`（把模型名寫進規則等於把答案給它）
3. 一整題 8 步約 US$0.008：agent 每輪重送全部內容，所以比單次聊天貴，但仍不到 1 美分
