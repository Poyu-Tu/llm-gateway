# M6 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID；個人帳號名稱（含終端機提示字元與路徑中的使用者資料夾名稱，一律寫成 `<user>`）。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`（檔名以 `m6-` 開頭，正式清單照決策書 11.4 的 S 編號），日誌另存於 `docs/logs/`。
> E 編號接續 `m5-evidence-log.md`（E127～E144），從 E145 開始。E145 是 M5 的收尾（實際花費），因為 M5 的紀錄已隨結案合併，照交接約定記在這裡。
> 紀錄日期：2026-10-25 建立（E145～E148）；10/26～10/27 補 E149～E154；10/27 晚補 E158（E155～E157 是 M7，在 `m7-evidence-log.md`）

---

## 紀錄規則（沿用 M5）

| # | 東西 | 規則 |
|---|---|---|
| 1 | 證據紀錄 | 本檔；每完成一組步驟就更新 |
| 2 | 里程碑報告 | 整關驗證通過後寫 `docs/milestones/m6-report.md`，格式同 M5；只向本人確認花費時間與實際花費 |
| 3 | 決策書 | M6 結案時出新版；期間的新定案先記在本檔 |
| 4 | 截圖、日誌、錄影 | 收到就改名、遮蔽；錄或截 AWS 主控台時框選範圍不含最上面那一列（帳號 ID） |
| 5 | 存放 | 所有文字檔也存一份到 Project |
| 6 | 個資測試 | 只用假資料 |
| 7 | 收錄範圍 | 只收與專題本身有關的內容；不記本人的預測、不寫責任歸屬、不寫個人環境的事 |
| 8 | 推送 | 一律開分支、開 PR、三個必要檢查（`Tests`、`Image scan`、`Config scan`）綠了才合併；commit 英文、PR 中文，都不附署名 |
| 9 | 查帳 | 用主控台的 Cost Explorer（免費）；CLI 每次 US$0.01，非必要不用 |

---

## E145. M5 實際花費：Cost Explorer 進帳（2026-10-25 09:30～，個人電腦，Chrome 主控台）

**做法：** AWS 主控台 → 帳單和成本管理 → Cost Explorer；未混合成本、每日、依服務分組；日期 UTC。主控台只顯示到小數兩位（M4 的 E129 用 CLI，精度較細）。

**UTC 10/19～10/24（合計 US$0.54）：**

| 日期（UTC） | 合計 | 內容 | 對應 |
|---|---|---|---|
| 10/19 | US$0.29 | EC2-其他 0.19、ALB 0.05、VPC 0.03、ECS 0.03 | M4 D、E 段（與 E129 的 0.291 一致） |
| 10/20 | US$0.02 | Cost Explorer 查詢費 | M5 E129 用 CLI 查帳 |
| 10/21、10/22 | US$0.00 | 長期層閒置（S3、DynamoDB、ECR、Lambda 等皆 0.00） | — |
| **10/23** | **US$0.22** | **EC2-其他 0.12、ALB 0.05、VPC 0.02、ECS 0.02、Cost Explorer 0.01**；Lambda、SQS、DynamoDB、Route 53 為 0.00 | **M5 上雲演練**（台灣 21:19～22:51 = UTC 13:19～14:51，全在 UTC 10/23 內） |
| 10/24 | US$0.01 | Cost Explorer 查詢費 | 10/24 早上用 CLI 查帳 |

**10/1～10/25：** US$0.57（含稅 0.03）。

**結論：**
- M5 演練本身約 **US$0.21**（0.22 扣掉查詢費 0.01）；演練當晚初估約 US$0.2，差約 5%。M4 估 0.22、實際 0.29（差 32%），M5 改用「建好到拆掉整段、不滿一小時進位」重估後對上
- EC2-其他 0.12 ≈ NAT 2 小時 × 0.062；ALB 0.05 ≈ 2 小時 × 0.0243，與按小時進位的算法一致（細項沒有用 CLI 拆用量類型，屬推定）
- Lambda、SQS、DynamoDB 在免費層，M5 新增的非同步記帳沒有多花錢
- **查帳本身要錢：** Cost Explorer API 每次 US$0.01，10/20～10/24 共 0.04，比 Lambda、SQS、DynamoDB 加起來還多 → 之後用主控台查（紀錄規則 9）
- 10/24 早上 CLI 查到 UTC 10/23 只有 0.00047：當時演練的費用還沒進帳；Cost Explorer 約隔天以上才完整

**截圖：** `docs/screenshots/m6-cost-explorer-m4-m5.png`（10/19～10/24 每日、依服務的長條圖；框選不含最上面那一列），簡報 v4.1 新增第 32 頁「拆完的帳單」放這張；結語（第 42 頁）的「US$0.5／兩次上雲的實際花費」以它為佐證。

**後續：** 決策書 v2.11.1 的 6.3、8.2 的 M5；`m5-report.md` 第 8 節、Part C；簡報 v4.1（第 32、42 頁）。

---

## E146. M6 開工定案：五項（2026-10-25 09:55～，個人電腦，只有定案）

**依據：** 決策書 v2.11.1 的 3.1（Demo Console、Demo 腳本、D65）、4.3、4.4、5.2、8.2 的 M6、8.4、12.5（M6 的項目）、D20、D92；`m5-report.md` Part C；`app/main.py`、`app/router.py`、`infra/persistent/logs.tf`（`main` = `553f1d7`）。

**範圍：** 只有定案，沒有寫程式、沒有登入 AWS。

| # | 題目 | 定案 | 沒選的 | 為什麼 |
|---|---|---|---|---|
| 1 | M6 範圍 | **四塊都做滿**：Demo Console（照 3.1 的畫面完整做：路由決策、回應、本次用量、剩餘配額條、429 變紅）、`/metrics`＋本機 Prometheus／Grafana、CD、S16 重拍；加上 M5 帶過來的待辦 | Console 先做最小版；砍 Grafana 只留 `/metrics`（8.4 第 4 項） | 本人選擇；代價：M7 很可能沒時間，走 8.2 的備案 |
| 2 | Console 要的資料 | **`/v1/chat` 的回應只加不改**：路由理由與是否備援、三個 token、`cost_micro_usd`、額度（上限、這次之後的已用＝呼叫前已用＋這次成本） | 另開 `GET /v1/quota`；只加成本與路由、不做額度條 | 這些值在 `chat_endpoint()` 裡都已經算好；M5 之後帳由 Worker 非同步記，回頭讀資料庫可能讀到還沒入帳的舊數字；只加欄位，舊客戶端不受影響 |
| 3 | Grafana 的來源 | **照 4.3**：本機先跑通；上雲那天筆電上的 Prometheus 帶通行證（SSM）經 ALB 抓雲端 `/metrics`；ALB 規則沒帶通行證回 403，也列為驗收 | 只抓本機 compose 裡的 Gateway | 4.3 不再停在設計；S15 是雲端呼叫的曲線。弱點：每次部署容器重開，計數器歸零（Prometheus 自己存歷史） |
| 4 | CD 的權限 | **只換映像的 CD**：建映像 → 掃描 → 推 ECR → apply 只改 `image_tag`；部署角色＝讀全部＋只能改任務定義與 ECS 服務；每日層由本人電腦先建好，沒建時 apply 被拒絕（安全地失敗） | 完整 CD（可蓋整個每日層，估 6～8 小時）；只推映像（不算 CD，8.2 的驗證做不到） | 權限最小又做得到驗收；與 M4 destroy 角色「只能拆貼每日標籤的東西」同一套思路。弱點：映像網址含帳號 ID，日誌要過濾（M5 E144 學到的）；Worker 的 Lambda 程式不在 CD 範圍 |
| 5 | CD 的觸發 | **手動觸發，只准 `main`**（environment 限制分支） | 合併就自動跑、每日層不在就跳過部署 | 照 D20；每日層平常是拆掉的，自動觸發多半只建了映像沒地方部署。8.2 的驗證改寫為「按一次，從建置、掃描到部署全自動」 |

**M5 帶過來、M6 一起做：** `audit_write_failed` 兩種意思拆成兩個事件名（`app/audit.py:125` 是沒花錢的稽核寫不進去；`app/main.py:184` 是花了錢、SQS 與備援都失敗），長期層的告警跟著加一個；`charge_queue_failed` 告警實際響一次；供應商預算用完的告警（12.5、D32）；上雲那天與 OpenAI 後台手動對帳（含「回答後、送 SQS 前」的空窗）。

**排程（Claude 粗估，不是量測）：** ① 回應欄位＋事件名拆分（本機）→ ② `/metrics`＋`monitoring/`（本機）→ ③ Console（本機）→ ④ Terraform（ALB 規則、SSM 通行證、告警）＋CD 角色與 workflow → ⑤ S16 分支 → ⑥ 上雲一次（CD 部署、Console 三章錄影、Grafana、告警、對帳、拆光）。合計約 18～24 小時；檢查點 11/1。

**後續：** 決策書 M6 結案版修訂 8.2 的 M6 驗證文字、D20 加註、12.5 的 M6 項目；練習本 AWS 架構「花費」補 M5 實際金額。

---

## E147. 程式兩塊：回應欄位、事件名拆分、`/metrics`（2026-10-25 10:00～11:00，個人電腦）

| PR | 內容 | 測試 |
|---|---|---|
| #31 | `/v1/chat` 回應只加不改：`route`（路由理由、有沒有降級）、`usage`（三個 token）、`cost_micro_usd`、`quota`（上限、呼叫前已用＋這次成本）；花了錢、記帳兩條路都失敗時事件名改 `charge_record_failed`（`report_audit_failure()` 加 `event` 參數，預設仍是 `audit_write_failed`） | 380 → 385 |
| #32 | `app/metrics.py`：自己的 `CollectorRegistry`、五個指標（決策書 5.2）、`observe_request()` 讀稽核紀錄已有的欄位；`chat_endpoint()` 四條路各記一次；`GET /metrics`；新套件 `prometheus-client 0.26.0`（7/24 上架，在 `exclude-newer` 9/27 之前，沒有其他依賴） | 385 → 390 |

- **做法改變（本人 10/25 10:06）：** 時間緊，Claude 改給完整程式＋一句為什麼，本人照打；測試仍由 Claude 寫
- **撞到的一次：** `REQUESTS.labels(uesr=...)` 打錯字 → 4 個測試 `ValueError: Incorrect label names`；套件對標籤名字很嚴格，寫錯當場報錯、不會默默記到錯的欄位
- **限制：** 本機 `/metrics` 沒有保護（雲端靠 ALB，見 4.3）；計數器在容器記憶體裡，重新部署歸零；資料庫在呼叫前就讀不到（503）的請求沒有計入

---

## E148. 本機 Prometheus／Grafana 跑通（2026-10-25 11:00～11:30，個人電腦）

**檔案：** `monitoring/compose.yaml`（Prometheus v3.15.1、Grafana 13.2.4，版本＋指紋鎖定；Docker Hub 推送 10/21、10/13，都過 3 天冷卻期；只綁 127.0.0.1）、`prometheus.yml`（每 15 秒抄 `host.docker.internal:8000`；雲端那一段用 `scrape_config_files` 從 `monitoring/secrets/*.yml` 讀，資料夾不進 repo）、`cloud-scrape.example.yml`（上雲那天的範本，帶 `X-Metrics-Token`）、Grafana 的資料來源與儀表板用檔案預先設定（8 個面板）。Grafana 免登入、只能看，登入表單與帳密驗證關掉。

**驗證：** 容器版 Gateway（`--profile gateway --build`，同一個映像會上雲）＋bob 問三題（`s05-easy`、`s05-hard`、`hi`）：
- Prometheus `/api/v1/targets`：`gateway-local` **up**，`lastError` 空、一次抄表約 0.2 秒
- Grafana：bob 累計 US$0.000979；`gpt-6-luna` 0.000011、`gpt-6-sol` 0.000968（簡單題走便宜模型、難題走強模型）；請求 `ok` 3；token luna 輸入 27／輸出 15、sol 輸入 34／輸出 90；延遲 p95 約 3.8 秒
- 「被擋下的次數」還沒被擋過時顯示 No data → 儀表板加 `noValue: 0`

**撞到的一次：** `python scripts/seed.py` → `ModuleNotFoundError: No module named 'app'`（直接跑檔案時只從 `scripts/` 找模組）；改 `python -m scripts.seed`。

**還沒做：** S15 正式截圖等上雲那天拍雲端的曲線；額度擋下（429）在 Grafana 上的樣子等 Console 錄影時一起看。

---

## E149. Demo Console 完成（2026-10-26 08:30～11:27，個人電腦；PR #34，`main` = `acb5707`）

**範圍：** 決策書 3.1 的 Console 與 4.4 的前端安全；10/26 10:30 本人看過第一版後改需求（三頁、聊天式、主題動畫），先講理解、問四題才動工。

**本人 10/26 的四個選擇：** 主題「日月軌道」（luna＝月亮銀藍、sol＝太陽金色；另兩個候選：光纖流量、收費站）；這次 `console.js` 由 Claude 放、本人讀懂（`main.py` 仍由本人打）；台幣顯示兩位有效數字（看得出便宜與強模型差幾倍）；要個資標籤。

| 檔案 | 內容 |
|---|---|
| `app/main.py` | `StaticFiles` 掛 `/static`；`GET /` 回 Console；中介層 `add_security_headers()` 每個回應加 CSP（`default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`）、`X-Frame-Options: DENY`、`nosniff`、`Referrer-Policy: no-referrer`、`Cache-Control: no-cache`；**新增 `GET /v1/me`**（只驗 Key、回名稱與額度，不呼叫模型、不花錢，給登入頁用）；`/v1/chat` 回應加 `pii_types`（只加不改，跟稽核同一份） |
| `app/static/` | 三頁：歡迎頁（SVG 軌道動畫，一個分頁只播一次，**不自動跳轉**，點一下或按任意鍵才進登入）→ 登入（`/v1/me` 驗證，五種問候輪流）→ 操作頁（左：聊天式問答，送出清空、保留歷史、Enter 送出、Shift+Enter 換行、注音選字的 Enter 不送；右：路由、用量、成本、剩餘額度、這次登入累計；左上角圖示與「新對話」回到三個範例題）；US$ 去掉尾巴的 0、附約略台幣（匯率 32.6 寫死，2026-10-20 台北收盤 32.617）；錯誤訊息依狀態碼改中文；429 寫出恢復日期時間 |
| 測試 | `tests/test_console.py` 10 個、`tests/test_me.py` 3 個、`tests/test_chat_response.py` 加 1 個；**390 → 404** |

**驗證：**
- 本機 `pytest -q` 404 passed；PR #34 的 `ci`、`CodeQL` 綠燈後合併
- Claude 在自己的環境（同一份程式＋Playwright，`/v1/*` 用假回應）：開頁沒有 CSP 錯誤；回答塞 `<img src=x onerror=alert(1)>` 被當文字印出、沒有執行；手機寬度 390 不會橫向捲動；歡迎頁等 7 秒仍停留、按鍵才進登入
- 推上去的 7 個檔案與 Claude 驗證版逐檔一致
- 本機容器（`--profile gateway --build`）：bob 問簡單題（luna）、分析題（sol）、含個資題（標籤「已遮罩 電話 才送出」）；alice 額度已用完 → 429，畫面顯示「11/1（日）00:00 恢復」
- 破壞實驗：拿掉 `pii_types`（2 個失敗）、`/v1/me` 改路徑（2 個失敗）、HTML 加 `style=`（1 個失敗）、拿掉 `Cache-Control`（1 個失敗）

**撞到的：**
1. **CSP 標頭名稱打錯**（`Content-Security-Poilcy`、`scripts-src`、`base-url`）：前者讓兩個測試失敗；後兩個瀏覽器只會默默略過、不報錯 → 測試補檢查 `base-uri 'none'`
2. **VS Code 自動完成把 `.value` 換成 `.ariaValueMax`**（4 處）、`bosy`、`$("message"),value`、漏打整個函式：8 個測試都抓不到（只檢查伺服器標頭與字串），靠逐行比對找到
3. **新 JS 配到瀏覽器快取的舊 CSS，畫面全亂**：沒有 `Cache-Control` 時 Chrome 依檔案年齡自己猜能用多久（舊 CSS 是前一天的檔、新 JS 是當天的）→ 加 `Cache-Control: no-cache`（用前先問伺服器，沒換就回 304、不重傳）；上雲用 CD 改版時也會遇到
4. **額度恢復時間**：Claude 一度說額度照 UTC 換月（台灣 08:00 恢復），實際 `app/quota.py` 的 `period_of()` 照台北時間 → 畫面「00:00」才對，前端備用計算也改照台北時間
5. **alice 一題就變紅**：強模型輸出每 token 10 micro-USD，一題分析題就超過 1,000 的月額度；只在呼叫前檢查、不預扣（決策書 7.10）

**設計取捨（本人要求寫進練習本）：沒有上下文記憶**——`chat_endpoint()` 只送這一句。有記憶的代價：每輪重送全部歷史、成本與額度難預估；要保存可能含個資的對話；多台容器要共用狀態。弱點：不能追問 → 畫面寫「每題各自獨立，不會記得上一題」。

**限制：** 登入仍是貼 API Key；本人提的「公司帳號登入後自動換 Key」只放簡報「未來」頁，沒做。台幣是固定匯率的參考值。`/v1/me` 跟 `/v1/chat` 一樣可以拿來試 Key（401 不花錢），靠 Key 是 256 位元亂數撐住；沒有登入次數限制。

**後續：** 上雲那天用 Console 錄三章（節費、個資、額度，D65）；決策書 M6 結案版：3.1 的畫面圖、4.4 加 `Cache-Control` 與 `/v1/me`、介面清單加 `GET /`、`GET /v1/me`；練習本待整理清單在 Project `claude/m6-console-draft/practice-book-todo.md`。

---

## E150. 長期層：兩組告警、deploy 角色、destroy 角色第五批（2026-10-26 11:46～13:03，個人電腦；PR #35，`main` = `80320c4`）

**範圍：** E146 第 3～5 項的「長期層＋程式」那一段（PR A）。每日層的 `/metrics` 規則（PR B）、`deploy.yml`（PR C）還沒做；這次沒有建每日層、沒有部署。

**開工前讀程式發現、交接沒寫到的：**
- 預算用完（`project_spend_limit_exceeded`）原本只寫稽核的 `error_code`、回 503，**沒有日誌**，指標篩選抓不到 → `main.py` 加一行事件
- 每日層加 Listener Rule 與 SSM 讀取後，destroy 角色拆之前也要讀它們（D87），所以 destroy 角色要跟著加權限
- ALB 比對標頭**不分大小寫**、`*` `?` 當萬用字元、值最長 128 字 → 通行證用 64 個十六進位字元（PR B 用）

**定案（本人 10/26 11:46）：CD 的 apply 範圍選 A「整份 plan＋守門」**

| 選項 | 做法 | 結果 |
|---|---|---|
| **A（選）** | 整份 `plan`，用 `terraform show -json` 檢查只准「新增任務定義＋更新 ECS 服務」，其他任何變動（含每日層沒建、要新建一堆）就停；`admin_cidr` 放 environment `deploy` 的 secret | 兩道防線：守門先擋、IAM 再擋 |
| B | `-target=aws_ecs_service.gateway`，`admin_cidr` 填假值 | 官方說 `-target` 只給例外用；範圍外的差異看不到，只剩 IAM 一道 |
| C | 不用 Terraform，`aws ecs` 直接換任務定義 | 違反 D92：帳本跟 AWS 對不上 |

弱點：多一個 secret 要記得換（家裡 IP 會變；對不上時 plan 會出現安全群組變動 → 守門擋下，是安全地失敗）；IP 要過濾，不能印進公開日誌。

| 檔案 | 內容 |
|---|---|
| `app/main.py` | `report_budget_exhausted()`：印 `{"event": "provider_budget_exhausted", "request_id", "routed_model", "error_code"}`，不記錯誤訊息；`chat_endpoint()` 判斷預算用完那條路呼叫它 |
| `infra/persistent/logs.tf` | `charge_record_failed`、`provider_budget_exhausted` 兩組指標篩選＋告警，都是 1 分鐘 ≥ 1 筆就響（前者錢花了帳沒記到、後者每個請求都 503，都沒有備援可接）；告警共 4 個，在每月前 10 個免費內 |
| `infra/persistent/daily_read.tf`（新） | 每日層「只看」的動作清單，destroy 與 deploy 角色共用；多 `elasticloadbalancing:DescribeRules`；通行證參數 `/llm-gateway/metrics-token` 的 ARN |
| `infra/persistent/github_oidc.tf` | destroy 角色第五批：三段 Describe 合成 `ReadDailyLayer`；`ReadMetricsToken`（只限通行證那一個參數）；`DeleteRule`＋資源種類加 `listener-rule/app/*`（仍限 `Layer=daily`）；Deny 加 deploy 角色與兩個新告警 |
| `infra/persistent/deploy_role.tf`（新） | `llm-gateway-deploy`：信任只限 environment `deploy`；讀寫每日層帳本與鎖檔、讀每日層、讀通行證；ECR 只准推 `llm-gateway`（含 `DescribeImages` 查標籤推過沒）；`RegisterTaskDefinition`（AWS 規定 `*`）；`TagResource` 只在 `ecs:CreateAction = RegisterTaskDefinition` 時；`PassRole` 只限 Gateway 兩個角色且只交給 `ecs-tasks`；`UpdateService` 只限那一個服務＋`Layer=daily`；Deny 改自己 |
| `infra/persistent/outputs.tf` | `deploy_role_arn` |
| `tests/test_chat_fallback.py` | 3 個：預算用完印一行（單號對得上稽核、模型、代碼）；日誌不含使用者問題與供應商訊息；只是限流不印 |
| `scripts/simulate_deploy_role.ps1`（新）、`simulate_destroy_role.ps1` | deploy 22 題；destroy 補第 13～16 題 |

**驗證：**
- `pytest`：404 → **407 passed**
- 破壞實驗（Claude 的驗證複本）：拿掉 `report_budget_exhausted(record)` 那一行 → 1 個測試失敗（`test_chat_logs_one_line_when_the_provider_budget_is_exhausted`）
- `terraform fmt`、`validate` 通過；`plan`：**6 to add, 1 to change, 0 to destroy**（新增兩個篩選、兩個告警、deploy 角色與它的政策；更新 destroy 角色的政策）；`apply`：**Apply complete! Resources: 6 added, 1 changed, 0 destroyed.**
- 權限模擬器：**destroy 16 題全 O**（舊的 12 題在 Describe 合併後照樣過；新的：拆規則 `allowed`、讀通行證 `allowed`、讀 HMAC 金鑰 `implicitDeny`、刪 deploy 角色 `explicitDeny`）；**deploy 22 題全 O**（推映像、登記、登記時貼標籤、交角色給 ECS、服務換版、讀通行證、讀寫每日層帳本 `allowed`；推別的倉庫、事後改標籤、交給 Lambda、交 Worker 角色、沒標籤的服務、刪／建服務、建 VPC、改安全群組、改 Worker、改規則、讀 HMAC 金鑰、寫長期層帳本 `implicitDeny`；給自己加權限 `explicitDeny`）

**撞到的（逐行比對抓到，`validate` 之前）：**
1. `logs.tf` 的 `aws_cloudwatch_log_group.gateway,name`（句點打成逗號）→ 語法錯，`validate` 會擋
2. **`deploy_role.tf` 的 `ReadWriteDailyState` 打成下一段 `LockDailyState` 的內容**（動作多 `DeleteObject`、資源指向 `.tflock`）：語法完全正確，`validate`、`plan` 都抓不到，結果是 CD 讀不到每日層帳本，要到上雲那天 `init` 才失敗 → 模擬器補第 20～22 題（讀寫每日層帳本、寫長期層帳本），以後同樣的錯在上雲前就會變 `X`

**限制：**
- 模擬器只問「這張卡刷這扇門會不會開」，標籤與 `ecs:CreateAction`、`iam:PassedToService` 都是用參數餵的；deploy 角色真的能不能跑完一次 `plan`（讀的動作有沒有漏）要等 CD 第一次實跑
- deploy 角色的 `RegisterTaskDefinition` 是 `Resource "*"`（AWS 規定）：能登記任何名字的任務定義，但交得出去的角色只有 Gateway 那兩個、能換版的服務只有一個
- 通行證參數還沒建（PR B 由本人 CLI 建）；兩個新告警還沒實際響過

**後續：** PR B（每日層 `/metrics` 規則、本人建通行證）→ PR C（`deploy.yml`、environment `deploy`）；決策書 M6 結案版：4.2 的 CI/CD 層、5.1、D20、12.5 的預算告警改「M6 已做」；練習本：`report_budget_exhausted()`、deploy 角色、`daily_read.tf`。

---

## E151. `/metrics` 的門禁：SSM 通行證＋ALB 兩條規則（2026-10-26 23:00～23:55，個人電腦；PR #36，`main` = `ff870e7`；只到 `plan`，沒有建每日層）

**範圍：** E146 第 3 項（決策書 4.3）的程式與通行證（PR B）。實際擋不擋得住要等上雲那天驗。

| 項目 | 內容 |
|---|---|
| 通行證 | 本人用 CLI 建 `/llm-gateway/metrics-token`（`SecureString`、AWS 預設 `aws/ssm` 金鑰、標準參數不收費）；值用 `secrets.token_hex(32)` 產生（64 個十六進位字元、256 位元），只放在 PowerShell 變數、建完就刪，沒有出現在畫面與任何檔案 |
| `infra/daily/metrics_access.tf`（新） | `data "aws_ssm_parameter"` 讀通行證；規則 **10**：路徑 `/metrics` **而且** 標頭 `X-Metrics-Token` 對 → 轉給 Gateway；規則 **20**：路徑 `/metrics`、`/metrics/*` → ALB 自己回 `403 Forbidden`（`fixed-response`），不轉給容器；其他請求照 listener 原本的轉給 Gateway |

**為什麼是兩條、順序為什麼這樣排：** ALB 從號碼小的比，第一條符合就停。放行那條要兩個條件同時成立；沒過的掉到 20 號一律 403。順序反過來，所有人都先被 403 擋。

**為什麼通行證是十六進位：** ALB 比對標頭**不分大小寫**、`*` `?` 是萬用字元、值最長 128 字（開工前讀文件發現）。十六進位只有 0～9、a～f，不會撞到萬用字元，大小寫也不影響強度。

**驗證（不花錢）：**
- 本人打的檔與 Claude 驗證版逐字一致
- `terraform validate` 通過；`plan`（`admin_cidr` 用文件專用位址 `192.0.2.1/32`、`image_tag` 填 `80320c4`，只算不建）：**`Plan: 42 to add, 0 to change, 0 to destroy`**（M5 的 40 個＋2 條規則）；`data.aws_ssm_parameter` 讀得到（本人的身分）
- 計畫裡規則 10 的兩個 `condition` 顯示 `At least one attribute in this block is (or was) sensitive, so its contents will not be displayed`：**通行證沒有出現在 `plan` 輸出**；規則 20 印出 `403`、`/metrics`、`/metrics/*`

**限制（誠實記錄）：**
- ALB 規則的條件要寫明文：通行證在每日層帳本、ALB 主控台的規則頁看得到；有讀這兩處權限的人就拿得到
- Demo 走 HTTP（7.8）：通行證在網路上是明文，靠 ALB 只放本人一個 IP 撐住
- 本機 `compose` 裡的 Gateway `/metrics` 仍然沒有保護（只綁 127.0.0.1）
- 換通行證要 apply 每日層（規則才會更新）；destroy 角色、deploy 角色都只准讀這一個參數（E150 模擬器第 14、17 題）

**上雲那天要驗的（驗收）：** 不帶標頭 → 403；帶錯 → 403；帶對 → 200 與 Prometheus 文字；`/metrics/` → 403；`/health`、`/` 照常 200；Prometheus `gateway-cloud` 目標 up（S15）。

**後續：** PR C（`deploy.yml`、environment `deploy`）；決策書 M6 結案版 4.3 補「十六進位通行證、兩條規則、明文的弱點」。

---

## E152. CD：`deploy.yml` 與部署前守門（2026-10-26 23:55～10-27 01:11，個人電腦；寫完、還沒合併、還沒跑）

**範圍：** E146 第 4 項（PR C）。程式寫完、本機測試；GitHub environment `deploy`、兩個 secret、第一次試跑在下一段。

| 檔案 | 內容 |
|---|---|
| `scripts/check_deploy_plan.py`（新） | `disallowed_changes(plan)`：讀 `terraform show -json`，列出「換映像以外」的每個改變；允許清單是「資源＋動作」的組合，只有 `aws_ecs_task_definition.gateway` 的 `delete/create`（或 `create/delete`）與 `aws_ecs_service.gateway` 的 `update`；`no-op`、`read` 不算改變。`main(path)` 有問題印出並回 1 |
| `tests/test_check_deploy_plan.py`（新） | 8 個：只換映像放行；沒改變放行；安全群組規則要換（IP 變了、secret 沒更新）擋；每日層沒建（全部 `create`）擋且全部列出；Worker 要更新擋；服務刪掉重建擋；`main` 回 1 並印出、回 0 |
| `.github/workflows/deploy.yml`（新） | `workflow_dispatch`；`permissions: {}`、工作上才開 `id-token: write`、`contents: read`；`environment: deploy`；`concurrency` 排隊不取消；Terraform 1.16.6 官方 zip＋SHA256（同 `destroy.yml`）；遮帳號 ID、`admin_cidr`（含不帶 `/32` 的寫法）；標籤＝`GITHUB_SHA` 前 7 碼；`docker build --provenance=false --sbom=false` → Trivy（同 CI 門檻）→ ECR（標籤已存在就沿用，IMMUTABLE）→ `init` → `plan -out` → `show -json` → 守門 → `apply` 那份計畫檔（不重算）；每個 Terraform 指令前重要一張身分證明；`plan`／`apply` 輸出過濾 `/32` |

**設計重點：**
- **兩道防線：** 守門（看計畫）先擋，deploy 角色的 IAM（E150）再擋；每日層沒建時守門列出所有 `create` 後停，apply 不開始
- **apply 照存好的計畫：** 守門看過什麼就做什麼，中間有人改了東西也不會被偷偷帶上
- **計畫檔與 JSON 含通行證、IP 原值：** 只在 runner 暫存區，不上傳 artifact、不印

**驗證（目前只有本機與 Claude 的驗證複本）：**
- Claude 的驗證複本：守門 8 個測試通過；破壞實驗：拿掉「在允許清單裡就放行」那一行 → 5 個失敗；`deploy.yml` 每個 `run` 區塊 `bash -n` 語法檢查通過
- 本人打的 `deploy.yml` 與驗證版逐字一致；`check_deploy_plan.py` 只差一處空白（`problems =[]`），不影響行為

**已知風險（誠實記錄）：**
- **Worker 的 zip 跨系統：** 本人 Windows、runner Linux；`archive_file` 打出的 zip 指紋若不同，`plan` 會要更新 Lambda → 守門擋下（安全地失敗，但部署做不下去）。`.gitattributes` 已規定 LF，要等第一次對著真的每日層跑才知道
- 守門只看「哪個資源、哪種動作」，不看改了哪個欄位（例如服務的 `desired_count`）；每日層設定都來自同一份 `main`，目前接受
- runner 連不到 ALB（只放本人 IP），CD 沒有部署後的煙霧測試；靠 `wait_for_steady_state`＋ALB 健康檢查＋部署斷路器，再由本人從電腦打 `/health`
- `deploy` 與 `destroy` 是兩個 `concurrency` 群組；同時按的話靠 Terraform 的 S3 鎖擋第二個

**下一步（驗收計畫）：** 合併 → 本人開 environment `deploy`（只准 `main`、取消管理員略過）、放 `AWS_DEPLOY_ROLE_ARN`、`ADMIN_CIDR` 兩個 environment secret → **每日層拆著的時候先跑一次**：預期建映像、Trivy、推 ECR 都綠，`plan` 列出約 42 個 `create`，**守門擋下、workflow 紅**；一次驗 OIDC、ECR 推送、讀帳本與通行證、守門、遮蔽。之後別的分支按一次（environment 擋）。上雲那天再按一次真的換版。

---

## E153. CD 第一次試跑：environment `deploy`、守門擋下、別的分支被擋（2026-10-27 13:30～14:10，公司電腦；PR #37，`main` = `8bcc043`；每日層拆著，沒有建任何東西）

**範圍：** E152 驗收計畫的第一段。上雲那天的「真的換版」還沒做。

| 項目 | 內容 |
|---|---|
| PR #37 | `deploy.yml`、`scripts/check_deploy_plan.py`、`tests/test_check_deploy_plan.py`（8 個，407 → 415）、E150～E152；檢查綠燈後本人合併 |
| environment `deploy` | 本人在 GitHub 設定：Deployment branches 選 Selected branches and tags、規則 `main`（「1 branch and 0 tags allowed」）；**取消** Allow administrators to bypass；Claude 重新整理設定頁核對過 |
| environment secret | `AWS_DEPLOY_ROLE_ARN`；`ADMIN_CIDR` 先填文件專用位址 `192.0.2.1/32`（試跑用不到真的 IP，也不把公司 IP 放進 GitHub；上雲那天改成家裡的 IP） |

**deploy #1（`main`，1 分 27 秒，紅——預期的紅）：**

| 步驟 | 結果 |
|---|---|
| Install Terraform | 1.16.6 指紋檢查通過 |
| Build the image | 綠（15 秒） |
| Scan the image with Trivy | 綠（21 秒）：沒有「有修補版」的 HIGH、CRITICAL |
| Push the image to ECR | 綠（18 秒）：OIDC 借到 deploy 角色、`Login Succeeded`、`llm-gateway:8bcc043` 推上去（ECR 原本沒有這個標籤） |
| Plan, check and apply | `init` 讀得到每日層帳本；四個 data（`archive_file.worker`、`aws_caller_identity`、SSM 通行證、DNS 查詢日誌設定）都讀成功；**`Plan: 42 to add, 0 to change, 0 to destroy.`**；守門印出 `The plan changes more than the Gateway image, so nothing was applied:` 並逐一列出 42 個 `create`，回 1，**`apply` 沒有開始** |

**deploy #2（`feat/m6-deploy-workflow`，3 秒，紅——預期的紅）：** `Branch "feat/m6-deploy-workflow" is not allowed to deploy to deploy due to environment protection rules.`；一個步驟都沒跑，沒有跟 GitHub 要身分證明，也就借不到角色。

**遮蔽（逐行看過 #1 的日誌）：**
- 帳號 ID 在映像網址、任務定義的 ARN、SQS 網址、DNS 允許清單裡都顯示 `***`
- `admin_cidr` 在安全群組規則顯示 `(sensitive value)`；`/metrics` 放行規則的兩個 `condition` 顯示 sensitive，通行證沒有出現
- 日誌裡沒有任何 IP

**這次證明了：**
1. 新角色 deploy 的 OIDC 信任條件（environment `deploy`）成立，別的分支連要證明的機會都沒有
2. deploy 角色的權限夠跑完「每日層沒建時」的 `init`＋`plan`、夠推 ECR（E150 限制「能不能跑完一次 `plan` 要等實跑」解除一半）
3. 守門在真的計畫上照設計擋下，`apply` 沒開始；E146 的「每日層沒建時安全地失敗」成立
4. 標籤＝`main` 的 commit 前 7 碼（`8bcc043`）

**還沒證明（上雲那天）：** 每日層建著時 `plan` 要 Describe 現有的 42 個資源，deploy 角色讀的權限夠不夠；只換映像時守門放不放行（Worker zip 跨系統的指紋，E152 已知風險）；`apply`、`wait_for_steady_state`、部署斷路器。

**觀察：**
- **Worker zip 跨系統（E152 已知風險）當天就驗了：** Linux runner 算出的 `source_code_hash` 是 `1z50L1kGoXaNff0iTZQ9eSbwx4gAKPbZOjKwNr8Q6k4=`；14:43 本人在公司電腦（Windows）`terraform -chdir=infra/daily plan`（同樣 `admin_cidr=192.0.2.1/32`、`image_tag=8bcc043`）算出**同一串**。打包的 6 個檔在 Windows 上沒有 CR、`git hash-object` 與 `8bcc043` 的內容逐檔相同；`worker.tf` 用 `source { content = file(...) }` 放內容，不讀檔案權限與修改時間 → 兩台系統打出同一個 zip。剩下的前提：上雲那天建每日層的個人電腦也要是 LF（同一份 `.gitattributes`），建之前用同一行指令再對一次
- 撞到的一次：在 repo 最上層跑 `terraform plan` → `Error: No configuration files`；改用 `terraform -chdir=infra/daily ...`，不用切換資料夾
- `docker login` 印出「credentials are stored unencrypted」：runner 用完即丟，workflow 推完會 `docker logout`，目前接受

**花費：** ECR 多一個映像（ECR 儲存每 GB 每月 US$0.10，一個映像每月不到 US$0.01）；Actions 用的是公開 repo 的免費額度。

---

## E154. S16：舊基底映像被 Trivy 擋下、現行基底通過（2026-10-27 15:10～15:30，公司電腦；PR #39 草稿、不合併）

**範圍：** 決策書 8.2 M6 的驗證「另開分支故意使用有已知漏洞的舊基底映像，看到 Trivy 擋下」、11.4 的 S16。M3 第一次 CI 已實際擋過一次（E104），這次照原計畫用分支重拍。

**做法：** 分支 `test/s16-old-base`：`Dockerfile` 兩個 `FROM` 的 digest 從現行 `a6e34c59…` 換回 10/4 的 `dddfd7e0…`（git 歷史 `bcb80e6`，就是 M3 被擋的那一版），第一行加註「S16 測試分支（不合併）」；開**草稿** PR #39，只為了觸發 CI。這個 `Dockerfile` 改動由 Claude 放進本人 repo（只用來測試、不合併）。

**結果（ci #85，`9fbfdf6`）：**

| 檢查 | 結果 |
|---|---|
| `Tests` | 綠 |
| `Config scan` | 綠 |
| **`Image scan`** | **紅**（28 秒）：建映像成功（舊 digest 仍拉得到），Trivy 回 1 |

Trivy 的表（`llm-gateway:ci (debian 13.7)`）：**`Total: 1 (HIGH: 1, CRITICAL: 0)`**

| Library | Vulnerability | Severity | Status | Installed | Fixed |
|---|---|---|---|---|---|
| `libpcre2-8-0` | CVE-2026-103111 | HIGH | fixed | `10.46-1~deb13u2` | `10.46-1~deb13u3` |

**對照（現行基底，`main` = `0d42dc9` 的 ci #84）：** `Image scan` 綠；同樣是 `debian 13.7`，弱點數 **0**（基底 10/13 換新指紋後 pcre2 已是修補版）。

**這次證明了：** 同一個專案、只差基底映像的指紋，有修補版的 HIGH 就讓 `Image scan` 失敗；三個必要檢查沒全綠就合併不了，所以不會進 `main`、也不會被 CD 部署（`deploy.yml` 建映像後也跑同一個門檻的 Trivy，E152）。

**誠實記錄：**
- 擋下的是「有修補版」的 HIGH、CRITICAL（`ignore-unfixed: true`）；沒有修補版的（M4 帶著上雲的 3 個 HIGH）不會擋，只能等上游
- 這次只驗了 CI 這一道；`deploy.yml` 裡的 Trivy 是同一套設定，沒有另外拿舊映像按 deploy（別的分支本來就被 environment 擋，E153）
- 弱點資料庫會更新：同一個舊映像日後可能多出別的弱點，表格內容以拍攝當天為準

**截圖：** `docs/screenshots/s16-trivy-block.png`（PR #39 的 Image scan：左側 Tests／Config scan 綠、Image scan 紅，右側 `Total: 1 (HIGH: 1)` 與 pcre2 那一列）、`docs/screenshots/s16-trivy-pass.png`（main 的 ci #84：三個都綠、debian 弱點 0）。由 Claude 用 Chrome 擷取，畫面不含帳號 ID 與個人資料。

**收尾：** PR #39 關閉、不合併；分支 `test/s16-old-base` 刪除。

---

## E158. 上雲一次：CD 真的換版、`/metrics` 驗收、Console 三章、S15、告警、對帳、拆光（2026-10-27 22:18～23:56，個人電腦、家裡網路；`main` = `1af1ede` → `8a9a3d9`）

**為什麼在家做：** 19:56 本人在咖啡店，本來要開始上雲；Claude 提醒 ALB 是 HTTP、只放行本人 IP，咖啡店整間共用一個對外 IP（門禁等於失效），開放 Wi-Fi 上送的 API Key 與 `/metrics` 通行證可能被同網路的人攔到。本人決定回家做（M7 收尾留在咖啡店做）。

| # | 步驟 | 結果 |
|---|---|---|
| 1 | `aws login`、`export-credentials` | 成功 |
| 2 | Worker 指紋 | 個人電腦 `plan` 的 `source_code_hash` 與 Linux runner、公司電腦相同（`1z50L1k…Q6k4=`） |
| 3 | 每日層 apply（`image_tag = 8bcc043`） | `Apply complete! Resources: 42 added`；ECS 服務 1 分 8 秒建好；任務定義 `llm-gateway:3`；`/health` → `{"status":"ok"} 200` |
| 4 | `ADMIN_CIDR` secret | 本人改成家裡 IP（與 `TF_VAR_admin_cidr` 同一個值，從 apply 那個分頁印出） |
| 5 | **deploy #3**（`1af1ede`） | 建映像、Trivy、推 ECR 綠；`plan` 1 add／1 change／1 destroy（映像 `8bcc043` → `1af1ede`），Lambda 不在計畫裡；**守門放行**（`The plan only swaps the Gateway image`）；新任務定義登記、`UpdateService` 送出；**等穩定時 `AccessDenied`：deploy 角色沒有 `ecs:ListServiceDeployments`** → 紅（1 分 17 秒）。事後 `describe-services`：`PRIMARY COMPLETED llm-gateway:4`，換版本身成功，只是 Terraform 沒權限確認 |
| 6 | 修正（分支 `fix/m6-deploy-watch-rollout`，PR #42） | `deploy_role.tf` 加 `WatchGatewayRollout`：`ListServiceDeployments`、`DescribeServiceDeployments`、`DescribeServiceRevisions`，資源只限這一個服務與它的部署、版本紀錄（AWS 文件的寫法），不加標籤條件（只讀、不確定支援）；模擬器加第 23～25 題；長期層 apply `0 added, 1 changed, 0 destroyed`；**模擬器 25 題全對**；PR #42 綠了合併（`8a9a3d9`） |
| 7 | **deploy #4**（`8a9a3d9`） | **成功（3 分 14 秒）**：守門放行 → `aws_ecs_service.gateway: Modifications complete after 1m54s` → `Apply complete! Resources: 1 added, 1 changed, 1 destroyed.` CD 第一次從頭到尾真的換版、等到穩定 |
| 8 | 雲端停舊 Key、發新 Key | `DYNAMODB_TARGET=aws`：`disable_key --user alice`、`--user bob`（M4、M5 的舊 Key）→ `seed` 發 alice、bob、carol（carol 第一次上雲端）→ 清掉 `DYNAMODB_TARGET` |
| 9 | **`/metrics` 驗收** | 不帶 403、帶錯 403、**帶對 200**、`/metrics/`（帶對）403、`/health` 200、`/` 200；通行證用變數、`-o NUL`，畫面不出現。插曲：第一輪 `$tok` 因憑證過期是空的 → 帶空白通行證也是 403（正確） |
| 10 | **Console 三章錄影**（Chrome、雲端 ALB） | ① 節費（bob）：簡單題 → luna、SQS／Kafka → sol；② 個資（bob）：四種假資料，luna 唸回 `TW_ID・PHONE・EMAIL・CARD`；③ 額度（**carol**）：5 題 sol，額度條一路掉，第 6 題被擋、寫出「11/1（日）00:00 恢復」 |
| 11 | **S15：Grafana 抓雲端** | `monitoring/secrets/cloud-targets.json`（ALB 網址，Claude 放）＋`metrics-token`（本人 `Set-Content -NoNewline -Encoding ascii`）；Prometheus `gateway-cloud` **UP**（207 ms）；儀表板 bob $0.002270、carol $0.010140（= Console 的 US$0.01014）、`ok` 8、`quota_exceeded` 4 |
| 12 | **告警響一次** | 往 `/ecs/llm-gateway` 新開 stream `alarm-test`，寫一行 `{"event":"provider_budget_exhausted","note":"alarm test"}` → 1～2 分鐘內 `llm-gateway-provider-budget-exhausted` 變 **`ALARM`** |
| 13 | **與 OpenAI 對帳** | 後台 10/27：**27 個請求**、約 US$0.03；我們這邊：本機 M7 19 個（bob 8、carol 8＋3）＋雲端 Console 8 個（bob 3、carol 5）＝**27**；花費 18,832＋12,410＝31,242 micro-USD ≈ US$0.031。被擋的 5 次（alice 4、carol 1；agent 的 carol 1 次在本機）沒有出現在 OpenAI。10 月累計 US$0.13（Project 硬上限 US$2） |
| 14 | **destroy #4** | 4 分 39 秒綠；之後直接問 AWS：NAT `[]`、ALB `[]`、ECS 服務 `[]` |

**撞到的與學到的：**
1. **deploy 角色缺「看換版進度」的權限**（上表 5～7）：模擬器 22 題全對，但沒有考到 Terraform 等穩定時會呼叫的 API → 只有實跑才知道。補權限後模擬器 25 題、實跑成功。面試說法：「模擬器只能驗我想得到的題目；第一次真的部署才發現 AWS provider 6.x 改用服務部署紀錄判斷成功，我補了三個只讀權限，限定到那一個服務，並把它加進模擬器，下次就考得到。」
2. **臨時憑證 15 分鐘就過期：** `export-credentials | iex` 把通行證抄進環境變數，過期後重新 `aws login` 也沒用（CLI 先讀環境變數）。解法：`Remove-Item Env:AWS_*` 再匯出；只用 AWS CLI 時乾脆不匯出，CLI 會自己換新
3. **`$env:` 變數只在設定它的分頁：** 第二個分頁印 `$env:TF_VAR_admin_cidr` 是空的
4. **alice 一登入就沒額度：** `quotas` 在長期層，10/23 的 M5 演練已用完 10 月；`seed` 只發新 Key、重設上限，**不歸零本月已花**（決策書 12.5 早已記錄的限制，排錄影時 Claude 沒想到）。改用 carol 錄第三章；alice 的畫面留作備用（`m6-console-3b-alice-already-used.mp4`）
5. **carol 超出額度 140 micro-USD：** 5 題累計 US$0.01014 ＞ US$0.01，因為「呼叫前檢查、不預扣」，第 5 題送出時還沒用完。最多超出一題的錢，刻意接受

**誠實記錄：**
- 告警驗的是「日誌篩選 → 告警 → SNS」這條管線；Gateway 程式真的印出 `provider_budget_exhausted` 由單元測試驗（OpenAI 預算不能真的用完）。測試 stream `alarm-test` 留在長期層的日誌群組裡
- 告警信：**已收到**（10/28 補記）。Gmail 10/27 23:45（台北）收到 `ALARM: "llm-gateway-provider-budget-exhausted"`，23:51 收到恢復 `OK` 的信
- `/metrics` 的 403／200 驗收**沒有截圖或錄影**（10/28 查過 repo、本人電腦的截圖與錄影資料夾）：只有上表第 9 列的文字。下次開每日層時補錄一段終端機
- 對帳的金額只對到「約 US$0.03」（後台只顯示兩位小數）；請求數精確對上
- deploy #3 的紅燈是真的紅（權限不足），不是預期的紅
- 雲端 `alice`、`bob` 的 10 月額度已用的部分不會因重灌歸零（同 12.5）

**截圖、錄影：**
- `docs/screenshots/m6-console-1-savings-bob.png`、`m6-console-2-pii-bob.png`、`m6-console-3-quota-carol.png`（三段錄影的最後一格）
- `docs/screenshots/s15-grafana-cloud.jpg`（Claude 用 Chrome 擷取，畫面沒有帳號 ID、IP）
- 10/28 補（Claude 用 Chrome 擷取並裁切；帳號 ID、GitHub 使用者名稱、ALB 位址、資源 ID 都不在畫面上）：`m6-cd-1-runs.png`（deploy 四次：#1～#3 紅、#4 綠；整次 3m21s，部署那個 job 3m14s）、`m6-cd-2-deploy1-guard-blocked.png`（#1 的 `Plan: 42 to add` 與守門 `The plan changes more than the Gateway image, so nothing was applied`）、`m6-cd-3-deploy4-only-swaps.png`（#4 的 `1 to add, 1 to change, 1 to destroy` 與 `The plan only swaps the Gateway image`）、`m6-cd-4-deploy4-apply-complete.png`（`Modifications complete after 1m54s`、`Apply complete!`）、`m6-alarm-email.png`（ALARM 信；AWS Account 那一行以下裁掉）
- 錄影存本人電腦 `Videos\llm-gateway-mp4\m6-console-*.mp4`（Key 沒有入鏡，Claude 逐段看過）

**花費：** 每日層約 1 小時 40 分（22:20 apply ～ 23:55 destroy）；OpenAI 雲端那段 12,410 micro-USD。AWS 實際金額等帳單出來再補（M6 報告）。
