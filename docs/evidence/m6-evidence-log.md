# M6 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID；個人帳號名稱（含終端機提示字元與路徑中的使用者資料夾名稱，一律寫成 `<user>`）。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`（檔名以 `m6-` 開頭，正式清單照決策書 11.4 的 S 編號），日誌另存於 `docs/logs/`。
> E 編號接續 `m5-evidence-log.md`（E127～E144），從 E145 開始。E145 是 M5 的收尾（實際花費），因為 M5 的紀錄已隨結案合併，照交接約定記在這裡。
> 紀錄日期：2026-10-25 建立（E145～E148）

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
