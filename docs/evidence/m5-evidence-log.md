# M5 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID；個人帳號名稱（含終端機提示字元與路徑中的使用者資料夾名稱，一律寫成 `<user>`）。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`（檔名以 `m5-` 開頭，正式清單照決策書 11.4 的 S 編號），日誌另存於 `docs/logs/`。
> E 編號接續 `m4-evidence-log.md`（E108～E126），M5 從 E127 開始。
> 紀錄日期：2026-10-20 建立，10-21 更新（E130～E133），10-22 更新（E134～E136）（M4 於 10/20 結案；M5 檢查點併入 11/1 的 M6 檢查點，本人目標 10/25 前完成 M5）

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

## E130. M5 第一塊：三本帳的共用交易 `app/ledger.py`（2026-10-20～10-21，公司電腦與個人電腦，分支 `feat/m5-ledger`）

**依據：** E127 定案 2、3；決策書 v2.10 的 3.2、7.10、12.5「`usage` 表」。

**生活比喻：** 便利商店結帳一次要寫三個地方：發票明細（`usage`）、會員卡的本月累積消費（`quotas`）、店內的紀錄簿（`audit`）。三個要嘛都寫、要嘛都不寫；同一張發票號碼（`request_id`）掃兩次，收銀機要說「這張結過了」，不能扣兩次錢。

**範圍：** 只有程式與本機測試（DynamoDB Local），沒有登入 AWS、沒有碰金鑰。Worker、SQS、Terraform 都還沒寫。

### 開工前的三個設計題（10/20，本人逐題作答）

| # | 題目 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 1 | 共用函式放哪裡 | **A：`app/ledger.py`**；Worker 打包只挑 `app/__init__.py`、`app/db.py`、`app/ledger.py`、`worker/handler.py` | 放進 `app/quota.py` 或 `app/audit.py`：Worker 打包會連帶拉進遮罩、路由等用不到的程式 |
| 2 | `usage` 存哪些欄位 | **A：只存記帳要的**：`request_id`、`period`、`model`、`input_tokens`、`output_tokens`、`reasoning_tokens`、`cost_micro_usd`；主鍵 `user_id`（分區）＋ `ts_request` = `timestamp#request_id`（排序） | 整筆抄 `audit`：路由理由、降級、個資類別存兩份，兩邊改欄位時容易對不上 |
| 3 | 重複時怎麼回報 | **A：`record_charge()` 回 `True`（這次寫進去）／`False`（已經入過帳）**；只有「被擋的每一件都是 `ConditionalCheckFailed`」才算重複，混了 `TransactionConflict` 等其他原因就往外丟 | 只要有一件「已經存在」就算重複：混了「同時有人在改同一筆額度」時，這次其實沒寫進去卻被當成已入帳，帳就掉了 |

### 改了哪些檔

| 檔案 | 誰寫 | 內容 |
|---|---|---|
| `app/db.py` | 本人 | `USAGE_TABLE = "usage"` |
| `scripts/create_tables.py` | 本人 | 建第四張表 `usage`（`user_id` + `ts_request`） |
| `app/ledger.py`（新） | 本人（填空） | `USAGE_FIELDS`、`ALREADY_EXISTS_CODE`、`usage_sort_key()`、`to_dynamodb_item()`、`is_duplicate()`、`record_charge()` |
| `tests/test_ledger.py`（新，14 個） | Claude | 6 個不連資料庫（排序鍵、`is_duplicate()` 的 5 種情況）＋ 8 個連 DynamoDB Local（三本都寫、`usage` 只有記帳欄位、`charged=True` 且不改呼叫者的 dict、累加、送兩次只扣一次、只有 `usage` 已存在、只有 `audit` 已存在、`usage` 表不存在時三本都不寫） |
| `tests/test_create_tables.py` | Claude | 三張表改四張，加 `usage` 主鍵測試 |

### `record_charge()` 怎麼做

1. 複製一份 `record` 再加 `charged = True`（呼叫者手上那份不被改到）
2. 從 `record` 挑出 `USAGE_FIELDS` 組成 `usage` 那一列
3. 一個 `TransactWriteItems` 三件事：`usage` `Put`（`attribute_not_exists(user_id)`）、`quotas` `Update`（`ADD used_micro_usd :amount`）、`audit` `Put`（`attribute_not_exists(request_id)`）
4. 交易被取消時交給 `is_duplicate()`：是重複就回 `False`，不是就往外丟（讓 SQS 重送或讓備援路線知道）

### 填空時寫錯、後來改對的地方（都是讀程式時抓到，沒有進 commit）

| 函式 | 寫成 | 應該是 | 為什麼不行 |
|---|---|---|---|
| `is_duplicate()` | 第 ④ 格 `return True`（「沒有任何原因」時） | `return False` | 取消了卻沒有原因時不能猜成重複，否則可能把沒寫進去的帳當成已入帳 |
| `is_duplicate()` | 第 ⑤ 格 `code != exc` | `code != ALREADY_EXISTS_CODE` | 要比的是取消原因的代碼字串，不是整個錯誤物件；寫成 `exc` 時每一件都「不相等」，永遠回 `False` |
| `record_charge()` | 函式第一行 `period, str` | `period: str` | Python 不會報錯，而是多出第四個叫 `str` 的參數：呼叫時少一個參數（8 個連資料庫的測試全紅），而且函式裡的 `str(...)` 被蓋掉 |
| `record_charge()` | 第 ⑦ 格 `"user_id"` | `"attribute_not_exists(user_id)"` | `ConditionExpression` 要放一個會成立或不成立的條件句，只有欄位名時 DynamoDB 會回 `ValidationException`、拒收整個交易 |

### 測試結果（10/21，公司電腦）

- `docker compose up -d` → `uv run pytest`：**340 passed**（25.79 秒；325 + `test_ledger.py` 14 + `test_create_tables.py` 新增 1）
- 本機 DynamoDB Local 交易被取消時**有**附 `CancellationReasons`，「送兩次只扣一次」是綠的；**雲端的錯誤格式要上雲確認**

### 破壞實驗（本人的版本，做完都改回來）

| # | 拆掉什麼 | 預期 | 實際 |
|---|---|---|---|
| ① | `is_duplicate()` 的「每一件都是 `ALREADY_EXISTS_CODE`」那段迴圈（註解掉） | 只有 `test_is_not_duplicate_when_a_reason_is_conflict` 紅 | `uv run pytest tests/test_ledger.py` → **1 failed, 13 passed**（2.19 秒），紅的就是那一個：`assert True is False` |
| ② | `usage` 那件的 `ConditionExpression`（註解掉） | 只有 `test_record_charge_stops_when_usage_row_already_exists` 紅 | **1 failed, 13 passed**（1.73 秒），紅的就是那一個：`assert True is False`（`usage` 被蓋過去、`quotas` 扣了錢、回 `True`） |
| — | 兩個都改回來 | 全綠 | `uv run pytest` → **340 passed**（20.20 秒） |

- 實驗 ② 時「同一筆送兩次」那題**仍是綠的**：`audit` 的「不存在才寫」也擋得住。兩道互為備援，所以要另外有「只有 `usage` 已存在」「只有 `audit` 已存在」兩題各自顧一道

### 這一步證明了什麼、沒證明什麼

- **證明：** 三本帳在同一個交易裡要嘛全寫、要嘛全不寫（`usage` 表不存在時 `quotas`、`audit` 都沒寫）；同一個 `request_id` 送兩次只扣一次；混了其他取消原因時不會誤判成重複
- **沒證明：** 雲端 DynamoDB 取消交易時的錯誤格式；交易的 IAM 與 Endpoint Policy 寫法；Gateway 與 Worker 還沒改成呼叫這一支（`chat_endpoint()` 仍是 M4 的 `add_usage()` ＋ `write_audit_record()`）

### 面試可用的說法

- 「SQS 保證至少送到一次，不是剛好一次。我把用量明細、加額度、寫稽核放進同一個 DynamoDB 交易，兩本新增的帳都加『不存在才寫』，用請求單號去重；送兩次的話整個交易取消，錢只扣一次。」
- 「交易被取消不一定是重複。我只有在每一件被擋的原因都是『已經存在』時才當作已入帳；混了『同時有人在改同一筆』就往外丟、讓它重試，不然那筆帳會默默掉掉。這個判斷我用破壞實驗驗證過：拿掉之後，就是那個測試變紅。」

---

## E131. M5 第二塊開工：五個設計題（2026-10-21 11:30～13:23，公司電腦，只讀程式）

**依據：** E127 定案 1～4、6；E130；`app/main.py`、`app/ledger.py`、`app/quota.py`、`compose.yaml`、`tests/fakes.py`（`main` = `ab583f9`，讀公司電腦的 repo）。

**範圍：** 只有定案，沒有寫程式、沒有登入 AWS。

**生活比喻：** 外場把點單放進出單夾、後台會計拿去記帳。這次講好：單子要不要裝信封、信封上寫什麼；出單夾的範本放哪裡；加油前還要不要先刷卡確認；會計拿到字跡糊掉的單怎麼辦；練習用的店沒裝出單夾時怎麼辦。

### 成功那條路改完的樣子（照 E127 定案 1、2 推出，不是這次選的）

```
算成本 cost，放進 record
├─ 送 SQS 成功 ─────────────► 回答（Gateway 不寫 audit，交給 Worker）
└─ 送 SQS 失敗 → record_charge()
      ├─ 回 True ───────────► 回答（Gateway 自己記好三本帳）
      ├─ 回 False ──────────► 回答（SQS 其實收到、只是回應逾時，Worker 已經記過）
      └─ 也出錯 → 印一行日誌 ─► 回答照給（錢已經付給 OpenAI）
```

沒花錢的三條路（429、500、502／503）不變，Gateway 照樣直接寫稽核。

### 讀程式時確認、寫進設計的事

- `period_of()`（`app/quota.py`）用**台北時間**切月份；Worker 打包不帶 `quota.py`，所以 `period` 由 Gateway 決定、放進事件
- `record_charge()` 寫 `audit` 時整份 `record` 照抄（`to_dynamodb_item(audit_record)`）：`period` 若塞進 `record`，`audit` 會多一個欄位，跟 Gateway 備援寫出來的不一致
- Worker 不能 import `app/main.py`：它一載入就執行 `load_config()` 與 `read_openai_auth()`，在 Lambda 上起不來，也會把 FastAPI、OpenAI 帶進打包
- 佇列網址若在請求進來時才讀，沒設定時丟 `KeyError`，備援只接 `BotoCoreError`／`ClientError`，結果是**錢已付給 OpenAI 卻回 500**；所以要在啟動時讀、啟動時檢查（同 `OPENAI_AUTH`）

### 定案（本人逐題作答）

| # | 題目 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | SQS 訊息放什麼 | **A：外面包一層信封**：`{"version": 1, "period": "2026-10", "record": {…完整稽核紀錄…}}`；`record` 原封不動交給 `record_charge()` | B 不包、`period` 塞進 `record`、不帶版本：`audit` 多一個欄位、兩條路寫出來不一致，改格式時分不出新舊訊息。C 不帶 `period`、Worker 用 `timestamp` 自己算：Worker 要多打包 `quota.py`，「算哪個月」兩處各算一次 | 版本號只能讓 Worker 認出「看不懂」，不會自動轉換舊格式 |
| 2 | 送 SQS 的程式放哪裡 | **A：新檔 `app/events.py`**：版本常數、組信封、拆信封、建 SQS 連線、送出；`app/main.py` 只加領用窗口 `get_sqs()`；逾時與重試 import `app/db.py` 的常數 | B 全寫在 `main.py`：Worker 不能 import `main.py`，拆信封要在 `worker/handler.py` 再寫一份，版本號與欄位名兩邊各抄一次。C 拆進 `db.py` 與 `ledger.py`：兩個檔名都不準了 | Gateway 與 Worker 都會打包到對方用不到的幾行；Worker 打包多一個檔 |
| 3 | 「花錢前先加 0」（`chat_endpoint()` 第 175～180 行） | **A：留著不改**：它驗的是「`quotas` 現在寫得進去」，正是 Worker 與備援最後都要做的事；DynamoDB 寫入壞掉時在花錢前回 503 | B 拿掉：寫入壞、讀取正常時照樣花錢，錢付了才發現；要刪 `test_chat_returns_503_before_spending_when_usage_cannot_be_written`。C 換成先查 SQS（`GetQueueAttributes`）：多一趟網路、多一個 IAM 權限，查得到不代表送得進去，而且 SQS 壞了本來就有備援 | 只驗「現在」，不驗「等一下」；驗不到 Worker 的權限與 SQS。Gateway 碰資料庫維持 4 次＋SQS 1 次 |
| 4 | Worker 收到看不懂的訊息（不是 JSON、版本不對、少欄位） | **A：一律往外丟**，跟 DynamoDB 出錯同一條路：重送 3 次 → DLQ（保留 14 天，修好可搬回佇列） | B 印日誌後當作成功：訊息不見；Gateway 先部署新版本、Worker 還是舊版時，整批帳被刪光。C Worker 自己送進 DLQ：Worker 要多 SQS 權限與網路，E127「放行清單一個網域都不用加」的優點沒了 | 明知會失敗還多跑 2 次；部署順序錯了訊息會整批塞進 DLQ（帳不掉，要人工搬回）。**部署順序：先 Worker、後 Gateway** |
| 5 | 沒有 SQS 的地方（本機、測試） | **A：`CHARGE_QUEUE_URL` 一定要寫**：值只能是 `https://` 開頭的佇列網址，或 `disabled`；`disabled` 時成功那條路直接 `record_charge()`、不試 SQS、啟動時印一行說明；沒寫或寫錯 Gateway 起不來。`compose.yaml` 的 gateway 加 `CHARGE_QUEUE_URL: disabled`，`infra/daily/ecs.tf` 寫真的網址 | B 沒寫就當作不用 SQS：雲端忘了設時默默變回 M4 的同步記帳，Worker 永遠閒著（違反 `app/db.py`「要連哪裡一定要明講」）。C 本機寫假網址、每次走備援：本機每次都印「送不進去」，真出問題時反而看不出來；容器裡沒有 AWS 身分，失敗原因是「找不到憑證」，不是網路壞 | 正式程式多一個模式、一個分支、一個測試；雲端誤寫 `disabled` 會安靜降級，靠啟動日誌與演練第 0 步抓 |

### 實作時照做的預設值（Claude 提出，本人沒有異議）

| 項目 | 預設 |
|---|---|
| Worker 結構 | `handler(event, context)` 只把 `event["Records"]` 每一則交給 `process_message(client, body)`；`process_message()` 拆信封（`app/events.py`）→ `record_charge()` → 回傳結果 |
| Worker 的 DynamoDB 連線 | 同一個 Lambda 執行環境只建一次（`@lru_cache`，同 `main.py` 的 `get_client()`）；Lambda 環境變數 `DYNAMODB_TARGET=aws` |
| Worker 日誌 | 每則一行 JSON：`charge_recorded` 或 `charge_already_recorded`，只放 `request_id`、`cost_micro_usd`，不放摘要與指紋 |
| Worker 打包 | `app/__init__.py`、`app/db.py`、`app/ledger.py`、`app/events.py`、`worker/__init__.py`、`worker/handler.py` |
| SQS 替身 | `tests/fakes.py` 加 `FakeSqs`（比照 `FakeDynamoDB`）：存下送出的訊息，也可設定成送出就丟 `ClientError`；測試用 `dependency_overrides[get_sqs]` 換掉 |
| 測試（Claude 寫） | 信封格式；送成功時 Gateway 不寫 `audit`、不扣 `quotas`；送失敗時 Gateway 記好三本帳；送失敗且 `record_charge()` 回 `False` 時照樣回答；兩條都失敗時印日誌、照樣回答；`disabled` 模式；Worker 的 `process_message()`（正常、重複、版本不對、不是 JSON） |
| 寫的順序 | `app/events.py` 的信封 → `worker/handler.py` → `app/events.py` 的 SQS 連線與送出 → `chat_endpoint()` → Terraform |

### 面試可用的說法

- 「記帳事件外面包一層信封，帶版本號和月份。月份由 Gateway 檢查額度時就決定，Worker 照著記，不重算；版本號讓 Worker 認得出看不懂的格式。看不懂就往外丟，三次後進 DLQ，帳不會被默默刪掉。所以部署時先更新 Worker、再更新 Gateway。」
- 「每個外部依賴都要明講連哪裡：DynamoDB 寫 `aws` 或網址，SQS 寫佇列網址或 `disabled`，沒寫 Gateway 就起不來。雲端忘了設定時，我寧可它起不來，也不要它安靜地降級。」
- 「花錢前那一次『加 0』我留著。它不保證等一下寫得進去，但能在 DynamoDB 寫入壞掉時，在付錢給 OpenAI 之前就擋下來。」

---

## E132. M5 第二塊（一）：記帳事件的信封 `app/events.py` 與 Worker `worker/handler.py`（2026-10-21 13:23～14:34，公司電腦，分支 `feat/m5-worker`）

**依據：** E131 定案 1、2、4 與預設值；E130 的 `record_charge()`。

**生活比喻：** 出單夾的單子裝進固定格式的信封（版本、月份、原封不動的單子）；後台會計照工作守則拿單、拆信封、記三本帳、在筆記本記一行；拆不開或帳本打不開就退回出單夾。

**範圍：** 只有程式與本機測試（DynamoDB Local），沒有登入 AWS、沒有碰金鑰。SQS 連線與送出、`chat_endpoint()` 的改動、Terraform 都還沒寫；Lambda 與 SQS 還沒建。

### 改了哪些檔

| 檔案 | 誰寫 | 內容 |
|---|---|---|
| `app/events.py`（新） | 本人（填空 9 格，全對） | `EVENT_VERSION = 1`、`InvalidEventError`（繼承 `ValueError`）、`build_event()`、`parse_event()` |
| `worker/__init__.py`（新，空檔） | Claude | 讓 `worker` 成為套件（同 `app/__init__.py`） |
| `worker/handler.py`（新） | 本人（填空 9 格，全對） | `get_client()`（`@lru_cache`）、`log_charge()`、`process_message()`、`handler(event, context)` |
| `tests/test_events.py`（新，11 個，不連資料庫） | Claude | 版本是 1；信封三欄；月份不塞進紀錄；組好再拆拿回同一份（含中文、`None`、布林、清單）；不是 JSON、不是物件、版本不對、沒有版本、少紀錄、少月份、紀錄不是物件都丟 `InvalidEventError` |
| `tests/test_worker.py`（新，8 個：3 個不連資料庫、5 個連考場） | Claude | 版本不對與不是 JSON 都往外丟、還沒碰資料庫；正常記帳回 `True` 並印 `charge_recorded`；同一則兩次第二次回 `False`、錢只扣一次；日誌沒有摘要、指紋、使用者；表不存在時 `ClientError` 往外丟；`handler()` 處理事件裡每一則；`handler()` 遇到壞訊息往外丟 |

### 測試結果（公司電腦）

- `uv run pytest tests/test_events.py`：**11 passed**（0.18 秒）
- `docker compose up -d` → `uv run pytest`：**359 passed**（22.65 秒；340 + 11 + 8）

### 破壞實驗（本人的版本，做完都改回來；跑 `tests/test_events.py tests/test_worker.py` 共 19 個）

| # | 拆掉什麼（代表哪個沒選的選項） | 預期 | 實際 |
|---|---|---|---|
| ① | `parse_event()` 的版本檢查兩行註解掉（等於第 1 題不帶版本號） | 3 個紅 | **3 failed, 16 passed**（1.89 秒）：`test_parse_event_rejects_unknown_version`、`test_parse_event_rejects_missing_version`（`DID NOT RAISE InvalidEventError`）、`test_process_message_raises_on_unknown_version`（`AttributeError: 'object' object has no attribute 'transact_write_items'`：第 2 版訊息一路走到寫帳那一步） |
| ② | `build_event()` 裡插一行 `record["period"] = period`（等於第 1 題選 B） | 2 個紅；`test_process_message_records_the_charge` 仍綠 | **2 failed, 17 passed**（1.22 秒）：`test_build_event_wraps_record_with_version_and_period`、`test_build_event_does_not_put_period_into_record`；Worker 那題仍綠 |
| — | 兩個都改回來 | 全綠 | `uv run pytest` → **359 passed**（20.11 秒） |

- 實驗 ② 證明「兩條路寫出來的 `audit` 一樣」靠的是信封的測試；Worker 的測試只檢查三本帳寫進去，看不出 `audit` 多了一個欄位

### 這一步證明了什麼、沒證明什麼

- **證明：** 信封組好再拆拿回同一份；不認得的版本、壞掉的訊息在碰資料庫之前就被擋下並往外丟；Worker 收到同一則兩次只扣一次、不丟錯；資料庫寫不進去時往外丟；日誌不帶摘要、指紋、使用者
- **沒證明：** 真的 Lambda 收到 SQS 事件的格式（`event["Records"][i]["body"]`，照 AWS 文件寫，要上雲確認）；Lambda 回報失敗後 SQS 真的重送、3 次後進 DLQ（演練第 5 步）；`get_client()` 的「只建一次」（沒有測試）；Gateway 還沒送 SQS

### 本人的提問（10/21）

- `handler()` 的 `context` 沒被用到是正常的嗎？→ 正常：Lambda 一定傳 `(event, context)` 兩個參數，`context` 是這次執行的資訊（執行編號、剩多久逾時），用不到也要留位置，少一個參數一呼叫就 `TypeError`

---

## E133. M5 第二塊（二）：`app/events.py` 加上 SQS 連線與送出（2026-10-21 15:27～16:36，公司電腦，分支 `feat/m5-gateway-sqs`）

**依據：** E131 定案 2、5 與預設值（SQS 連線的逾時與重試比照 DynamoDB）。

**生活比喻：** 信封格式定好之後，決定出單夾放哪裡（佇列網址，一定要明講）、怎麼走過去（連線，走不到時很快放棄）、怎麼投進去（送出，投不進去由外場自己決定改走備援）。

**範圍：** 只有程式與本機測試；PR #22（信封與 Worker）已合併，`main` = `0b05449`。`chat_endpoint()` 還沒改。分支由 Claude 在公司電腦的終端機開（原本約定打字由本人來，之後指令交給本人打）。

### 改了哪些檔

| 檔案 | 誰寫 | 內容 |
|---|---|---|
| `app/events.py` | 本人（填空 7 格，全對） | 加 import（`os`、`boto3`、`Config`、`app/db.py` 的區域與逾時常數）、`QUEUE_DISABLED = "disabled"`、`read_queue_url()`、`make_sqs_client()`、`send_event()` |
| `tests/fakes.py` | Claude | `FakeSqs`：存下送出的訊息；給 `error` 時送出就丟那個錯誤 |
| `tests/test_events.py` | Claude | 加 11 個（8 支函式，其中一支參數化 4 組）：`disabled` → `None`、https 網址原樣回傳、沒設定 → `KeyError`、空白／大寫／`http://`／少開頭 → `ValueError`、連東京的 `sqs`、逾時 2／5 秒與最多試 2 次、送出的內容是 `build_event()` 的信封、送不進去時 `ClientError` 往外丟 |

### 測試結果

- 公司電腦：本人回報「都完成了」，Claude 沒看到終端機畫面（螢幕權限閒置過期）
- 個人電腦重跑（2026-10-21 18:43，分支 `feat/m5-gateway-sqs` = `7d1e782`，DynamoDB Local 兩個容器 Running），Claude 截圖確認：`tests/test_events.py` **22 passed**（26.68s）；全部 **370 passed**（59.28s）

### 這一步證明了什麼、沒證明什麼

- **證明：** 佇列網址只有兩種合法寫法，沒寫或寫錯就報錯；SQS 連線的逾時與重試跟 DynamoDB 一樣；送出的內容就是信封
- **沒證明：** 真的 SQS 收得到（要上雲）；DNS 被擋時真的很快失敗（演練第 6 步）；沒有做破壞實驗

### 開工時發現、還沒定的事（下一個設計題）

`chat_endpoint()` 成功那條路改成送 SQS（或 `disabled` 時直接 `record_charge()`）之後，成功那一筆**不再經過 `get_audit_writer()`**。目前有 6 個測試檔用 `make_file_audit_writer()` 換掉它，從暫存檔讀稽核紀錄來檢查（`test_chat.py`、`test_chat_auth.py`、`test_chat_fallback.py`、`test_chat_routing.py`、`test_chat_truncation.py`、`test_demo_fallback.py`），其中有些也用 `FakeDynamoDB`（只有 `update_item`，沒有 `transact_write_items`）。這些測試要怎麼跟著改，下一個對話先問本人再動。

---

## E134. M5 第二塊（三）：`chat_endpoint()` 成功那一筆改送 SQS、送不進去自己記帳（2026-10-21 18:43～10-22 00:34，個人電腦，分支 `feat/m5-gateway-sqs`）

**依據：** E127 定案 1、2；E131 定案 2、3、5 與「成功那條路改完的樣子」；E133。

**生活比喻：** 外場收完錢，把單子裝進信封投進出單夾，交給後台會計記帳，自己不再記；出單夾卡住投不進去，外場就自己把三本帳記好；連帳本都打不開，就在交班本寫一行「這筆 7 元沒記到」，並按鈴叫人。今天不收外送的店（`disabled`），外場連外送平台都不打電話，直接自己記。

### 開工前的三個設計題（本人逐題作答）

| # | 題目 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 1 | 不用 Docker 的 5 個聊天測試檔（`test_chat.py`、`test_chat_fallback.py`、`test_chat_routing.py`、`test_chat_truncation.py`、`test_demo_fallback.py`，59 個測試；21 個讀成功那一筆、4 個看假資料庫扣了多少）怎麼改 | **A：換上 `FakeSqs`，成功那一筆從送出的信封拆出來讀** | B 設成 `disabled`、連 DynamoDB Local 讀 `audit` 表：59 個測試全變成要 Docker，測到的是備援路不是雲上的主路。C「轉信替身」把信封拆開寫進同一個稽核暫存檔：只改 5 個準備函式，但分不出成功那筆走哪條路，Gateway 若送了 SQS 又自己寫一次稽核也抓不到，測試名字跟實際檢查的東西對不上 |
| 2 | 要 Docker 的 4 個檔（`test_chat_auth.py` 7、`test_chat_quota.py` 9、`test_chat_charge.py` 7、`test_chat_audit_store.py` 5）怎麼改 | **C：4 個舊檔用 `disabled`、走真的 `record_charge()`；另開新檔放 Gateway→信封→Worker 的端到端測試** | A 只做舊檔：沒有「接起來是對的」的證據。B 舊檔也換 `FakeSqs`、測試自己叫 Worker：額度測試變成「Worker 扣錢」，備援路反而沒有真的交易測過 |
| 3 | 小決定 11 項 | **照預設**：載入時讀 `CHARGE_QUEUE_URL`；啟動印 `{"event": "charge_queue_mode", "mode": "sqs"/"disabled"}`、不印網址（網址有帳號 ID）；領用窗口 `get_queue_url()`、`get_sqs()`（`@lru_cache`）；成功那段拆成 `save_charge()`、放 `main.py`（不放會被打包進 Worker 的 `app/events.py`）；只有 SQS 失敗印 `charge_queue_failed`、不告警；兩條都失敗先設 `charged = False` 再用既有的 `report_audit_failure()`（長期層已有 `audit_write_failed` 的 metric filter 與告警，Terraform 不用改）；只接 `BotoCoreError`、`ClientError`；`record_charge()` 回 `False` 不印日誌；`conftest.py` 與 `compose.yaml` 設 `disabled`；新測試分三個檔 | 弱點：`audit_write_failed` 兩種意思（沒花錢的稽核寫不進去／花了錢兩條都失敗）要看 `status`、`charged` 才分得出來；SQS 長時間壞掉時帳是對的但沒人被通知 |

第 2 題：舊檔有 4 個測試的意思變了，因為三本帳現在是同一個交易：「稽核寫不進去但有扣到」這種狀態不存在了（刪 1 個），「扣款失敗」與「兩個都失敗」變成同一件事（合併成 1 個）。

### 改了哪些檔

| 檔案 | 誰寫 | 內容 |
|---|---|---|
| `app/main.py` | 本人（填空 14＋2 格） | import `json`、`sys`、`report_audit_failure`、`send_event`、`record_charge`；`CHARGE_QUEUE_URL = read_queue_url()`；`log_queue_mode()`；`get_queue_url()`、`get_sqs()`（`disabled` 時交回 `None`、不建連線）；`report_queue_failure()`；`save_charge()`；`chat_endpoint()` 多 `sqs`、`queue_url` 兩個參數，成功那段改成算成本 → `save_charge()`；刪掉成功路上的 `add_usage(cost)` 與 `write_audit_record(record)`（花錢前的「加 0」與三條失敗路的稽核保留） |
| `compose.yaml` | 本人 | gateway 加 `CHARGE_QUEUE_URL: disabled` |
| `tests/conftest.py` | Claude | `os.environ["CHARGE_QUEUE_URL"] = "disabled"` |
| `tests/fakes.py` | Claude | `FAKE_QUEUE_URL`、`read_sent_record()` |
| 舊測試 10 個檔 | Claude | 5 個不用 Docker 的檔換 `FakeSqs`、讀信封；`test_chat_charge.py` 改讀 `audit` 表、道具換成「交易一律失敗」；`test_chat_audit_store.py` 刪 2 個；`test_message_limit.py`（借用 `make_test_client()`）、`test_seed.py` 跟著改 |
| `tests/test_chat_sqs.py`（新，6 個，不用 Docker） | Claude | 剛好送一封信封、送到設定的佇列、紀錄沒有 `charged`；月份照台北時間（UTC 10/31 16:00 算 11 月）；送出後不寫稽核檔、只有「加 0」；模型失敗不送；啟動那行不印網址；`disabled` 時 `get_sqs()` 交回 `None` |
| `tests/test_chat_charge_fallback.py`（新，4 個，連考場） | Claude | SQS 失敗 → 自己記好三本帳、只印 `charge_queue_failed`（三個欄位）；SQS 失敗且交易說「已經記過」→ 不印 `audit_write_failed`；兩條都失敗 → 兩行日誌、三本都沒寫；`disabled` → 不碰 SQS、不印任何一行 |
| `tests/test_chat_worker_e2e.py`（新，2 個，連考場） | Claude | Gateway 送出時還沒扣錢、沒有稽核，信封交給 `process_message()` 後三本帳才寫好；Worker 那條路與備援那條路寫出來的 `audit` 欄位完全一樣 |

### 填空時寫錯、後來改對的地方（讀程式時抓到，沒有跑過、沒有進 commit）

| 位置 | 寫成 | 應該是 | 為什麼不行 |
|---|---|---|---|
| `report_queue_failure()` ⑦ | `record["error_type"]` | `type(error).__name__` | 成功那一筆的紀錄沒有 `error_type`（只有失敗路才設）：`KeyError`，錢付了卻回 500 |
| `save_charge()` ⑧ | `raise` | `return` | 送成功時沒有正在處理的錯誤，`raise` 會變成 `RuntimeError`，`except` 接不住：**每一次送成功都回 500** |
| `chat_endpoint()`（填空範圍外） | `outcome.setting` | `outcome.settings` | 改旁邊時誤刪一個字母：每次成功都 `AttributeError` |

### 跑全部測試時才發現的錯（Claude 的設計錯誤）

第一次跑全部：**25 failed, 354 passed**（50.76 秒）。

| 個數 | 原因 | 修正 |
|---|---|---|
| 19 | 設計題 3 第 3 列 Claude 說「建 SQS 連線不會連網路，`disabled` 時建了也不會用」——錯。**boto3 建連線時就會解析憑證**；個人電腦用 `aws login`，需要 `botocore[crt]` → `MissingDependencyException`。FastAPI 進 `chat_endpoint()` 前先把所有領用窗口跑一遍，連 429 路也一起倒（401／503 在驗票口就結束，不受影響）。本機容器沒有憑證時，可能一路找到 EC2 中繼資料服務、等逾時 | `get_sqs()`：`CHARGE_QUEUE_URL is None` 時交回 `None`、不建連線（本人填空 2 格）；`save_charge()`、`chat_endpoint()` 的 `sqs` 型別改 `BaseClient \| None`；加測試 `test_get_sqs_builds_no_client_when_disabled` |
| 6 | Claude 漏改 `test_message_limit.py`（5 個，借用 `make_test_client()`，回傳多一個值）與 `test_seed.py`（1 個，從暫存檔讀成功那一筆） | 跟著改；`test_message_limit.py` 補上跑完還原領用窗口 |

### 測試結果（個人電腦，Claude 截圖確認）

- 修正後 `uv run pytest`：**380 passed**（31.08 秒；370 − 2 + 12）。比修正前少約 20 秒：本機不再每次去找 AWS 憑證
- 破壞實驗做完改回來後再跑一次：**380 passed**（30.03 秒）
- 三個新檔單獨那一行（預期 12 passed）沒有截到，數字由全部的 380 推得

### 破壞實驗（本人的版本，做完都改回來）

| # | 拆掉什麼（代表什麼） | 跑哪些 | 預期 | 實際 |
|---|---|---|---|---|
| ① | `get_sqs()` 的 `if ... return None` 兩行（`disabled` 也建連線） | `tests/test_chat_sqs.py` | 1 紅 | **1 failed, 5 passed**（4.17 秒）：`test_get_sqs_builds_no_client_when_disabled`，`MissingDependencyException`（`botocore/credentials.py`） |
| ② | `save_charge()` 的 `record["charged"] = False`（兩條都失敗時日誌少了「沒扣到」） | `tests/test_chat_charge.py tests/test_chat_charge_fallback.py` | 2 紅 | **2 failed, 9 passed**（6.92 秒）：`test_chat_still_answers_when_charge_fails_after_the_model_replied`、`test_chat_logs_the_uncharged_cost_when_sqs_and_the_fallback_both_fail`，都是 `assert None is False` |
| ③ | `report_queue_failure(record, exc)` 下一行加 `return`（E127 第 1 題的 C：SQS 壞了只印日誌、不走備援） | `tests/test_chat_charge_fallback.py` | 2 紅、「已經記過」那題仍綠 | **2 failed, 2 passed**（5.72 秒）：`test_chat_records_the_charge_itself_when_sqs_fails`（`assert 0 == 7`）、`test_chat_logs_the_uncharged_cost_when_sqs_and_the_fallback_both_fail`（少了 `audit_write_failed`） |

- 實驗 ③「已經記過」那題仍綠：它只證明「沒有多印」，證明不了「有沒有去記帳」；記帳靠 `test_chat_records_the_charge_itself_when_sqs_fails` 抓

### 這一步證明了什麼、沒證明什麼

- **證明：** 成功那一筆只送一封信封、Gateway 不寫稽核、只做「加 0」；SQS 送不進去時 Gateway 用同一個交易記好三本帳；SQS 其實收到（交易說已經記過）時不誤報；兩條都失敗時回答照給、日誌帶成本與 `charged: false`、走既有告警；`disabled` 不建 SQS 連線；Worker 與備援寫出來的 `audit` 欄位一樣；信封月份照台北時間
- **沒證明：** 真的 SQS、Lambda、DNS 防火牆（上雲演練 0～7）；SQS 長時間故障時的告警（只有日誌，`charge_queue_failed` 沒有 metric filter）；「拿到 OpenAI 回答之後、送 SQS 之前」Gateway 當掉的空窗（E127 已記，靠 M6 對帳）

### 面試可用的說法

- 「成功那一筆我只送一封信封給 SQS，Gateway 不再自己寫稽核。測試直接拆開送出去的信封檢查，所以我證明得出『成功那筆在信封裡、稽核檔裡沒有』。」
- 「SQS 送不進去時，Gateway 用跟 Worker 同一支交易函式自己記帳；交易說『已經記過』，代表佇列其實收到了，帳是對的，不誤報。兩條都失敗才印那一行會告警的日誌，帶著成本，事後補收得到。」
- 「我原本以為建 SQS 連線不會碰網路，全部測試一跑就抓到：boto3 建連線時就會去找憑證。所以本機模式根本不建連線，並加一個測試鎖住。」

---

## E135. M5 第三塊開工：Terraform 的八個設計題（2026-10-22 13:23～13:48，公司電腦，只讀程式）

**依據：** E127 定案 3、5 與預設值；E131 定案 5；E134 定案 3；`infra/persistent/`、`infra/daily/`（`main` = `c82d845`，公司電腦的 repo 已從 `0b05449` 快轉到 `c82d845`）；AWS 文件（DynamoDB 交易的 IAM、Lambda 的 SQS 觸發、SQS 的 SSE-SQS）。

**範圍：** 只有定案，沒有寫 Terraform、沒有登入 AWS。

**生活比喻：** 餐廳要裝出單夾（SQS）和會計的座位（Lambda）。開工前講好：分幾次施工、單子失敗幾次才進問題抽屜、會計一張單最多處理多久、會計的權限卡怎麼寫、座位的門禁、出單夾卡住要不要按鈴、出單夾要不要上鎖、打烊拆除組要多哪些工作證。

### 讀 `infra/` 時確認的現況

- `infra/persistent/dynamodb.tf` 只有三張表，註解寫「`usage` 表等 M5 的 Worker 再建」
- `infra/persistent/ecs_roles.tf` 任務角色只開三張表（`api_keys` GetItem、`quotas` GetItem＋UpdateItem、`audit` PutItem）
- `infra/daily/endpoints.tf` 的 DynamoDB Endpoint Policy 只列三張表、三個動作，註解寫「M5 加 `usage` 表時再補」
- `infra/daily/dns_firewall.tf` 放行清單沒有 SQS 的網域
- `infra/persistent/github_oidc.tf` destroy 角色沒有任何 `lambda:` 權限
- `.github/workflows/destroy.yml` 的 `timeout-minutes` 是 30

### 查證的事實（寫 Terraform 時照這些）

| 項目 | 查到的 | 來源 |
|---|---|---|
| 交易的 IAM | 沒有 `dynamodb:TransactWriteItems` 這個權限；交易裡每一件照本來的動作檢查（`Put` 看 `PutItem`、`Update` 看 `UpdateItem`）；條件 `dynamodb:EnclosingOperation` = `TransactWriteItems` 可以寫成「只准在交易裡做」 | DynamoDB 開發者指南「Using IAM with DynamoDB transactions」 |
| `maxReceiveCount` | AWS 建議**至少 5**：Lambda 被限流時訊息也算收過一次 | Lambda 開發者指南「Creating and configuring an Amazon SQS event source mapping」 |
| 隱藏時間 | 必須 ≥ 函式逾時（建立觸發時會檢查）；建議 = 6 × 函式逾時 | 同上 |
| SSE-SQS | 免費；不用建金鑰、不用改權限；HTTPS 建的新佇列預設就開 | SQS 開發者指南「Configuring server-side encryption for a queue using SQS-managed encryption keys」 |
| Worker 最壞卡多久 | `app/db.py`：連線 2 秒＋讀取 5 秒，最多 2 次，加退避約 1 秒 → 約 15 秒 | 讀程式 |

### 定案（本人逐題作答）

| # | 題目 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | 分幾個 PR | **A：兩個 PR，長期層先**。PR①：`usage` 表、SQS、DLQ、Worker 執行角色、Worker 日誌群組、任務角色加 `usage` 與 `sqs:SendMessage`、destroy 角色加拆 Lambda 的權限與新的 Deny、`charge_queue_failed` 告警；合併後在公司電腦 apply 長期層（沒有 ALB、不用 `admin_cidr`、幾乎不花錢）。PR②：每日層（Lambda、打包、SQS 觸發、Worker 安全群組、DNS 放行 SQS、Endpoint Policy 加 `usage`、ECS 加 `CHARGE_QUEUE_URL`），演練當天在個人電腦 apply | B 一個 PR：兩層 apply 的時機和電腦不一樣，出錯分不清是哪一層。C 三個 PR（`usage` 表單獨）：單獨上去沒人用 | 多一個 PR；中間一段時間長期層有佇列沒人拿（Gateway 還沒有佇列網址，不會送） |
| 2 | 失敗幾次進 DLQ | **B：5 次**（原 E127 定 3 次，改） | A 維持 3：比 AWS 建議少，限流時正常的帳可能被誤送進 DLQ（帳不掉，但搬回前額度沒扣）。C 10 次以上：壞訊息再試也不會過，只是越晚發現 | 演練第 5 步多等約 2 分鐘；`worker/handler.py` 的註解「三次後進 DLQ」要改成五次 |
| 3 | Lambda 逾時與隱藏時間 | **B：逾時 20 秒、隱藏時間 120 秒**；記憶體先用預設 128 MB，演練第 0 步看 `REPORT` 那行再記實際用量 | A 10／60：比 Worker 最壞的 15 秒短，DynamoDB 慢時 Lambda 先被切掉，日誌只有 `Task timed out`、看不到原因（帳仍安全，交易全寫或全不寫）。C 30／180：多的 10 秒換不到東西 | 壞訊息進 DLQ 約要等 4 × 120 秒 ≈ 8 分鐘；卡在整點邊緣時 NAT 可能多算一小時 |
| 4 | 交易的 IAM | **A：Worker 三個動作（`usage` PutItem、`quotas` UpdateItem、`audit` PutItem）都加 `dynamodb:EnclosingOperation = TransactWriteItems`；Gateway 任務角色新加的 `usage` PutItem 也加；Gateway 的 `quotas`、`audit` 不加（交易外也要用）**。Worker 不給 GetItem、DeleteItem，碰不到 `api_keys`。長期層 apply 完在公司電腦用 `aws iam simulate-principal-policy` 免費模擬一次 | B 不加條件：對入侵者的保護一樣，少了「只能三本一起寫」的保險。C 寬權限：推翻 E116 | 擋的是寫錯的程式，擋不了入侵者（把動作包進交易就過）；本機 DynamoDB Local 不檢查 IAM，條件寫錯要到演練第 0 步才看得到，所以先模擬；模擬過不了就退回 B |
| 5 | Worker 安全群組 | **A：出口只開 443 到 DynamoDB 的 prefix list（Gateway Endpoint 的 `prefix_list_id`），入口不開**；不寫 `0.0.0.0/0`，不用加 Trivy AWS-0104 豁免 | B 比照 Gateway 開 `0.0.0.0/0`：Worker 只需要一個目的地，開一樣寬只靠 DNS 防火牆擋，豁免講不出理由。C 共用 Gateway 的安全群組：入口規則用不到，兩個角色門禁混在一起 | prefix list 是「東京所有 DynamoDB」，攻擊者自己帳號的表也在裡面，要靠 Endpoint Policy 鎖表（PR② 一定要把 `usage` 加進去，兩層缺一不可）；以後 Worker 多連一個服務要多開一條 |
| 6 | `charge_queue_failed` 告警 | **A：加 metric filter 與告警，門檻「5 分鐘內 ≥ 3 筆」**；`audit_write_failed` 兩種意思這次不拆，記進 v2.11 待改、M6 處理 | B 不告警：SQS 整個壞掉時系統默默退回同步記帳，沒人知道，正是 E131 定案 5 不要的「安靜降級」。C 1 筆就響：備援的目的就是偶爾失敗不影響服務，1 筆就響久了會被關掉 | 多一組 filter 與告警（每月約 US$0.10，前 10 個免費）；Demo 的量湊不到 3 筆，演練第 6 步只聊一次告警不會響，只能看日誌與指標數字 |
| 7 | SQS 加密 | **A：主佇列與 DLQ 都用 SSE-SQS，Terraform 明寫 `sqs_managed_sse_enabled = true`** | B 自管 KMS：每月約 US$1，Gateway、Lambda、觸發都要加 KMS 權限；SNS 當時是因為告警送不進加密主題才豁免，SQS 沒有這個問題。C 不加密：Config scan 多一個 HIGH | 鑰匙是 AWS 的，不能自己輪替或撤銷 |
| 8 | destroy 角色拆 Lambda | **A：** Describe／Get／List 類寫 `"*"`、動作逐一列（`lambda:GetFunction`、`GetFunctionCodeSigningConfig`、`GetPolicy`、`ListVersionsByFunction`、`GetEventSourceMapping`、`ListTags`）；`lambda:DeleteFunction` 限東京、本帳號、`Layer = daily`；`lambda:DeleteEventSourceMapping` 不依賴標籤，改用 AWS 給觸發專用的條件 `lambda:FunctionArn` = Worker 函式的 ARN（10/22 更正：設計題當時說「觸發沒有標籤」不準確，觸發能不能用標籤條件沒有查到確定的說法；`lambda:FunctionArn` 不管有沒有標籤都成立）；Deny 新增兩個佇列、Worker 執行角色、Worker 日誌群組。`destroy.yml` 的 30 分鐘先不改，第 7 步實測接近上限再改 45 | B `lambda:*` 加標籤條件：觸發能不能靠標籤鎖不確定，可能拆不掉觸發；還給了 Create、UpdateFunctionCode。C 演練前用 CLI 手動刪觸發：放棄「一鍵拆光」的證據 | 缺了沒列到的 Describe 時 destroy 會卡一次，看錯誤補一個再跑（同 E121 的節奏） |

### 面試可用的說法

- 「我原本定失敗 3 次進 DLQ，寫 Terraform 前查 AWS 文件，發現建議至少 5 次，因為限流也會算一次接收。我改了，並把差別記進決策書。」
- 「Lambda 逾時我設 20 秒，因為算過 Worker 最壞會卡 15 秒。逾時比它長，才一定是我的程式先決定失敗、丟出看得懂的錯誤，而不是被平台切掉只剩 `Task timed out`。」
- 「IAM 沒有交易專用的權限，每一件照本來的動作檢查。我多加一個條件『只准在交易裡做』，把『三本帳要嘛全寫、要嘛全不寫』從程式層鎖到權限層。它擋的是寫錯的程式，擋不了入侵者，入侵者靠的是每張表只給一個動作那一層。」
- 「Worker 從網路層就只走得到 DynamoDB，表的範圍再由 Endpoint Policy 鎖住；它連 NAT 都碰不到。Gateway 開 `0.0.0.0/0` 是因為 OpenAI 的 IP 不固定、沒得選；Worker 有得選，就選最窄的。」
- 「佇列用 SQS 自管鑰匙加密，免費、不用改權限；SNS 那邊因為 CloudWatch 告警送不進加密主題才接受豁免，兩個決定的理由不一樣。」

### 實作進度（10/22 13:56～17:07 公司電腦，17:07 前 commit 並推上分支 `feat/m5-terraform-persistent`；剩下的在個人電腦完成，見 E136）

| 檔案 | 狀態 | 填空時寫錯、後來改對的地方 |
|---|---|---|
| `infra/persistent/dynamodb.tf` | 完成：`usage` 表（`user_id` + `ts_request`、刪除保護、時光機）；第 1～2 行註解改成四張表 | 無 |
| `infra/persistent/sqs.tf`（新） | 完成：DLQ（保留 1209600 秒、SSE-SQS）、主佇列（隱藏 120 秒、SSE-SQS、`maxReceiveCount` 5）、DLQ 只收主佇列（`redrive_allow_policy`） | `queue_url` 寫成 `.user_id`（應為 `.id`）；`sourceQueueArns` 寫成不存在的 `aws_sqs_queue_redrive_allow_policy.charge.arn`（應為 `aws_sqs_queue.charge.arn`） |
| `infra/persistent/worker_role.tf`（新） | 完成：信任 `lambda.amazonaws.com`（限本帳號、限 Worker 函式）；主佇列 Receive／Delete／GetQueueAttributes；三本帳各一個動作加 `EnclosingOperation`；網卡 7 個動作（`"*"`）；只寫自己的日誌群組 | 服務名少引號；SQS 資源寫成角色自己的 ARN；`usage` 寫成 `worker_trust`；日誌群組用了函式名而非群組名；`role` 指到政策自己。共同點：「要寫被操作的東西，寫成了操作的人」 |
| `infra/persistent/logs.tf` | 完成：Worker 日誌群組（30 天、防刪）；`charge_queue_failed` 篩選（Gateway 的群組）與告警（300 秒、≥ 3） | 群組名沒引號且自己重組（改用 `local.worker_log_group`）；篩選事件名寫成 `audit_write_failed`（`validate`、`plan` 都抓不到）；描述裡的全形分號 |
| `infra/persistent/ecs_roles.tf` | 完成：任務角色加 `usage` PutItem（交易內）、`sqs:SendMessage`（主佇列） | `sqs:ReceiveMessage`（應為 `SendMessage`：上雲後會每筆都走備援、告警會響） |
| `infra/persistent/github_oidc.tf` | 完成（E136） | 見 E136 |
| `infra/persistent/outputs.tf`、`worker/handler.py` 註解 | 完成（E136） | 見 E136 |

---

## E136. M5 第三塊（一）：PR① 長期層 Terraform 填空完成、本機驗證（2026-10-22 18:36～19:45，個人電腦，分支 `feat/m5-terraform-persistent`）

**依據：** E135 定案 1、2、4、6、7、8 與「實作進度」；`docs/handoff/m5-terraform-persistent-wip-handoff.md` 第 4 節。

**範圍：** 只有 Terraform 與一行註解、本機驗證；沒有登入 AWS、沒有 `plan`／`apply`、沒有開 PR。

**生活比喻：** 拆除工班多拿一張「拆會計室」的工作證：每間房都能進去看，只能拆門上貼「每日」貼紙的會計室，叫人鈴線只能剪接到這間會計室的那條；管理處的禁止清單加上出單夾、問題抽屜、第四本帳與會計的員工證；收據多印三樣東西。

### 開工

| # | 步驟 | 結果 |
|---|---|---|
| 1 | 看個人電腦 repo 的狀態（Claude 讀 `.git/HEAD` 與 `refs/heads/main`） | 已在 `main` = `c82d845`；交接檔以為停在 `feat/m5-gateway-sqs`，實際已切回 `main`，所以省掉 `git switch main` |
| 2 | 本人 `git status` → `git pull` → `git switch feat/m5-terraform-persistent` | `HEAD` 換到新分支；`infra/persistent/` 出現 `sqs.tf`、`worker_role.tf`（Claude 讀資料夾確認） |

### 改了哪些檔

| 檔案 | 誰寫 | 內容 |
|---|---|---|
| `infra/persistent/github_oidc.tf` | 本人（填空） | 檔頭註解加第四批。允許 3 條：`DescribeDailyWorker`（6 個 `lambda:` 只看的動作，`"*"`）；`DeleteDailyWorker`（`lambda:DeleteFunction`，限東京本帳號的函式＋`aws:ResourceTag/Layer = daily`）；`DeleteWorkerTrigger`（`lambda:DeleteEventSourceMapping`，資源 `event-source-mapping:*`，條件 `ArnEquals` `lambda:FunctionArn` = `local.worker_function_arn`）。Deny：`DenyPersistentTables` 加 `usage`（註解三張表改四張表）；`DenyGatewayRolesChange` 加 Worker 角色；`DenyAlertsChange` 加 `charge_queue_failed` 告警；`DenyPersistentLogsChange` 加 Worker 群組兩種寫法；新增 `DenyChargeQueues`（主佇列與 DLQ：`DeleteQueue`、`SetQueueAttributes`、`AddPermission`、`RemovePermission`、`PurgeQueue`、`ReceiveMessage`、`DeleteMessage`） |
| `infra/persistent/outputs.tf` | 本人（填空） | `dynamodb_table_arns` 加 `usage`；新增 `charge_queue_url`（`aws_sqs_queue.charge.url`）、`worker_role_arn` |
| `worker/handler.py` | 本人 | `process_message()` 上方註解「三次後進 DLQ」改「五次後進 DLQ」 |
| `infra/persistent/worker_role.tf` | 本人 | 第 40 行（角色描述）、第 56 行（`sid`）的 `transcation` 改 `transaction` |
| `infra/persistent/sqs.tf`、`worker_role.tf` | `terraform fmt` | 對齊 `maxReceiveCount`；`actions =[` 補空格 |

### 新的小定案（本人 10/22 選 A）

| 題目 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|
| `DenyChargeQueues` 要不要也擋「一張張拿單、銷單」 | **A：加 `sqs:ReceiveMessage`、`sqs:DeleteMessage`**，跟四張表連「改資料」都擋的風格一致 | B 照 E135 原本的 5 個：拆除組現在沒有任何 SQS 允許、碰不到；但以後允許若寫成 `sqs:*`，工班能把還沒記的帳一張張拿走銷掉，那些花費就漏記 | 沒有額外成本；兩個動作名稱要在模擬器驗過才算數 |

### 填空時寫錯、後來改對的地方（讀檔時抓到，沒有進 commit）

| 位置 | 寫成 | 應該是 | 為什麼不行 |
|---|---|---|---|
| `DeleteWorkerTrigger` 的 `actions` | `lambda:DeleteTrigger` | `lambda:DeleteEventSourceMapping` | AWS 沒有這個動作。IAM 不檢查動作名稱，`validate`、`plan`、`apply` 都會過，只會被當成「沒給」，要到 destroy 拆觸發時才 `AccessDenied`（同 E120 的 `dynamodb:Delete`） |
| `DeleteWorkerTrigger` 的條件值 | `local.data.aws_caller_identity.current.account_id` | `local.worker_function_arn` | 語法錯（`local.` 後面只能接 `locals` 裡的名字，`validate` 會報錯）；意思也錯：帳號 ID 永遠不等於函式 ARN，條件永遠不成立 |
| `outputs.tf` 的 `charge_queue_url` | `aws_sqs_queue.sqs.url` | `aws_sqs_queue.charge.url` | 中間那格是自己取的名字（`charge`），不是服務名；`validate` 會報找不到這個資源 |
| `DenyPersistentLogsChange` 的註解 | 「三種都列」 | 「兩種都列」 | 兩種是指每個群組的 ARN 有兩種寫法（結尾有沒有 `:*`），跟群組個數無關（只是註解，不影響執行） |

- 跟 E135 的共同點一樣：兩個都是「種類」和「哪一個」混在一起（服務名 vs 自己取的名字；帳號 vs 函式）

### 本機驗證（個人電腦，Claude 截圖確認）

- `terraform fmt`：改了 `sqs.tf`、`worker_role.tf`。`logs.tf` 檔尾沒有換行，`fmt` **沒有**補（交接檔原本預期會補）
- `terraform validate`：**`Success! The configuration is valid.`**（沿用已 `init` 的目錄，沒有登入 AWS）
- `uv run pytest -q`：**380 passed in 35.00s**（Python 只改註解）
- `git add infra/persistent worker/handler.py` → commit `feat: let destroy role tear down the worker and guard new persistent resources`（5 個檔）

### 這一步證明了什麼、沒證明什麼

- **證明：** 長期層所有資源名、`local`、`data` 的互相參照都找得到；Python 沒有被影響
- **沒證明：** 動作名稱與條件鍵存在、寫對（`validate` 不檢查，要用模擬器）；`plan` 的數字（照檔案數預期 **9 個新增、2 個政策更新**：`usage` 表、兩個佇列、DLQ 收單政策、Worker 角色與政策、Worker 日誌群組、篩選、告警；任務角色與 destroy 角色的政策。交接檔原估約 12／3，以實際 `plan` 為準）；`EnclosingOperation` 條件在 AWS 上的實際判斷（合併後模擬）；destroy 角色真的拆得掉 Lambda 與觸發（要等 PR② 與演練第 7 步）

### 面試可用的說法

- 「IAM 不會檢查動作名稱存不存在。我把刪觸發的動作寫成一個不存在的名字，`validate`、`plan` 都照過，只會被當成沒給，要等到真的拆的時候才 `AccessDenied`。所以我每次改權限，都用 `simulate-principal-policy` 逐一問。」
- 「拆除組刪 Lambda 的觸發，我不靠標籤，用 `lambda:FunctionArn` 鎖住『只能剪接到這一個函式的線』。」
- 「拆除組現在根本沒有 SQS 權限，我還是在 Deny 裡擋了拿單和銷單。Deny 是安全帶，防的是以後有人把允許寫太寬。」

---

## 目前進度（2026-10-22）

- M5 七項定案完成（E127）
- Terraform 1.16.6：PR #17 合併（`main` = `46fd3eb`），6 個檢查全過（E128）
- M4 的 AWS 實際金額：約 US$0.29（E129），已寫進 M4 docs PR #18（`main` = `d25e36f`）
- M5 第一塊 `app/ledger.py`（三本帳的共用交易）：本機 340 passed、兩個破壞實驗符合預期（E130）；分支 `feat/m5-ledger` 開 PR
- M5 第一塊 PR #21 合併（`main` = `ab583f9`）
- M5 第二塊五個設計題定案（E131）：事件包信封帶版本、`app/events.py`、加 0 保留、看不懂的訊息進 DLQ、`CHARGE_QUEUE_URL` 必填（網址或 `disabled`）
- M5 第二塊（一）：`app/events.py` 的信封與 Worker `worker/handler.py`，本機 359 passed、兩個破壞實驗符合預期（E132）；分支 `feat/m5-worker` 開 PR
- PR #22 合併（`main` = `0b05449`）
- M5 第二塊（二）：`app/events.py` 的 SQS 連線與送出（E133），分支 `feat/m5-gateway-sqs`（`7d1e782`），個人電腦確認 22 passed／全部 370 passed
- M5 第二塊（三）：`chat_endpoint()` 成功那一筆改送 SQS、送不進去自己記帳（E134），本機 380 passed、三個破壞實驗符合預期；分支 `feat/m5-gateway-sqs` 開 PR
- PR #23 合併（`main` = `c82d845`，10/22 01:12 前）
- M5 第三塊 Terraform 八個設計題定案（E135）：兩個 PR 長期層先、DLQ 5 次、逾時 20／隱藏 120、交易 IAM 加 `EnclosingOperation`、Worker 出口只到 DynamoDB prefix list、`charge_queue_failed` 告警 5 分鐘 ≥ 3、SSE-SQS、destroy 角色加 Lambda 權限
- PR① 長期層填空全部完成（E135、E136）：`validate` 通過、380 passed；`DenyChargeQueues` 多擋 `ReceiveMessage`、`DeleteMessage`
- 下一步：
  1. PR①：push → 開 PR → 三個必要檢查綠了合併 → 公司電腦 `aws login` → 長期層 `plan`（預期 9 新增、2 更新）→ `apply` → `simulate-principal-policy`（Worker 的交易條件、Gateway 的 `SendMessage`／`ReceiveMessage`、destroy 角色新加的允許與 Deny）
  2. PR②：每日層 Terraform（Lambda、打包、觸發、Worker 安全群組、DNS 放行 SQS、Endpoint Policy 加 `usage`、ECS 加 `CHARGE_QUEUE_URL`）
  3. 上雲演練 0～7（個人電腦；部署順序先 Worker 後 Gateway；花費照「整段＋不滿一小時進位」重估）
- 下一筆證據是 **E137**

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
| 10 | 3.2 `usage`、7.10 | `record_charge()` 放 `app/ledger.py`；`usage` 只存 7 個記帳欄位；回 `True`／`False`，只有每一件取消原因都是 `ConditionalCheckFailed` 才算重複（E130） |
| 11 | 2.2 [9]、3.1 Worker 職責、3.3、7.10、PART 9 | 事件格式：信封 `version`＋`period`＋`record`；`app/events.py`；花錢前加 0 保留；Worker 看不懂的訊息往外丟、進 DLQ；部署順序先 Worker 後 Gateway；`CHARGE_QUEUE_URL` 必填（佇列網址或 `disabled`），啟動時檢查（E131） |
| 12 | 2.2 [9]、3.3、12.5 | Gateway 成功那一筆：`save_charge()` 先送 SQS、失敗或 `disabled` 時 `record_charge()`；只有 SQS 失敗印 `charge_queue_failed`；兩條都失敗用既有 `audit_write_failed` 告警、帶 `charged: false`；`disabled` 不建 SQS 連線（boto3 建連線即解析憑證）（E134） |
| 13 | 3.5、5.1 兩層的表、7.10、D12、8.2 的 M5、PART 9 IaC | Terraform 八個定案：兩個 PR 長期層先；DLQ `maxReceiveCount` 5（E127 原寫 3，改）；Lambda 逾時 20 秒、隱藏時間 120 秒、記憶體 128 MB；Worker 與 Gateway 的 `usage` 交易權限加 `dynamodb:EnclosingOperation`；Worker 安全群組出口只到 DynamoDB prefix list；`charge_queue_failed` 告警 5 分鐘 ≥ 3 筆；SQS 與 DLQ 用 SSE-SQS；destroy 角色加 Lambda 的 Describe／Delete（`DeleteEventSourceMapping` 用 `lambda:FunctionArn` 條件）、Deny 新增佇列（含 `ReceiveMessage`、`DeleteMessage`）與 Worker 角色、日誌（E135、E136） |
| 14 | 3.3、12.5 | `audit_write_failed` 兩種意思（沒花錢的稽核寫不進去／花了錢兩條都失敗）要拆成兩個事件名，M6 處理（E134、E135） |

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| DynamoDB Gateway Endpoint Policy 與交易的配合 | 加 `usage` 表；動作維持 `GetItem`、`PutItem`、`UpdateItem`（交易照每件的動作檢查）；AWS 文件沒寫清楚 Endpoint Policy 是否認得 `EnclosingOperation`，先不在 Endpoint Policy 加條件 | PR② 寫每日層時 |
| Lambda 網卡收回時間 | 第 6 題第 7 步實測；超過 destroy workflow 上限（30 分鐘）就先改 45，再不夠就改放 VPC 外 | M5 上雲 |
| Lambda 記憶體實際用量 | 預設 128 MB；演練第 0 步看 `REPORT` 那行 | M5 上雲 |
