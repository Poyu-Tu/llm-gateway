# M0 / M0.5 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、使用者唯一 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`，日誌另存於 `docs/logs/`。
> 紀錄日期：2026-09-23 起（M0 提前於 10/1 開工前進行）；2026-09-25 新增 E11～E19（M0.5 與供應商決策）；2026-09-26 新增 E20～E28（OpenAI 查證與防線、M0 收尾、M0.5 完成）

---

## E1. 舊存取金鑰使用調查（CloudTrail）

**背景：** IAM 使用者 `terry-admin` 有一把長期存取金鑰，Last used 顯示 5 天前、服務為 STS。刪除前先查使用來源，避免誤刪正在使用中的金鑰。

**查詢方式：** CloudTrail → Event history → Lookup attribute = Access key ID，區域 ap-northeast-1。

**查到的事件（已遮蔽）：**

```json
{
    "eventTime": "2026-09-17T17:13:09Z",
    "eventSource": "sts.amazonaws.com",
    "eventName": "GetCallerIdentity",
    "awsRegion": "ap-northeast-1",
    "userIdentity": {
        "type": "IAMUser",
        "principalId": "AIDAXXXXXXXXXXXXXXXXX",
        "arn": "arn:aws:iam::XXXXXXXXXXXX:user/terry-admin",
        "accountId": "XXXXXXXXXXXX",
        "accessKeyId": "AKIAXXXXXXXXXXXXXXXX",
        "userName": "terry-admin"
    },
    "sourceIPAddress": "XXX.XXX.XXX.XXX",
    "userAgent": "aws-cli/2.36.47 ... os/windows#11 ... md/installer#exe ... md/command#sts.get-caller-identity",
    "readOnly": true
}
```

**判讀：**
- 唯一動作是 `GetCallerIdentity`（只查「我是誰」），`readOnly: true`
- userAgent 顯示為 Windows 11 上的 AWS CLI 手動執行 `sts get-caller-identity`
- 後續在第二台電腦的 `~\.aws\credentials` 找到 `[terry-admin]` 設定檔，版本同為 2.36.47，確認來源

**結論：** 金鑰只被本人手動測試過，無外洩使用 → 停用後刪除，兩台電腦的殘留檔皆已清除。

---

## E2. CLI 改用臨時憑證（`aws login`）

**兩台電腦驗證結果（已遮蔽）：**

```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "XXXXXXXXXXXX",
    "Arn": "arn:aws:iam::XXXXXXXXXXXX:user/terry-admin"
}
```

- AWS CLI 版本：2.36.47（`aws login` 需 2.32.0 以上）
- 憑證為臨時性，自動續期最長 12 小時
- 第二台電腦在登入前先刪除舊 `credentials` 檔（舊檔優先順序高於 `aws login`，不刪會一直拿失效金鑰去驗證）

---

## E3. Bedrock 呼叫失敗（M0 阻礙）

**錯誤訊息：**

```
ValidationException
Error 002: Access to Bedrock models is not allowed for this account
```

**排查紀錄：**

| 測試 | 區域 | 結果 | 推論 |
|---|---|---|---|
| Claude Haiku 4.5（`jp.` 跨區推論） | ap-northeast-1 | Error 002 | — |
| Amazon Nova Micro | ap-northeast-1 | Error 002 | 非 Anthropic 專屬，屬帳號層級封鎖 |
| 帳號方案 | — | 2025 年以前開立的舊制隨用隨付帳號 | 排除「新制免費方案不能用 Bedrock」 |

**AWS Support 回覆重點（第一、二次）：**
- 原因是信用卡處於錯誤狀態，授權被發卡銀行拒絕，導致 Marketplace 訂閱無法完成
- 可能原因：發卡行要求語音確認、CVV2 設定、額度不足、帳單地址不符
- 更新付款方式後會自動重試授權

**已處理：**
- 舊卡（有效期限顯示「未驗證」）已移除
- 新卡：已驗證、設為預設，上個月曾成功支付 AWS 帳單
- 海外線上交易：已開通
- 無未付款帳單

**目前狀態：** 仍為 Error 002，待 AWS Support 進一步處理（改用 Chat 並要求提供被拒授權的時間、金額、商家名稱）。

---

## E4. Docker Desktop 安裝驗證（第二台電腦）

```
Docker version 29.7.2, build a7dcaa6

Hello from Docker!
This message shows that your installation appears to be working correctly.

Digest: sha256:5e23090353324d887c48ad5e5c56d294eab81588df9605b07d1afe895f9cc8f8
```

- 環境：Windows 11 25H2（26200）、WSL 2.7.8、虛擬化已啟用、16 GB RAM
- 過程中遇到：CLI 已裝好但引擎未啟動（`dockerDesktopLinuxEngine` 找不到）→ 啟動 Docker Desktop 後解決
- 安全設定：`Expose daemon on tcp://localhost:2375 without TLS` 關閉；開機自動啟動關閉（見 `m05-docker-settings.png`）

---

## E5. Bedrock 支援結論與後續（2026-09-23）

**AWS Support 最終回覆重點（案件已結案）：**
- Bedrock 服務團隊通常不開放模型存取給「消費紀錄很少」的帳號，需要一段時間成功的付款紀錄
- 可透過 AWS 業務（Account Manager）替帳號爭取例外開通

**已採取行動：**
| 路線 | 做法 | 狀態 |
|---|---|---|
| A | AWS 台灣業務聯絡表單（見 `m0-sales-form-submitted.png`） | 已送出，待聯絡 |
| B | 詢問指導老師課程是否提供可用 Bedrock 的帳號或教育額度 | 老師查詢中 |
| 保底 | M1～M3 本機以 mock 模型開發，不受影響 | — |

**決策期限：** 10/12（M3 需實際呼叫模型）。屆時未解決，評估替代方案並記入決策書。

**後續（2026-09-25）：** 提前於原訂的 9/27 期限前決定改用 OpenAI API，網路改為受控出口（見 E12、決策書 v2.5 的 D23～D26）。業務與老師兩條路仍保留，若開通可經由薄介面切回 Bedrock。

**過程中的誤判與修正：** 曾把帳單主控台的「免費方案」頁面（舊制 Free Tier 用量追蹤）誤認為 2025/7 新制「免費帳號方案」，推論需要升級方案；經本人指出帳號於 2025 年前開立後修正，未執行不可逆的升級動作。

---

## E6. 東京可用的 `jp.` 推論設定檔（決策書 12.5 第一項）

**指令：**
```
aws bedrock list-inference-profiles --region ap-northeast-1 --output table --query "inferenceProfileSummaries[?contains(inferenceProfileId,'jp.')].inferenceProfileId"
```

**結果：**
```
jp.anthropic.claude-sonnet-4-5-20250929-v1:0
jp.anthropic.claude-haiku-4-5-20251001-v1:0
jp.amazon.nova-2-lite-v1:0
jp.anthropic.claude-sonnet-4-6
jp.anthropic.claude-opus-4-7
jp.anthropic.claude-opus-4-8
jp.anthropic.claude-opus-5-5
```

**觀察：**
- 查詢清單的管理 API 不受 Error 002 影響（被擋的是模型呼叫）
- Haiku 只有一個選項：Claude Haiku 4.5
- Sonnet 有 4.5 與 4.6 兩個 `jp.` 選項；清單中沒有 Sonnet 5 的 `jp.` 設定檔

**對照：東京可用的 `apac.` 推論設定檔**

```
apac.anthropic.claude-3-sonnet-20240229-v1:0
apac.anthropic.claude-3-5-sonnet-20240620-v1:0
apac.anthropic.claude-3-haiku-20240307-v1:0
apac.anthropic.claude-3-5-sonnet-20241022-v2:0
apac.amazon.nova-micro-v1:0
apac.amazon.nova-lite-v1:0
apac.amazon.nova-pro-v1:0
apac.anthropic.claude-sonnet-4-20250514-v1:0
```

**結論（D17 修改依據）：**
- `apac.` 只涵蓋 Claude 3.x、3.5 與 Sonnet 4，**沒有 Haiku 4.5、Sonnet 4.5／4.6 等新一代模型**
- 新一代 Claude 在東京改用 `jp.`（資料只在日本境內處理）或 `global.`
- 定案：Haiku → `jp.anthropic.claude-haiku-4-5-20251001-v1:0`；Sonnet → `jp.anthropic.claude-sonnet-4-6`

---

## E7. Fargate 東京單價（決策書 12.5 第二項之一）

**來源：** AWS Pricing Calculator，Asia Pacific (Tokyo)、Linux、x86（見 `m0-pricing-fargate-tokyo.png`）

| 項目 | 東京單價 |
|---|---|
| vCPU | $0.05056 / vCPU / 小時 |
| 記憶體 | $0.00553 / GB / 小時 |
| 暫時性儲存 | 前 20 GB 不另收費 |

**換算 D15 規格（0.25 vCPU / 0.5 GB）：**
- 0.25 × 0.05056 + 0.5 × 0.00553 = **$0.0154 / 小時**
- 常駐一個月（730 小時）：**$11.25**
- 決策書 6.2 原估 ~$0.012 / 小時 → **低估約 28%**，v2.5 更正
- 6.3 全期約 50 小時上雲：~$0.77（原估 ~$0.60）

**踩到的坑：估價單位錯誤（見 `m0-pricing-fargate-unit-trap.png`）**
- 第一次試算時「任務數量」的單位是「每天」，計算器算成一個月 30.42 個任務、每個各跑 730 小時，月費顯示 $342.09
- 從單價反推發現總額不合理，把單位改成「每月」後得到正確的 $11.25
- 教訓：雲端估價最容易錯的是單位，不是單價；同類錯誤發生在擴縮或排程設定上，就是真實的帳單事故

---

## E8. ALB 東京單價（決策書 12.5 第二項之二）

**來源：** AWS Pricing Calculator，Asia Pacific (Tokyo)（見 `m0-pricing-alb-hourly.png`、`m0-pricing-alb-lcu.png`）

| 項目 | 東京單價 |
|---|---|
| ALB 固定費 | **$0.0243 / 小時**（常駐一個月 $17.74） |
| LCU | **$0.008 / LCU / 小時** |

**對照決策書 6.2：** 原估 ~$0.0225 / 小時 → 低估約 8%，v2.5 更正。
**6.3 全期約 50 小時：** 固定費 ~$1.22（原估 ~$1.10，含 LCU）。

**LCU 試算的第二個單位陷阱：**
- 試算時「處理的位元組」填了每小時 1 GB，而且 Lambda 目標與 EC2／IP 目標兩欄都填了 → 3.5 LCU，月費 $20.44
- 實際情況：本案 ALB 的目標是 Fargate（IP 類型），Lambda 目標那欄應為 0；Demo 流量以 MB 計，不是每小時 GB
- LCU 取「新連線、作用中連線、處理位元組、規則評估」四個維度中最高的那個計費；Demo 流量下每項都遠低於 1 LCU，LCU 費用可忽略，ALB 成本幾乎等於固定費
- 修正：Lambda 目標欄位歸零後為 1 LCU、月費 $5.84（見 `m0-pricing-alb-lcu-fixed.png`）；此時仍以「每小時 1 GB」估算，實際 Demo 流量遠低於此
- Demo 流量試算（見 `m0-pricing-alb-lcu-demo.png`）：處理位元組改為每小時 0.001 GB（約 1 MB，以每次請求 10 KB、每小時 100 次估算）後，處理位元組只剩 0.001 LCU，**最大值改由「新連線」維度決定（每秒 1 次 → 0.04 LCU）**，月費 $0.23；若新連線改用 Demo 實際量（每秒約 0.03 次），LCU 費用趨近於零
- 這張截圖剛好示範了 LCU 的計費規則：四個維度取最大值，改變輸入後「主導維度」會換人
- 教訓同 E7：先確認每個欄位的單位與適用對象，再看總額

---

## E9. 預算告警管道驗證（S18 前半）

**證據：** `s18-cost.png`（帳號 ID 已遮蔽）
- 寄件者：`budgets@costalerts.amazonaws.com`
- 2026-09-12，`zero-cost-alert` 預算（門檻：實際成本 > $0.01）觸發，當時實際成本 $1.53
- 證明此帳號的 Budgets Email 告警管道實際寄得出信、收得到信
- 未額外調低 `llm-gateway-monthly-20usd` 做測試：兩個預算寄往同一信箱、走同一條告警管道，以既有觸發紀錄替代，省去等待 Budgets 更新週期
- S18 後半（結案時 Cost Explorer 實際花費）於專題結案時補拍

---

## E10. NAT Gateway 東京單價（為 9/27 供應商決定準備）

**來源：** AWS Pricing Calculator，Asia Pacific (Tokyo)（見 `m0-pricing-nat-tokyo.png`）

| 項目 | 東京單價 |
|---|---|
| NAT 固定費 | **$0.062 / 小時**（常駐一個月 $45.26） |
| 資料處理 | **$0.062 / GB** |

與決策書 6.2（v2.3 已用東京單價更正）一致，無需修改。

**若改用外部 API（受控出口），常駐成本比較（單 AZ，每小時）：**

| 方案 | 組成 | 每小時 | 全期 50 小時 |
|---|---|---|---|
| 原設計 Zero Egress | Interface Endpoint × 6（含 `bedrock-runtime`） | $0.084 | ~$4.2 |
| 受控出口・保留 Endpoint | NAT + 公有 IP + Interface Endpoint × 5 | ~$0.137 | ~$6.9 |
| 受控出口・只用 NAT | NAT + 公有 IP；S3、DynamoDB 仍走免費 Gateway Endpoint | ~$0.067 | ~$3.4 |

註：Interface Endpoint 單價 $0.014 / 小時沿用決策書 v2.3 的東京查價；公有 IPv4 $0.005 / 小時沿用 6.2；DNS 防火牆費用待 9/28 查證（已於 E20 完成）。

---

# M0.5 拆解 LiteLLM

## E11. LiteLLM 映像選版與簽章驗證（M0.5 第 1 步，2026-09-25）

**選版（冷卻期規則，決策書 D27）：**

| 版本 | 發布時間 | 判斷 |
|---|---|---|
| v1.102.0 | 2026-09-20 | ✅ 上架 5 天、正式版、未撤回 |
| v1.102.1 | 2026-09-23 | ✗ 0 天，不符冷卻期；內容為 Anthropic 相關修正的回補，非資安修補 |

- 冷卻期門檻：上架滿 3 天、未撤回、無未修補 KEV
- KEV 檢查：CVE-2026-59822（MCP 端點驗證繞過，9/2 列入 KEV）影響 1.84.0 以下，本版不受影響
- 觀察：9/23 同時有 1.99、1.100、1.101、1.102 四條版本線出修補版，10/1 做需要模型的部分前再檢查一次

**公鑰：** 取自固定 commit 的網址（`.../0112e53046018d726492c814b3644b7d376029d0/cosign.pub`），不用 tag 網址；已確認與 v1.102.0 tag 下的公鑰內容一致，檔案 178 bytes，開頭為 `-----BEGIN PUBLIC KEY-----`

**拉取與驗證：**

```
docker pull ghcr.io/berriai/litellm-database:v1.102.0
Digest: sha256:70e3754699d2c5e969c65445e3b52cf58cf7998a815f2cb3551776152bbffaaf

cosign-windows-amd64 verify --key cosign.pub ghcr.io/berriai/litellm-database@sha256:70e3754699d2c5e969c65445e3b52cf58cf7998a815f2cb3551776152bbffaaf
- The cosign claims were validated
- Existence of the claims in the transparency log was verified offline
- The signatures were verified against the specified public key
```

**判讀：**
- 驗證對象是 digest 而不是 tag：確保「驗過的」與「等下實際執行的」是同一個映像
- 透明紀錄的 `integratedTime: 1789879892` 換算為 **2026-09-20 04:51 UTC**，與發版時間一致，代表是發版當下簽的，不是事後補簽
- 映像大小 **1.65 GB**（觀察 2 的背景資料：映像越大，雲端冷啟動拉取越久、經過 NAT 的流量越多）

**過程中遇到的小狀況：**
- 映像很大，海外倉庫下載需要一段時間；中途闔上電腦中斷，重新 `docker pull` 時已完成的層直接沿用（`Already exists`），只補剩下的
- 在新開的 PowerShell 視窗執行 `type cosign.pub` 找不到檔案：新視窗從家目錄開始，切到 `litellm-lab` 資料夾後正常

**截圖：** `s19-part1-cosign.png`（驗簽）、`m05-image-size.png`（digest 與大小）、`m05-litellm-pull-digest.png`（拉取完成與 digest）

---

## E12. 供應商與網路層決策（2026-09-25）

**起因：** Bedrock 帳號層級封鎖（E3、E5），M3 需要實際呼叫模型，等不起業務例外。

| # | 題目 | 定案 | 關鍵理由 |
|---|---|---|---|
| D23 | 平台層 | 自建 Gateway；LiteLLM 只當 M0.5 對照；官方 SDK + 薄介面 | 個資遮罩、fail-closed、HMAC 稽核要自己寫才展示得出來；成本最低 |
| D24 | 供應商 | OpenAI API | 業界通用格式；省錢效果好展示；薄介面保留切回 Bedrock |
| D25 | 出口管控 | NAT + DNS 防火牆放行清單 + 安全群組只開 443 | 幾乎零成本；Network Firewall 50 小時約 +$17，吃掉整個預算 |
| D26 | Interface Endpoint | 不保留 | D25 已接受直接用 IP 的殘餘風險，多付一倍（~$6.9 對 ~$3.4）只買到部分保護 |

**過程中釐清的觀念：**
- LiteLLM 和 OpenAI 是不同層的東西：LiteLLM 是「平台層」（外送平台），OpenAI、Bedrock 是「供應商層」（餐廳）。LiteLLM 不需要 Bedrock，兩層可以任意組合
- 只要接 AWS 以外的供應商，就一定要有出口；Zero Egress 只有 Bedrock 做得到
- 換成外部供應商後，決策書 10.4「接外部供應商就違背 Zero Egress」這個不用 LiteLLM 的理由已不成立，v2.5 刪除並改寫

**連帶發現的新風險：** 資料出境、多一把長期金鑰、AWS Budgets 看不到 OpenAI 帳單（決策書 4.5）

---

## E13. LiteLLM 官方 docker-compose 安全預設值拆解（文件審查，2026-09-25）

**來源：** LiteLLM v1.102.0 tag 下的 `docker-compose.yml`

| # | 官方範例 | 風險 | 本實驗的做法 |
|---|---|---|---|
| 1 | 資料庫密碼 `dbpassword9090` 寫在檔案裡 | 推上 GitHub 就外洩 | 放 `.env`，不進版控 |
| 2 | 管理金鑰範例 `sk-1234` | 照抄沒改 | 用亂數產生 |
| 3 | PostgreSQL 開 `5432:5432` | 資料庫暴露在電腦的網路上，同網段都連得到 | 不對外開埠，只給 LiteLLM 內部連 |
| 4 | LiteLLM 開 `4000:4000` | 預設綁定所有網卡，等於對區網開放 | 只綁 `127.0.0.1` |
| 5 | 映像用 `main-stable` 浮動標籤 | 每次拉到的內容可能不同 | 用 digest 鎖定 |
| 6 | 附帶 Prometheus，沒鎖版本、沒驗證 | 多一個不需要的服務 | 拿掉 |
| 7 | 啟動時從 GitHub `main` 分支下載模型價格表（E15 實測發現） | 資料未驗證、未鎖版本，卻決定預算怎麼算 | `LITELLM_LOCAL_MODEL_COST_MAP: "True"` |

**結論：** 範例檔的目的是「五分鐘跑起來」，不是「可以上線」。拆解現成方案不只看功能，也要看它的預設值安不安全。這張表對應決策書 10.2 第 10 環節「網路邊界是部署者的責任」。

**實驗原則：** PostgreSQL 維持官方的 16 版，只改跟資安有關的設定，減少變數。

---

## E14. 強化版 docker-compose 與首次啟動（M0.5 第 2～4 步，2026-09-25）

**PostgreSQL 映像：** `postgres:16`，digest `sha256:1a6ab3f5345eb6dbe04a1349529caabdb0ab09293a09590fad07b2246bfa4b54`，642 MB。維持官方範例的 16 版以減少變數；只用 digest 鎖定、不另外驗簽（實驗主角是 LiteLLM，刻意的範圍控制）。

**建立的檔案（`scripts/litellm-lab/`）：** `.env`（三組密鑰，不進版控）、`docker-compose.yml`、`.gitignore`

- 密鑰用 `[guid]::NewGuid().ToString("N")` 產生：Windows PowerShell 5.1 內建、只有 0-9a-f。只用英數字是因為密碼會組進 `postgresql://帳號:密碼@db:5432/...`，含 `@`、`:`、`/` 會把網址切錯。正式環境改用 Secrets Manager 產生
- `.env` 用記事本建立：Windows PowerShell 5.1 的 `>`、`Out-File` 預設寫出 UTF-16，Docker Compose 讀不懂
- 每個容器只拿自己需要的變數（資料庫容器拿不到管理金鑰）；官方範例用 `env_file` 把整包塞進容器

**格式驗證：**
- `docker compose config --quiet` 無輸出 = 通過。刻意不用不加 `--quiet` 的版本，因為它會印出展開後的完整設定，包含密碼
- `.env` 為 157 bytes，與「三行、每組 32 字、最後一行無換行」的計算完全吻合 → 三組長度正確，且為 UTF-8 無 BOM（有 BOM 會是 160）

**啟動與網路綁定：**

| 檢查 | 結果 | 意義 |
|---|---|---|
| 啟動順序 | db `Healthy`（7.1s）後 litellm 才 `Started` | `condition: service_healthy` 生效 |
| `docker compose ps` | db：`5432/tcp`（無箭頭）；litellm：`127.0.0.1:4000->4000/tcp` | 資料庫只在 Docker 內部網路；LiteLLM 只綁本機 |
| `netstat -an \| findstr "4000 5432"` | 只有 `127.0.0.1:4000 LISTENING`，沒有 5432 | 作業系統層再確認一次 |
| 健康檢查 | `"I'm alive!"` | 服務正常 |

**啟動日誌判讀（`m05-litellm-startup.log`）：**
- 未出現任何密碼或金鑰；資料庫只顯示 `at "db:5432"`
- 首次啟動執行 171 筆資料表更新，接著自動比對差異並 `prisma db execute` 修補，約 6 秒
- **發現：** 應用程式每次啟動都會改資料表結構，代表它的資料庫帳號必須有「改結構」的高權限；日誌也提醒多容器輪流更新時可能發生 schema thrashing。正式環境通常把資料表更新拆成獨立的一次性工作。對照本案：DynamoDB 沒有資料表結構更新，Gateway 的 IAM 角色只需要讀寫權限
- 容器內 `Uvicorn running on http://0.0.0.0:4000` 與只綁本機不矛盾：容器內監聽所有網卡是慣例，外部能否連入由埠對應決定
- 待查（不下結論）：更新清單中有 `mcp_default_public_internet_true`，名稱看起來是把 MCP 伺服器的「可從公網使用」預設改成開啟；本實驗不啟用 MCP

**截圖：** `m05-postgres-pull.png`、`m05-postgres-digest.png`、`m05-compose-validate.png`、`m05-compose-up-ps.png`
**日誌：** `m05-litellm-startup.log`

---

## E15. 斷網實驗：啟動時的對外連線（觀察 3，M0.5 第 5 步，2026-09-25）

**方法：** 用覆蓋檔 `egress-test.yml`（`networks.default.internal: true`）模擬 Zero Egress，主設定不動。以「從容器連 `http://github.com`」作為控制檢查。

| 組別 | 條件 | 控制檢查 | 啟動日誌 |
|---|---|---|---|
| 對照組 | 一般網路 | 無輸出（連得到） | 乾淨，無警告 |
| 實驗組 | 斷網 | `[Errno -3] Temporary failure in name resolution`（斷網生效） | 4 行 `WARNING` |
| 解法組 | 斷網 + `LITELLM_LOCAL_MODEL_COST_MAP=True` | — | 警告全部消失，直接從 Prisma 開始 |

**實驗組的日誌：** 啟動時從 `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json` 下載模型價格表；失敗後重試 3 次（間隔 2.9 秒、4.0 秒），最後保留映像內建的備份。從第一次失敗（04:54:37）到進入下一階段（04:54:47）約 **10 秒**，服務仍能正常啟動（優雅降級）。

**最重要的發現：簽章驗證的缺口**
- 映像驗過簽、用 digest 鎖定，但啟動時會抓一份**沒有驗證、沒有鎖版本**的資料（網址是 `main` 分支）
- 這份資料直接決定預算怎麼算：同一個映像不同日期算出的費用可能不同；若被竄改（例如把單價改成 0），預算管控會失效且沒有錯誤訊息
- 是資料不是程式碼，嚴重度低於惡意程式，但打中的正是成本治理
- 教訓：驗證映像簽章還不夠，還要看它執行時會去拿什麼

**解法與決定：**
- 設定 `LITELLM_LOCAL_MODEL_COST_MAP: "True"`，價格跟著映像版本走；已寫入主設定（E13 強化第 7 項）
- 代價是價格要升級映像才更新；在成本治理系統裡這反而是優點：價格變更變成經過驗簽流程的版本變更。本案 Gateway 把單價放在 repo 設定檔，是同一個思路
- 不選「把 `raw.githubusercontent.com` 加進 DNS 放行清單」：GitHub raw 常被用來放惡意程式或接收外洩資料

**附帶觀察：**
- 完全斷網時，本機也連不進服務（`curl: (7) Failed to connect ... after 2056 ms`）：internal 網路沒有通往主機的閘道。說明 AWS 上要的是「只管出口」而不是「拔光網路」（D25）
- 斷網的錯誤是 `[Errno -3]`（暫時性）；AWS DNS 防火牆封鎖預設回 NXDOMAIN，錯誤會是 `[Errno -2]`，重試行為可能不同，M4 驗證

**限制（誠實記錄）：** 證明了「價格表下載」這一項消失；其他失敗時不寫日誌的連線，光看日誌抓不到。要完全排除需在容器網路抓封包，本次不做：要多拉一個抓封包工具映像（多一個供應鏈要驗證），且 M4 的 DNS 防火牆查詢日誌會補上

**截圖：** `m05-egress-test-up.png`
**日誌：** `m05-egress-test.log`、`m05-egress-test-localmap.log`

---

## E16. 待機記憶體（觀察 2，M0.5 第 6 步，2026-09-25）

**條件：** 主設定（已含 E15 的解法）、一般網路、啟動約 1 分鐘、無任何請求

| 容器 | 記憶體 | PIDS |
|---|---|---|
| LiteLLM | **584 MiB** | 22 |
| PostgreSQL | 34.46 MiB | 10 |

**判讀：**
- 本案 Fargate 規格「0.5 GB」實際是 **512 MiB**。LiteLLM 待機 584 MiB，**還沒收到請求就塞不進去**，至少要 0.25 vCPU / 1 GB。證實決策書 10.4「記憶體需求約兩倍」
- 單位的坑（同 E7）：直接拿 584 跟「0.5 GB」比很容易看錯，要先統一成 MiB
- PIDS 包含執行緒，不能直接推論 worker 數

**成本的誠實修正：記憶體兩倍 ≠ 成本兩倍**

| 規格 | 每小時 | 50 小時 |
|---|---|---|
| 0.25 vCPU / 0.5 GB（本案） | $0.0154 | $0.77 |
| 0.25 vCPU / 1 GB（LiteLLM） | $0.0182 | $0.91 |

Fargate 記憶體便宜、vCPU 貴，只多約 18%。真正的成本差異是 LiteLLM **必須常駐 PostgreSQL**（資料庫容器本身只用 34 MiB，問題不在記憶體，而在雲端要多一個 24 小時開著的託管資料庫）。10.4 的措辭於 v2.5.1 修正。

**待補：** 有 OpenAI 金鑰後量「有負載」的數字（已於 E27 完成）；M1 完成後用同一指令量本案 Gateway，三個數字一起對照

**截圖：** `s20-litellm-memory.png`（S20；同時執行的其他無關專案容器已裁掉）
**日誌：** `m05-memory-idle.log`

---

## E17. 預算為 0 的虛擬金鑰（S19 後半，M0.5 第 7 步，2026-09-25）

**方法：** 用不存在的模型 `gpt-test` 當探針，從錯誤訊息判斷檢查順序，不需要任何供應商金鑰。管理金鑰從 `.env` 讀進變數使用，全程不出現在指令列（PowerShell 會把指令存進歷史紀錄檔）。

| 組別 | 金鑰 | 回應 |
|---|---|---|
| 實驗組 | `max_budget: 0` 的虛擬金鑰 | `Budget has been exceeded! ... Current cost: 0.0, Max budget: 0.0`，type `budget_exceeded`，code 429 |
| 對照組 | 管理金鑰 | `Invalid model name passed in model=gpt-test`，code 400 |

**判讀：**
- 預算檢查排在模型檢查之前：超額請求碰不到模型供應商，一毛錢都不會花出去。與本案 Gateway 的順序相同（驗身分 → 查配額 → 路由）
- `max_budget: 0` 被正確當成嚴格上限（0 ≥ 0 → 擋），沒有被誤當成「無上限」。LiteLLM 這題做對了
- 管理金鑰不受預算限制，性質同 AWS root 帳號，絕不能給應用程式使用

**帶出的設計問題（M2 待決）：** 超額回 429。但 429 的原意是「太頻繁，稍後再試」，許多客戶端（含 OpenAI 官方 SDK）會自動重試；月額度用完時重試不會成功，只會增加負載。本案 M2 原定「超額回 429」，實作時考慮：錯誤類型寫明額度用完、不附 `Retry-After`，或改用其他狀態碼

**過程中的小狀況：** `$mk = ((gc .env) -match ...) -replace ...` 之後 `$mk.Length` 是 1 而不是 35。`-match` 作用在陣列（多行）上時結果仍是陣列，`.Length` 算的是元素個數；改用 `$mk = $mk[0]` 取出字串後為 35。若沒先驗證長度，這個錯誤會被「剛好能用」掩蓋（單元素陣列放進字串會自動攤平），直到 `.env` 出現重複設定才以難懂的方式爆出來

**截圖：** `s19-part2-budget-blocked.png`（S19 後半；錯誤訊息中虛擬金鑰末 4 碼已遮蔽）
**日誌：** `m05-zero-budget-key.log`

**收尾驗證：金鑰沒有進入 PowerShell 歷史紀錄（2026-09-25）**
- 實驗結束後以 `Remove-Variable mk,vk,h,vh,fh,r` 清除工作階段中的金鑰變數
- 第一次搜尋 `sls "sk-" (Get-PSReadLineOption).HistorySavePath`：命中多行，但除了假金鑰 `sk-fake-1234` 與搜尋指令本身，其餘都是誤判（過去練習指令中的 `flask-image` 含有 `sk-` 字串）
- 改用金鑰格式精準搜尋 `sls "sk-[0-9a-f]{32}" (Get-PSReadLineOption).HistorySavePath`：**無輸出**
- 結論：「從 `.env` 讀進變數再使用」的做法有效，真實金鑰從未出現在指令列與歷史紀錄
- 教訓：搜尋條件太寬會被誤判淹沒，與 SOC 告警規則調校同理；用「資料格式」而不是「片段字串」來找
- 第一次搜尋的輸出含個人帳號名稱，未收錄

---

## E18. 執行中資料庫斷線（觀察 1 情境 A，M0.5 第 8 步，2026-09-25）

**方法：** LiteLLM 持續執行，只關閉 PostgreSQL（`docker compose stop db`）。延續 E17 的探針（不存在的模型 `gpt-test`），測兩把金鑰：預算 0 的虛擬金鑰、不存在的假金鑰 `sk-fake-1234`。

| 時間點 | 預算 0 金鑰 | 假金鑰 |
|---|---|---|
| 剛關資料庫 | 503 `no_db_connection` | 503 `no_db_connection` |
| 120 秒後 | 503 `no_db_connection` | 503 `no_db_connection` |
| 資料庫恢復 15 秒後（LiteLLM 未重啟） | 429 `budget_exceeded` | 401 `token_not_found_in_db` |

**判讀：**
- **fail-closed：** v1.102.0 預設在驗證用資料庫連不上時一律拒絕，2 分鐘後仍拒絕，沒有靠記憶體暫存放行，假金鑰也混不過去
- **自我恢復：** 資料庫恢復後不需重啟 LiteLLM，行為自動回到正常
- **金鑰雜湊方式：** 假金鑰錯誤訊息回傳的 `Key Hash` 經本機計算，等於 `SHA-256("sk-fake-1234")` = `c57606c7…57cba90b`。LiteLLM 以未加鹽 SHA-256 存放金鑰雜湊，與本案 `api_keys` 表的設計相同
- **fail-closed 的代價：** 資料庫掛 = 整個服務停擺，所以資料庫本身必須高可用。RDS 要另付 Multi-AZ；DynamoDB 天生跨多個 AZ，不需額外設定

**推翻了決策書的說法（最重要）：** v2.2～v2.5 在 10.3、10.5 寫「LiteLLM 沒接資料庫時預算會放行，所以本案的配額設計成讀不到就拒絕」。實測在「資料庫斷線」情境，LiteLLM 與本案做法完全相同。原說法把「沒設資料庫」與「資料庫斷線」兩種情境混在一起，決策書 v2.5.1 已改寫，並保留更正紀錄。

**截圖：** `m05-db-down-503.png`（斷線 120 秒後）、`m05-db-recovered.png`（恢復後；虛擬金鑰末 4 碼已遮蔽）
**日誌：** `m05-db-outage.log`

---

## E19. 根本沒設資料庫（觀察 1 情境 B，M0.5 第 8b 步，2026-09-25）

**方法：** 另開獨立專案 `nodb-compose.yml`：沒有 db 服務、沒有 `DATABASE_URL`、埠 `127.0.0.1:4001`，其餘同主設定，與原環境並存。

| 測試 | 結果 |
|---|---|
| 啟動日誌 | 沒有 Prisma、沒有資料表更新、沒有 query-engine，也**沒有任何警告** |
| 管理金鑰呼叫探針 | 400 `Invalid model name`（身分檢查通過） |
| 管理金鑰發預算 0 的虛擬金鑰 | 500 `DB not connected. This endpoint needs a database...` |
| 待機記憶體 | 473.5 MiB、PIDS 6（有資料庫時 584 MiB、PIDS 22） |

**判讀：**
- 沒有資料庫就發不出虛擬金鑰 → 沒有每人預算，只剩管理金鑰。「預算功能必須接資料庫」得到實證
- 要讓應用程式使用，只能把管理金鑰發出去 = 把 root 權限交給每個應用程式
- 服務照常啟動、健康檢查會過，日誌卻沒有提醒「預算功能不可用」：**安靜地降級**，是維運上最難發現的狀態
- 資料庫相關功能約占 110 MiB（584 → 473.5）；無資料庫時仍達 512 MiB 規格的 92%，沒有餘裕

**未驗證（誠實記錄）：** 官方文件記載「沒接資料庫時全域預算檢查會被跳過」。要驗證需另寫設定檔設全域預算並比較有無資料庫兩種狀況，本次不做；決策書標示為「官方文件記載、未實測」。

**日誌：** `m05-no-db.log`

---

# 2026-09-26：OpenAI 查證與防線、M0 收尾、M0.5 完成

## E20. OpenAI 與 DNS 防火牆查證（原訂 9/28，提前於 9/26 完成）

**來源：** OpenAI 官方文件（`developers.openai.com` 的 Pricing、Models、各模型頁、Deprecations、Data controls、Conversation state、Spend limits）、OpenAI Help Center（Prepaid billing、Projects）、AWS Route 53 價格頁。查證日期 2026-09-26。

**1. 模型與單價（每百萬 token，Standard 層級）：**

| 模型 ID | 輸入 | 快取輸入 | 輸出 | 定位 | 判斷 |
|---|---|---|---|---|---|
| `gpt-6-luna` | $0.10 | $0.01 | $0.50 | GPT-6 最省成本 | ✅ 便宜模型 |
| `gpt-6-sol` | $2.00 | $0.20 | $10.00 | GPT-6 中階，平衡能力與成本 | ✅ 強模型 |
| `gpt-6-astra` | $10.00 | $1.00 | $50.00 | GPT-6 旗艦 | ✗ 貴 5 倍，預算撐不住 |
| `gpt-5.6-luna` | $0.20 | $0.02 | $1.20 | 上一代 nano 級（v2.5 原候選） | ✗ 比 GPT-6 Luna 貴一倍以上 |
| `gpt-5.6-terra` | $2.00 | $0.20 | $12.00 | 上一代 mini 級（v2.5 原候選） | ✗ 輸出比 GPT-6 Sol 貴 20% |

- v2.5 的候選 GPT-5.6 Luna / Terra 仍在服務、未列入淘汰清單，但新一代 GPT-6 更便宜
- 便宜與強模型價差 **20 倍**（輸入、輸出皆是），智慧路由的省錢效果好展示
- **全部是推理模型：** 思考用的 token 以輸出單價計費；`reasoning_effort` 預設 `medium`，可設 `none`／`low`／`medium`／`high`／`xhigh`／`max`
- 資料落地（regional processing）端點對 2026/3/5 之後發布的模型加收 10%；本案不使用
- Tier 1 速率上限：`gpt-6-luna`、`gpt-6-sol` 皆為 500 RPM / 500,000 TPM

**2. API 資料保留：**
- 2023/3/1 起，送進 API 的資料預設**不用於訓練**（除非主動選擇分享）
- 為監測濫用，內容最多保留 **30 天**（法律要求時更久）
- **Zero Data Retention 需經 OpenAI 業務審核**，本案申請不到 → 送出的內容會在 OpenAI 端停留最多 30 天，入口個資遮罩是必要（M2）
- **Responses API 預設把回應存 30 天**（`store` 預設開啟）；Chat Completions 預設不存 → 本案用 Chat Completions（D29）

**3. 儲值與花費上限：**
- 預付制最低 **$5**，上限依帳號等級；儲值金 **1 年後過期、不可退款**
- **自動加值在設定時預設開啟**（見 E21），不關掉就沒有上限
- Project 可設**硬性**花費上限：超過後回 **429**、代碼 `project_spend_limit_exceeded`；攔截不是即時的，最後花費可能略超過上限
- Project 可限制可用的模型（Model usage → Allowed models）
- 兩份官方說明有出入：Help Center 的 Projects 文章寫花費上限只是提醒，Spend limits 文件寫可以硬擋 → 以實際畫面為準（E21：畫面有 Enforce a hard limit 開關）

**4. Route 53 Resolver DNS 防火牆：**
- 自訂網域清單：每個網域每月 **$0.0005**（按小時比例計），放行清單 20 個網域約每月 $0.01
- 查詢：每百萬次 $0.60（前 10 億次）
- AWS 託管的網域清單不收網域費，只收查詢費
- Resolver 查詢日誌本身不收費，寫進 CloudWatch Logs／S3 另依該服務計費

**對決策書的影響：** 3.4、4.5、6.2、6.3、D28、D29（v2.6）

---

## E21. OpenAI 端的五道防線（S21，2026-09-26 16:16～16:40）

**做法：** 換成外部供應商後，把 AWS 端的最小權限、預算上限、短期憑證同樣做在 OpenAI 端。

| # | 防線 | 設定 | 擋什麼 | 證據 |
|---|---|---|---|---|
| 1 | 預付儲值、不自動加值 | 儲值 $5、Auto-reload OFF | 錢包見底就停，畫面明寫「餘額 $0 時 API 請求停止」 | `m0-openai-prepaid-no-autoreload.png` |
| 2 | Project 硬性花費上限 | `llm-gateway-capstone` 每月 $2、Enforce a hard limit 開啟 | 一個月最多花 $2；比錢包更早擋下 | `s21-part2-spend-hard-limit.png` |
| 3 | 模型白名單 | 只允許 `gpt-6-luna`、`gpt-6-sol` | 金鑰外洩也叫不動貴的模型 | `s21-part1-allowed-models.png`、E22 實測 |
| 4 | 金鑰最小權限 | Restricted：只有 Chat completions = Request，其餘（含 Responses、List models）皆 None | 不能傳檔案、訓練模型；**不能用 Responses 把資料存在 OpenAI** | `m0-openai-key-permissions.png` |
| 5 | 服務帳號 + 30 天到期 | Owned by Service account、名稱 `m0-m05-lab`、有效期限 30 天 | 金鑰不綁個人帳號；外洩也會自己失效 | `m0-openai-key-create-settings.png` |

**過程中的發現：**
- **自動加值預設開啟：** 設定畫面預設「儲值 $10、餘額低於 $5 自動補到 $10」，不改的話等於沒有上限
- **金鑰預設「永不過期」：** OpenAI 自己在畫面上警告長期金鑰外洩的風險，並建議改用「工作負載身分聯盟」取得短期憑證（`m0-openai-key-expiry-warning.png`）。跟 E13 同類：**預設值是為了方便，不是為了安全**
- **服務帳號在建立時沒有權限選項：** 建立後才能從列表的編輯按鈕改成 Restricted；改之前列表顯示 `Inherited`（沿用服務帳號全部權限），改之後顯示 `Restricted`（`m0-openai-key-list-inherited.png` → `m0-openai-key-list-restricted.png`）
- **權限分三級：** None（不能用）／Request（可以呼叫）／Write（可以呼叫，也能讓 OpenAI 存資料，例如 Responses）
- **權限變更要幾分鐘才生效**（畫面提示）
- 花費上限的警告框明寫：超過回 429、攔截非即時、最後可能略超過

**新線索（M4 前評估）：** 工作負載身分聯盟（Workload Identity Federation）。若支援以 AWS IAM 角色換取 OpenAI 短期憑證，Fargate 就不需要 OpenAI API Key，決策書 4.5「多了一把長期金鑰」的風險可直接消除

**截圖：** `m0-openai-prepaid-no-autoreload.png`、`m0-openai-project-created.png`、`s21-part1-allowed-models.png`、`s21-part2-spend-hard-limit.png`、`m0-openai-key-expiry-warning.png`、`m0-openai-key-create-settings.png`、`m0-openai-key-list-inherited.png`、`m0-openai-key-permissions.png`、`m0-openai-key-list-restricted.png`（金鑰列表遮蔽 Tracking ID、金鑰末 4 碼、建立者 user ID）

---

## E22. M0 收尾：第一次成功呼叫與模型白名單實測（2026-09-26 16:57～17:00）

**金鑰處理：** 寫入 `scripts/litellm-lab/.env`（記事本編輯），以 E17 的方法讀進變數 `$ok`，只印出前綴與長度驗證：`sk-svcacct-`、167（`m0-openai-key-env-check.log`）

**第一次呼叫（Windows PowerShell 5.1，`Invoke-RestMethod`）：**
- 請求：`gpt-6-luna`、`reasoning_effort: none`、`max_completion_tokens: 50`、英文短句（避開 PowerShell 5.1 送中文的編碼問題）
- 回應：`gpt-6-luna` → `Hi there, how are you today?`
- `usage`：輸入 13、輸出 11、**`reasoning_tokens: 0`**

| | token | 單價（每百萬） | 花費 |
|---|---|---|---|
| 輸入 | 13 | $0.10 | $0.0000013 |
| 輸出 | 11 | $0.50 | $0.0000055 |
| **合計** | | | **$0.0000068 = 6.8 micro-USD** |

**判讀：**
- `reasoning_effort: none` 有效：沒有思考 token，輸出全部是看得到的字
- **D1 的新問題：** 以 micro-USD 整數儲存時，6.8 要記 6 還是 7 → 定案**無條件進位**（D30）：治理系統寧可多算，不能讓額度被每次的零頭慢慢偷走
- **挫折：** 第一次網址打成 `/v1/chat/completion`（少一個 s）→ **404**。狀態碼分層：401 身分、403 權限、404 地址錯（還沒輪到檢查身分）。Gateway 用官方 SDK，網址由 SDK 處理（D23 的小理由）

**反向測試：模型白名單（S21 的實測證明）：**
```json
{
    "error": {
        "message": "Project `proj_XXXXXXXXXXXXXXXXXXXXXXXX` does not have access to model `gpt-6-astra`",
        "type": "invalid_request_error",
        "param": null,
        "code": "model_not_found"
    }
}
```
- 不在白名單的 `gpt-6-astra` 在 OpenAI 端被擋下，未產生費用
- 錯誤代碼是 `model_not_found` 而不是「沒有權限」：刻意不洩漏資源是否存在（同 GitHub 私人 repo 對無權限者回 404）
- 對 Gateway 的啟示：M3 要記錄供應商的原始錯誤代碼，否則設定檔寫錯模型名稱時很難查；M2 的 API Key 錯誤也只回「驗證失敗」，不透露是「不存在」還是「已停用」

**日誌：** `m0-openai-key-env-check.log`、`m0-openai-first-call.log`、`m0-openai-model-allowlist-block.log`（Project ID 已遮蔽）

**M0 狀態：✅ 完成**

---

## E23. 內建價格表沒有新模型 → 預算安靜失效（M0.5 追加，2026-09-26 17:08～17:32）

**起因：** E15 為了安全關掉線上價格表（`LITELLM_LOCAL_MODEL_COST_MAP=True`），價格只用映像內建的版本。v1.102.0 於 9/20 發布，不一定收錄本案的模型。

**設定變更：** `docker-compose.yml` 的 `litellm` 服務新增 `OPENAI_API_KEY: ${OPENAI_API_KEY}`；`db` 服務不給（延續 E14 每個容器只拿需要的變數）

**查詢 1：** `litellm.model_cost.get('gpt-6-luna')` → **`None`**

**查詢 2（排除「只是名稱不同」）：** 列出名稱含 `gpt-6`、`luna`、`terra` 的所有項目

| 模型 | 內建價格表 |
|---|---|
| `gpt-6-astra`（旗艦） | ✅ 有，含 Azure、Bedrock、OpenRouter 等前綴版本 |
| `gpt-5.6-luna`、`gpt-5.6-terra`（上一代） | ✅ 有 |
| **`gpt-6-luna`、`gpt-6-sol`（本案選用）** | ❌ 任何前綴下都沒有 |

→ 不是價格表整份過時，而是**平價新模型沒被收錄**；偏偏最常用、最需要記帳的就是平價模型

**A 段實驗：不填單價直接使用**
1. 以 `/model/new` 加入 `gpt-6-luna`（`api_key` 填環境變數參照 `os.environ/OPENAI_API_KEY`，資料庫不存金鑰本體）
2. 發一把 `max_budget: 0.01`、只允許 `gpt-6-luna` 的虛擬金鑰，呼叫一次（17:29:53）
3. 結果：呼叫成功，`usage` 23 token；**回應標頭 `x-litellm-response-cost` 沒有值**；用戶端沒有任何錯誤或警告
4. 直接查 PostgreSQL（約 2 分鐘後）：

| 資料 | token | spend |
|---|---|---|
| `LiteLLM_SpendLogs` 該筆明細 | 23 | **0** |
| 虛擬金鑰累計（max_budget 0.01） | — | **0** |

**判讀：**
- LiteLLM **知道用了多少 token，卻不知道值多少錢**；這把金鑰可以無限呼叫，預算永遠不會觸發
- 因果鏈：為了安全關掉線上價格表（E15）→ 新模型沒被收錄 → 預算安靜失效 → **驗簽章、鎖版本還不夠，價格資料也是治理的一部分**
- 與 E19（沒設資料庫時安靜失去預算）同類：系統看起來正常，治理功能其實已經沒了
- 本案對策（D30）：單價放 repo 設定檔；**設定檔沒有單價的模型一律拒絕呼叫**，不當成 0 元

**附帶觀察：**
- 9/25 被擋下的探針請求（`gpt-test`）也記進了 SpendLogs：失敗的請求同樣留紀錄，對稽核是好設計
- `startTime` 以 **UTC** 儲存（09:29:50 = 台北 17:29:50）；本案 D2 的額度週期是台北時間，M2 要處理時區轉換
- 明細記錄的是底層名稱 `openai/gpt-6-luna`，不是對外名稱 `gpt-6-luna`

**日誌：** `m05-cost-map-check.log`、`m05-model-new.log`、`m05-unpriced-model-call.log`、`m05-unpriced-model-db.log`

---

## E24. 模型設定加密與手動補單價（M0.5 追加，2026-09-26 17:11、17:35）

**模型設定加密：** `/model/new` 送進去的是明文 `openai/gpt-6-luna`、`os.environ/OPENAI_API_KEY`，回傳的 `model`、`api_key` 都是密文。LiteLLM 以 `.env` 的 **`LITELLM_SALT_KEY`** 加密後存進資料庫。

- 連不是機密的模型名稱、「指路文字」都一起加密：資料庫外洩時，連「金鑰放在哪裡」都看不到
- 同一個明文兩次加密出的密文不同（`jfB8...` 對 `arv8...`）：每次加密使用隨機值，無法從密文比對出兩筆設定相同
- 數字型參數（單價）以明文存放
- **維運風險：`LITELLM_SALT_KEY` 不能輪替、不能遺失。** 一換掉，資料庫裡的模型設定全部解不開。正式環境要放 Secrets Manager、嚴格限制存取並備份，不能套用一般密碼的定期輪替習慣。與本案 D4 的 HMAC 金鑰同類：換金鑰，舊資料就對不上（E28 實際遇到）

**B 段：刪除後重新加入並手動填單價**
- 單價換算：輸入 $0.10 ÷ 1,000,000 = `1e-7`；輸出 $0.50 ÷ 1,000,000 = `5e-7`
- 最容易錯的是位數：少一個 0 就差 10 倍（同 E7 的單位陷阱）
- 回傳確認 `input_cost_per_token=1E-07`、`output_cost_per_token=5E-07`

**日誌：** `m05-model-new.log`、`m05-model-new-priced.log`

---

## E25. 花費是同步寫還是批次寫（觀察 4，2026-09-26 17:37）

**方法：** 呼叫一次後，每 2 秒查一次資料庫，共 20 次。同時看兩個值：虛擬金鑰的累計 spend（預算比對用）、`LiteLLM_SpendLogs` 總筆數（呼叫前為 9）。

**結果（以呼叫完成 17:37:06 為基準）：**

| 資料 | 最後一次舊值 | 第一次新值 | 寫入延遲 |
|---|---|---|---|
| SpendLogs 明細（9 → 10） | 17:37:13 | 17:37:16 | 約 **7～10 秒** |
| 金鑰累計 spend（0 → 值） | 17:37:18 | 17:37:20 | 約 **12～14 秒** |

**判讀：**
- **非同步、批次寫入：** 使用者拿到回答時，帳還沒記（17:37:13 兩者仍為舊值）。與本案 M5 非同步記帳同一思路
- **分兩次寫：** 先寫明細，再寫累計，相隔數秒
- 補上單價後回應標頭有值 `cost=6.799999999999999e-06`，與 E23 A 段（無單價、無值）形成對照

**附帶發現：浮點數誤差實證**
- 13 × 1e-7 + 11 × 5e-7 應為 **0.0000068**，LiteLLM 與 PostgreSQL 都存成 **6.799999999999999e-06**
- 二進位浮點數無法精確表示十進位小數；單次誤差極小，但百萬次加總會對不上帳
- 本案 D1 以 **micro-USD 整數**儲存金額，原本是文件上的理由，現在有實測證據

**限制（誠實記錄）：** 輪詢從 17:37:13 才開始（手動輸入指令），7 秒內的變化看不到；延遲為區間估計。

**日誌：** `m05-spend-write-timing.log`

---

## E26. 記帳寫入前當機 → 永久掉帳（M0.5 追加，2026-09-26 17:40）

**動機：** E25 顯示花費在回應後約 7～14 秒才寫入。測試這段空窗內當機的後果。

**方法：** 呼叫完成後立刻 `docker compose kill litellm`（SIGKILL，模擬斷電、記憶體耗盡、Fargate 工作被強制回收；程式沒有機會收尾）。不用 `stop`：`stop` 會先送結束通知，程式有機會把帳寫完，不像真實當機。

| 時間點 | 金鑰累計 spend | SpendLogs 筆數 |
|---|---|---|
| 呼叫前 | 6.799999999999999e-06 | 10 |
| 呼叫完成 17:40:28.423（`cost=6.8e-06`），17:40:29.247 被 kill | — | — |
| LiteLLM 停止中 | 6.799999999999999e-06 | 10 |
| 重啟 30 秒後 | 6.799999999999999e-06 | 10 |

**判讀：**
- 使用者已拿到回答、LiteLLM 已算出花費、OpenAI 已計費，但回應後 **0.8 秒**被強制終止 → 明細與累計都沒寫入；重啟後也沒補回 → **永久遺失**
- 原因：待寫入的花費只存在程式記憶體，程式一死就跟著消失
- 後果：**預算少扣**（使用者可超用）、**稽核少一筆**（查不到這次呼叫）

**照出本案設計的缺口（最重要）：**
- 決策書 2.2 原本寫「[7a] 回傳給使用者」與「[7b] 丟事件進 SQS」**平行**進行。照這樣寫，Gateway 在「回答已送出、事件還沒進 SQS」時當機，**一樣會掉帳**。SQS 只保護已經進到佇列的事件
- 修正（D31）：**先確認事件送進 SQS，再回答使用者**。代價是每次請求多一次 SQS 寫入（約十幾毫秒，相對模型回應的數秒可忽略）；換到「使用者拿到回答 = 帳一定在佇列裡」
- 待 M5 定案：SQS 寫入失敗時，回答照給並記錯誤，還是不給回答

**限制（誠實記錄）：**
- 只做一次
- 未測 `stop`（正常關機）是否會先把記憶體中的帳寫完
- 未設定 Redis；LiteLLM 多容器部署時的緩衝機制能否避免此情況，本次未驗證

**對帳的啟示：** OpenAI 後台今天會顯示 `gpt-6-luna` 成功呼叫的次數多於 LiteLLM 帳上有金額的筆數（E23 的 0 元、E26 的遺失）。用供應商帳單核對自己的帳（對帳）是發現這類問題的最後一道防線（12.5 待評估）

**日誌：** `m05-crash-lost-spend.log`

---

## E27. 輕度負載下的記憶體（觀察 2 補測，2026-09-26 17:44～17:49）

**方法：** 背景工作（`Start-Job`）連續呼叫 30 次（一次一個，非併發），前景每 3 秒 `docker stats --no-stream` 一次，共 10 次。LiteLLM 於 E26 被 kill 後重啟，本次為重啟約 3 分鐘後。

| 狀態 | 記憶體 |
|---|---|
| 待機（E16，首次啟動約 1 分鐘） | 584 MiB |
| 輕度負載，連續 30 次呼叫 | **574.2 → 578.3 MiB** |
| 本案 Fargate 規格 | 512 MiB |

**判讀：**
- 30 次呼叫只多約 4 MiB 並趨於平穩：記憶體主要是**啟動就佔用**，不是隨請求成長
- 結論不變：LiteLLM 至少需要 1 GB 規格
- `Receive-Job` 無輸出：30 次呼叫都沒有錯誤

**收尾查帳（17:49）：** SpendLogs 10 → **40** 筆，30 次全部寫入；累計 spend `0.00020429999999999998`（浮點尾差再次出現）。**正常運作時批次寫入不會掉帳，只有當機時會（E26）**

**限制（誠實記錄）：** 屬輕度負載；多人同時使用的併發負載未測。

**日誌：** `m05-memory-load.log`

---

## E28. 收尾與一次密鑰外洩的應變（2026-09-26 17:45～17:54）

**收尾：**
- `docker compose down`；`Remove-Variable` 清除所有金鑰變數
- OpenAI 金鑰 `m0-m05-lab` **撤銷**：狀態變為 `Revoked`，仍留在列表（保留稽核軌跡：看得到曾經存在、最後使用日期）（`m05-openai-key-revoked.png`）
- `.env` 刪除 `OPENAI_API_KEY` 那一行。M1 會另開新金鑰：實驗用過的金鑰已進過 `.env` 與容器，正式程式碼給一把沒在其他地方出現過的新金鑰，出事時容易追查

**事件：** 確認 `.env` 已刪除那一行時，記事本視窗開著 `.env`、疊在終端機上，截終端機畫面時把 **`LITELLM_MASTER_KEY`、`LITELLM_SALT_KEY`、`POSTGRES_PASSWORD` 三組明文一起拍進去**，並傳到了對話中。該截圖未存檔、未收錄於任何紀錄。

**風險評估：** 低。三組都只用於本機實驗環境：LiteLLM 只綁 `127.0.0.1`、資料庫不對外開埠、容器已關閉。但密鑰離開本機就視同外洩（SOC 事件處理的標準判斷）。

**兩難（E24 預言的風險當天就遇到）：** `LITELLM_SALT_KEY` 外洩後，不換 → 外洩的鹽值可以解開資料庫裡的密文；換掉 → 資料庫裡的模型設定全部作廢。

**處置：** 實驗已完成、證據都在日誌中，選擇**清掉資料庫、三組全部重新產生**：
```
docker compose down -v
$g = { [guid]::NewGuid().ToString("N") }
[IO.File]::WriteAllText("$PWD\.env", "LITELLM_MASTER_KEY=sk-$(& $g)`r`nLITELLM_SALT_KEY=$(& $g)`r`nPOSTGRES_PASSWORD=$(& $g)")
(gc .env).Count; (gi .env).Length
```
- 結果：volume `litellm-lab_pgdata` 已刪除；`.env` 為 **3 行、157 bytes**，與 E14 的計算一致
- 新密鑰**全程沒有出現在畫面上**：直接寫檔，不經記事本；`WriteAllText` 預設寫出無 BOM 的 UTF-8，避開 E14 的 UTF-16 問題
- `down -v` 時出現 `The "OPENAI_API_KEY" variable is not set` 警告：`docker-compose.yml` 仍引用此變數、`.env` 已無此值，屬預期；`.env.example` 補一行 `OPENAI_API_KEY=` 作範本

**教訓：**
- 確認 `.env` 內容時，**只看行數、長度、前綴，不打開檔案截圖**
- 正式環境中，SALT_KEY 這類「外洩了也很難換」的金鑰，必須放在 Secrets Manager 並嚴格限制存取；這正是它的風險所在

---

## M0.5 總結（2026-09-26 完成）

| # | 觀察 | 結論 | 證據 |
|---|---|---|---|
| 1 | 拿掉資料庫，預算還有效嗎 | 斷線 → 503 拒絕並自動恢復；沒設 → 無虛擬金鑰、無每人預算、無警告 | E18、E19 |
| 2 | 記憶體 | 待機 584 MiB、輕度負載 574～578 MiB，超過 512 MiB 規格；成本只多約 18%，主要差異在常駐資料庫 | E16、E19、E27 |
| 3 | 啟動時對外連線 | 下載 GitHub `main` 分支的價格表；以設定關閉 | E15 |
| 4 | 花費同步或批次寫 | **批次**：明細約 7～10 秒、累計約 12～14 秒後寫入 | E25 |
| 5 | 官方預設值安全性 | 7 項需強化，已全數處理 | E13 |
| 追加 ① | 內建價格表缺新模型 | 預算安靜失效（token 有記、金額為 0） | E23 |
| 追加 ② | 寫入前當機 | 永久掉帳；照出本案 2.2 流程的缺口 | E26 |
| 追加 ③ | 模型設定加密 | SALT_KEY 不能輪替；當天就遇到外洩兩難 | E24、E28 |
| 附帶 | 浮點數誤差 | 6.8e-6 存成 6.799999999999999e-06，佐證 D1 用整數 | E25、E27 |

**M0.5 狀態：✅ 完成**（OpenAI 呼叫實際花費約 $0.0003）
