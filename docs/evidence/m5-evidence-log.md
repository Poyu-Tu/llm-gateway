# M5 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID；個人帳號名稱（含終端機提示字元與路徑中的使用者資料夾名稱，一律寫成 `<user>`）。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`（檔名以 `m5-` 開頭，正式清單照決策書 11.4 的 S 編號），日誌另存於 `docs/logs/`。
> E 編號接續 `m4-evidence-log.md`（E108～E126），M5 從 E127 開始。
> 紀錄日期：2026-10-20 建立（M4 於 10/20 結案；M5 檢查點併入 11/1 的 M6 檢查點，本人目標 10/25 前完成 M5）

---

## 紀錄規則（沿用 M4）

| # | 東西 | 規則 |
|---|---|---|
| 1 | 證據紀錄 | 本檔；每完成一組步驟就更新，回傳完整新版 |
| 2 | 里程碑報告 | 整關驗證通過後寫 `docs/milestones/m5-report.md`，格式同 M4；只向本人確認花費時間與實際花費 |
| 3 | 決策書 | M5 結案時出 v2.11；期間的新定案先記在本檔，待改項目列在本檔的「決策書 v2.11 待改項目」表 |
| 4 | 截圖、日誌、錄影 | 收到就改名、遮蔽、回傳；只截 11.4 清單（S12～S14）與出錯、決策、驗證的關鍵畫面；每個驗收條件錄一段，影片不進 repo；錄 AWS 主控台時框選範圍不含最上面那一列 |
| 5 | 存放 | 所有回傳的文字檔也存一份到 Project |
| 6 | 個資測試 | 只用假資料 |
| 7 | 收錄範圍 | 只收與專題本身有關的內容；不記本人的預測、不寫責任歸屬、不寫個人環境的事 |
| 8 | 推送 | 一律開分支、開 PR、三個必要檢查（`Tests`、`Image scan`、`Config scan`）綠了才合併；commit 英文、PR 中文，都不附署名 |

---

## E127. M5 開工：七項定案（2026-10-20 09:04～11:09，公司電腦，只讀程式）

**依據：** 決策書 v2.10 的 2.2（計費事件順序）、3.2、3.3、7.10、8.2 的 M5、12.5（SQS 寫入失敗、預扣、`usage` 表）、D12、D31；`docs/milestones/m4-report.md` Part C；`app/main.py`（`main` = `bd849c1`，從 GitHub 公開 repo 讀）。

**範圍：** 只有定案，沒有寫程式、沒有登入 AWS。

**生活比喻：** 餐廳要加一個出單夾（SQS）和一位後台會計（Lambda Worker）。開工前先講好：出單夾壞了怎麼辦、誰記哪本帳、同一張單收到兩次怎麼辦、要不要先刷卡預授權、會計坐在哪裡、消防演習怎麼演、工具要不要先更新。

### 讀程式時確認的現況

`chat_endpoint()` 有 4 個地方寫稽核，只有成功那條路花錢：

| 行號 | 情況 | 花錢 |
|---|---|---|
| 168 | 額度用完，回 429 | 否 |
| 192 | 查不到模型設定，回 500 | 否 |
| 217 | 模型呼叫失敗，回 502／503 | 否 |
| 247～252 | 成功：`add_usage()` 扣額度，再 `write_audit_record()` | 是 |

一次成功的聊天碰資料庫 6 次（`api_keys` 讀 1、`quotas` 讀 2、加 0、扣錢、`audit` 寫 1）；決策書 v2.8 的「最多 5 次」是稽核還在檔案裡的時候。

### 定案（本人逐題作答）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | SQS 寫不進去時 | **B：回答照給，改走 M4 的同步記帳**（Gateway 自己扣額度、寫 `audit`）；兩條路都失敗才印一行日誌並告警 | A 回 503：錢已經付給 OpenAI，使用者重試會再花一次，SQS 一壞服務就停。C 只印日誌、事後補收：雲端最可能的故障是設定錯誤（DNS 漏網域、IAM 少權限），會連續發生，這段時間額度完全失效 | Gateway 對 `quotas` 的寫入權限拿不掉；維護兩條記帳路線；「SQS 其實收到、回應逾時」會重複處理（第 3 題處理） |
| 2 | 稽核由誰寫 | **B：成功那條路，一筆事件帶完整稽核紀錄進 SQS，Worker 一次寫 `usage`、加 `quotas`、寫 `audit`；沒花錢的三條路（429、500、502／503）Gateway 照樣直接寫** | A Gateway 4 處都自己寫、SQS 只帶扣錢：一次成功拆成兩次寫入，中間當機帳就對不上（同 M0.5 拆 LiteLLM 時發現的缺口），稽核寫入仍在回答之前。C 4 條都送事件：沒花錢的紀錄綁上 SQS 換不到好處，事件要分好幾種 | 稽核有兩個寫入者；Gateway 對 `audit` 的 `PutItem` 拿不掉（備援要用）；Worker 那條路不會寫出 `charged: false`，只有備援路線會 |
| 3 | 重複扣款與 `usage` 主鍵 | **B：一個交易（`TransactWriteItems`）寫三本帳**：`usage` 新增、`quotas` `ADD`、`audit` 新增，`usage` 與 `audit` 都加「不存在才寫」；任一條件不成立整個交易取消。Worker 與 Gateway 備援**共用同一支函式**。`usage` 主鍵：`user_id`（分區）＋ `timestamp#request_id`（排序）。Worker 遇到「條件不成立而取消」當作已入帳、刪訊息；其他錯誤丟出、讓 SQS 重送，失敗 3 次進 DLQ | A 不防重複：多扣的錢記在使用者身上。C 不建 `usage`：按人查用量要掃 `audit` 全表，M6 對帳又要補回來 | Gateway 多一個 `usage` 的 `PutItem`；交易寫入費用 2 倍（Demo 的量不到一分錢）；交易的 IAM 與 Endpoint Policy 寫法要在寫 Terraform 前查證；雲端取消交易的錯誤格式要上雲確認；M2～M4 的扣款測試要跟著改 |
| 4 | 預扣 | **A：M5 不做**，維持「呼叫前檢查、事後記帳」；故障演練實測同時送多個請求超出多少；預扣留在升級路線 | B 完整預扣：以「最多可能花多少」做條件加法、事後退差額——便宜模型最多約 1,400 micro-USD，比 alice 的額度 1,000 還大，alice 一次都叫不了；退款路線本身是新故障點。C 只擋大的（已用＋最多可能花多少 > 額度就不呼叫）：擋不住同時送多個請求，alice 一樣第一次就被擋 | 額度是軟上限；一次最多超扣：便宜模型約 1,400、強模型約 28,000 micro-USD（約 US$0.028，D58 的輸出上限讓它算得出來） |
| 5 | Worker 放哪裡 | **A：照 D12 放私有子網；Lambda 函式本身放每日層**；SQS、DLQ、Worker 的角色、日誌群組放長期層 | B 放 VPC 外、全放長期層：destroy 不受影響，但繞過 DNS 防火牆、推翻 D12 | 放 VPC 的 Lambda 會建網卡，拆的時候 AWS 收回網卡要一段時間，拆子網與安全群組可能要等（要實測），destroy workflow 30 分鐘上限可能不夠；執行角色要多「建網卡」權限（只能寫 `Resource: *`）；destroy 角色要多刪 Lambda 的權限。退路：實測超過上限就改 B，理由與數字記進決策書 |
| 6 | 故障演練 | **A：一次上雲做完 0～7**（見下表），約 2 小時，估約 US$0.25 | B 備援路線只用本機測試證明：沒有雲端證據。C 只做 S12、S13（8.4 砍除順序第 6 項）：少了對照 LiteLLM 的那一項與超扣數字 | 第 6 步要多 apply 兩次（只改 DNS 清單） |
| 7 | Terraform 1.16.6 | **A：M5 第一個 PR 單獨升級**：`destroy.yml` 的 `TF_VERSION`、`TF_SHA256` 兩行（指紋由本人從官方 `SHA256SUMS` 抄）、個人電腦 winget 升級；升完對長期層 `plan` 看到 `No changes` 才算完成 | B 11/7 之後再升：待辦一直掛著，M6 寫 CD 時又要面對 | 多一個小 PR，約 15 分鐘 |

### 第 6 題的演練順序

| # | 做什麼 | 怎麼做 | 證明什麼 |
|---|---|---|---|
| 0 | 正常聊一次 | bob 問一題 | Worker 寫好三本帳；**S14**（`audit` 表只有指紋與摘要） |
| 1 | 停觸發 | `aws lambda update-event-source-mapping --no-enabled` | **S12** 前半 |
| 2 | 量超扣 | alice 連續送 3～5 題 | 每題都拿到回答（**S12**），佇列訊息越堆越多，`quotas` 不動 |
| 3 | 停 Gateway | `aws ecs stop-task` | 訊息還在佇列（對照 M0.5 LiteLLM 寫帳前被停掉就掉帳） |
| 4 | 重開觸發 | `--enabled` | 帳全部補上；記錄 alice 實際超出多少 |
| 5 | DLQ | CLI 往佇列丟一則格式壞掉的訊息 | Worker 失敗 3 次後進 DLQ（**S13**）；正常的帳不受影響 |
| 6 | 備援路線 | DNS 放行清單暫時拿掉 SQS 的網域、apply → 聊一次 → 加回來 | 回答照給、Gateway 自己記帳、日誌多一行 |
| 7 | 拆 | 按 destroy workflow，計時 | Lambda 網卡收回要多久；修好後的一鍵拆光（M4 帶來）；DNS 網域結尾的點有沒有消除假改動（M4 帶來） |

- 本機不另裝 SQS 模擬器：Gateway 送 SQS 用替身；Worker 的 handler 直接餵假事件、連 DynamoDB Local 測交易
- 錄影：S12、S13 與第 3 步；S14 只截圖

### 實作時照做的預設值（Claude 提出，本人沒有異議；實作時再確認）

| 項目 | 預設 |
|---|---|
| Worker 打包 | zip，只放專案自己的程式；boto3 用 Lambda 內建版本，不裝第三方套件；用 HashiCorp 官方 `archive` 外掛打包（鎖版本、過冷卻期、鎖檔進 Git） |
| 共用函式 | 第 3 題的交易寫成一個共用模組，Gateway 備援與 Worker 都 import |
| SQS | 批次大小 1；失敗 3 次進 DLQ；DLQ 保留 14 天；隱藏時間設 Lambda 逾時的 6 倍（AWS 文件建議值，寫 Terraform 時查證） |
| DNS 放行清單 | 加 SQS 的網域（`sqs.ap-northeast-1.amazonaws.com`，寫 Terraform 時以 ALERT 階段的查詢日誌確認實際網域） |
| Gateway 的 SQS 連線 | 逾時與重試比照 DynamoDB（連線 2 秒、讀取 5 秒、最多 2 次），DNS 被擋時要快速失敗才會走備援 |

### 查到、寫進設計的事

- **Worker 幾乎不需要網路：** SQS 觸發由 Lambda 服務代為拉訊息、日誌由 Lambda 服務代寫，都不經過函式自己的網路；寫 DynamoDB 走現有的 Gateway Endpoint。所以放 VPC 內不用新增放行網域
- **SQS Standard 是「至少送到一次」：** 加上第 1 題的備援，同一筆帳可能被處理兩次，所以第 3 題要去重
- **交接檔的更正：** `m4-closed-handoff.md` 寫 Terraform 升級要改「兩層 `versions.tf`」；實際 `infra/persistent/versions.tf` 是 `required_version = "~> 1.16.5"`（1.16.x 都允許），不用改。要改的只有 `destroy.yml` 的兩行與本機安裝
- **Terraform 1.16.6（10/14 發佈）的內容**（[releases.sh](https://releases.sh/hashicorp/terraform-releases.md)）：兩個錯誤修正（`cloud` 後端的工作區標籤、`terraform test` 的已棄用輸出）與 CVE-2026-78669（HTTP/2 資源耗盡，前提是外掛或模組的下載來源被控制）；S3 後端、鎖檔、AWS 登入沒有變動

### 演練證明不了的缺口（誠實記錄）

順序是「呼叫 OpenAI → 送 SQS → 回答」。Gateway 若在**拿到 OpenAI 回答之後、送 SQS 之前**當掉：使用者看到錯誤、OpenAI 的錢已經花了、沒有記帳也沒有稽核。空窗只有幾十毫秒，正式環境要靠和 OpenAI 後台對帳補（決策書 12.5 列在 M6）。

### 面試可用的說法

- 「記帳事件送不進 SQS 時，我不拒絕回答，因為錢已經付給 OpenAI 了；我改走原本的同步記帳。雲端最可能的故障是設定錯誤，會連續發生，只印日誌的話這段時間額度等於失效。」
- 「SQS Standard 保證至少送到一次，不是剛好一次。我用一個 DynamoDB 交易同時寫用量明細、加額度、寫稽核，用請求單號當去重的鑰匙，送兩次也只扣一次；而且三本帳要嘛全寫、要嘛全不寫。」
- 「我沒有做預扣。照最壞情況預扣的話，便宜模型一次最多約 1,400 micro-USD，比我的示範帳號額度還大，她會一次都叫不了。我算過一次最多超扣多少：強模型約 0.028 美元。硬上限的做法是預扣，我知道它的代價。」
- 「Worker 放在私有子網，跟容器受同一套出口管控。它其實只需要連 DynamoDB，走免費的 Gateway Endpoint 就到得了，所以放行清單一個網域都不用加。代價是拆的時候 AWS 收回網卡要時間，我會實測。」

---

## E128. Terraform 1.16.6 升級（2026-10-20 12:04～，公司電腦，分支 `chore/terraform-1.16.6`）

**依據：** E127 定案 7；決策書 v2.10 的 D19、12.5「Terraform 1.16.6」。

**生活比喻：** 換一把同型號、修好小毛病的新扳手。工地（雲端）上的東西不動；要確認的是「換了扳手之後，藍圖和工地還是對得上」（`plan` 看到 `No changes`），以及「工地另一邊的機器人（destroy workflow）也拿到同一把、而且驗過是原廠貨」（指紋）。

### 本人 10/20 的新定案：在哪台電腦做

| 項目 | 定案 | 理由 | 弱點 |
|---|---|---|---|
| 公司電腦能做什麼 | **沒碰到金鑰的都可以做，包含 AWS CLI**（`aws login`、`plan`）；OpenAI 金鑰與 `.env` 仍只在個人電腦 | 公司電腦也有 AWS CLI；`aws login` 是瀏覽器登入換來的暫時憑證，電腦上不留長期金鑰（M0 已刪長期金鑰） | 修訂 D34 的 v2.10 補充（「登入 AWS 與 `plan`/`apply` 只在個人電腦」）。**每日層 `apply` 在公司網路要注意：** ALB 只放行 `admin_cidr`，在公司網路查到的是全公司共用的對外 IP，放行它等於全公司都連得到 ALB；每日層 apply 與上雲演練仍建議在個人電腦做 |

### 做了什麼

| # | 步驟 | 結果 |
|---|---|---|
| 1 | 公司電腦的 repo `git pull` | 從 `b259965` 快轉到 `bd849c1`，工作區乾淨 |
| 2 | 開分支 `chore/terraform-1.16.6` | 成功 |
| 3 | 指紋：Claude 從官方 `https://releases.hashicorp.com/terraform/1.16.6/terraform_1.16.6_SHA256SUMS` 讀 `linux_amd64` 那一行；本人在公司電腦 `irm` 同一個網址 | `38034b38d03096399a7a1264a14561a8029b2b496fd1f169452656e53968f1b7  terraform_1.16.6_linux_amd64.zip`；**兩份一致**（公司電腦 `irm` 印出 15 行，`linux_amd64` 那一行與 Claude 讀到的相同） |
| 4 | `destroy.yml` | `TF_VERSION` 1.16.5 → 1.16.6、`TF_SHA256` 換成上面的指紋；兩行註解改成「1.16.6、10/20」與「`versions.tf` 寫 `~> 1.16.5`，同一個 1.16.x 不用改」（原註解寫三處要一起改，與 E127 的更正不一致）。4 行改動 |
| 4b | `.gitignore` 加一行 `*.tfplan`（本人 10/20 同意放進這個 PR） | 計畫檔含帳本內容；原本沒有擋（M4 證據紀錄 10/20 的更正）。擋好之後，之後就算用 `plan -out` 存計畫檔，也不會被 `git add` 收進去 |
| 5 | 本機 `winget upgrade Hashicorp.Terraform` | winget 從 `releases.hashicorp.com` 下載 `terraform_1.16.6_windows_amd64.zip`（35.0 MB）、「已成功驗證安裝程式雜湊」；`terraform version` → **`Terraform v1.16.6 on windows_amd64`**。第一次把套件名打成 `Terrafrom`，winget 回「嘗試更新來源失敗」，改正後成功 |
| 6 | 清 `AWS_*` 環境變數 → `aws login`（瀏覽器登入，更新 `default` 設定檔的暫時憑證）→ 長期層 `init`（`Successfully configured the backend "s3"`、沿用鎖檔的 `hashicorp/aws` v6.68.0，沒有問要不要搬移 State）→ `plan` | **`No changes. Your infrastructure matches the configuration.`**；Refresh 了 State bucket 政策、destroy 角色、任務角色與執行角色的政策等；最後 `Releasing state lock`（S3 鎖檔正常釋放） |

### 這一步證明了什麼、沒證明什麼

- **證明：** 本機用 1.16.6 讀同一份 S3 帳本、同一份 `.terraform.lock.hcl`，長期層沒有任何改動；`versions.tf` 的 `~> 1.16.5` 接受 1.16.6
- **沒證明：** destroy workflow 在 GitHub 上用 1.16.6 實際下載、比對指紋、拆除；要等 M5 第一次 apply 每日層後按 destroy 才知道（與 M4 帶來的「修正後的一鍵拆光」同一次實測）。每日層的 `plan` 這次沒有跑（每日層目前是空的）

---

## E129. Cost Explorer：M4 期間的 AWS 實際金額（2026-10-20 約 14:00～15:43，公司電腦）

**依據：** `m4-closed-handoff.md` 第 3 節；決策書 v2.10 的 6.3「M4 實測花費」（AWS 實際金額待補）。

**指令：** `aws ce get-cost-and-usage --time-period Start=2026-10-14,End=2026-10-21 --granularity DAILY --metrics UnblendedCost`（每次呼叫 US$0.01，這筆會出現在之後的帳上）。日期是 **UTC**：`2026-10-19` 那一格 = 台北 10/19 08:00～10/20 08:00。

| UTC 日期 | UnblendedCost（USD） | 那天做了什麼 |
|---|---|---|
| 10/14 | 0.0000050016 | 開工前準備（本機），身分聯盟探測 |
| 10/15 | 0.000005 | 本機；長期層骨架還沒上雲 |
| 10/16 | 0 | 沒有上雲 |
| 10/17 | 0.00023588 | 長期層上雲（State bucket、表、ECR、角色等） |
| 10/18 | 0.000172354 | 每日層免費骨架（C 段）與 `destroy #1` |
| 10/19 | **0.2909840749** | D、E 段上雲驗收（台北 20:49～22:38）、`destroy #2` 失敗後本機補拆 |
| 10/20 | 0 | 每日層已拆；當天資料可能還沒進來 |
| **合計** | **約 0.2914** | |

- 每一格都標 `"Estimated": true`（月底結帳前都是估計值），10/20 那一格之後可能再變動
- **跟估算對照：** 決策書 v2.10 用 6.2 的單價估 D、E 段約 US$0.22（每小時約 0.12 × 約 1 小時 50 分），實際 10/19 那一格約 **US$0.29**，多約 32%

### 10/19 分計費項目（`--group-by Type=DIMENSION,Key=USAGE_TYPE --output table`，再一次 US$0.01）

| 計費項目 | 金額（USD） | 換算 |
|---|---|---|
| `APN1-NatGateway-Hours` | **0.186** | = 3 × 0.062：**計了 3 小時** |
| `APN1-LoadBalancerUsage` | 0.0486 | = 2 × 0.0243：計了 2 小時 |
| `APN1-PublicIPv4:InUseAddress` | 0.026823615 | ≈ 5.4 個「IP·小時」（ALB 兩個、NAT 一個） |
| （第一項，名稱在終端機捲動上限之外，沒看到） | 0.0224500445 | 推定是 Fargate vCPU（0.25 vCPU × 0.05056 ≈ 1.8 小時），**未確認** |
| `APN1-PublicIPv4:IdleAddress` | 0.000973615 | ≈ 0.19 小時（約 12 分鐘）：彈性 IP 沒掛在 NAT 上、還沒被釋放的時間，對得上 `destroy #2` 卡在 `DisassociateAddress`、本機補拆前那一段 |
| `APN1-NatGateway-Bytes` | 0.0003954081 | 流量費，可以忽略 |
| `APN1-Requests-Tier1`、`Requests-Tier2` | 0.0002397、0.00003737 | S3 請求（State、映像層） |
| `APN1-TimedStorage-ByteHrs` | 0.0000708617 | S3 儲存 |
| `APN1-WriteRequestUnits`、`ReadRequestUnits` | 0.000013585、0.00000228 | DynamoDB |
| `APN1-LCUUsage` | 0.0000009778 | ALB 的 LCU，可以忽略 |
| 其他（`Lambda-GB-Second`、`VendedLog-Bytes`、`KMS-Requests`、跨區 `AWS-In-Bytes`、`ScheduledInvocation`、`USE1-Catalog-Request` 等） | 0 | |

- 看得到的各項加總約 0.2858；跟 10/19 的總額 0.2910 差約 0.005，推定是沒看到的 Fargate 記憶體那一項（0.5 GB × 0.00553 × 1.8 小時 ≈ 0.005），**未確認**
- **多出來的錢在哪裡（有證據）：** 主要是 **NAT 計了 3 小時**（0.186），估算時只算 1 小時 50 分（約 0.114）。可能的原因（推測）：NAT 在驗收開始（20:49）前就建好了、而且不滿一小時也照一小時算；ALB 也是 2 小時（0.0486）。彈性 IP 閒置只有約 12 分鐘、0.001，不是主因
- **學到的：** 估雲端花費時，按小時計費的資源要算「建好到拆掉」的整段，還要把不滿一小時的部分進位成一小時；M5 上雲演練（約 2 小時）照這個方法重估
- 長期層閒置幾乎不花錢的說法得到佐證：10/16、10/20 都是 0，10/17、10/18 加起來不到 US$0.0005

**寫進哪裡（今晚 M4 docs PR）：** `docs/milestones/m4-report.md` 第 8 節、決策書 v2.10 的 6.3 與 M4 結果的「實際時間 / 成本」、變更紀錄的「時間與花費」：AWS 實際約 US$0.29（Cost Explorer，UTC 10/14～10/20，估計值），比估算多的主因是 NAT 計了 3 小時；M4 報告可以在花費那一節補一句「按小時計費要算整段、不滿一小時進位」。

---

## 目前進度（2026-10-20）

- M5 七項定案完成（E127）
- Terraform 1.16.6：PR #17 合併（`main` = `46fd3eb`），6 個檢查全過（E128）
- M4 的 AWS 實際金額：約 US$0.29（E129），今晚寫進 M4 docs PR
- 下一步：
  1. 個人電腦（今晚）：M4 結案的 docs PR（`docs/m4-closure`）；這個 Terraform PR 只動 `destroy.yml` 與本檔（PR #17 已合併），跟個人電腦上還沒推的三個 M4 檔不重疊，`git pull` 不會衝突；M4 docs PR 要一併放進本檔（E129 的新版）
  2. M5 程式與 Terraform（公司電腦可寫草稿、跑不碰金鑰的測試；上雲演練在個人電腦）
- 下一筆證據是 **E130**

---

## 決策書 v2.11 待改項目

| # | v2.10 的位置 | 要改什麼 |
|---|---|---|
| 1 | 2.2、3.3、12.5「SQS 寫入失敗時的處理」 | 回答照給，改走同步記帳；兩條都失敗才印日誌並告警；12.5 該列劃掉（E127） |
| 2 | 2.2 [9]、3.1 Worker 職責、3.2 `audit` 的「誰讀寫」 | 成功那條路由 Worker 寫三本帳；沒花錢的三條路 Gateway 直接寫（E127） |
| 3 | 3.2 `usage`、12.5「`usage` 表」、7.10 | `usage` 主鍵 `user_id` ＋ `timestamp#request_id`；一個交易寫三本帳、以單號去重；Worker 與 Gateway 備援共用函式（E127） |
| 4 | 7.10、7.9「預扣」、12.5「預扣」 | M5 不做；一次最多超扣的數字；12.5 該列改成「升級路線」（E127） |
| 5 | D12、3.5、5.1 兩層的表 | Worker 放私有子網、Lambda 函式在每日層；SQS、DLQ、角色、日誌在長期層（E127） |
| 6 | 8.2 的 M5 驗證 | 演練 0～7 的順序（E127） |
| 7 | D19、12.5「Terraform 1.16.6」與「`.gitignore` 沒有擋 `*.tfplan`」、PART 9 IaC 列 | 升級只改 `destroy.yml` 兩行與本機安裝，`versions.tf` 不用改；1.16.6 已升、長期層 `plan` 乾淨；`.gitignore` 已擋 `*.tfplan`；12.5 兩列劃掉（E127、E128） |
| 8 | 2.2 v2.10 補充 | 一次成功的聊天碰資料庫 6 次（不是 5 次）（E127） |
| 9 | D34、PART 9「開發機」列 | 公司電腦可做不碰金鑰的事，含 `aws login`、`plan`；金鑰、`.env`、真實呼叫仍只在個人電腦；每日層 apply 注意 `admin_cidr`（E128） |

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| 交易的 IAM 動作與 Endpoint Policy 寫法 | 寫 Terraform 前查 AWS 文件 | M5 寫 Terraform 時 |
| Lambda 網卡收回時間 | 第 6 題第 7 步實測；超過 destroy workflow 上限就改放 VPC 外 | M5 上雲 |
| SQS 隱藏時間與 Lambda 逾時的數字 | 隱藏時間 = 6 × Lambda 逾時（查證後定） | M5 寫 Terraform 時 |
