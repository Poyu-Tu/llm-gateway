# M2 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID；個人帳號名稱（含終端機提示字元與路徑中的使用者資料夾名稱，一律寫成 `<user>`）。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`（檔名以 `m2-` 開頭，正式清單照決策書 11.4 的 S 編號），日誌另存於 `docs/logs/`。
> E 編號接續 `m1-evidence-log.md`（E29～E75），M2 從 E76 開始。
> 紀錄日期：2026-10-04 建立（M1 結案當天，提前開工）

---

## 紀錄規則（沿用 M1，交接說明第 4 節）

| # | 東西 | 規則 |
|---|---|---|
| 1 | 證據紀錄 | 本檔；每完成一組步驟就更新，回傳完整新版 |
| 2 | 里程碑報告 | 整關驗證通過後寫 `docs/milestones/m2-report.md`，格式同 M1；只向本人確認花費時間與實際花費 |
| 3 | 決策書 | M2 結案時出 v2.8；期間的新定案先記在本檔，待改項目列在結案報告附錄 |
| 4 | 截圖、日誌 | 收到就改名、遮蔽、回傳；只截 11.4 清單（S01～S04）與出錯、決策、驗證的關鍵畫面 |
| 5 | 存放 | 所有回傳的文字檔也存一份到 Project |
| 6 | 個資測試 | 只用假資料（假身分證字號、假手機、`example.com` 信箱、測試用卡號） |
| 7 | 收錄範圍 | 只收與專題本身有關的內容；開發機的個人環境問題（例如筆電記憶體）不收錄 |

---

## M2 步驟規劃（2026-10-04）

**原則（M1 結案報告第 4 節）：** 每個驗收條件先寫成測試，再寫功能。

| # | 步驟 | 需要 Docker | 需要金鑰 | 對應驗收 |
|---|---|---|---|---|
| 1 | 個資遮罩 `mask()`：Email → 手機 → 身分證字號 → 信用卡號（Luhn）；「跨在第 50 字」邊界測試 | 否 | 否 | S04 |
| 2 | 個資類別：稽核記「偵測到哪一類」，不記內容 | 否 | 否 | S04 |
| 3 | `period` 函式：台北時間切月 + 跨月邊界測試 | 否 | 否 | — |
| 4 | 成本換算最小版：token × 單價 → 無條件進位成 micro-USD（M2 同步扣減需要；路由與完整單價表仍屬 M3） | 否 | 否 | S02 |
| 5 | DynamoDB Local：docker-compose、boto3、建表腳本 | 是 | 否 | — |
| 6 | API Key 驗證：`api_keys` 表、SHA-256、錯誤只回「驗證失敗」 | 是 | 否 | S01 |
| 7 | 額度檢查：`quotas` 表、超額回應（**待定案：狀態碼、錯誤類型、`Retry-After`**）、fail-closed 503、「額度 0」邊界 | 是 | 否 | S02、S03 |
| 8 | 同步扣減：DynamoDB 原子累加（`ADD`） | 是 | 否 | S02 |
| 9 | `append_audit()` 換成寫入 DynamoDB；加 `user_id` 與個資類別；呼叫端不動 | 是 | 否 | S04 |
| 10 | 種子腳本：alice（US$0.001）、bob（US$1.00），Key 只顯示一次 | 是 | 否 | — |
| 11 | 真實驗收：連續呼叫到超額、停掉 DynamoDB Local、送假身分證字號；截圖 S01～S04 | 是 | 是 | 全部 |
| 12 | 結案：再量一次記憶體、M2 結案報告、決策書 v2.8 | — | — | — |

**為什麼從 `mask()` 開始：** 它是純 Python 函式，不需要 Docker、資料庫或金鑰，可以直接照「先寫測試」的做法進行；也是 M1 結案報告列的第一個限制（送往 OpenAI 的內容未遮罩）。新的基礎設施（DynamoDB Local、boto3）排在第 5 步，一次只引入一樣新東西。

**規劃時發現的缺口（誠實記錄）：** 決策書把「token × 單價換算成本」排在 M3，但 M2 就要「由 Gateway 同步扣減額度」，扣減需要金額。M2 先做只含 `gpt-6-luna` 的最小成本函式（含 D30 的無條件進位），M3 再擴充為完整單價設定檔與「沒有單價就拒絕」。結案時列入 v2.8 待改項目。

---

## E76. 開工前待辦 1：Gateway 待機記憶體（2026-10-04 17:25）

**來源：** M0／M0.5 結案報告的待辦，M1 未執行，移到 M2 開工前（決策書 12.5、M1 結案報告 Part C）。

**指令與結果：**

```
PS C:\Users\<user>\llm-gateway> docker images llm-gateway
IMAGE            ID             DISK USAGE   CONTENT SIZE
llm-gateway:m1   18b325917e54        220MB         50.9MB

PS C:\Users\<user>\llm-gateway> docker run -d --rm --name gw -p 127.0.0.1:8000:8000 llm-gateway:m1

PS C:\Users\<user>\llm-gateway> irm http://127.0.0.1:8000/health
status
------
ok

PS C:\Users\<user>\llm-gateway> docker stats --no-stream gw
CONTAINER ID   NAME   CPU %    MEM USAGE / LIMIT     MEM %    NET I/O          BLOCK I/O     PIDS
a995849fad9a   gw     0.15%    56.08MiB / 7.567GiB   0.72%    2.7kB / 1.02kB   40.1MB / 0B   2
```

**對照：**

| 項目 | 待機記憶體 | 對 Fargate 0.5 GB（512 MiB，D15） | 來源 |
|---|---|---|---|
| LiteLLM v1.102.0（有資料庫） | 584 MiB | 超過，需升至 1 GB | E16 |
| LiteLLM v1.102.0（無資料庫） | 473.5 MiB | 約 92% | E19 |
| **本案 Gateway（M1 映像）** | **56.08 MiB** | **約 11%** | 本筆 |

**判讀：**
- Gateway 待機約為 LiteLLM 的十分之一（56.08 ÷ 584 ≈ 9.6%），D15 的最小規格有充足餘裕
- `LIMIT 7.567GiB` 是 Docker Desktop 虛擬機的記憶體，代表這個容器沒有另設上限；M4 由 Fargate 的工作定義設定 512 MiB
- `PIDS 2`：容器內只有 2 個行程

**刻意不帶 `--env-file`：** 量待機記憶體不需要呼叫模型，所以不把金鑰交給容器（最小權限）。容器照常啟動、`/health` 回 `ok`，附帶證明程式是在處理請求時才讀取金鑰，不是啟動時就需要全部金鑰。

**限制（誠實記錄）：**
- 功能不對等：LiteLLM 含管理後台、上百家供應商、資料庫連線；這個數字只能說明「只需要這些功能時不必付那麼多記憶體」，不能說明程式品質
- 只量一次，只送過一次 `/health`，尚未呼叫模型；E27 的 LiteLLM「輕度負載」數字（574～578 MiB）沒有對應的量測
- M2 加入 boto3 與資料庫連線後會增加，M2 結案時再量一次（步驟 12）

**面試可用的說法：** 「拆解 LiteLLM 時我量到它待機 584 MiB，超過我規劃的 512 MiB 規格。自己的 Gateway 做好後我用同一個指令量，是 56 MiB。兩者功能不對等，所以我不會說我的比較好；這個數字的意義是：只需要一家供應商加上額度與稽核時，最小規格就夠用，而且還有九成的餘裕。」

---

## E77. 步驟 1-1：Email 遮罩 `mask()`（2026-10-04 19:41～19:59）

**依據：** 決策書 8.2 M2「個資偵測」、D6（摘要取遮罩後的前 50 字）、E34（先遮罩再截斷）。M1 的 `mask()` 是空殼，這一步開始填內容。

**定案：遮罩後的樣式用類別標籤 `[EMAIL]`，不用 `***`。**

| 樣式 | 遮完的句子 | 評估 |
|---|---|---|
| `***` | `Contact me at *** please` | 模型看不出被遮的是什麼；稽核分不出是信箱還是卡號 |
| **`[EMAIL]`（採用）** | `Contact me at [EMAIL] please` | 模型知道這裡原本是信箱，句子仍讀得通；步驟 2 記「偵測到哪一類」時可直接沿用 |

**做法：先寫測試、看它失敗，再寫功能。**

測試（本人撰寫，`tests/test_audit.py`）：

| 測試 | 檢查 | 目的 |
|---|---|---|
| `test_mask_replaces_email` | `"Contact me at amy@example.com please"` → `"Contact me at [EMAIL] please"` | 該遮的有遮 |
| `test_mask_keeps_text_without_personal_data` | `"Say hi"` 不變 | 不該遮的沒被動到（防止遮過頭） |

第一次執行（`mask()` 仍是空殼）：

```
E       AssertionError: assert 'Contact me a...le.com please' == 'Contact me at [EMAIL] please'
E         - Contact me at [EMAIL] please
E         + Contact me at amy@example.com please
1 failed, 18 passed in 1.62s
```

失敗的樣子符合預期：`-` 是預期、`+` 是實際，信箱原封不動。

**新工具：`re`（正規表示式）。** 不知道使用者會打哪個信箱，所以描述的是「信箱的形狀」，不是某一個信箱。

```python
EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
```

| 片段 | 意思 |
|---|---|
| `[A-Za-z0-9._%+-]+` | `@` 前面的名字：這些字元一個以上 |
| `@` | `@` 本身 |
| `[A-Za-z0-9.-]+` | 網域 |
| `\.` | 字面上的點（不加 `\` 會變成「任何字元」） |
| `[A-Za-z]{2,}` | 結尾至少 2 個字母 |

**生活比喻：** 在停車場找車，不說「找 ABC-1234」，而是說「找車牌是三個英文字母、一條橫線、四個數字的車」。

**為什麼用簡單版，不用完整的信箱規格：** 完整規格的表示式有數百個字元，無法閱讀也無法維護。簡單版抓得到絕大多數日常信箱，而且每一段都講得出來；代價是罕見格式會漏。

### 挫折：改了 `mask()`，測試還是失敗

本人第一版：

```python
def mask(text: str) -> str:
    re.sub(EMAIL_PATTERN, "[EMAIL]", "amy@example.com")
    return text
```

結果仍是 `1 failed, 18 passed`，錯誤訊息與空殼時**完全相同**。

- **怎麼判讀：** 訊息與上一次一樣，代表函式回傳的仍是原文；問題在 `mask()` 內，不在測試，也不在形狀描述
- **原因 1：** `re.sub` 的第三個參數（要在哪段文字裡找）寫成固定字串，沒有用到函式收到的 `text`
- **原因 2：** `re.sub` 不會修改原字串，而是回傳一份新的；結果沒有用變數接住，下一行回傳的是舊字串
- **解法（本人依方向提示自行修正）：**

```python
def mask(text: str) -> str:
    """Replace personal data with a category label before the text leaves the gateway."""
    result = re.sub(EMAIL_PATTERN, "[EMAIL]", text)
    return result
```

- **結果：** `19 passed in 1.07s`
- **學到的：** Python 的字串不能被就地修改，處理字串的函式都是「回傳新的」，一定要接住

**限制（誠實記錄）：**
- 簡單版的形狀描述會漏掉罕見格式的信箱；正式環境換成託管的內容防護服務（決策書 8.2 M2）
- 只測了一句英文、一個信箱；一句話有多個信箱、信箱前後緊貼中文或標點的情況尚未測
- **`mask()` 目前只確定在 `make_summary()` 裡被呼叫（E64）。送往 OpenAI 的內容是否已經過遮罩，尚未檢查 `app/main.py`；** 四類個資做完後補一個 `test_chat` 的測試，確認假的 OpenAI 收到的是遮罩後的句子

**面試可用的說法：** 「個資遮罩我是先寫測試再寫功能，而且測兩個方向：有信箱的句子要被換成類別標籤，沒有個資的句子不能被動到。只測前者的話，一個把所有文字都換掉的函式也會通過。」

---

**收尾與推送（20:05）：** `EMAIL_PATTERN` 移到檔案上方的常數區；`append_audit` 的 docstring 拼字 `overwirte` 改為 `overwrite`。`feat: mask email addresses in prompts`、`docs: record M2 step 1-1 evidence`，推送結果 `1dad49e..5e9f237  main -> main`。

---

## E78. 步驟 1-2：手機號碼遮罩（2026-10-04 20:07～20:24）

**定案：範圍取「日常寫法」，標籤 `[PHONE]`。**

| 方案 | 抓得到 | 評估 |
|---|---|---|
| A 只抓連續 10 碼 | `0912345678` | 最簡單；常見的 `0912-345-678` 會漏 |
| **B（採用）** | `0912345678`、`0912-345-678`、`0912 345 678`、`+886912345678` | 涵蓋日常寫法，表示式仍講得出來 |
| C 連市話、各國號碼 | 幾乎全部 | 規則暴增，容易把訂單編號、金額誤判成電話 |

**取捨的依據：** 遮罩有兩種錯。漏遮是個資外流；誤遮是把正常數字塗掉，模型讀不懂問題。C 為了少漏一點，換來大量誤遮。

**形狀描述：**

```python
PHONE_PATTERN = r"(?<!\d)(\+886[- ]?|0)9\d{2}[- ]?\d{3}[- ]?\d{3}(?!\d)"
```

| 片段 | 意思 |
|---|---|
| `(?<!\d)` | 左邊不能是數字（只看一眼，不算進抓到的範圍） |
| `(\+886[- ]?\|0)` | 開頭二選一：`+886` 或 `0` |
| `9\d{2}` | 9 開頭，再 2 個數字 |
| `[- ]?\d{3}`（兩次） | 可有可無的橫線或空格，再 3 個數字 |
| `(?!\d)` | 右邊不能是數字 |

**生活比喻（左右檢查）：** 在電影院找「剛好 10 個人坐一起的團體」；左右還緊貼著別人，就是更大一團的一部分，不算。

**測試（本人撰寫，先看失敗）：**

| 測試 | 輸入 | 預期 |
|---|---|---|
| `test_mask_replaces_mobile_phone` | `Call me at 0912345678 tonight` | `Call me at [PHONE] tonight` |
| `test_mask_replaces_mobile_phone_with_dashes` | `Call me at 0912-345-678 tonight` | 同上 |
| `test_mask_replaces_mobile_phone_with_country_code` | `Call me at +886912345678 tonight` | 同上 |
| `test_mask_keeps_long_number` | `Order 20260912345678 shipped` | 不變（防誤遮） |

- 寫功能前：`3 failed, 20 passed`（前三個失敗、第四個通過，符合預期）
- 寫功能後：`23 passed in 1.28s`，一次通過

**本人撰寫：**

```python
def mask(text: str) -> str:
    """Replace personal data with a category label before the text leaves the gateway."""
    email_result = re.sub(EMAIL_PATTERN, "[EMAIL]", text)
    result = re.sub(PHONE_PATTERN, "[PHONE]", email_result)
    return result
```

第二次替換處理的是第一次的結果（`email_result`），E77 的錯誤沒有再犯。

### 遮罩順序：先信箱、後手機，並用測試鎖住

**理由：** 有的信箱開頭長得像手機，例如 `0912345678@example.com`。先換手機會把它切成兩半，信箱規則就認不出剩下的部分。

**補一個測試：** `test_mask_treats_phone_like_email_as_email`（`Mail 0912345678@example.com now` → `Mail [EMAIL] now`）。

**這個測試一寫就通過，所以刻意破壞一次，確認它真的在把關：**

| 動作 | 結果 |
|---|---|
| 把 `mask()` 的兩次替換對調（先手機、後信箱） | `1 failed, 23 passed` |
| 改回原順序 | `24 passed in 1.26s` |

對調時的失敗訊息：

```
E         - Mail [EMAIL] now
E         + Mail [PHONE]@example.com now
```

**判讀：** 順序錯的時候，`@example.com` 這段網域會留在送出去的內容裡。這是實際的外流，不只是標籤不同。

**生活比喻：** 裝好煙霧偵測器後，拿打火機在下面晃一下，確定它真的會叫。

**限制（誠實記錄）：**
- 不含市話、分機、其他國家的號碼
- 沒有 `+` 的 `886912345678` 不會被抓到
- 全形數字（`０９１２…`）不會被抓到
- 手機前後緊貼英文字母的情況未測

**面試可用的說法：**
- 「電話只是一串數字，最怕誤判。我的規則要求號碼左右不能再貼著數字，並且用一個測試確認訂單編號裡剛好含手機樣子的數字不會被遮。」
- 「遮罩的先後順序我有測試鎖住。寫完測試我故意把順序對調，確認它會變紅，而且看到失敗的樣子是網域外流，才改回來。一寫就通過的測試，我會先確認它失敗得了。」

---

**推送（20:27）：** `feat: mask mobile phone numbers in prompts`、`docs: record M2 step 1-2 evidence`，推送結果 `5e9f237..69077d0  main -> main`。

---

## E79. 指導老師 10/5 回饋與定案（2026-10-05）

**來源：** 本人 10/5 向指導老師回報進度（Google 文件「LLM Gateway 專題進度回報（10/5）」），老師留了四則註解；在另一個對話整理後交接過來。完整內容見 Project 的 `docs/handoff/teacher-feedback-1005-handoff.md`。

### 老師的四則註解（原文照錄）

| # | 註解位置 | 老師原文 |
|---|---|---|
| 1 | 「Bedrock 被帳號層級封鎖（Error 002）」 | 為什麼會被封鎖？ bedrock以後必然會引入open ai 等各家模型的調度監控 在未來會變成很重要的學習主題。 |
| 2 | 佐證表「Bedrock 被擋，已向 AWS Support 開案…」 | 恩恩 |
| 3 | 「向量資料庫那一步（老師的 Step 2）我列為不做，可以嗎」 | 看你對你的定性，如果你是把自己定性成 替企業做ai化， knowledge的部分躲不了，而且應該要考慮到data drift，且因應企業kw建立測試集等流程 |
| 4 | 「或另附一支技術版影片」 | 恩 另附一隻 會比較好 |

### 定案

| # | 項目 | 定案 | 理由 |
|---|---|---|---|
| A | 影片 | **兩支**：6 分鐘主影片（外行版 3 分鐘 + 內行精華 3 分鐘），另附一支技術版（10～15 分鐘） | 老師 10/5 同意另附 |
| B | 定位 | **雲端工程師，做 AI 上線後的治理層**（額度、計費、稽核、網路邊界），不是「替企業做 AI 化」 | 回應老師「看你對你的定性」 |
| C | 知識層 | 知識檢索（RAG）**維持不實作**；決策書補一段「正式環境會怎麼做」 | 定位是治理層；離 11/7 不到五週；老師的話是條件句 |
| D | Bedrock | **維持 D33（已退場）**，架構不改；不再追 AWS 業務、不新增升級路線 | 帳號未開通，改回等於網路層重做 |
| E | M7 小型 agent | **要做**。最小版、不改 Gateway、有條件開工、限時 6 小時 | 本人 10/5 決定，想挑戰自己並承諾其他關卡加快。Claude 原本建議取消，本人決定保留 |

**知識層不做，但 M3 會用同一種做法：** 老師提到的 data drift 與測試集，對應到本案是 M3 的 20 題路由測試集。模型換版、單價變更、路由門檻調整時要重跑並比對。

### M7 的做法與開工條件

| 項目 | 做法 |
|---|---|
| 位置 | 獨立的客戶端腳本（例如 `scripts/agent-demo/`），當 Gateway 的使用者，對本機的 Gateway 執行；`POST /v1/chat` 與 `ChatRequest`（D38）不改 |
| 迴圈 | 文字約定：模型回 `CALL 工具名(參數)` 就執行工具，結果放進下一輪的 `message`；回 `FINAL 答案` 就結束 |
| 工具 | 一到兩個本機小工具，不連外部服務 |
| 保護 | 最大步數上限；每一步都經過 Gateway 的身分、額度、遮罩、稽核 |
| 要演出的畫面 | ① 正常完成兩三步的任務，稽核看得到每一步；② 拿掉步數上限、改用低額度的 alice，迴圈被額度擋下 |

**為什麼不用 OpenAI 原生的工具呼叫：** 原生做法要讓 Gateway 接受完整對話紀錄與工具定義，等於改掉 D38 的請求格式，遮罩與稽核也要處理工具回傳的內容，估 8～12 小時，而且會動到 M1、M2 已驗收的東西。文字約定版不動 Gateway，估 5～6 小時。代價是它不是原生工具呼叫，文件與影片要照實說明，原生做法列為升級路線。

**與 M2 的關聯（開工前要注意）：** 工具結果會經過 `mask()`，一串數字可能被當成手機或卡號遮掉（E78 的規則）；`message` 上限 4000 字，任務設計成三步以內。

| 時段 | 開工條件 |
|---|---|
| 10/17～10/18 | M3 與 CI 都在 10/16（五）前完成（建議搶這一個） |
| 10/31～11/1 | M6 在 10/30（五）前完成 |
| 11/2～11/3 | M6 在 11/1 準時完成，且沒有要補的進度、截圖或錄影；金鑰要用新的 |

三個時段都沒達到就不做，改用備案：把 M2 驗收的「連續呼叫到超額」寫成十幾行的迴圈腳本，旁白講成模擬失控的迴圈。

### 時程影響（誠實記錄）

里程碑的檢查點不動。多出的工作量：各關驗收錄影約 3 小時、技術版影片剪接與旁白約 5～6 小時、M7 限時 6 小時，合計約 14～15 小時。決策書 8.5 估的餘裕只有 5～15 小時，影片的 8～9 小時是必做，已吃掉大部分；M7 只能靠前面幾關提早完成來換，所以一定要有開工條件。

**每關收尾新增錄影：** 每個驗收條件錄一段 20～30 秒（Windows 剪取工具，`Win + Shift + R`）。M2 要錄 S01～S04。錄之前先輸入 `function prompt {"PS> "}`，提示字元就不顯示使用者資料夾；影片存在 repo 外面。

### 10/5 的 repo 變動

| 項目 | 內容 |
|---|---|
| 重遮截圖 | 12 張 M0.5 終端機截圖的路徑露出使用者資料夾名稱，共 35 處，已用灰色方塊重遮。commit `da2cad2`（`docs: remask user folder in M0.5 screenshots`） |
| 舊圖仍在 git 歷史 | 評估後不處理：清除要改寫歷史並強制推送，`main` 禁止強制推送；該名稱與 GitHub 帳號接近，不是金鑰等級 |
| 新增截圖 | AWS Support 案件四張（`m0-support-case-1-list.png`～`-4-reply.png`），對應 E3、E5，commit `80d27d7`（`docs: add AWS support case screenshots`）。遮蔽：帳號名稱與帳號 ID、案例 ID、信用卡末四碼、客服姓名、本人名字 |
| 上傳方式 | 兩筆都從 GitHub 網頁上傳；**開發機要先 `git pull`，否則下一次 push 會被拒絕** |
| 目前 repo 狀態 | `docs/screenshots/` 87 張、`docs/logs/` 18 個。正式清單 S01～S21 共 21 項，到位 4 項（S19、S20、S21 完整，S18 只有前半） |
| 用字更正 | 進度回報文件寫「正式截圖 21 張到位 6 張」，單位混用；正確是「21 項到位 4 項」（6 是檔數） |

### 更正：三張被引用的截圖不存在（2026-10-05 19:29 本人確認）

| 檔名 | 引用處 | 狀態 |
|---|---|---|
| `m0-openai-key-list-inherited.png` | E21 | 當時沒有存檔 |
| `m1-workspace-trust-enabled.png` | M1 證據紀錄（E45 的待存清單） | 當時沒有存檔 |
| `m1-workspace-trust-list.png` | 同上 | 當時沒有存檔 |

- 這三張都不在決策書 11.4 的正式清單（S01～S21）內，不影響驗收
- 對應的設定與結果在證據紀錄中有文字記載，文字紀錄仍然有效；只是沒有圖可以佐證
- 不補拍：畫面是當時的狀態，事後重拍的圖不能代表當時
- 舊紀錄中的引用處，M2 結案整理文件時改成「截圖未存檔」

**學到的（截圖）：** 紀錄裡寫了檔名不等於檔案存在。之後每次收到截圖，改名、遮蔽、回傳後，要確認它出現在 `git status` 裡才算完成。

**學到的：** 遮蔽做過一次不代表做完。12 張舊圖是回報前重新檢查才發現露出資料夾名稱；公開 repo 的東西推上去就收不回來，檢查要在推送前做。

**面試可用的說法：** 「老師問我要不要做知識庫。我的回答是先講清楚自己的定位：我做的是 AI 上線之後的治理層，所以不實作，但我在文件寫了知識檢索接進來時會經過 Gateway 的哪些環節。範圍是依定位決定的，不是做不完才砍的。」

### 決策書 v2.8 待改項目（M2 結案時搬進結案報告附錄）

| # | v2.7 的位置 | 要改什麼 |
|---|---|---|
| 1 | 11.1、PART 9「呈現方式」、12.5 | 影片時長改為定案：6 分鐘主影片 + 另附技術版（10～15 分鐘）；12.5 該列劃掉 |
| 2 | 7.9 的「RAG / 向量資料庫」那一列（v2.7 的舊標題） | 標題改為「知識檢索（RAG）」，整列改寫，新文字見 E84「7.9 那一列的新寫法」 |
| 3 | 1.3、8.1 | 補一句定位：雲端工程師，做 AI 上線後的治理層 |
| 4 | 1.3、8.1、8.2 的 M7、PART 9 | M7 由「選配」改為「有條件開工」；做法改為文字約定 |
| 5 | D38 的「不選的選項」 | 補評估結果：M7 用文字約定，D38 不改；原生工具呼叫列為升級路線 |
| 6 | 8.3 每關收尾清單 | 新增第 6 項「錄影」 |
| 7 | 8.4 砍除順序 | 第 1 項維持 M7；新增第 2 項「技術版影片縮為 6～8 分鐘」，其餘順延 |
| 8 | 8.5 時程表、12.5「M7 做不做」 | 照本筆的時程與三個開工時段更新 |
| 9 | 11.4 截圖清單下方 | 補 M0 佐證：AWS Support 案件四張 |
| 10 | 11.5 截圖規範 | 新增：信用卡末四碼必遮；錄影時提示字元改短；錄主控台不框最上面那一列；影片檔不進 repo |
| 11 | 7.1 的歷史說明（選擇性） | 可補：老師提醒 Bedrock 的多模型調度是未來重要的學習主題；本案因帳號未開通維持不採用 |
| 12 | 8.2 的 M2、M3 | 成本換算排在 M3，但 M2 扣額度就需要金額（本檔「M2 步驟規劃」的缺口） |
| 13 | PART 11（11.1～11.3）、PART 9「呈現方式」 | 新增：簡報檔是兩支影片的共同骨架與腳本；每個里程碑驗收後更新對應頁面與附錄的素材狀態，版號 +0.1（E84） |
| 14 | PART 11、8.3 每關收尾清單 | 新增：旁白逐字稿與動畫記在獨立檔案（`docs/slides/narration-v*.md`），素材全部到齊後才放進簡報；每關收尾時同步更新簡報對應頁與旁白稿（E84） |
| 15 | D22（repo 結構）、11.5 | 新增 `docs/slides/`：放簡報與旁白稿；影片檔不進 repo（E84） |
| 16 | 全文用詞：1.3、7.9、8.1、PART 9 與其他出現處 | 「RAG」與「向量資料庫」不並列當同義詞。不做的項目一律寫「知識檢索（RAG）」；「向量資料庫」只在講元件或成本時單獨出現。1.3 的「不做知識檢索(RAG)/向量資料庫」改為「不做知識檢索（RAG）」（E84） |
| 17 | 3.2 的 `audit` 表、8.2 的 M2 | 補上個資類別的欄位名稱與寫法：`pii_types`，值為不含中括號的類別名稱清單，順序固定為 `EMAIL`、`CARD`、`PHONE`、`TW_ID`，沒有個資時為空清單；成功與失敗的紀錄都有此欄（E85） |
| 18 | 3.2 的「時區注意」、D2、D22（repo 結構） | 補上實作：`app/quota.py` 的 `period_of(moment)`，以固定偏移 `TAIPEI_TZ`（UTC+8）換算後回傳 `YYYY-MM`；只收帶時區的時間，沒帶時區丟 `ValueError`；不使用時區資料庫與 `tzdata`。repo 結構加上 `app/quota.py`（E86） |
| 19 | D30、8.2 的 M2 與 M3、D22（repo 結構） | 補上 M2 的實作：`app/pricing.py` 的 `cost_micro_usd(model, input_tokens, output_tokens)`；單價以整數存（每一百萬個 token 多少 micro-USD），輸入與輸出加總後進位一次；沒有單價的模型丟 `ValueError`。M2 單價為程式內的字典常數，M3 搬到設定檔並加入 `gpt-6-sol`。repo 結構加上 `app/pricing.py`（E87） |
| 20 | 12.5「超額回應的狀態碼與重試語意」、10.3 第 9 點、2.2 流程圖 [3]、3.2 的 `audit` 表、8.2 的 M2 | 補上超額回應的定案：429、`{"detail": "Monthly quota exceeded"}`、附 `Retry-After`（到台北時間下個月 1 號 00:00 的秒數，進位成整數）；已用 ≥ 額度就擋；被擋的請求寫稽核（`status` 新增 `quota_exceeded`），API Key 驗證失敗的不寫；額度讀不到回 503 `Quota service unavailable`、Key 錯誤回 401 `Authentication failed`。12.5 該列劃掉。實作為 `app/quota.py` 的 `is_over_quota()`、`seconds_until_next_period()`（E88） |
| 21 | D22（repo 結構） | 加上 `compose.yaml`、`app/db.py`、`scripts/create_tables.py`、`tests/conftest.py`（E89） |
| 22 | D36、8.2 的 M2 | 補上 D36 之後的資料層做法：本機用 DynamoDB Local（`amazon/dynamodb-local:3.3.1`，鎖 digest，`-sharedDb -inMemory`，只綁 `127.0.0.1:8001`）；連線由 `app/db.py` 的 `make_dynamodb_client()` 建立，網址來自必填的環境變數 `DYNAMODB_ENDPOINT_URL`；建表在 `scripts/create_tables.py`，不放進 Gateway（E89） |
| 23 | 3.2 的 `quotas` 表 | 補上欄位名：`limit_micro_usd`、`used_micro_usd`；M2 只建 `api_keys`、`quotas`、`audit` 三張，`usage` 於 M5 建立（E89） |
| 24 | 8.2 的 M2 | 補上：碰資料庫的測試打真的 DynamoDB Local，標 `integration`；測試用獨立的容器（`127.0.0.1:8002`），每個測試前清空（E89） |
| 25 | 12.8 的「冷卻期的一次例外」、12.5 | 補上複查結果：10/7 以 `docker buildx imagetools inspect` 確認 `python:3.12-slim` 的 digest 仍存在且未變；未掃弱點（E89） |
| 26 | 2.2 流程圖 [2]、8.2 的 M2、4.2 應用層 | 補上驗證的做法：`Authorization: Bearer gw_…`；失敗一律回 401 `{"detail": "Authentication failed"}` 並附 `WWW-Authenticate: Bearer`；驗證寫成 FastAPI 的相依，失敗的請求不碰模型、不寫稽核（E90） |
| 27 | 3.2 的 `api_keys` 表、D3 | 補上 `status` 欄位：值是 `active` 才放行，其餘（含欄位不存在）一律拒絕；Key 的格式為 `gw_` 加 `secrets.token_hex(32)`（E90） |
| 28 | 12.5「超額回應…」那一列與本表第 20 項、2.2 流程圖 [3]、10.3 第 1 點 | 資料庫讀不到時的 503 訊息改為驗證與額度共用：`{"detail": "Service temporarily unavailable"}`（取代第 20 項寫的 `Quota service unavailable`）；資料庫連不上時最先出錯的是驗證（E90） |
| 29 | D10、3.4 或 3.2、D22（repo 結構） | 補上資料庫連線的逾時與重試：連線 2 秒、讀取 5 秒、總共試 2 次、`standard` 模式；實測預設值要 48.1 秒才報錯，設定後 6.7 秒。repo 結構加上 `app/auth.py`（E90） |

---

## E80. 步驟 1-3：身分證字號遮罩（2026-10-05 19:32～20:04）

**開工前：** `git pull`，`69077d0..80d27d7`，Fast-forward，16 個截圖檔（10/5 從網頁上傳的兩筆 commit，E79）。

**定案：**

| 決定 | 選擇 | 為什麼 |
|---|---|---|
| 標籤 | `[TW_ID]` | 沿用類別標籤的做法（E77） |
| 小寫開頭 | 也遮 | 使用者不一定會按大寫，漏掉就是外流 |
| 檢查碼 | 不驗 | 身分證寧可多遮也不要漏：遮掉一串假號碼沒有損失，漏掉一個真的代價很大。信用卡才驗（Luhn），因為 16 位純數字太容易與其他數字相撞 |
| 測試用的假號碼 | `A123456780` | 常見範例 `A123456789` 的檢查碼成立，理論上可能是真人的字號；最後一碼改為 0 後檢查碼不成立 |

**測試（本人撰寫，先看失敗）：**

| 測試 | 輸入 | 預期 |
|---|---|---|
| `test_mask_replaces_tw_id` | `My ID is A123456780 thanks` | `My ID is [TW_ID] thanks` |
| `test_mask_replaces_lowercase_tw_id` | `My ID is a123456780 thanks` | 同上 |
| `test_mask_keeps_product_code` | `Part AB123456780 in stock` | 不變（前面多一個字母是料號） |

寫功能前：`2 failed, 25 passed`，符合預期。

**這次由本人自己組形狀描述。** 用到的語法都學過，所以只給「每一段要表達什麼」，不給答案。

本人第一版：

```python
TW_ID_PATTERN = r"(?<![A-Za-z0-9])[A-Za-z][1?|2]{\d}(?![A-Za-z0-9])"
```

五段中三段正確（左邊檢查、一個字母、右邊檢查），中間兩段有誤：

| 段 | 寫成 | 問題 | 正確 |
|---|---|---|---|
| 1 或 2 | `[1?\|2]` | 把圓括號的「`A\|B`」寫法帶進中括號。中括號本身就是「任選一個字元」，裡面的 `?` 和 `\|` 會變成普通字元，等於 `1`、`?`、`\|`、`2` 四選一 | `[12]` |
| 8 個數字 | `{\d}` | 順序反了，也少了次數。規則是「東西在前、大括號在後、大括號裡放次數」 | `\d{8}` |

**生活比喻（中括號）：** 自助餐的夾菜區，放進去的每一樣都是可以選的菜；把寫著「或」的牌子丟進菜盤，它就變成一道菜。

**本人修正後：**

```python
TW_ID_PATTERN = r"(?<![A-Za-z0-9])[A-Za-z][12]\d{8}(?![A-Za-z0-9])"

def mask(text: str) -> str:
    """Replace personal data with a category label before the text leaves the gateway."""
    email_result = re.sub(EMAIL_PATTERN, "[EMAIL]", text)
    phone_result = re.sub(PHONE_PATTERN, "[PHONE]", email_result)
    result = re.sub(TW_ID_PATTERN, "[TW_ID]", phone_result)
    return result
```

**結果：** `27 passed in 1.85s`。三次替換接力，變數名稱（`email_result`、`phone_result`）看得出是哪一步的結果。

**為什麼左右檢查要包含英文字母：** 手機只怕被包在更長的數字裡；身分證是「字母 + 數字」，還要防它被包在更長的英數字串裡。

**限制（誠實記錄）：**
- 第一版的錯誤沒有實際跑過測試，是貼出來時就被指出的；所以「`[1?|2]` 會讓哪個測試失敗」沒有實測紀錄
- 只涵蓋本國身分證字號；外來人口統一證號（第二碼為 8、9 的新式，或兩個英文字母開頭的舊式）不會被抓到
- 不驗檢查碼，所以形狀相同的非身分證字串（例如某些產品序號 `A123456780`）會被遮掉；這是刻意的取捨
- 全形字元不會被抓到

**面試可用的說法：** 「身分證字號和信用卡我用了相反的策略。身分證不驗檢查碼，寧可多遮；信用卡要驗 Luhn，因為 16 位純數字太容易誤判。判斷依據是這類資料漏掉的代價，和誤遮的機率。」

---

**推送（20:58）：** `feat: mask Taiwan ID numbers in prompts`、`docs: record teacher feedback and M2 step 1-3 evidence`，推送結果 `80d27d7..2d83a89  main -> main`。

---

## E81. 步驟 1-4：信用卡號遮罩與 Luhn 檢查（2026-10-05 20:57～22:29）

**時程評估（20:57，誠實記錄）：** 本人問今天能不能把 M2 做完。評估剩餘約 18～20 小時（步驟 1 收尾 2、步驟 2～4 共 3、步驟 5 為 3、步驟 6～9 共 7～8、步驟 10～12 共 3～4），當天做不完。改訂：當晚完成步驟 1，10/10 結案（原訂 10/11）。理由：後半段是全新的工具，趕著做會變成照抄，面試講不出來。

**為什麼信用卡要驗算、身分證不用（接 E80）：** 13～19 位純數字的東西太多（訂單編號、物流單號）。隨機一串數字通過 Luhn 的機率是十分之一，驗過再遮可減少約九成誤遮。

**生活比喻：** 超商條碼的最後一碼是算出來的；手動輸入打錯一碼，收銀機會拒絕。

### 第一段：`luhn_valid()`

**測試（本人撰寫）：**

| 測試 | 檢查 |
|---|---|
| `test_luhn_accepts_valid_card_number` | `luhn_valid("4111111111111111") is True`（金流業公開的測試卡號） |
| `test_luhn_rejects_wrong_check_digit` | `luhn_valid("4111111111111112") is False` |

**新的失敗樣子：收集階段出錯。** 函式還不存在時，結果不是 `failed`：

```
collected 10 items / 1 error
tests\test_audit.py:5: in <module>
E   ImportError: cannot import name 'luhn_valid' from 'app.audit'
!!!!! Interrupted: 1 error during collection !!!!!
```

測試檔在 `import` 那行就停了，pytest 還在清點測試，一個都沒跑。`failed` 是跑了但結果不對；`error` 是跑不起來。

**算法（以 `5611` 示範）：** 從右往左，第 2、4、6… 位乘 2，乘完超過 9 就減 9，全部加總，除以 10 餘 0 即合法。1 + 2 + 6 + 1 = 10。

**新語法：** `enumerate(reversed(digits))`（倒著走並附編號，從 0 開始）、`int(ch)`、`%` 取餘數。

### 挫折：四次才通過，每次的訊息都指向不同的問題

| 次 | 訊息 | 原因 | 誰找到的 |
|---|---|---|---|
| 1、2 | `assert 4 is True` | 回傳的是 `total`（數字），不是布林值 | 本人 |
| 3 | `assert None is True` | 沒有 `return` 到東西；函式走到底沒遇到 `return` 就回傳 `None` | 本人 |
| 4 | `assert False is True`，`1 failed, 28 passed` | 迴圈內的兩個邏輯錯誤（見下） | 經指出方向後本人修正 |
| 5 | `29 passed` | — | — |

第 4 次的程式：

```python
    for index, ch in enumerate(reversed(digits)):
        num = int(ch)
        if index % 2 != 0:
            total = total + (num * 2)
            if total > 9:
                total = total - 9
```

- **錯誤 1：** 加總寫在 `if` 裡面，不用乘 2 的那幾位完全沒被加進去
- **錯誤 2：** 「超過 9 就減 9」檢查的是累計的 `total`，應該檢查這一位的值
- **排查方法：** 拿 `5611` 逐圈手算，得到 3 而不是 10
- **第二個測試是碰巧通過的：** 這個版本對任何輸入都回 `False`，所以「錯的卡號要回 `False`」過了，但不是算對的。只測一個方向會誤以為函式寫好了（呼應 E77 的兩個方向）

**生活比喻：** 結帳時每樣商品都要刷進總金額，只是有些要先貼折扣貼紙改價。錯的寫法是「只有貼了貼紙的才刷」，而且折扣打在總金額上。

**本人撰寫（最終版）：**

```python
def luhn_valid(digits: str) -> bool:
    """Return True when the digits pass the Luhn checksum."""
    total = 0
    for index, ch in enumerate(reversed(digits)):
        num = int(ch)
        if index % 2 != 0:
            num = num * 2
            if num > 9:
                num = num - 9
        total = total + num

    if total % 10 == 0:
        return True
    else:
        return False
```

### 第二段：接進 `mask()`

**測試（本人撰寫）：**

| 測試 | 輸入 | 預期 |
|---|---|---|
| `test_mask_replaces_card_number` | `Pay with 4111111111111111 today` | `Pay with [CARD] today` |
| `test_mask_replaces_card_number_with_spaces` | `Pay with 4111 1111 1111 1111 today` | 同上 |
| `test_mask_keeps_number_failing_luhn` | `Order 4111111111111112 shipped` | 不變 |

寫功能前：`2 failed, 30 passed`，符合預期。

**形狀描述（由 Claude 提供並逐段說明）：**

```python
CARD_PATTERN = r"(?<!\d)\d([- ]?\d){12,18}(?!\d)"
```

第 1 個數字，加上「可有可無的分隔符號 + 1 個數字」這一組重複 12～18 次，共 13～19 個數字；左右不能再貼著數字。

**新觀念：`re.sub` 的第二格放函式。** 前三類是「抓到就換」；信用卡要「抓到後先驗算，過了才換」。`re.sub` 每抓到一段就交給這個函式，函式回傳什麼，那一段就變成什麼；回傳原文等於不換。

**生活比喻：** 前三類像自動門；信用卡像有警衛的門，先看證件再放行。

**說明不清楚的一次（Claude 的問題，照實記錄）：** 第一次講解一口氣放了三個新觀念（把函式交給 `re.sub`、`match.group(0)`、新的形狀描述），而且只講概念。本人卡了約半小時後表示看不懂。改成「拿一句話走六個步驟」的表格，並給填空版後才接上。之後一次只引入一個新觀念，並且先給走一遍的例子。

**本人撰寫（填空版，四個空格）：**

```python
def replace_card_if_valid(match: re.Match) -> str:
    """Return the card label when the digits pass Luhn, otherwise the original text."""
    found = match.group(0)
    digits = re.sub(r"[- ]", "", found)
    if luhn_valid(digits):
        return "[CARD]"
    else:
        return found


def mask(text: str) -> str:
    """Replace personal data with a category label before the text leaves the gateway."""
    email_result = re.sub(EMAIL_PATTERN, "[EMAIL]", text)
    card_result = re.sub(CARD_PATTERN, replace_card_if_valid, email_result)
    phone_result = re.sub(PHONE_PATTERN, "[PHONE]", card_result)
    result = re.sub(TW_ID_PATTERN, "[TW_ID]", phone_result)
    return result
```

**順序：信箱 → 信用卡 → 手機 → 身分證。** 信用卡是最長的數字，先處理，後面的規則不會碰到它的片段。

### 挫折：形狀描述本身被寫進了句子

第一次執行 `2 failed, 30 passed`，失敗的是兩個「不該被遮」的測試：

```
E         - Order 20260912345678 shipped
E         + Order (?<!\d)\d([- ]?\d){12,18}(?!\d) shipped
```

- **怎麼判讀：** `+`（實際）那行出現的是 `CARD_PATTERN` 的內容。代表驗算沒過的那條路，回傳的不是原本抓到的文字
- **原因（本人確認）：** `else` 分支寫成 `return CARD_PATTERN`。「沒過就放回原樣」要放回的是抓到的那段文字（`found`），不是用來找它的形狀描述
- **結果：** 本人自行修正為回傳 `found`，`32 passed in 0.81s`
- **意外的幫手：** 被抓到的不只新測試，還有 E78 的 `test_mask_keeps_long_number`。`20260912345678` 有 14 個數字，符合卡號形狀，會被送去驗算（總和 57，不通過）。一個為手機寫的測試，擋下了信用卡功能的錯誤

**限制（誠實記錄）：**
- 通過 Luhn 的一般編號仍會被誤遮，機率約十分之一
- 卡號後面隔一個空格緊接其他數字時（例如 `4111111111111111 12`），會被一起抓成 18 位去驗算，驗算不過就整段不遮，卡號因此漏掉；未處理
- 沒有檢查發卡機構的開頭碼與各家卡的實際長度
- 全形數字不會被抓到
- 正式環境換成託管的內容防護服務（決策書 8.2 M2）

**面試可用的說法：**
- 「信用卡我先比對形狀、再用 Luhn 驗算，過了才遮。隨機數字通過 Luhn 的機率是十分之一，所以訂單編號被誤遮的情況少九成。」
- 「寫 Luhn 的時候我有一版對任何輸入都回 False，結果『錯的卡號要被拒絕』那個測試是綠的。因為我同時測了合法的卡號，才知道函式其實沒寫對。」

---

**推送（22:33）：** `feat: mask card numbers that pass the Luhn check`、`docs: record M2 step 1-4 evidence`，推送結果 `2d83a89..92d7bc5  main -> main`。

---

## E82. 步驟 1-5：「個資跨在第 50 字」的邊界測試（2026-10-05 22:33～22:41）

**來源：** E34、E64 留下的缺口。M1 已把 `make_summary()` 的順序寫成「先遮罩、再截斷」，但沒有測試保護這個順序。

**在防什麼：** 摘要只留前 50 個字。手機號碼剛好落在第 47～56 個字時，切的位置在號碼中間。

| 做法 | 過程 | 摘要結尾 |
|---|---|---|
| 先截斷、再遮罩（錯） | 切完號碼只剩 `0912`，不符合手機的形狀，不會被遮 | `… 0912`，留下半截號碼 |
| **先遮罩、再截斷（採用）** | 整串先換成 `[PHONE]` 再切 | `… [PHO`，沒有數字 |

**生活比喻：** 把寫了電話的紙裁成小卡。先塗黑再裁，裁到哪都看不到號碼；先裁再塗，剩下的半截號碼不像電話，沒人會去塗它。

**測試（本人撰寫）：**

```python
# 手機跨在第 50 字前後時，摘要不能留下被切一半的號碼（先遮罩再截斷）
def test_summary_does_not_leak_split_phone():
    text = "a" * 45 + " 0912345678 end"

    result = make_summary(text)

    assert "0912" not in result
```

**這個測試一寫就通過，所以刻意破壞一次：**

| 動作 | 結果 |
|---|---|
| 把 `make_summary()` 改成先截斷、再遮罩 | `1 failed, 32 passed` |
| 改回原順序 | `33 passed in 0.99s` |

破壞時的失敗訊息：

```
>       assert "0912" not in result
E       AssertionError: assert '0912' not in 'aaaaaaaaaaa...aaaaaaa 0912'
E         '0912' is contained here:
E           aaaaaaaaaa 0912
E         ?            ++++
```

**判讀：** 順序錯的時候，稽核摘要的結尾真的留下了號碼的前四碼。pytest 用 `++++` 標出洩漏的位置。

**限制（誠實記錄）：**
- 只測了手機跨界的情況；信箱、身分證字號、信用卡號跨界沒有各自的測試（機制相同，都是先遮罩）
- 只檢查「前四碼不在摘要裡」，沒有檢查摘要的完整內容
- 被截斷的標籤（`[PHO`）會留在摘要裡，看得出是標籤被切到，但類別不完整；個資類別另外記在稽核欄位（步驟 2），不依賴摘要

**面試可用的說法：** 「摘要我是先遮罩再截斷。如果反過來，號碼剛好跨在第 50 個字時會被切成半截，半截不符合規則就不會被遮。這個順序我有測試守著，也實際把順序對調過，看到摘要結尾留下號碼前四碼才改回來。」

---

**推送（22:44）：** `test: guard mask-before-cut order in summary`、`docs: record M2 step 1-5 evidence`，推送結果 `92d7bc5..170d6c3  main -> main`。commit 前以 `git status` 確認只有 `tests/test_audit.py` 被改動，破壞實驗已完全還原。

---

## E83. 步驟 1-6：確認送往模型與寫入稽核的內容都已遮罩（2026-10-05 22:44～23:14）

**來源：** E77 留下的待確認項目。`mask()` 四類都完成了，但只確定它在 `make_summary()` 裡被呼叫；送往 OpenAI 的內容有沒有遮，要看 `app/main.py` 才知道。

**生活比喻：** 店裡的訂單存根把電話塗黑了，但送進廚房的那張單子有沒有塗，要走去廚房看。

**檢查結果：接線在 M1 就寫好了，`main.py` 不需要修改。**

```python
masked = mask(request.message)
...
result = chat(client, MODEL, [{"role": "user", "content": masked}], REASONING_EFFORT)
```

M1 時 `mask()` 是空殼所以沒有效果；M2 補上內容後，這條線自動生效（E64「呼叫順序從現在就寫對」的設計在這裡兌現）。

| 去處 | 使用的值 | 是否遮罩 |
|---|---|---|
| 送給 OpenAI | `masked` | 是 |
| 稽核的摘要 | `make_summary(request.message)`，內部先遮罩 | 是 |
| 稽核的指紋 | `hash_prompt(request.message, …)`，對原文計算 | 否（D4 的定案：存的是 HMAC 結果，看不到原文；對原文算才能事後比對） |

**問題：這條線沒有測試保護。** 有人把 `masked` 改回 `request.message`，原本的 33 個測試仍然全部通過。

**測試（測試道具由 Claude 提供並逐行說明，`tests/test_chat.py`）：**

```python
# M2 驗收條件：送給模型的內容已遮罩，找不到原本的個資
def test_chat_sends_masked_message_to_model(tmp_path):
    client, completions, _ = make_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "My ID is A123456780 thanks"})

    sent = completions.last_request["messages"][0]["content"]
    assert sent == "My ID is [TW_ID] thanks"


# M2 驗收條件：稽核紀錄裡也找不到個資，摘要是遮罩後的
def test_chat_audit_does_not_contain_personal_data(tmp_path):
    client, _, audit_path = make_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "My ID is A123456780 thanks"})

    text = audit_path.read_text(encoding="utf-8")
    record = json.loads(text)
    assert "A123456780" not in text
    assert record["summary"] == "My ID is [TW_ID] thanks"
```

- 假的 OpenAI（`tests/fakes.py`）會把收到的請求記在 `last_request`；測試從裡面取出實際送出的那句話
- 兩個測試分別檢查兩個去處：送給模型的內容、寫進稽核檔的紀錄

**說明不清楚的一次（Claude 的問題，照實記錄）：** 第一次只在說明文字中給了 `sent = completions.last_request[...]` 這一行，沒有講它要放在測試裡的哪個位置。本人反映後改為給完整的測試並逐行對應「準備、執行、檢查」。之後給程式片段時，一律連同它所在的位置一起給。

**破壞實驗（兩個測試一寫就通過）：**

| 動作 | 結果 |
|---|---|
| 把 `chat(...)` 的 `masked` 改成 `request.message` | `1 failed, 34 passed` |
| 改回 `masked` | `35 passed in 0.89s` |

破壞時的失敗訊息：

```
>       assert sent == "My ID is [TW_ID] thanks"
E       AssertionError: assert 'My ID is A123456780 thanks' == 'My ID is [TW_ID] thanks'
E         - My ID is [TW_ID] thanks
E         + My ID is A123456780 thanks
```

**判讀：** 假的 OpenAI 收到了完整的身分證字號。在真實環境，這就是個資被送出 AWS、在供應商端最多保留 30 天（E20）。只失敗一個是對的：第二個測試檢查的是稽核檔，摘要走的是 `make_summary()`，不受這次破壞影響。

**步驟 1 完成。** 個資遮罩的四類、順序、邊界、兩個去處都有測試。測試數由 M1 結案時的 17 個增加到 35 個。

**限制（誠實記錄）：**
- 兩個端到端測試只用了身分證字號；其他三類在 `test_audit.py` 以單元測試涵蓋，沒有各自的端到端測試
- 只驗證假的 OpenAI 收到的內容；真實呼叫留到步驟 11 的驗收（S04）
- 模型的**回覆**沒有經過遮罩。模型若在回答中寫出個資（例如使用者要求它編造），會原樣回給使用者；這不在 M2 的範圍
- 稽核的指紋對原文計算；持有 HMAC 金鑰的人可以用猜測的原文比對指紋（D4 已記載的取捨）

**面試可用的說法：**
- 「遮罩我驗證了兩個去處：送給模型的內容，和寫進稽核的紀錄。測試用的是一個會把收到的請求記下來的假模型，所以我檢查的是實際送出去的那句話，不是我以為會送出去的。」
- 「M1 的時候遮罩函式還是空的，但我先把『先遮罩、再送出』的呼叫順序寫好。M2 把函式補上之後，主程式一行都不用改。」

---

**推送（23:16）：** `test: verify masked content reaches the model and the audit log`、`docs: record M2 step 1-6 evidence`，推送結果 `170d6c3..7b4e1bc  main -> main`。

---

## E84. 期末簡報 v1（2026-10-05～10-06）

**來源：** 在另一個對話製作，10/6 交接過來。完整內容見 Project 的 `docs/handoff/slides-v1-handoff.md`。

### 經過

| 時間 | 事件 |
|---|---|
| 10/5 | 老師看完進度回報後回覆：「收到，那我們應該要開始確認你的最終簡報脈絡了」「是否能先給我一個你預計的簡報大綱」 |
| 10/5 | 交出簡報大綱（三欄：章節／內容／素材狀態；主影片與技術版各一份） |
| 10/5 | 老師未對大綱評論，判讀為想先看到實際內容，產出 PPTX v0.1（18 頁） |
| 10/5 | 老師補充：期末目標是簡報影片「給外人的感受，是你想要的定位」，重點不能跑掉 |
| 10/5 | 重新審視後產出 v0.2（31 頁），確立「一份簡報，兩支影片」的結構（未上傳） |
| 10/6 | 逐頁放大檢查、數字逐項對照決策書 v2.7 與證據紀錄後定為 v1（32 頁） |
| 10/6 | 本人指出第 10 頁把「RAG」與「向量資料庫」寫成同一件事，簡報兩處、旁白一處統一改為「知識檢索（RAG）」 |
| 10/6 | 本人決定：v1 只固定骨架；逐字稿與動畫記在獨立檔案，素材全部到齊後才放進簡報 |

### 定案

| # | 項目 | 定案 | 理由 |
|---|---|---|---|
| A | 簡報的角色 | **簡報是兩支影片的共同骨架**，同時是腳本 | 兩支影片講的是同一個系統，分開做兩份會互相對不上 |
| B | 逐字稿與動畫 | 記在獨立檔案；**素材全部到齊後才放進簡報** | 現在放進去，之後每換一張畫面就要重調一次 |
| C | 更新方式 | 每個里程碑驗收後，替換對應頁面的畫面、更新狀態標籤與附錄的素材狀態、旁白稿同步改；版號 +0.1 | 簡報跟著實際進度走，不到最後才一次補 |
| D | 存放 | 簡報與旁白稿進 `docs/slides/`；影片檔不進 repo | 影片檔大，repo 是公開的 |
| E | 用詞 | 不做的項目寫「**知識檢索（RAG）**」；「向量資料庫」只在講元件或成本時單獨出現 | RAG 是整套做法，向量資料庫只是其中一個元件，兩者不是同義詞 |

### v1 的內容

- 檔案：`docs/slides/llm-gateway-slides-v1.pptx`、`docs/slides/narration-v1.md`
- 結構：封面 → 時間預算 → 主影片 9 頁（深色）→ 技術版 20 頁（淺色）→ 附錄 2 頁（素材狀態、時程，不進影片），共 32 頁
- 簡報本身不含逐字稿與動畫；每頁的旁白、字數秒數、畫面出現順序記在 `narration-v1.md`
- 技術版第 20 頁「升級路線與結論」是新增的，讓技術版有收尾
- 定位句出現三次（封面、主影片 03、主影片 09）：「雲端工程師，負責 LLM 上線之後的治理」

### 時間預算

以每分鐘 220 字估算；中文字算 1、英數詞算 2。

| 影片 | 旁白字數 | 旁白時間 | 上限／目標 |
|---|---|---|---|
| 主影片 | 872 | 約 4.0 分鐘 | 6 分鐘（其餘約 2 分鐘給示範畫面與轉場） |
| 技術版 | 1776 | 約 8.1 分鐘 | 10～15 分鐘（加示範後約 10～12 分鐘） |

### v0.1 → v1 的改動與原因

| 改動 | 原因 |
|---|---|
| 18 頁 → 32 頁，主影片與技術版分成兩套版型 | v0.1 一頁塞太多，講不完也不好讀；拆開後每頁只講一件事 |
| 每頁寫旁白逐字稿與秒數（存獨立檔案） | 沒有逐字稿就無法回答「6 分鐘講不講得完」 |
| 定位句固定出現在開頭、中段、結尾 | 老師要求外人看完的感受要等於想要的定位 |
| 「發現二」的程式碼框改貼近 log 原文 | v0.1 是改寫過的輸出；佐證應該用原文 |
| 還沒有結果的頁面加上狀態標籤（待 M3、M4 驗收時錄製等） | 不把還沒做的東西畫成已完成 |

### 待補頁面（目前是示意）

| 頁 | 內容 | 何時補 |
|---|---|---|
| 主影片 04 面板 2 | 月額度 503 畫面 | **M2（10/10）** |
| 主影片 04 面板 1 | 智慧路由畫面 | M3（10/18） |
| 主影片 05 | X%（路由省下的比例） | M3 測試集結果 |
| 主影片 07、技術版 14 | 網路邊界實測 | M4（10/25） |
| 技術版 13 | 雲端稽核紀錄 | M5（11/1） |

M2 結案時要換的是主影片 04 的面板 2，素材來自步驟 11 的 S03 截圖與錄影。

### 7.9 那一列的新寫法（v2.8 採用）

| 項目 | 為什麼不做 | 正式環境會怎麼做 |
|---|---|---|
| **知識檢索（RAG）** | 本專題定位是 LLM 上線後的治理層（見 1.3）。指導老師 10/5 回覆「看定性」，本案定性為治理層，維持不做。RAG 已在過往專案（面試練習網站）做過，再做一次不會產生新的證明，也會擠壓專題時程 | 知識檢索接進來時：① embedding 與生成兩種呼叫都要經過 Gateway，同樣受身分、額度、計費、稽核、個資遮罩管理；② data drift：企業文件更新後檢索結果會變，要定期重跑測試集並比對；③ 測試集：為企業知識建一組固定問答當驗收基準。M3 的 20 題路由測試集是同一種做法，重跑時機為模型換版、單價變更、路由門檻調整。向量資料庫是其中一個元件，依資料量與成本另行選型 |

### 限制（誠實記錄）

- 時間是用字數估算的，**尚未計時試講**
- 版面只用 LibreOffice 轉成圖檔檢查過，尚未用 PowerPoint 桌面版確認字型與換行
- 五處畫面仍是示意（見上表）；主影片的「省下 X%」還沒有數字
- 影片尚未開始剪接；v1 只有骨架，不含逐字稿與動畫（定案 B）

**上傳（10/6 02:06）：** 推送前以 `git status -uall` 確認 `docs/slides/` 只有 `llm-gateway-slides-v1.pptx` 與 `narration-v1.md` 兩個檔，沒有 PowerPoint 的暫存檔（`~$` 開頭）與舊版本。`docs: add final presentation deck v1 and narration script`，推送結果 `7b4e1bc..8508164  main -> main`。由開發機本機 commit（不是從 GitHub 網頁上傳），所以不需要先 `git pull`。

**學到的：** 老師要大綱時沒有回應，改交實際的簡報才得到明確的方向（定位不能跑掉）。抽象的大綱很難引出具體的回饋。

**面試可用的說法：** 「我的簡報從第一版就跟著專題一起改：還沒做完的頁面標上狀態，每過一關就換成真的畫面。逐字稿先算字數估時間，確定 6 分鐘講得完才定頁數。」

---

## E85. 步驟 2：個資類別帶進稽核紀錄（2026-10-06 02:13～10-07 00:45）

**依據：** 決策書 8.2 M2「稽核表記錄『偵測到哪一類個資』，不記內容」、3.2 的 `audit` 表、4.2 資料層；對應驗收 S04。

**問題：** `mask()` 只回傳遮好的句子，不會告訴呼叫的人它遮了哪幾類。

**生活比喻：** 外帶店的師傅把餐裝盒後從窗口遞出餐盒。現在要多一張貼紙寫「內含：花生、海鮮」，問題是貼紙由誰寫、從哪裡遞出來。

### 定案 1：類別怎麼帶出來（10/6 12:00 本人決定採用 C）

| 選項 | 做法 | 比對邏輯幾份 | 既有 35 個測試 | 評估 |
|---|---|---|---|---|
| A | 改 `mask()`，一次回傳句子與類別 | 1 | 二十多個要改 | 結果一定一致，但會動到 E77～E83 剛驗收的東西 |
| B | `mask()` 不動，另寫一個函式重新比對 | 2 | 不用改 | 兩邊會對不上（見下） |
| **C（採用）** | 內部函式 `mask_and_detect()` 一次算出兩樣；`mask()` 只取句子，`detect_pii_types()` 只取類別 | 1 | 不用改 | 介面不變，舊測試變成重構的保護網；代價是多一層函式 |

**為什麼不選 B：** 既有的測試資料就能讓它出錯。`Mail 0912345678@example.com now` 經 `mask()` 會整段變成 `[EMAIL]`，手機規則沒機會碰到；B 的函式若拿原文逐類比對，會回報 `["EMAIL", "PHONE"]`，稽核就多記了一類沒遮過的手機。要修好就得照同樣順序重做一遍替換並加上 Luhn，等於把 `mask()` 抄一份。

**為什麼選 C 不選 A：** 兩者都只有一份邏輯，差別在改動面。重構過程實際示範了 A 的代價：`mask()` 一度回傳整包，20 個測試同時失敗（見挫折 1）。

**不採用的做法：** 用「遮好的句子裡有沒有 `[EMAIL]` 字樣」反推類別。使用者自己打出這幾個字就會誤判。

### 定案 2：類別的呈現

| 項目 | 定案 | 為什麼 |
|---|---|---|
| 欄位名稱 | `pii_types` | 短，看得出是「類別」不是內容 |
| 值的寫法 | `"TW_ID"`，不含中括號 | 中括號是給模型看的標籤樣式，稽核存的是資料 |
| 沒有個資 | 空清單 `[]`，欄位一定存在 | 「檢查過、沒找到」和「沒這個欄位」要分得出來 |
| 順序 | 固定為遮罩順序：`EMAIL`、`CARD`、`PHONE`、`TW_ID` | 照處理順序自然產生，不用另外排序 |
| 重複 | 同一類出現多次只記一次 | 記的是「哪幾類」，不是次數 |
| 失敗的請求 | `status: error` 那筆也要有 | 遮罩發生在呼叫模型之前，上游失敗時個資一樣進來過 |

### 定案 3：`main.py` 呼叫哪個函式

| 做法 | 評估 |
|---|---|
| **甲（採用）** `mask()` 那行不動，另外呼叫 `detect_pii_types(request.message)` | `main.py` 只用兩個窗口，內部函式不外露；代價是同一句話多處理一次 |
| 乙 改成直接呼叫 `mask_and_detect()`，一次接兩樣 | 只處理一次；但 `detect_pii_types()` 變成只有測試在用，`main.py` 直接碰內部函式 |

傳進去的是**原文**，不是 `masked`：遮好的句子裡已經沒有個資，拿它去偵測永遠得到空清單。

### 做法：分八小段，先寫測試、看它失敗，再寫功能

| 段 | 內容 | 結果 |
|---|---|---|
| 1 | 兩個單元測試（找到身分證字號、沒有個資回空清單） | `ImportError`，`1 error during collection` |
| 2 | 把 `mask()` 的內容搬進 `mask_and_detect()`，類別暫時寫死為 `[]` | `20 failed, 17 passed` → 修正後 `1 failed, 36 passed` |
| 3 | 每一步比較前後，有變就把類別加進清單 | `37 passed` |
| 4 | 補五個單元測試 | `42 passed`（一寫就通過） |
| 5 | 兩個破壞實驗 | `1 failed, 41 passed`、`7 failed, 35 passed`；還原後 `42 passed` |
| 6 | 兩個端到端測試 | `TypeError`（測試寫錯）→ 修正後 `KeyError: 'pii_types'`，`2 failed, 42 passed` |
| 7 | `main.py` 加匯入與 `pii_types` 欄位 | `44 passed` |
| 8 | 失敗請求的端到端測試與破壞實驗 | `45 passed`；破壞時 `1 failed, 44 passed` |

**先搬家、再加功能（第 2、3 段）：** 一次改一件事。搬完 35 個舊測試一個都沒改就全部通過，證明重構沒弄壞東西，才處理「怎麼算類別」。

### 怎麼知道某一步有沒有遮到東西：比較前後

句子變了，就代表這一類被遮了。以 `Mail amy@example.com or 0912345678` 走一遍：

| 步驟 | 處理前 → 處理後 | 有變嗎 | 清單 |
|---|---|---|---|
| 信箱 | `text` → `email_result` | 有 | `["EMAIL"]` |
| 信用卡 | `email_result` → `card_result` | 沒有 | `["EMAIL"]` |
| 手機 | `card_result` → `phone_result` | 有 | `["EMAIL", "PHONE"]` |
| 身分證 | `phone_result` → `result` | 沒有 | `["EMAIL", "PHONE"]` |

**生活比喻：** 快遞每過一個檢查站秤一次重；進站和出站重量不同，就知道這一站動過包裹。

這個做法同時滿足三項定案：順序固定（照四個步驟的先後加入）、同類只記一次（每一類只比較一次）、沒通過 Luhn 的數字不會被記（`replace_card_if_valid` 放回原文，前後相同）。使用者自己打的 `[EMAIL]` 字樣在處理前後都一樣，也不會被記。

**新語法：** 一個函式回傳兩樣東西（`return result, found_types`，稱為 tuple）；接的時候左邊寫兩個名字，不要的那個位置寫底線；`list.append()` 接在清單最後；清單用 `==` 比較時內容與順序都要相同。

**生活比喻（tuple）：** 點套餐，店員一次遞給你漢堡和發票，你兩手各接一樣；不要發票就不拿。

### 本人撰寫（`app/audit.py`）

```python
# 遮罩和類別由同一次處理算出來，兩邊才不會對不上（遮了沒記、記了沒遮）
def mask_and_detect(text: str) -> tuple[str, list[str]]:
    """Return the masked text together with the categories that were masked."""
    found_types = []
    email_result = re.sub(EMAIL_PATTERN, "[EMAIL]", text)
    if text != email_result:
        found_types.append("EMAIL")
    card_result = re.sub(CARD_PATTERN, replace_card_if_valid, email_result)
    if email_result != card_result:
        found_types.append("CARD")
    phone_result = re.sub(PHONE_PATTERN, "[PHONE]", card_result)
    if card_result != phone_result:
        found_types.append("PHONE")
    result = re.sub(TW_ID_PATTERN, "[TW_ID]", phone_result)
    if phone_result != result:
        found_types.append("TW_ID")
    return result, found_types


# 個資遮罩：內容會送出 AWS 到供應商那邊，個資要在離開前先換掉
def mask(text: str) -> str:
    """Replace personal data with a category label before the text leaves the gateway."""
    sentence_result, _ = mask_and_detect(text)
    return sentence_result


# 稽核只記「有哪幾類個資」，不記內容；類別來自實際遮罩的結果，不另外比對
def detect_pii_types(text: str) -> list[str]:
    """Return the categories of personal data found in the text, without the data itself."""
    _, list_result = mask_and_detect(text)
    return list_result
```

`app/main.py` 只改兩處：匯入名單加上 `detect_pii_types`；`record` 的前半段（成功或失敗都要記的欄位）加一行 `"pii_types": detect_pii_types(request.message)`。

### 測試（本人撰寫，共 10 個；測試數 35 → 45）

單元測試（`tests/test_audit.py`）：

| 測試 | 輸入 | 預期 | 在守什麼 |
|---|---|---|---|
| `…_finds_tw_id` | `My ID is A123456780 thanks` | `["TW_ID"]` | 該記的有記 |
| `…_returns_empty_list_without_personal_data` | `Say hi` | `[]` | 不該記的沒記 |
| `…_lists_all_types_in_fixed_order` | `ID A123456780 call 0912345678 pay 4111111111111111 mail amy@example.com` | `["EMAIL", "CARD", "PHONE", "TW_ID"]` | 輸入刻意倒著放，確認順序固定；同時確認四個名稱沒打錯 |
| `…_reports_each_type_once` | `Mail amy@example.com and bob@example.com` | `["EMAIL"]` | 同類只記一次 |
| `…_treats_phone_like_email_as_email_only` | `Mail 0912345678@example.com now` | `["EMAIL"]` | 否決選項 B 的那句話 |
| `…_ignores_number_failing_luhn` | `Order 4111111111111112 shipped` | `[]` | 沒遮的不能記 |
| `…_ignores_label_typed_by_user` | `Please write [EMAIL] here` | `[]` | 使用者自己打標籤不算 |

（測試名稱開頭皆為 `test_detect_pii_types`。）

端到端測試（`tests/test_chat.py`）：

| 測試 | 送出的 `message` | 檢查 |
|---|---|---|
| `test_chat_audit_records_pii_types` | `My ID is A123456780 call 0912345678` | `pii_types` 為 `["PHONE", "TW_ID"]`；稽核檔全文找不到身分證字號與手機 |
| `test_chat_audit_records_empty_pii_types_without_personal_data` | `Say hi` | `pii_types` 為 `[]` |
| `test_chat_error_audit_still_records_pii_types` | `My ID is A123456780 thanks`（假的 OpenAI 設為出錯） | `status` 為 `error`；`pii_types` 為 `["TW_ID"]`；稽核檔全文找不到身分證字號 |

### 破壞實驗（四次）

| # | 改了什麼 | 結果 | 判讀 |
|---|---|---|---|
| 1 | `"PHONE"` 打成 `"PHON"` | `1 failed, 41 passed`：`At index 2 diff: 'PHON' != 'PHONE'` | 名稱打錯一個字母就會被抓到。稽核用 `"PHONE"` 查詢時，打錯的紀錄會全部查不到，而且沒有錯誤訊息 |
| 2 | 信用卡那一步的 `!=` 寫成 `==` | `7 failed, 35 passed` | 沒有卡號的六句**多**記一個 `CARD`（`assert ['CARD'] == []`），有卡號的那句反而**少**記 |
| 3 | 把 `pii_types` 從 `record` 前半段搬到「成功區」 | `1 failed, 44 passed`：`KeyError: 'pii_types'` | 成功的請求照常，只有失敗的請求少一欄 |
| 4 | 摘要改成不遮罩（`request.message[:50]`） | `3 failed, 42 passed` | 見下方「更正」 |

**第 2、3 個實驗的共同點：** 改錯之後程式不會當掉，使用者端完全看不出來。第 3 個尤其如此：正常請求全部沒事，只有上游出錯的那些紀錄少一欄，要等到 OpenAI 出狀況之後有人去查稽核才會發現。與 E69「重構後稽核少了四個欄位、使用者端看不出來」同類。

**生活比喻（第 3 個）：** 餐廳把「過敏原」欄印在出餐單上，而不是點餐單上。順利出餐的都有記錄，只有廚房做失敗的那幾單沒有。

### 挫折 1：搬家後 20 個測試同時失敗

```
E       AssertionError: assert ('Contact me at [EMAIL] please', []) == 'Contact me at [EMAIL] please'
E       AssertionError: assert 2 == 50
20 failed, 17 passed
```

- **怎麼判讀：** 實際值外面有一層圓括號，裡面是「句子、空清單」。20 個失敗都是同一個形狀，所以是同一個原因。`assert 2 == 50` 也是：`len()` 量到的是「這一包有 2 樣」
- **原因：** `sentence_result = mask_and_detect(text)` 等號左邊只有一個名字，Python 把整包交給它。`mask_and_detect()` 本身是對的
- **解法（本人修正）：** 左邊改成接兩樣，`sentence_result, _ = …` 與 `_, list_result = …`
- **順帶修正：** `detect_pii_types` 的參數型別原本標成 `list[str]`，實際傳入的是一句話，改為 `str`。型別標註寫錯 Python 不會報錯，沒有測試會抓到，但讀的人會被誤導
- **學到的：** 回傳兩樣的函式，呼叫端要用兩個名字去接

### 挫折 2：端到端測試在送出請求前就失敗

```
>       client.post("/v1/chat", json={"My ID is A123456780 call 0912345678"})
E       TypeError: Object of type set is not JSON serializable
2 failed, 42 passed
```

- **怎麼讀很長的訊息：** 只看兩個地方。最下面 `E` 那行是真正的錯誤；往上找第一個落在自己檔案裡的 `>` 那行是出事的起點。中間 `.venv` 與 Python 安裝路徑的那一串是套件內部，可以跳過
- **原因：** 大括號有冒號是字典（`{"message": "Say hi"}`），沒有冒號是集合（`{"Say hi"}`）。JSON 沒有集合，轉換時就報錯，請求根本沒送出
- **為什麼要修到看見 `KeyError`：** `TypeError` 是測試自己寫錯造成的紅，不能當成「功能還沒做」的證據。修正後看到 `KeyError: 'pii_types'`，才是要的失敗：請求送到了、稽核寫了，只差這個欄位
- **新的失敗樣子：** `KeyError` 是跟字典要一個它沒有的欄位；程式停在「拿欄位」那一步，還沒走到比較。pytest 仍算成 `failed`

### 更正：三個檢查推送時沒有在把關（10/7 00:38 發現，00:45 修正）

第一次推送（`ad28caa`）的三個端到端測試裡，有三行寫成：

```python
assert "A123456780" not in record
```

- **原因：** `record` 是字典。對字典用 `in` 只看**欄位名稱**，不看內容；沒有任何欄位叫做 `A123456780`，所以這一行永遠通過
- **生活比喻：** 檢查表單有沒有洩漏電話，結果只看了「姓名、地址」這些欄位標題，沒看填了什麼
- **怎麼發現的：** Claude 撰寫本筆紀錄時對照已推送的程式才看到。測試當時是 `45 passed`，結果畫面看不出問題
- **影響：** 功能沒有壞，稽核檔裡確實沒有個資。壞的是保護：之後有人改壞時，這三行不會有反應；其中「失敗請求」那條路沒有其他測試在看

**修正與驗證（破壞實驗 4）：** 三處改為 `not in text`。把摘要暫時改成不遮罩後：

| 測試的寫法 | 結果 |
|---|---|
| 修正前（`not in record`） | `1 failed, 44 passed`，只有 E83 的舊測試抓到（Claude 在公開 repo 的副本上重現） |
| 修正後（`not in text`） | `3 failed, 42 passed`，新測試也抓到，包含失敗請求那一筆（本人在開發機執行） |

修正後、破壞時的失敗訊息：

```
E         'A123456780' is contained here:
E           "My ID is A123456780 thanks", "pii_types": ["TW_ID"], "status": "error", "error_type": "OpenAIError"}
E         ?           ++++++++++
```

**判讀：** 這筆紀錄的 `pii_types` 正確寫著 `["TW_ID"]`，旁邊的摘要卻留著完整的身分證字號。類別記對了不代表內容沒洩漏，兩件事要分開檢查。

**學到的：**
- 通過的測試不代表它在檢查你以為的東西。這三個測試是先看過失敗才通過的，但失敗的是 `pii_types` 那一行；同一個測試裡的其他斷言從頭到尾沒有失敗過
- 破壞實驗要對著**每一個斷言**想一次「它在什麼情況下會紅」，不是每個測試做一次就夠
- `in` 用在字串是找內容，用在字典是找欄位名稱

### 限制（誠實記錄）

- **`pii_types` 記的是「規則偵測到的」，不是「句子裡實際有的」。** E78～E81 列的漏網格式（全形數字、市話、外來人口統一證號等）會讓它顯示 `[]`，但句子裡其實有個資。空清單不能解讀成「這句話沒有個資」
- 同一句話在 `main.py` 被處理三次（`mask()`、`make_summary()`、`detect_pii_types()`）。用的是同一份邏輯所以結果一致，4000 字以內的成本可忽略，但確實是重複工作（定案 3 的代價）
- 單元測試第 4、5、7 個（同類記一次、像手機的信箱、使用者自己打標籤）沒有做破壞實驗：它們擋的是「整個做法被改寫成另一種」的情況，無法用改一行的方式弄壞
- 端到端測試只用了身分證字號與手機；信箱與信用卡的類別只有單元測試
- 類別欄位本身是中繼資料：看得出某筆請求含哪類個資，看不到內容。這是需求（8.2 M2），但持有稽核讀取權限的人仍可得知「誰在何時送過身分證字號」
- 步驟 9 換成 DynamoDB 時，`pii_types` 的型別要選能存空值的（預計用 List；Set 是否接受空集合，屆時查證官方文件）
- 只驗證寫入檔案的稽核紀錄；真實呼叫留到步驟 11 的驗收（S04）

### 面試可用的說法

- 「稽核要記這句話含哪幾類個資。我沒有另外寫一個偵測函式，因為遮罩有先後順序，像長得像手機的信箱只會被當成信箱遮掉，另外比對一次就會多記一類沒遮過的手機。所以遮罩和類別是同一次處理算出來的，對外仍是兩個各取所需的函式，原本三十幾個測試一行都不用改。」
- 「類別我放在成功和失敗都會寫的那一段，並且用一個測試守著。我試過把它搬到只有成功才會走到的地方，正常請求全部沒事，只有呼叫模型失敗的那些紀錄少一欄。這種錯使用者看不出來，只有測試擋得住。」
- 「我推上去的測試裡有三行其實沒有在檢查：我拿個資字串去對字典做 `in`，那只會比對欄位名稱，永遠通過。是寫紀錄時回頭讀程式才發現的。修正後我把摘要故意改成不遮罩，確認三個測試都會變紅才算數。從那之後，我做破壞實驗是對著每一個斷言想，不是每個測試做一次。」

---

**推送：**
- 程式（10/7 00:38）：`feat: record pii categories in the audit log`，`b33144c..ad28caa  main -> main`。commit 前以 `git status` 確認只有 `app/audit.py`、`app/main.py`、`tests/test_audit.py`、`tests/test_chat.py`
- 更正（10/7 00:45）：`test: check the audit file text for leaked personal data`，`ad28caa..53a4491  main -> main`，1 個檔、3 行。commit 前以 `git status` 確認只有 `tests/test_chat.py`，破壞實驗已完全還原

---

## E86. 步驟 3：`period_of()` 以台北時間切月（2026-10-07 01:05 定案；10:05～11:42 實作）

**依據：** 決策書 D2（`quotas` 的排序鍵 `period`，`YYYY-MM`，台北時間）、3.2「時區注意」（台北 10/1 00:30 = UTC 9/30 16:30，應歸入 10 月）、8.2 M2「`period` 以台北時間切月，寫成單一函式並加跨月邊界的 pytest」。

**問題：** 系統內的時間都用 UTC 記。台北比 UTC 快 8 小時，每個月 1 號的 00:00～07:59（台北）在 UTC 還是上個月的最後一天；直接取 UTC 的月份，這 8 小時的用量會記到上個月的額度。

**生活比喻：** 跨年夜台北已經倒數完，倫敦還在 12/31 下午。同一個瞬間，兩地的日曆不同頁；記帳前要先講好看誰的日曆。

### 定案（四項，10/7 01:05 本人決定）

| # | 決定 | 採用 | 不選的選項 | 為什麼 |
|---|---|---|---|---|
| 1 | 台北時間怎麼表示 | 固定偏移 `timezone(timedelta(hours=8))`，寫成具名常數 `TAIPEI_TZ` | 時區資料庫 `ZoneInfo("Asia/Taipei")` | 台灣沒有日光節約時間，兩者結果相同。時區資料庫在 Windows 要另外安裝 `tzdata`（多一個相依套件，要過 D35 的冷卻期），容器與 Lambda 有沒有時區資料也要各自確認；固定偏移全用 Python 內建，三個環境一定一致。代價：規則改變時要手動改程式 |
| 2 | 函式收什麼 | 收一個時間點 `period_of(moment)` | 函式自己取「現在」 | 跨月邊界一個月只出現一次；函式自己取時間，測試就無法重現邊界。呼叫端傳 `datetime.now(timezone.utc)` |
| 3 | 沒帶時區的時間 | 拒絕，丟 `ValueError` | 當成 UTC | 不知道是哪個時區就不該猜；與 D30「不知道多少錢不能當成不用錢」同一個想法 |
| 4 | 放哪個檔 | 新檔 `app/quota.py`、`tests/test_quota.py` | 放進 `app/audit.py` | 它屬於額度，不屬於稽核；步驟 7、8 的額度檢查與扣減也會放這裡 |

**升級門檻（定案 1）：** 系統要服務多個時區，或服務的地區有日光節約時間時，改用時區資料庫。

### 做法：分六小段，先寫測試、看它失敗，再寫功能

| 段 | 內容 | 結果 |
|---|---|---|
| 1 | 互動模式做出一個帶時區的時間點，看 `.year`、`.month` | — |
| 2 | 第一個測試（月中） | `ModuleNotFoundError: No module named 'app.quota'`，`1 error during collection` |
| 3 | 最小版函式：只把時間格式化成 `YYYY-MM` | `46 passed` |
| 4 | 四個邊界測試 → 加上換算台北時間 | `3 failed, 47 passed` → `50 passed` |
| 5 | 兩個破壞實驗 | `1 failed, 49 passed`、`4 failed, 46 passed`；還原後 `50 passed` |
| 6 | 沒帶時區的測試 → 加上拒絕 | `1 failed, 50 passed`（`DID NOT RAISE ValueError`）→ `51 passed` |

**新的失敗樣子（第 2 段）：** E81 是「檔案在、函式不在」（`ImportError: cannot import name`）；這次是「整個檔都不在」（`ModuleNotFoundError`）。兩者都停在收集階段，45 個舊測試一個都沒跑。

### 新觀念（一次一個）

| 觀念 | 白話 | 生活比喻 |
|---|---|---|
| `datetime(年, 月, 日, 時, 分, tzinfo=…)` | 一個時間點；`tzinfo` 那一格記時區 | 電影票：印著日期時間，還有一格「哪間影城」。少了那一格就不知道是哪一場 |
| `strftime("%Y-%m")` | 照樣板把時間印成文字；`%Y` 是四位數的年，`%m` 是補 0 的兩位數月 | 喜帖上印好「＿＿年＿＿月」，把日期填進空格 |
| `timedelta(hours=8)` | 一段時間的長度 | 票上的開演時間是時間點，「片長 2 小時」是長度 |
| `moment.astimezone(TAIPEI_TZ)` | 同一個瞬間，換一地的日曆來讀 | 跨年倒數那一刻，倫敦看到 12/31 16:00，台北看到 1/1 00:00 |
| `raise ValueError("…")` | 函式不交結果，直接報錯並停住 | 收銀機刷到讀不出來的條碼會拒收，不會自己猜一個價錢 |
| `with pytest.raises(ValueError):` | 測試預期區塊內會發生這種錯誤；沒發生才算失敗 | 消防演習按測試鈕：鈴有響才合格 |

**為什麼用 `%m`，不把 `.year` 和 `.month` 接起來：** `.month` 是數字，一月是 `1`，接起來變成 `2027-1`。`period` 是排序鍵，`2027-1` 與 `2027-10` 排在一起會亂；`%m` 會補 0。

**互動模式的確認（第 4 段）：**

```
>>> moment = datetime(2026, 9, 30, 16, 30, tzinfo=timezone.utc)
>>> taipei_moment = moment.astimezone(TAIPEI)
>>> taipei_moment
datetime.datetime(2026, 10, 1, 0, 30, tzinfo=datetime.timezone(datetime.timedelta(seconds=28800)))
>>> taipei_moment.month
10
>>> taipei_moment == moment
True
```

兩個值印出來的日期不同，但比較結果是 `True`：換算沒有改變時間點，只改變用哪一地的日曆讀它。

### 本人撰寫（`app/quota.py`）

```python
from datetime import datetime, timezone, timedelta

# 台北時間固定比 UTC 快 8 小時（台灣沒有日光節約時間）；用固定偏移就不必另外安裝時區資料
TAIPEI_TZ = timezone(timedelta(hours=8))


# 額度按台北時間的月初切；系統內的時間是 UTC，直接取月份會把每月 1 號凌晨算上個月
def period_of(moment: datetime) -> str:
    """Return the quota period (YYYY-MM, Taipei time) that the moment belongs to."""
    if moment.tzinfo is None:
        raise ValueError("Moment must include a timezone")
    taipei_moment = moment.astimezone(TAIPEI_TZ)
    result = taipei_moment.strftime("%Y-%m")
    return result
```

### 測試（本人撰寫，`tests/test_quota.py`，6 個；測試數 45 → 51）

| 測試 | 輸入（UTC） | 台北時間 | 預期 | 在守什麼 |
|---|---|---|---|---|
| `…_returns_year_and_month` | 2026-10-15 03:00 | 10/15 11:00 | `2026-10` | 回傳的格式 |
| `…_keeps_last_minute_of_month` | 2026-09-30 15:59 | 9/30 23:59 | `2026-09` | 換算不能多推 |
| `…_moves_first_minute_to_new_month` | 2026-09-30 16:00 | 10/1 00:00 | `2026-10` | 換算不能少推 |
| `…_matches_decision_book_example` | 2026-09-30 16:30 | 10/1 00:30 | `2026-10` | 決策書 3.2 的例子 |
| `…_moves_new_year_to_next_year` | 2026-12-31 16:00 | 2027/1/1 00:00 | `2027-01` | 年份跟著進位、月份補 0 |
| `…_rejects_time_without_timezone` | 2026-10-15 03:00（沒帶時區） | — | 丟 `ValueError` | 不猜時區 |

（測試名稱開頭皆為 `test_period_of`。）

### 每個斷言都看過它失敗

| # | 程式的狀態 | 結果 | 紅的是哪幾個 |
|---|---|---|---|
| 1 | 還沒換算，直接用 UTC 的年月（第 4 段寫功能前） | `3 failed, 47 passed` | 16:00、16:30、跨年 |
| 2 | 破壞：`hours=8` 改成 `hours=9` | `1 failed, 49 passed` | 15:59 |
| 3 | 破壞：樣板的 `%m` 改成 `%d` | `4 failed, 46 passed` | 月中、15:59、16:00、16:30 |
| 4 | 還沒加拒絕（第 6 段寫功能前） | `1 failed, 50 passed` | 沒帶時區 |

第 1 項的失敗訊息：

```
E       AssertionError: assert '2026-09' == '2026-10'
E       AssertionError: assert '2026-12' == '2027-01'
```

**判讀：** 台北 10/1 00:00 的請求被記到 9 月的額度；跨年那筆的年與月都錯。

第 2 項的失敗訊息：

```
E       AssertionError: assert '2026-10' == '2026-09'
```

**判讀：** 15:59 那個測試一寫就通過，多推一小時才看到它變紅。它守「不能多推」，另外三個邊界守「不能少推」，兩邊夾住才確定偏移剛好是 8 小時。

第 3 項的失敗訊息：

```
FAILED …::test_period_of_returns_year_and_month - AssertionError: assert '2026-15' == '2026-10'
FAILED …::test_period_of_keeps_last_minute_of_month - AssertionError: assert '2026-30' == '2026-09'
FAILED …::test_period_of_moves_first_minute_to_new_month - AssertionError: assert '2026-01' == '2026-10'
FAILED …::test_period_of_matches_decision_book_example - AssertionError: assert '2026-01' == '2026-10'
```

**判讀：** 「日」被印在「月」的位置，10/1 的用量會被記成 `2026-01`。**跨年那個測試沒有變紅：** 它的台北時間是 1 月 1 日，月與日都是 `01`，印錯欄位也得到 `2027-01`。

第 4 項的失敗訊息：

```
E       Failed: DID NOT RAISE ValueError
```

**判讀：** Python 遇到沒帶時區的時間不會報錯，而是當成「這台機器的當地時間」。開發機設的是台北時間、雲端的機器通常是 UTC，同一行程式、同一個輸入，在月初那 8 小時會算出不同的月份，而且沒有任何錯誤訊息。

**還原確認：** 兩個破壞實驗改回後 `50 passed`；`git status` 只有 `app/quota.py`、`tests/test_quota.py` 兩個未追蹤的新檔。

**學到的：**
- 測試資料的月與日相同時，分不出程式用的是月還是日。與 E81「對任何輸入都回 `False`，錯的卡號測試碰巧通過」同類；這次由另外四個測試的日期（15 日、30 日、10 月 1 日）夾住
- 邊界要從兩邊測：只測「該換月的有換」，偏移寫成 9 小時也會通過

### 限制（誠實記錄）

- **`period_of()` 還沒有被任何地方呼叫。** 它在步驟 7（額度檢查）與步驟 8（扣減）才接進 `main.py`；目前只有單元測試
- 固定偏移只適用台北時間；規則改變或要支援其他時區時必須改程式（定案 1 的代價）
- 邊界只測了 9 月 → 10 月與跨年兩處；2 月底、閏年沒有各自的測試（換算由 `datetime` 處理，機制相同）
- 傳入的時間都是 UTC；傳入其他時區的時間（例如本來就是台北時間）沒有測試
- 「沒帶時區」只以 `tzinfo is None` 判斷
- 跨年的測試資料月與日相同（見上）；沒有改資料，靠其他測試涵蓋
- 第一個破壞方向（拿掉換算）沒有另外做一次，以第 4 段寫功能前的失敗紀錄代替

### 面試可用的說法

- 「額度按台北時間切月，但系統內的時間是 UTC，每個月 1 號的前 8 小時最容易記到上個月。我把換算寫成單一函式，函式收時間點、不自己取現在時間，所以測試可以直接給 9/30 15:59 和 16:00 這兩個相鄰的時間點。」
- 「時區我用固定的 +8，沒有用時區資料庫。台灣沒有日光節約時間，兩者結果相同；固定偏移不需要多裝套件，本機、容器、Lambda 一定一致。如果系統要服務有日光節約的地區，就該換成時區資料庫，這我寫在升級門檻裡。」
- 「沒帶時區的時間我直接拒絕。Python 預設會把它當成機器的當地時間，開發機是台北、雲端是 UTC，同一個輸入會算出不同的月份而且不報錯。」
- 「我把偏移故意改成 9 小時，確認『月底最後一分鐘』那個測試會紅；又把月份的格式故意換成日，結果跨年那個測試沒紅，因為 1 月 1 日的月和日一樣。挑測試資料時我現在會避開這種巧合。」

---

**推送（10/7 11:56）：** `feat: add period_of to split quota months in Taipei time`（`07457ec`）、`docs: record M2 step 3 evidence`（`249921d`），推送結果 `3badc2e..249921d  main -> main`。commit 前以 `git status` 確認只有 `app/quota.py`、`tests/test_quota.py`、`docs/evidence/m2-evidence-log.md`；以 `git log -3 --format="%h %ae %s"` 確認作者信箱為 GitHub noreply 信箱（D21）。

---

## E87. 步驟 4：最小成本函式 `cost_micro_usd()`（2026-10-07 11:59 定案；13:32～14:55 實作）

**依據：** 決策書 D1（額度以 micro-USD 整數儲存）、D30（單價放 repo；沒有單價的模型一律拒絕；無條件進位成 micro-USD 整數）、E22（13 / 11 個 token = $0.0000068）、本檔「M2 步驟規劃」的缺口（成本換算排在 M3，但 M2 扣額度就需要金額）。

**範圍：** M2 只做 `gpt-6-luna` 的最小版。完整單價設定檔、路由、Gateway 遇到沒有單價時回什麼給使用者，仍屬 M3。

**生活比喻：** 計程車跳表。里程乘單價算出車資，不足一塊的零頭一律進位。

### 定案（五項，10/7 11:59 本人決定）

| # | 決定 | 採用 | 不選的選項 | 為什麼 |
|---|---|---|---|---|
| 1 | 放哪個檔 | 新檔 `app/pricing.py`、`tests/test_pricing.py` | 放進 `app/quota.py` | 算價錢與管額度是兩件事；M3 的完整單價表與路由會接在這裡 |
| 2 | 單價寫在哪 | `pricing.py` 內的字典常數 `PRICES` | 現在就做獨立設定檔（JSON 或 TOML） | D30 的重點是單價在 repo 裡、改價要經過版本紀錄、不從網路下載，字典常數做得到。設定檔留到 M3 與路由規則一起做。代價：M3 要搬一次 |
| 3 | 單價用什麼數字存 | 整數：每一百萬個 token 多少 micro-USD（Luna 輸入 `100_000`、輸出 `500_000`） | 小數 `0.10`、`0.50` | 小數有誤差（E25：6.8 被存成 6.799999999999999）；全程整數就不會發生 |
| 4 | 進位幾次 | 輸入與輸出的金額先加總，最後進位一次（1.3 + 5.5 = 6.8 → 7） | 輸入、輸出各自進位再相加（2 + 6 = 8） | 各自進位每次最多多收 1 micro-USD，也對不上 D30 的 7 |
| 5 | 沒有單價的模型 | 丟 `ValueError` | 當成 0 元 | D30：「不知道多少錢」不能當成「不用錢」（E23 的失敗模式） |

**函式：** `cost_micro_usd(model, input_tokens, output_tokens)`，回傳整數。思考 token 不另外傳入（見限制）。

### 做法：分五小段，先寫測試、看它失敗，再寫功能

| 段 | 內容 | 結果 |
|---|---|---|
| 1 | 第一個測試（兩百萬 / 一百萬 → 700,000） | `ModuleNotFoundError: No module named 'app.pricing'`，`1 error during collection` |
| 2 | 單價字典與最小版函式（先乘完加完，最後整數除法） | `52 passed` |
| 3 | 13 / 11 → 7 的測試 → 加上進位 | `1 failed, 52 passed`（`assert 6 == 7`）→ `53 passed` |
| 4 | 沒有單價的模型的測試 → 加上拒絕 | `1 failed, 53 passed`（`KeyError: 'gpt-6-astra'`）→ `54 passed` |
| 5 | 補極小用量的測試；三個破壞實驗 | `55 passed`；破壞結果見下 |

### 幾個設計上的重點

**測試資料的輸入與輸出數量故意不同。** 兩邊都用一百萬時，程式把兩個單價拿反，答案一樣是 600,000，測試照樣通過。這是 E86「跨年測試的月與日相同」學到的事，當天就用上。

**先乘完加完，最後只除一次。** 先除的話，`13 × 100_000 ÷ 1_000_000` 會先出現 1.3 這種零頭，整數就守不住。

**進位用餘數判斷，不用新語法。** `//` 取商的整數部分，`%` 取餘數；餘數不是 0 代表有零頭，就多收 1。

| 例子 | `total` | `total // MILLION` | `total % MILLION` | 結果 |
|---|---|---|---|---|
| 13 / 11 | 6,800,000 | 6 | 800,000 | 6 + 1 = 7 |
| 兩百萬 / 一百萬 | 700,000,000,000 | 700,000 | 0 | 700,000 |

**生活比喻（進位）：** 遊覽車一台坐 40 人。81 個人，剩下的 1 個人還是要再派一台；剛好 80 人就不用多派。

**沒有單價的模型：原本就會報錯，為什麼還要改。** 寫功能前，查字典那行已經會丟 `KeyError`。仍然加上明確的檢查，原因有二：① 原本是碰巧擋下的，哪天有人把查字典改成「查不到就給 0」，沒有單價的模型就變成免費，而測試會在那時變紅；② `KeyError: 'gpt-6-astra'` 只說字典沒有這個欄位，看日誌的人要的是「這個模型沒有設定單價」。

**生活比喻：** 自動販賣機按了沒有貨的按鈕，機器卡住也算沒有出貨，但應該亮「此商品未販售」的燈。

**新語法：** 字典裡再放字典（`PRICES["gpt-6-luna"]["input"]`，像飲料店價目表先找品項、再找杯型）；數字裡的底線（`1_000_000`，只是給人看的千分位）；`//` 整數除法；`not in`；`f"…{model}"`（把變數的值填進字串）。

### 本人撰寫（`app/pricing.py`）

```python
# 一百萬：單價是以「每一百萬個 token」報價的
MILLION = 1_000_000

# 單價寫在 repo 裡，改價要經過版本紀錄；不從網路下載價格表
# 單位：每一百萬個 token 多少 micro-USD（Luna 輸入 $0.10 → 100_000，輸出 $0.50 → 500_000）
PRICES = {
    "gpt-6-luna": {"input": 100_000, "output": 500_000},
}


# 金額全程用整數算，避免小數誤差；額度就是靠這個數字扣的
def cost_micro_usd(model: str, input_tokens: int, output_tokens: int) -> int:
    """Return the cost of one call in micro-USD, rounded up to a whole number."""
    if model not in PRICES:
        raise ValueError(f"No price configured for model: {model}")
    price = PRICES[model]
    total = input_tokens * price["input"] + output_tokens * price["output"]
    result = total // MILLION
    if total % MILLION != 0:
        result = result + 1
    return result
```

### 測試（本人撰寫，`tests/test_pricing.py`，4 個；測試數 51 → 55）

| 測試 | 輸入 | 預期 | 在守什麼 |
|---|---|---|---|
| `test_cost_uses_input_and_output_prices` | Luna，2,000,000 / 1,000,000 | `700_000` | 兩個單價各用在對的地方；沒有零頭時不能多收 |
| `test_cost_rounds_up_to_whole_micro_usd` | Luna，13 / 11 | `7` | D30 的例子：有零頭要進位 |
| `test_cost_rejects_model_without_price` | `gpt-6-astra`，13 / 11 | 丟 `ValueError` | 沒有單價不能當成 0 元 |
| `test_cost_charges_at_least_one_for_tiny_usage` | Luna，1 / 0 | `1` | 0.1 micro-USD 也要收 1 |

### 每個斷言都看過它失敗

| # | 程式的狀態 | 結果 | 失敗訊息 |
|---|---|---|---|
| 1 | 還沒進位（第 3 段寫功能前） | `1 failed, 52 passed` | `assert 6 == 7` |
| 2 | 還沒加拒絕（第 4 段寫功能前） | `1 failed, 53 passed` | `KeyError: 'gpt-6-astra'` |
| 3 | 破壞 A：兩個單價對調 | `2 failed, 53 passed` | `assert 1100000 == 700000`、`assert 8 == 7` |
| 4 | 破壞 B：`!= 0` 改成 `>= 0`（不管有沒有零頭都多收 1） | `1 failed, 54 passed` | `assert 700001 == 700000` |
| 5 | 破壞 C：`result + 1` 改成 `result + 0`（忘了進位） | `2 failed, 53 passed` | `assert 6 == 7`、`assert 0 == 1` |

**判讀：**
- 第 3 項：輸入與輸出的 token 數不同，拿反才看得出來。極小用量那個測試沒有變紅：只有 1 個 token 時，用哪個單價都不到 1 micro-USD，進位後都是 1；它守的是進位，不是單價
- 第 4 項：第一個測試同時守著「沒有零頭不能多收」；它與 13 / 11 那個測試從兩邊夾住進位的條件
- 第 5 項：`assert 0 == 1` 就是「極短的請求免費」的樣子。不進位時，alice 的 US$0.001 額度擋不住一直送極短請求的人

**還原確認：** 每個實驗做完立刻改回；最後 `55 passed`，`git status` 只有 `app/pricing.py`、`tests/test_pricing.py` 兩個未追蹤的新檔。

### 挫折 1：測試檔名打錯

測試檔一開始存成 `tests/test_princing.py`。pytest 只看檔名是否以 `test_` 開頭，所以照常執行，沒有任何錯誤；是從輸出的 `ERROR collecting tests/test_princing.py` 那行看出來的。commit 前以 `ren tests\test_princing.py test_pricing.py` 改正。

- **學到的：** 檔名打錯不會讓測試失敗；公開 repo 的檔名與 commit 訊息一樣，推上去之前要讀一遍

### 挫折 2：破壞實驗 A 第一次做的不是原本要做的實驗

第一次對調單價時，把 `output` 打成 `ouput`：

```
FAILED tests/test_pricing.py::test_cost_uses_input_and_output_prices - KeyError: 'ouput'
FAILED tests/test_pricing.py::test_cost_rounds_up_to_whole_micro_usd - KeyError: 'ouput'
FAILED tests/test_pricing.py::test_cost_charges_at_least_one_for_tiny_usage - KeyError: 'ouput'
3 failed, 52 passed
```

- **怎麼判讀：** 三個測試都紅，但訊息是 `KeyError`，不是金額不符。紅的原因是「字典沒有這個欄位」，不是「單價拿反」，所以還沒有驗證到要驗的東西
- **解法：** 重做一次，得到上表第 3 項的 `2 failed`
- **附帶的觀察：** 欄位名稱打錯，Python 當場報錯、三個測試全紅，不會安靜地算出錯的金額。E85 的 `"PHON"` 是值打錯，程式照跑；這次是欄位名打錯，程式直接停
- **學到的：** 破壞實驗變紅之後要讀失敗訊息，確認是為了預期的原因而紅。與 E85 挫折 2（`TypeError` 是測試自己寫錯造成的紅，不能當成功能還沒做的證據）同類

### 限制（誠實記錄）

- **`cost_micro_usd()` 還沒有被任何地方呼叫。** 步驟 8（同步扣減）才接進 `main.py`；目前只有單元測試
- **思考 token 的算法尚未查證。** 函式只收輸入與輸出兩個數字，前提是「回應的輸出 token 數已包含思考 token」（思考 token 以輸出單價計費，D28）。這個前提沒有對照 OpenAI 官方文件與 `app/providers/openai_client.py`，步驟 8 接線時確認，否則可能漏算或重複計算。`gpt-6-luna` 設為 `reasoning_effort: none`，實測思考 token 為 0（E22），所以 M2 不受影響
- 只有 `gpt-6-luna` 的單價；`gpt-6-sol` 在 M3 加入
- 單價是手動抄進程式的，OpenAI 改價時不會自動更新，也沒有檢查機制；與供應商帳單對帳排在 M6（決策書 12.5）
- 沒有單價時丟的是通用的 `ValueError`。M3 要讓 Gateway 針對這種情況回應時，可能需要專用的錯誤類型才能與其他 `ValueError` 區分
- token 數是負數、或不是整數時的行為沒有定義，也沒有測試
- 0 個 token（0 / 0）沒有測試
- 單價寫成字典常數而不是設定檔，與 D30「放 repo 設定檔」的字面不完全相同；M3 搬到設定檔（定案 2 的代價）

### 面試可用的說法

- 「成本我全程用整數算：單價存成『每百萬 token 多少 micro-USD』，先乘完加完，最後才除一次。拆解 LiteLLM 時我看過它用浮點數把 6.8 存成 6.799999，所以我不讓小數出現在算式裡。」
- 「零頭一律進位。我有一個測試是只送 1 個 token，成本 0.1 micro-USD，要收 1。不進位的話它是 0 元，額度很小的使用者就能用極短的請求無限次呼叫。」
- 「沒有設定單價的模型，函式直接拒絕。其實不加檢查，查字典那行本來就會報錯；但那是碰巧擋下的，哪天有人把它改成查不到就給 0，沒單價的模型就變成免費。所以我寫成明確的檢查，並用測試鎖住。」
- 「我做破壞實驗時有一次打錯字，三個測試全紅，但訊息是欄位不存在，不是金額算錯。那次的紅不能算數，我重做了一次。變紅之後我會讀訊息，確認它是為了我預期的原因而紅。」

---

## E88. 步驟 7 的純邏輯：超額回應定案、`is_over_quota()`、`seconds_until_next_period()`（2026-10-07 15:05 定案；15:05～18:26 實作）

**依據：** 決策書 2.2 流程圖 [3]（超額回 429、讀不到回 503）、8.2 M2（超額回 429、fail-closed、「額度 0」邊界、API Key 錯誤只回「驗證失敗」）、10.3 第 9 點與 12.5「超額回應的狀態碼與重試語意」（M2 定案）、7.10（同步扣減允許小幅超用）、D37（失敗的請求也要寫稽核）；E17、E21（LiteLLM 與 OpenAI 的超額都回 429）。

**範圍：** 步驟 7 裡不需要資料庫的部分。兩個函式都還沒有接進 `main.py`；讀額度、回 429／503、寫稽核的接線在步驟 5（DynamoDB Local）之後做。

**生活比喻：** 停車場滿位時，入口的看板要做兩件事：擋下車子（`is_over_quota`），並且寫出「下一個空位預計幾分鐘後」（`seconds_until_next_period`）。

### 定案（五項，10/7 15:05 本人決定）

已推送的 `main.py` 目前唯一的錯誤回應是 502，格式是 `{"detail": "Upstream model error"}`。

| # | 決定 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 1 | 超額的狀態碼 | **429** | 402（非標準用法，使用者也無法用「付費」解決）、403（與權限問題混淆）。429 與決策書流程圖、`s02-quota-429.png`、LiteLLM 與 OpenAI 的做法一致（E17、E21）。429 會讓客戶端 SDK 自動重試，但額度檢查排在呼叫模型之前，重試碰不到 OpenAI，不會多花錢 |
| 2 | 回應內容 | 固定字串 `{"detail": "Monthly quota exceeded"}`，與 502 同格式 | 結構化（另帶錯誤類型代碼）：會讓 502 與 429 的格式不一致。本 Gateway 的 429 只有一種原因（不做限速；供應商限流依 D10 回 503），狀態碼就夠分辨 |
| 3 | `Retry-After` | **附上**，值是距離台北時間下個月 1 號 00:00 的秒數（整數，不足一秒進位） | 不附：客戶端不知道額度何時恢復 |
| 4 | 被擋下的請求 | 寫稽核，`status` 為 `quota_exceeded`，沒有模型與 token 欄位，前半段（含 `pii_types`）照記 | 不寫：事後查不到誰在額度用完後還一直送請求。與 D37 同一個想法。**API Key 驗證失敗的請求不寫**：沒有身分可記，也避免被假 Key 灌爆稽核表 |
| 5 | 何時算超額 | 已用 **≥** 額度就擋 | `>`：額度 0 的人還能呼叫一次（E17 的邊界） |

**照決策書、不另外定案的兩項：** 額度資料讀不到回 **503** `{"detail": "Quota service unavailable"}`（fail-closed，S03）；API Key 錯誤回 **401** `{"detail": "Authentication failed"}`，不透露是不存在還是已停用。

### 第一部分：`is_over_quota()`

**本人撰寫（`app/quota.py`）：**

```python
# 額度剛好用完就擋；額度 0 代表一次都不能用，不是沒有上限
def is_over_quota(limit_micro_usd: int, used_micro_usd: int) -> bool:
    """Return True when the user has used up the monthly quota."""
    if used_micro_usd >= limit_micro_usd:
        return True
    return False
```

**測試（本人撰寫，`tests/test_quota.py`，4 個；測試數 55 → 59）：**

| 測試（開頭皆為 `test_is_over_quota`） | 檢查 | 在守什麼 |
|---|---|---|
| `…_allows_usage_below_limit` | `is_over_quota(1000, 999) is False` | 還沒用完就放行；兩個值差 1，參數拿反時答案不同 |
| `…_blocks_usage_equal_to_limit` | `is_over_quota(1000, 1000) is True` | 剛好用完要擋 |
| `…_blocks_usage_above_limit` | `is_over_quota(1000, 1001) is True` | 超過要擋 |
| `…_treats_zero_limit_as_strict` | `is_over_quota(0, 0) is True` | 額度 0 是嚴格上限（E17） |

**先寫測試：** `ImportError: cannot import name 'is_over_quota' from 'app.quota'`，`1 error during collection`。寫完 `59 passed`，一次全綠，所以做破壞實驗：

| # | 改了什麼 | 結果 | 紅的是哪幾個 |
|---|---|---|---|
| A | `>=` 改成 `>` | `2 failed, 57 passed` | 等於額度、額度 0（`assert False is True`） |
| B | 兩個變數對調 | `2 failed, 57 passed` | 低於額度（`assert True is False`）、超過額度（`assert False is True`） |

兩個實驗合起來，四個斷言都看過失敗；還原後 `59 passed`。

**判讀：** 實驗 A 的「額度 0」那一個，就是 E17 測過的邊界：寫成 `>` 時，額度 0 的人已用 0，`0 > 0` 不成立，會被放行一次。

### 第二部分：未完成的函式先推「空殼加跳過」

`is_over_quota` 完成時，`seconds_until_next_period` 的 5 個測試已經寫好，函式還沒寫。這時要推送，有三種做法：

| 做法 | 評估 |
|---|---|
| 測試照推、函式不存在 | `main` 變紅（`ImportError`，整個測試檔跑不起來） |
| 先把 5 個測試刪掉，之後再加回來 | `main` 是綠的，但測試離開了版本紀錄，要靠人記得補回 |
| **（採用，本人提出）函式寫成空殼 `raise NotImplementedError(…)`，5 個測試掛 `@pytest.mark.skip(reason="function not written yet")`，一起推** | `main` 是綠的，測試跟著 Git 走；結果列會顯示 `5 skipped`，看得出有東西還沒做 |

推送內容：`8184c53`（`feat: add is_over_quota and a stub for seconds_until_next_period`，10/7 16:57），`59 passed, 5 skipped`。

**這個做法的風險與對策：** 跳過的測試不會提醒自己還在跳過；忘了撕標記，函式寫錯也是全綠。所以接著做的第一件事是撕掉 5 個標記、先看到紅（17:58）：

```
FAILED tests/test_quota.py::test_seconds_until_next_period_counts_last_minute - NotImplementedError: seconds_until_next_period is not written yet
FAILED tests/test_quota.py::test_seconds_until_next_period_covers_whole_month_at_start - NotImplementedError: seconds_until_next_period is not written yet
FAILED tests/test_quota.py::test_seconds_until_next_period_crosses_year - NotImplementedError: seconds_until_next_period is not written yet
FAILED tests/test_quota.py::test_seconds_until_next_period_rounds_up_partial_second - NotImplementedError: seconds_until_next_period is not written yet
FAILED tests/test_quota.py::test_seconds_until_next_period_rejects_time_without_timezone - NotImplementedError: seconds_until_next_period is not written yet
5 failed, 59 passed
```

第五個等的是 `ValueError`，拿到 `NotImplementedError` 一樣算失敗。

**生活比喻：** 煙霧偵測器貼著「施工中暫停」的貼紙。裝潢完第一件事是撕貼紙、按測試鈕確認會叫，再做別的。

### 第三部分：`seconds_until_next_period()`

**做法（五步），以 UTC 10/31 15:59 走一遍：**

| 步 | 做什麼 | 這個例子的值 |
|---|---|---|
| ① | 沒帶時區就拒絕 | 有帶 UTC，通過 |
| ② | 換成台北時間 | 台北 10/31 23:59 |
| ③ | 算出下個月是哪年哪月 | 不是 12 月 → 2026 年、11 月 |
| ④ | 做出下個月 1 號 00:00 | 台北 2026-11-01 00:00 |
| ⑤ | 相減、換成秒、進位成整數 | `60.0` → `60` |

**為什麼日固定是 1：** 額度在每個月 1 號重置，與今天是幾號無關。`period_of()` 回的是 `YYYY-MM`，沒有日，所以下一個 period 一定從下個月 1 號 00:00 開始。**生活比喻：** 手機流量每月 1 號重置；10/15 用完，恢復的時間是 11/1，不是 11/15。

**為什麼進位、不捨去：** 差 0.5 秒時回 `0`，等於告訴客戶端「現在就能重試」，但額度還沒恢復。

**為什麼這裡可以出現小數：** `total_seconds()` 回的是小數，但只用一次就進位成整數，一個月最多兩百多萬秒，不會像金額那樣累加放大誤差（對照 E87 的全程整數）。

**新語法：** `import math` 與 `math.ceil()`（無條件進位到整數）；兩個時間相減得到 `timedelta`，`.total_seconds()` 換成秒。

**本人撰寫（`app/quota.py`）：**

```python
# Retry-After 的值：告訴被擋下的客戶端，額度什麼時候恢復
def seconds_until_next_period(moment: datetime) -> int:
    """Return whole seconds from the moment until the next quota period starts."""
    if moment.tzinfo is None:
        raise ValueError("Moment must include a timezone")
    taipei_moment = moment.astimezone(TAIPEI_TZ)
    if taipei_moment.month == 12:
        next_year = taipei_moment.year + 1
        next_month = 1
    else:
        next_year = taipei_moment.year
        next_month = taipei_moment.month + 1
    next_start = datetime(next_year, next_month, 1, tzinfo=TAIPEI_TZ)
    diff = next_start - taipei_moment
    result = math.ceil(diff.total_seconds())
    return result
```

**測試（本人撰寫，`tests/test_quota.py`，5 個；測試數 59 → 64）：**

| 測試（開頭皆為 `test_seconds_until_next_period`） | 輸入（UTC） | 台北時間 | 預期 | 在守什麼 |
|---|---|---|---|---|
| `…_counts_last_minute` | 2026-10-31 15:59 | 10/31 23:59 | `60` | 基本的算法；日不能寫錯 |
| `…_covers_whole_month_at_start` | 2026-09-30 16:00 | 10/1 00:00 | `2_678_400`（十月 31 天） | 剛換月要等一整個月，不能回 0；**唯一擋得住「沒換算台北時間」的測試** |
| `…_crosses_year` | 2026-12-31 15:00 | 12/31 23:00 | `3600` | 十二月的下個月是明年一月 |
| `…_rounds_up_partial_second` | 2026-10-31 15:59:59.5 | 10/31 23:59:59.5 | `1` | 不足一秒要進位 |
| `…_rejects_time_without_timezone` | 2026-10-15 03:00（沒帶時區） | — | 丟 `ValueError` | 不猜時區 |

### 挫折：第一版四處錯誤，測試一次只會指出走得到的那一個

第一版（18:14）：

```python
    if taipei_moment.month == 12:
        next_year = taipei_moment.year + 1
        next_month = taipei_moment.month + 1
    else:
        next_month = taipei_moment.month + 1
    next_start = datetime(next_year, next_month, taipei_moment.day, tzinfo=TAIPEI_TZ)
    diff = next_start - taipei_moment
    result = math.ceil(diff.total_seconds)
```

結果 `4 failed, 60 passed`（沒帶時區那個已通過，①② 是對的）：

```
>       next_start = datetime(next_year, next_month, taipei_moment.day, tzinfo=TAIPEI_TZ)
                              ^^^^^^^^^
E       UnboundLocalError: cannot access local variable 'next_year' where it is not associated with a value

E       ValueError: month must be in 1..12
```

| # | 錯誤 | 訊息 | 原因 |
|---|---|---|---|
| 1 | `else` 沒有給 `next_year` | `UnboundLocalError`（三個非十二月的測試） | `if / else` 兩條路要把同樣的變數都填齊；走 `else` 的請求到下一行時 `next_year` 沒有值 |
| 2 | 十二月寫成月加 1 | `ValueError: month must be in 1..12`（跨年那個） | 12 + 1 = 13 月 |
| 3 | 日寫成 `taipei_moment.day` | 未實測 | 算出的是「下個月的同一天」，不是「下個月 1 號」；10/31 會去做不存在的 11/31 |
| 4 | `total_seconds` 少了 `()` | 未實測 | 拿到的是函式本身，不是它算出的秒數 |

- **怎麼讀 `UnboundLocalError`：** 新的錯誤類型。`^^^^^^^^^` 指著 `next_year`，意思是要用這個名字，但它在這條路上還沒被放過值
- **生活比喻：** 表格有兩條填寫路線。走 A 路線的人填了「年」和「月」，走 B 路線的人只填了「月」；櫃檯要看「年」那格時，B 路線的人交不出來
- **四個失敗都停在同一行：** 程式遇到第一個錯就停，後面的第 3、4 個錯誤被擋在後面看不到。修好前兩個之後才會輪到它們
- **結果（18:20）：** 四處一起修正，`64 passed`
- **學到的：** 失敗訊息只講「最先撞到的那一個」；全部測試都停在同一行時，那一行之後的程式還沒有被任何測試走到

### 每個斷言都看過它失敗（五個破壞實驗，18:26）

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| 1 | 拿掉換算（`taipei_moment = moment`） | `1 failed, 63 passed`：剛換月 | `assert 0 == 2678400` |
| 2 | `math.ceil` 換成 `int` | `1 failed, 63 passed`：半秒 | `assert 0 == 1` |
| 3 | 十二月的分支改成與 `else` 相同 | `1 failed, 63 passed`：跨年 | `ValueError: month must be in 1..12` |
| 4 | 日的 `1` 改成 `2` | `4 failed, 60 passed`：前四個 | `assert 86460 == 60`、`assert 2764800 == 2678400`、`assert 90000 == 3600`、`assert 86401 == 1` |
| 5 | 檢查時區的兩行註解掉 | `1 failed, 63 passed`：沒帶時區 | `Failed: DID NOT RAISE ValueError` |

**判讀：**

- **實驗 1 只紅一個。** 拿掉換算後，受影響的只有 ③ 的月份判斷；⑤ 的相減不受影響，因為 `next_start` 帶台北時區、`moment` 帶 UTC，兩個都有時區，Python 會算出真正的時間差。所以只有「UTC 的月份與台北的月份不同」時才會算錯，也就是台北每月 1 號的 00:00～07:59。四個測試裡只有「剛換月」落在這段：程式以為還在 9 月，去找 10/1 00:00，而那正是現在，於是回 `0`
- 這與 E86 是同一個問題換一種樣子：月初那 8 小時最容易錯。在這裡錯的結果是 `Retry-After: 0`，告訴剛被擋下的人「現在就可以重試」
- 實驗 2 的 `0` 是同一種錯：差半秒時叫客戶端立刻回來
- 實驗 4 每個都剛好多 86,400（一天的秒數）：日寫錯，所有人都被多叫等一天
- 實驗 5：`astimezone` 遇到沒帶時區的時間不會報錯，而是當成這台機器的當地時間（E86 第 4 項的同一件事）

**還原確認：** 每個實驗做完立刻改回；最後 `64 passed`，`git status` 只有 `app/quota.py`、`tests/test_quota.py` 兩個已修改的檔。

### 更正：一行測試註解與實測不符

`test_seconds_until_next_period_counts_last_minute` 上方的註解（`8184c53` 已推送）寫著「沒換算成台北會算成 8 小時又 1 分鐘」。實驗 1 顯示這個測試在沒換算時**仍然通過**（結果還是 60），原因見上方判讀。註解於本次一併改正；守住時區換算的是「剛換月」那一個測試。

- **學到的：** 「這個測試在守什麼」寫在註解裡只是推測，要做過破壞實驗才知道。帶時區的時間相減不受「用哪個時區表示」影響，這是 E86 互動模式看過的 `taipei_moment == moment` 為 `True` 的另一面

### 限制（誠實記錄）

- **兩個函式都還沒有被 `main.py` 呼叫。** 五項定案中的 429、`Retry-After` 標頭、`quota_exceeded` 稽核、503、401 都還沒有實作，目前只有判斷與計算的函式和單元測試
- **`Retry-After` 的值可能長達 31 天（約 268 萬秒）。** 各家客戶端 SDK 遇到這麼大的值會怎麼處理（照等、設上限、或忽略後照自己的節奏重試）沒有查證，不確定它能阻止自動重試
- `≥` 仍會小幅超用：已用 999、額度 1000 的人會被放行，那一次可能花超過 1。不做預扣，這是 7.10 已接受的取捨
- `is_over_quota()` 沒有檢查負數或非整數的輸入
- 守住時區換算的測試只有一個，而且輸入剛好落在台北 10/1 00:00 整；月初 8 小時內的其他時間點（例如 00:30、07:59）沒有各自的測試
- 第一版的錯誤 3、4 是貼出來時就被指出的，沒有實際看過它們的失敗訊息（`day is out of range for month`、`TypeError`）
- 二月（28 或 29 天）、小月（30 天）沒有各自的測試；天數由 `datetime` 相減得出，沒有自己寫天數表
- 固定偏移只適用台北時間（E86 定案 1 的代價）
- 稽核的 `status` 多一種值（`quota_exceeded`）後，步驟 9 換成 DynamoDB 時要一併納入

### 面試可用的說法

- 「超額我回 429 並附 `Retry-After`，值是到台北時間下個月 1 號的秒數。我考慮過 402 和 403：402 暗示付費就能解決，403 會跟權限問題混在一起。429 的缺點是 SDK 會自動重試，但我的額度檢查排在呼叫模型之前，重試只會打到我的 Gateway，不會多花一毛錢。」
- 「判斷超額我用大於等於。用大於的話，額度 0 的人還能呼叫一次，這是我拆 LiteLLM 時特別測過的邊界。我把它寫成測試，也實際改成大於、看到它變紅。」
- 「被額度擋下的請求我照樣寫稽核，不然查不到誰在額度用完之後還一直打。但 API Key 驗證失敗的不寫，因為沒有身分可以記，而且任何人都能拿假 Key 把稽核表灌爆。」
- 「我做破壞實驗時把時區換算拿掉，五個測試只紅一個。原因是兩個帶時區的時間相減，Python 算的是真正的時間差，所以只有月份判斷會錯，而且只錯在每月 1 號的前 8 小時。那個測試如果沒寫，這個錯會讓剛被擋下的人收到『0 秒後重試』。我也因此改掉一行寫錯的測試註解。」
- 「函式還沒寫完但要先推送時，我不刪測試，而是函式留空殼、測試掛跳過標記一起推，主線保持綠燈，測試也不會離開版本紀錄。回來接著做的第一步是撕掉標記、先看到紅，因為跳過的測試不會提醒你它還在跳過。」

---

**推送：** `is_over_quota` 與空殼：`8184c53`（10/7 16:57，已推送）。`seconds_until_next_period` 的實作 `a5bd2e9`（`feat: implement seconds_until_next_period for Retry-After`）、測試註解的更正 `cf4ac06`（`test: correct comments on what the period tests guard`）、本筆紀錄 `b3d1d73`（`docs: record M2 step 7 pure logic evidence`），10/7 18:34 推送，結果 `8184c53..b3d1d73  main -> main`；commit 前以 `git status` 確認只有 `app/quota.py`、`tests/test_quota.py`。

---

## E89. 步驟 5：DynamoDB Local、boto3 連線、建表（2026-10-07 18:57～10-08 00:04；收尾 10-08 11:19～13:50）

**依據：** 決策書 3.2（四張表與主鍵）、D2（`quotas` 用 `user_id` + `period`）、D3（`api_keys` 只存雜湊）、D19（版本與 digest 鎖定）、D35（套件冷卻期）、D36（M1 的稽核存檔案，M2 換成 DynamoDB Local）、8.2 M2（本機階段用 DynamoDB Local）、10.3 第 6 點（Gateway 的角色只給讀寫權限）；E13（官方範例預設對外開埠）、E74（`python:3.12-slim` 的冷卻期例外）。

**範圍：** 把本機的資料庫跑起來、讓程式連得上、建好 M2 要用的三張表。`main.py` 這一步沒有動；讀寫資料表的接線在步驟 6～9。

**生活比喻：** 駕訓班有兩塊場地。練習場（8001）是平常開發、驗收用的，裡面的東西會留著；考場（8002）每考一題就把場地清空重擺。兩塊分開，考試才不會把練習場擺好的東西清掉。程式裡的註解也用「練習場」「考場」這兩個詞。

### 開工前待辦 2：`python:3.12-slim` 的 digest 複查（10/7 19:04～19:06，E74 的冷卻期例外結案）

| 指令 | 結果 |
|---|---|
| `docker manifest inspect python:3.12-slim@sha256:dddfd7e0…0016` | `manifest verification failed for digest sha256:dddfd7e0…` |
| `docker buildx imagetools inspect`（同一個 digest） | `MediaType: application/vnd.oci.image.index.v1+json`、`Digest: sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` |

- 第二個指令回報的 digest 與 `Dockerfile` 鎖定的一致：映像仍然存在，指紋沒有變
- 第一個指令的訊息不是「被撤回」；撤回會是 `no such manifest` 或 `manifest unknown`。推測是這個較舊的指令遇到多平台索引時，自己驗算指紋對不上；**這個推測沒有查證**
- **限制：** 只確認存在且指紋未變，沒有掃弱點（Trivy 於 CI 建立時加入）

### 定案 1：compose（10/7 19:09 本人決定）

| # | 決定 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 1 | 映像 | `amazon/dynamodb-local:3.3.1`，鎖 digest `sha256:ff89bd48…0dab`（7/31 上架，已過冷卻期；Docker Hub 的標籤清單與本人 `docker buildx imagetools inspect` 的結果一致） | `latest`：不可重現（D19） |
| 2 | 資料 | `-inMemory`，容器停止即清空 | 掛磁碟：會留下資料檔，測試被舊資料干擾。代價：每次重開要重新建表、塞種子資料 |
| 3 | 埠 | `127.0.0.1:8001:8000` | 8000 是 Gateway 的；不寫 `127.0.0.1` 會開給區域網路（E13） |
| 4 | `-sharedDb` | 加 | 不加：會依存取金鑰與區域分成不同的資料庫，互相看不到，而且沒有任何錯誤 |
| 5 | 檔名 | 根目錄 `compose.yaml` | `docker-compose.yml` 是舊檔名 |
| 6 | 內容 | 只放 DynamoDB Local；Gateway 等步驟 11 前再加 | 一次只引入一樣新東西 |

### 定案 2：連線（10/7 19:37 本人決定）

| # | 決定 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 1 | 網址來源 | 環境變數 `DYNAMODB_ENDPOINT_URL`，必填，沒設就 `KeyError` | 給預設值：boto3 的預設是連真的 AWS，並自動使用電腦上 `aws login` 的身分 |
| 2 | 假帳密 | 程式內的具名常數 `LOCAL_ACCESS_KEY`、`LOCAL_SECRET_KEY`（值 `"local"`），明確帶入 | 不帶：boto3 會去找真的 AWS 身分。放 `.env`：會讓人以為它是秘密 |
| 3 | 位置 | `app/db.py` 的 `make_dynamodb_client()` | 放 `main.py`：腳本要用連線就得匯入整個 Gateway |

**弱點：** M4 上雲時要回頭改 `app/db.py`。真的 AWS 不給網址、不帶假帳密，用 Fargate 的 IAM 角色。列入待決。

### 定案 3：資料表與測試（10/7 20:10、20:39 本人決定）

| # | 決定 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 1 | M2 建哪幾張 | `api_keys`、`quotas`、`audit` | `usage`：M5 的 Worker 才寫 |
| 2 | 主鍵 | 照決策書 3.2：`key_hash`；`user_id` + `period`；`request_id`。全部是字串 | — |
| 3 | 計費模式 | 練習場用 `PAY_PER_REQUEST` | 雲端用哪一種留到 M4（與免費額度有關，未查證），列入待決 |
| 4 | 表名 | `app/db.py` 的常數 `API_KEYS_TABLE`、`QUOTAS_TABLE`、`AUDIT_TABLE` | 各處寫字串：打錯只會變成「找不到表」。常數名稱打錯會直接報錯 |
| 5 | 建表程式 | `scripts/create_tables.py` 的 `create_tables(client)`，已存在的表就跳過 | 放 `app/`：會進容器；Gateway 在雲端不該有建表的權限（10.3 第 6 點） |
| 6 | 碰資料庫的測試 | 打真的 DynamoDB Local，標 `integration`；連不到就明確地紅，不自動跳過 | 手寫的假 DynamoDB：不會解讀運算式，步驟 8 最容易錯的部分測不到。`moto`：多一個相依套件。沒有 Docker 的環境用 `uv run pytest -m "not integration"` |
| 7 | 測試隔離 | compose 多一個 `dynamodb-test`（`127.0.0.1:8002`），測試只連它；`tests/conftest.py` 的 `dynamodb` fixture 把網址寫死為 8002，每個測試前刪掉所有表 | 共用 8001：驗收中途跑測試會清掉種子資料。拿掉 `-sharedDb`、用不同的假帳號分庫：依賴練習場獨有的行為 |

**欄位名（10/7 20:21）：** `quotas` 的額度與已用量欄位叫 `limit_micro_usd`、`used_micro_usd`，與 `is_over_quota()` 的參數同名（E88）。

### 做法：分九小段

| 段 | 內容 | 結果 |
|---|---|---|
| 1 | `compose.yaml`，把 DynamoDB Local 跑起來 | 容器 `Up`，`127.0.0.1:8001->8000/tcp` |
| 2 | `uv add boto3` | `64 passed` |
| 3 | 互動模式第一次連線 | `list_tables()` 回空清單、狀態 200 |
| 4 | `make_dynamodb_client()`：先寫 2 個測試 → 寫函式 → 兩個破壞實驗 | `1 error during collection` → `66 passed` |
| 5 | 互動模式建第一張表、寫一筆、讀一筆 | `ACTIVE`；找不到資料時回應沒有 `Item` |
| 6 | 測試專用的容器 `dynamodb-test` | 兩個容器都 `Up`（8001、8002） |
| 7 | `create_tables()`：先寫 5 個測試 → 寫函式 | `1 error during collection` → `5 errors` → `1 failed, 70 passed` → `71 passed` |
| 8 | 補註解與型別、三個破壞實驗（10/8） | 見「破壞實驗」；還原後 `71 passed` |
| 9 | 執行入口，對練習場實際建表（10/8） | 8001 上有三張表；重複執行沒有錯誤 |

### 第一部分：DynamoDB Local 跑起來（10/7 19:15）

- `docker compose up -d`：映像 `Pulled 26.9s`、網路 `llm-gateway_default`、容器 `llm-gateway-dynamodb-1 Started`
- `docker compose ps`：`Up`，`127.0.0.1:8001->8000/tcp`
- 直接用 `curl.exe` 連 `http://127.0.0.1:8001`，回應內容是：

```
{"__type":"com.amazonaws.dynamodb.v20120810#MissingAuthenticationToken","Message":"Request must contain either a valid (registered) AWS access key ID or X.509 certificate."}
```

容器有在回應，並且要求帶存取金鑰（任何值都可以，但一定要有）。指令的 `-i` 打成了 `-1`，所以只看到回應內容，沒看到狀態碼那一行。

- `docker stats --no-stream`：`190.9MiB / 3.823GiB`，`PIDS 41`

| 項目 | 待機記憶體 | 來源 |
|---|---|---|
| 本案 Gateway（M1 映像） | 56.08 MiB | E76 |
| DynamoDB Local（一個容器） | 190.9 MiB | 本筆 |
| LiteLLM v1.102.0（有資料庫） | 584 MiB | E16 |

DynamoDB Local 只在開發機上跑，不算進 Fargate 的 512 MiB；雲端用的是託管的 DynamoDB。兩個容器同時開時（20:53）：`dynamodb-test-1` 170.9 MiB、`dynamodb-1` 212.1 MiB。

### 第二部分：boto3 與 `make_dynamodb_client()`（10/7 19:27～20:07）

**安裝：** `uv add boto3` → `boto3==1.43.103`、`botocore==1.43.103`、`jmespath==1.1.0`、`python-dateutil==2.9.0.post0`、`s3transfer==0.19.2`、`six==1.17.0`、`urllib3==2.8.0`，共 7 個套件；`64 passed`。`pyproject.toml` 的 `exclude-newer` 是 `2026-09-27T00:00:00Z`（D35），這 7 個都在冷卻期之外。

**互動模式第一次連線（19:32）：** `db.list_tables()` → `'TableNames': []`、`'HTTPStatusCode': 200`、`'server': 'Jetty(12.1.11)'`。

**新觀念：`boto3.client(…)` 的五格。** 要連哪個服務、網址、區域、存取金鑰、密鑰。**生活比喻：** 寄包裹的託運單，五格都要填；「收件地址」那一格空著，貨運行會照預設送到總倉（真的 AWS）。

**測試（`tests/test_db.py`，2 個，不需要容器；測試數 64 → 66）：**

| 測試 | 準備 | 檢查 | 在守什麼 |
|---|---|---|---|
| `test_make_dynamodb_client_requires_endpoint` | `monkeypatch.delenv` 拿掉環境變數 | 丟 `KeyError` | 沒說要連哪裡就不連 |
| `test_make_dynamodb_client_uses_endpoint_from_env` | `monkeypatch.setenv` 設成 `http://127.0.0.1:9999` | `client.meta.endpoint_url` 等於這個網址 | 連線真的指向環境變數給的網址 |

- 第二個測試的埠用 9999 而不是 8001：函式把網址寫死成 8001 時，用 8001 測會碰巧通過
- **新道具 `monkeypatch`：** 在一個測試的期間暫時改環境變數，測試結束自動還原。**生活比喻：** 試衣間，出來時衣服會掛回原位，不會穿著走

**先寫測試：** `ERROR tests/test_db.py`，`1 error during collection`（`app/db.py` 還不存在）。

**本人撰寫（`app/db.py`）：**

```python
import os

import boto3
from botocore.client import BaseClient

# 區域固定東京，和之後上雲一致
REGION = "ap-northeast-1"

# 練習場用的假帳密：DynamoDB Local 不驗證真假，但一定要有值
# 明確帶入，boto3 才不會去找這台電腦上真的 AWS 身分來用
LOCAL_ACCESS_KEY = "local"
LOCAL_SECRET_KEY = "local"

# 表名只寫在這一處，別處一律用常數：常數名稱打錯會直接報錯，字串打錯只會變成「找不到資料表」
API_KEYS_TABLE = "api_keys"
QUOTAS_TABLE = "quotas"
AUDIT_TABLE = "audit"


# 要連哪裡一定要明講：沒設定就報錯，不讓 boto3 照預設去連真的 AWS
def make_dynamodb_client() -> BaseClient:
    """Return a DynamoDB client for the endpoint named in the environment."""
    endpoint = os.environ["DYNAMODB_ENDPOINT_URL"]
    client = boto3.client(
        "dynamodb",
        endpoint_url=endpoint,
        region_name=REGION,
        aws_access_key_id=LOCAL_ACCESS_KEY,
        aws_secret_access_key=LOCAL_SECRET_KEY,
    )
    return client
```

第一版的回傳型別寫成 `-> bytes`、`import os, boto3` 寫在同一行；改為 `-> BaseClient`、分行匯入。結果 `66 passed`。

**破壞實驗（兩個測試各看過一次失敗）：**

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| A | `os.environ["…"]` 改成 `os.environ.get("…")` | `1 failed, 65 passed` | `Failed: DID NOT RAISE KeyError` |
| B | `endpoint_url=endpoint,` 那一行註解掉 | `1 failed, 65 passed` | `- http://127.0.0.1:9999` / `+ https://dynamodb.ap-northeast-1.amazonaws.com` |

**判讀：**

- 實驗 A：`.get()` 查不到會安靜地回 `None`，`boto3` 拿到 `None` 就照預設連真的 AWS。中括號查不到會當場報錯。兩種寫法只差在「查不到時吵不吵」
- 實驗 B：少傳一格，連線就指向真的 AWS 東京，**程式沒有任何錯誤**。失敗訊息裡的 `+` 那行就是它本來會去的地方

### 第三部分：互動模式建第一張表（10/7 20:17～20:30，連 8001）

- `create_table` 建 `quotas`：`'TableStatus': 'ACTIVE'`，`'TableArn': 'arn:aws:dynamodb:ddblocal:000000000000:table/quotas'`
- `put_item`（`alice`、`2026-10`、`limit_micro_usd` 為 `{"N": "1000"}`、`used_micro_usd` 為 `{"N": "0"}`）→ 200
- `get_item` 拿回四欄；數字是帶引號的字串，要用時得 `int()`
- 找不存在的 `bob`：回應裡沒有 `Item`（`"Item" in …` 為 `False`），不會報錯

**新觀念：**

| 觀念 | 白話 | 生活比喻 |
|---|---|---|
| `KeySchema` 的 `HASH`／`RANGE` | 分割鍵／排序鍵 | 置物櫃：`HASH` 是「哪一排」，`RANGE` 是「那一排的第幾格」 |
| `AttributeDefinitions` | 只列主鍵用到的欄位；其他欄位寫入時才出現，不用事先宣告 | 訂抽屜櫃時只要講怎麼分格，不用講每格會放什麼 |
| 型別標籤 `{"S": …}`／`{"N": "…"}` | 每個值都要標是字串還是數字；數字也寫成字串 | 寄國際包裹，每樣物品都要在申報單上填類別 |

**步驟 7 的伏筆：** 「這個人這個月沒有額度紀錄」不會報錯，和「資料庫壞了」是兩種不同的情況。前者要擋還是放，尚未定案（列入待決）。

### 第四部分：測試專用的容器（10/7 20:49～20:53）

compose 加上 `dynamodb-test` 後，兩個容器都 `Up`，埠 8001 與 8002（過程見挫折 2）。

**為什麼要分兩個容器：** fixture 每個測試前會刪掉所有資料表。和開發用的共用一個，驗收做到一半跑一次測試，種子資料就沒了。

**為什麼 fixture 的網址寫死、不讀環境變數：** 這個道具會刪掉它連到的地方的所有資料表。讀環境變數的話，哪天環境變數指到別的地方，它就去刪那裡的表。

**本人撰寫（`tests/conftest.py`，由提供的版本改寫）：**

```python
"""Shared fixtures for tests."""

import pytest

from app.db import make_dynamodb_client

# 考場的網址寫死在這裡：這個道具會刪掉所有資料表，絕不能被指到別的地方
TEST_ENDPOINT_URL = "http://127.0.0.1:8002"


# 每個測試拿到的都是空的考場：先把上一個測試留下的表全部刪掉
@pytest.fixture
def dynamodb(monkeypatch):
    """Return a client for the test-only DynamoDB Local, with all tables removed."""
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", TEST_ENDPOINT_URL)
    client = make_dynamodb_client()
    for name in client.list_tables()["TableNames"]:
        client.delete_table(TableName=name)
    return client
```

**新觀念：** `conftest.py` 是 pytest 的固定檔名，裡面的 fixture 所有測試檔都拿得到，不用匯入；`pytestmark = pytest.mark.integration` 把整個檔的測試都貼上同一張標籤；標籤要先在 `pyproject.toml` 的 `markers` 登記。

**標籤的驗證（10/8 11:24）：** `uv run pytest -m "not integration"` → `66 passed, 5 deselected`。`deselected` 是「這次沒選它」，與 E88 的 `skipped`（測試自己掛著跳過）不同。

### 第五部分：`create_tables()`（10/7 20:54～10/8 00:04；註解與型別 10/8 11:41）

**測試（`tests/test_create_tables.py`，5 個，都要連考場；測試數 66 → 71）：**

| 測試（開頭皆為 `test_create_tables`） | 檢查 | 在守什麼 |
|---|---|---|
| `…_creates_three_tables` | `sorted(names) == ["api_keys", "audit", "quotas"]` | 三張表都在；表名直接寫字串，常數的值打錯才抓得到 |
| `…_gives_quotas_a_two_part_key` | `quotas` 的 `KeySchema` 是 `user_id`（`HASH`）加 `period`（`RANGE`） | 少了 `period`，換月會蓋掉上個月的紀錄 |
| `…_keys_api_keys_by_key_hash` | `api_keys` 的 `KeySchema` 是 `key_hash` | 拿到 Key 的雜湊就能直接查 |
| `…_keys_audit_by_request_id` | `audit` 的 `KeySchema` 是 `request_id` | 使用者拿回應裡的編號就能對回紀錄 |
| `…_can_run_twice_and_keeps_data` | 建表、寫一筆、再建一次，沒有錯誤，而且那一筆還在 | 重複執行不出錯、不清資料 |

**從紅到綠：**

| 次 | 結果 | 原因 |
|---|---|---|
| 1 | `ModuleNotFoundError: No module named 'scripts.create_tables'`，`1 error during collection` | 函式還沒寫（預期的） |
| 2 | `fixture 'dynamodb' not found`，`66 passed, 5 errors` | 見挫折 3 |
| 3 | `1 failed, 70 passed`：`At index 0 diff: {'AttributeName': 'user_id', 'KeyType': 'HASH'} != {'AttributeName': 'key_hash', 'KeyType': 'HASH'}` | 見挫折 4 |
| 4 | `71 passed` | — |

函式以填空版（提示二）完成。

**本人撰寫（`scripts/create_tables.py`，`dac3d3c` 的版本）：**

```python
from botocore.client import BaseClient

from app.db import API_KEYS_TABLE, QUOTAS_TABLE, AUDIT_TABLE, make_dynamodb_client


# 建表放在 scripts/，不放 app/：Gateway 在雲端不該有建表的權限
def create_tables(client: BaseClient) -> None:
    """Create the tables this milestone needs, skipping any that already exist."""
    # 已經存在的表就跳過：重複執行不會報錯，也不會清掉裡面的資料
    existing = client.list_tables()["TableNames"]

    # 主鍵是 key_hash：Gateway 手上只有 Key 的雜湊，要拿它查出是誰
    if API_KEYS_TABLE not in existing:
        client.create_table(
            TableName=API_KEYS_TABLE,
            AttributeDefinitions=[
                {"AttributeName": "key_hash", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "key_hash", "KeyType": "HASH"},
            ],
            # 練習場用隨用隨付；雲端用哪一種留到 M4 決定
            BillingMode="PAY_PER_REQUEST",
        )

    # user_id + period：換月自然是新的一筆，不用寫每月重置的排程
    if QUOTAS_TABLE not in existing:
        client.create_table(
            TableName=QUOTAS_TABLE,
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "period", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "period", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

    # 一筆請求一筆紀錄，事後用 request_id 找
    if AUDIT_TABLE not in existing:
        client.create_table(
            TableName=AUDIT_TABLE,
            AttributeDefinitions=[
                {"AttributeName": "request_id", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "request_id", "KeyType": "HASH"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )


# 直接執行這個檔時才建表；被測試 import 時不會自己跑
if __name__ == "__main__":
    create_tables(make_dynamodb_client())
```

**為什麼 `api_keys` 的主鍵一定是 `key_hash`：** Gateway 收到請求時手上只有 Key 的雜湊，要拿它去查「這是誰」。主鍵是 `user_id` 的話查不了，而且一個人只能有一把 Key。

**為什麼「已存在就跳過」：** 練習場的資料只放記憶體，每次重開容器都要重新建表；腳本要能放心地重複執行。

**`-> None`（10/8）：** 表示這個函式做完事就結束，不交回東西。第一次補型別時漏了這一段，程式照跑、測試也是綠的（型別標註執行時不起作用），是讀 `git diff` 才看到的。

### 破壞實驗（10/8 12:18～14:06）

5 個測試裡，只有「`api_keys` 的主鍵」在寫功能時看過為了對的原因失敗（上表第 3 次），其餘四個一寫就通過。一次改一處，跑完立刻改回。

| # | 改了什麼 | 結果 | 紅的是哪幾個 | 失敗訊息 |
|---|---|---|---|---|
| A | `audit` 那一段整個註解掉 | `2 failed, 3 passed` | 三張表都在；`audit` 主鍵 | `assert ['api_keys', 'quotas'] == ['api_keys', ...it', 'quotas']`、`At index 1 diff: 'quotas' != 'audit'`；`ResourceNotFoundException … DescribeTable operation: Cannot do operations on a non-existent table` |
| B | `quotas` 的主鍵拿掉 `period`（`AttributeDefinitions` 與 `KeySchema` 各一行） | `2 failed, 3 passed` | `quotas` 兩段式主鍵；重複執行 | `assert [{'AttributeN...ype': 'HASH'}] == [{'AttributeN...pe':'RANGE'}]`；`ValidationException … GetItem operation: The number of conditions on the keys is invalid` |
| C | `quotas` 的 `if QUOTAS_TABLE not in existing:` 改成 `if True:` | `1 failed, 4 passed` | 重複執行 | `ResourceInUseException … CreateTable operation: Cannot create preexisting table` |
| D | `audit` 的兩處 `request_id` 改成 `user_id` | `1 failed, 4 passed` | `audit` 主鍵 | `At index 0 diff: {'AttributeName': 'user_id', 'KeyType': 'HASH'} != {'AttributeName': 'request_id', 'KeyType': 'HASH'}` |

**判讀：**

- **實驗 A：** 少建一張表，被兩個角度各抓一次。「數有幾張」的測試走到 `assert` 才紅；「`audit` 主鍵」的測試還沒走到 `assert`，在 `describe_table` 那一步就被資料庫退回。pytest 的 `At index 1 diff` 是照位置一格一格比的，「右邊多一項 `quotas`」指的是右邊的清單比較長，真正少的是 `audit`
- **實驗 B：** 主鍵設錯，**建表照樣成功**。只用 `user_id` 當主鍵是合法的表，資料庫不知道設計上想要兩段。這個錯要靠測試把「我要兩段式主鍵」寫下來才抓得到
- **實驗 B 的第二個紅：** 錯誤發生在 `GetItem`，不是 `PutItem`。寫入時 `period` 被當成普通欄位收下，沒有任何錯誤；讀取時指定兩段主鍵才對不上。「10 月的額度蓋掉 9 月的」就是這樣無聲發生的
- **實驗 C：** 只紅一個。fixture 每個測試前都清空考場，所以只呼叫一次 `create_tables` 的四個測試碰不到「表已存在」；只有「跑兩次」的測試會製造這個情況
- **實驗 D 與實驗 A 的差別：** 兩個都讓「`audit` 主鍵」的測試變紅。A 是表不存在，測試停在 `describe_table`，沒有走到 `assert`；D 是表在、主鍵欄位錯，停在 `assert schema == …`。這個斷言要抓的是後者，所以 A 不能算看過它失敗，另外補做 D。失敗摘要的第一行兩邊都被縮成 `[{'AttributeN...ype': 'HASH'}]`，看起來一樣，差異要看 `At index 0 diff` 那一行
- 實驗 B、D 的 `AttributeDefinitions` 要一起改；以 B 為例：只拿掉 `KeySchema` 那一行，DynamoDB 會在建表時先回報宣告了沒用到的欄位，五個測試全紅，但那是為了別的原因而紅

**生活比喻（實驗 B）：** 跟木工訂抽屜櫃，本來要「每人一排、每月一格」，下單時漏寫月份，木工就做成每人一格。這是一張正常的訂單，木工不會打電話來問。

**還原確認：** 每個實驗做完立刻改回，`git diff` 沒有輸出；最後 `71 passed`。

### 執行入口：第一次對練習場建表（10/8 13:47）

`scripts/create_tables.py` 最下面加上 `if __name__ == "__main__":`。**新觀念：** 檔案被直接執行時 `__name__` 是 `"__main__"`，被 `import` 時是檔案自己的名字。沒有這個判斷，測試檔 `import` 這個檔的瞬間就會去建表。**生活比喻：** 樂譜被收進館藏時不會發出聲音，有人拿上台演奏才會響。

| 步驟 | 指令 | 結果 |
|---|---|---|
| 1 | `uv run pytest` | `71 passed`：`import` 時不會自己建表 |
| 2 | `uv run python -m scripts.create_tables`（沒設環境變數） | `KeyError: 'DYNAMODB_ENDPOINT_URL'` |
| 3 | 設 `DYNAMODB_ENDPOINT_URL` 為 `http://127.0.0.1:8001` 後再執行 | 沒有輸出、沒有錯誤 |
| 4 | `list_tables()` | `['api_keys', 'audit', 'quotas']` |
| 5 | 再執行一次 | 沒有輸出、沒有錯誤 |

步驟 2 的輸出：

```
  File "…\scripts\create_tables.py", line 57, in <module>
    create_tables(make_dynamodb_client())
  File "…\app\db.py", line 23, in make_dynamodb_client
    endpoint = os.environ["DYNAMODB_ENDPOINT_URL"]
KeyError: 'DYNAMODB_ENDPOINT_URL'
```

**判讀：** 定案 2 第 1 項（沒設就報錯，不照預設連真的 AWS）第一次在測試以外的實際執行中起作用。

**為什麼用 `python -m scripts.create_tables`：** `python scripts/create_tables.py` 會從 `scripts/` 資料夾找 `app`，找不到；`-m` 從專案根目錄找。

### 挫折 1：兩個 `KeyType` 都打成 `HASH`（互動模式，10/7）

```
botocore.exceptions.ClientError: An error occurred (ValidationException) when calling the CreateTable operation: Too many hash keys specified.  All Dynamo DB tables must have exactly one hash key
```

- **怎麼讀 `ClientError`：** 括號裡是錯誤的種類，`when calling the … operation` 是哪個動作，冒號後面是原因
- **判讀：** 這個檢查是 DynamoDB Local 做的，手寫的假資料庫不會有。佐證定案 3 第 6 項「測試打真的」

### 挫折 2：`Started`，但 `ps` 看不到容器（10/7 20:49）

`dynamodb-test` 的 `command` 把 `DynamoDBLocal.jar` 的句點打成逗號。`docker compose up -d` 顯示 `Started`，但 `docker compose ps`、`docker stats` 都只有一個容器。

- **原因（本人找到）：** compose 不懂 `command` 裡的字是什麼意思，照樣啟動容器；容器裡的 Java 找不到那個檔，啟動後立刻結束
- **容器的錯誤訊息沒有留下**
- **學到的：** `Started` 只代表「啟動的動作做了」，不代表還活著。`Started` 但 `ps` 看不到時，用 `docker compose ps -a`（連已結束的也列出來）與 `docker compose logs 服務名稱` 找原因

### 挫折 3：`fixture 'dynamodb' not found`（10/7）

```
E       fixture 'dynamodb' not found
66 passed, 5 errors
```

- **原因：** 檔案存成 `tests/test_conftest.py`。pytest 只認 `conftest.py` 這個檔名；多了 `test_` 開頭，它被當成一般的測試檔，裡面沒有 `test_` 開頭的函式，所以什麼都沒做，也沒有報錯
- **解法：** `ren` 改名
- **新的失敗樣子：** `ERROR at setup of …`，結果列是 `E` 不是 `F`。測試本身還沒開始跑，是道具準備失敗
- 與 E87 挫折 1（`test_princing.py`）同類：檔名打錯不會有任何錯誤訊息指出檔名

### 挫折 4：`api_keys` 的主鍵寫成 `user_id`（10/7）

三段 `create_table` 是照著第一段改的，`api_keys` 那段留著 `user_id`。失敗訊息的 `At index 0 diff` 指出第 0 項（第一個主鍵）的 `AttributeName` 不同，改成 `key_hash` 後 `71 passed`。這是 5 個測試裡第一個為了對的原因失敗的。

### 挫折 5：破壞實驗 A 第一次做的不是原本要做的實驗（10/7）

把 `os.environ["…"]` 改成 `.get` 時，留著中括號寫成 `os.environ.get["…"]`：

```
TypeError: 'method' object is not subscriptable
2 failed, 64 passed
```

- **怎麼讀：** `not subscriptable` 是「這個東西不能用中括號」。`.get` 是一個方法，要用圓括號呼叫
- 兩個測試都紅，但原因是語法用錯，不是「查不到時不報錯」。重做後得到 `1 failed, 65 passed` 與 `DID NOT RAISE KeyError`（與 E87 挫折 2 同類）

### 更正：`.env.example` 有一行不合法的內容（10/8 11:26 修正，`c7e279a`）

`b3a41fa` 推送的 `.env.example`，註解被斷成兩行，第二行 `from compose.yaml` 前面沒有 `#`，既不是註解也不是 `名稱=值`。接回一行。

- `.env` 本身沒有這個問題（10/7 以 `Select-String "^DYNAMODB" .env` 確認，只印出符合的那一行，不露出金鑰）
- 讀取工具遇到這一行會報錯還是略過，沒有實測
- **學到的：** 範本檔沒有任何測試在讀它，內容錯了只能靠推送前讀 `git diff`

### 三種「不是綠的」

| 樣子 | 意思 | 這一步在哪裡看到 |
|---|---|---|
| `error during collection` | 測試檔讀不進來，一個都沒跑 | 函式或檔案還不存在 |
| `ERROR at setup of …`（結果列是 `E`） | 道具準備失敗，測試還沒開始 | 挫折 3 |
| `FAILED`（結果列是 `F`） | 跑了，但結果不對 | 挫折 4、破壞實驗 |

### 限制（誠實記錄）

- **「重複執行不會清掉資料」的斷言（`"Item" in …`）沒有看過失敗。** 實驗 B、C 讓這個測試變紅，但都停在斷言之前；其餘四個測試的斷言都看過失敗。要改成「表存在就先刪再建」才會讓它紅，沒有做
- 執行入口的兩行沒有自動化測試，只有 10/8 的手動執行
- `make_dynamodb_client()` 的區域與假帳密有沒有帶對，沒有斷言在看
- 假帳密寫在程式裡，只能連 DynamoDB Local；M4 上雲要改 `app/db.py`（定案 2 的弱點）
- 資料只放記憶體：容器重開後表與資料都不見，要重新執行建表腳本；目前沒有自動化，靠人記得
- 5 個 `integration` 測試需要容器開著；沒開時會紅，不會自動跳過（定案 3 第 6 項，刻意的）。CI 要怎麼跑它們尚未定案
- DynamoDB Local 與雲端的 DynamoDB 行為不保證完全相同（例如 `TableArn` 是 `ddblocal`、帳號是 12 個 0，建表立刻 `ACTIVE`）；雲端要到 M4 才驗證
- 雲端的建表會由 Terraform 做，`scripts/create_tables.py` 只用於本機；兩邊的主鍵定義要靠人保持一致
- `create_tables()` 只看「表在不在」，不檢查已存在的表主鍵對不對
- `quotas` 的 `limit_micro_usd`、`used_micro_usd` 目前只在互動模式寫過，程式還沒有讀寫它們
- digest 複查沒有掃弱點；第一個指令失敗的原因是推測
- `curl.exe` 那次沒有看到狀態碼

### 面試可用的說法

- 「連資料庫的函式，網址我設成必填，沒給就直接報錯。因為 boto3 的預設是連真的 AWS，還會自動用電腦上登入的身分。我做過一個實驗：把傳網址的那一行拿掉，程式沒有任何錯誤，連線就指向東京的正式端點。這種『少寫一行就打到正式環境』的事，我用一個測試鎖住。」
- 「碰資料庫的測試我打真的 DynamoDB Local，不用手寫的假資料庫。建第一張表時我把兩個鍵都打成分割鍵，是資料庫本身把我退回的，假的不會擋。代價是測試要容器開著，所以我用標籤把它們分出來，沒有 Docker 的環境可以只跑其他的。」
- 「測試用的資料庫和開發用的是兩個容器。測試道具每次都會清空所有資料表，所以它連的網址我直接寫死，不讀環境變數，避免哪天被指到別的地方去刪表。」
- 「我把 `quotas` 的主鍵故意少寫一段，建表完全成功，寫入也成功，是讀取的時候才出錯。資料庫不會替你檢查設計對不對，只用一段主鍵的話，每個月的額度紀錄會互相覆蓋，而且沒有任何錯誤訊息。」
- 「建表的腳本可以重複執行，已經有的表會跳過。我把那個判斷拿掉試過，五個測試只有『跑兩次』的那一個會紅；沒寫那個測試的話，要到第二次執行腳本才會發現。」
- 「建表的程式我放在 `scripts/`，不放在 Gateway 的程式裡。Gateway 在雲端的角色只需要讀寫資料，不該有建表的權限。」

---

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `a5ae0a2` | 10/7 18:56 | `style: remove a duplicated comment marker`（`tests/test_quota.py` 一行註解開頭多了一個 `#`） |
| `8a2543b` | 10/7 19:25 | `chore: add compose file for DynamoDB Local` |
| `977a4c6` | 10/7 19:36 | `chore: add boto3 dependency` |
| `0519419` | 10/7 20:00 | `feat: add DynamoDB client factory that requires an explicit endpoint` |
| `b3a41fa` | 10/7 20:06 | `chore: document the DynamoDB endpoint setting` |
| `a92e373` | 10/7 20:54 | `chore: add a test-only DynamoDB Local, table names and the integration marker` |
| `f9b15e8` | 10/8 00:03 | `feat: add create_tables with integration tests against DynamoDB Local` |
| `c7e279a` | 10/8 11:26 | `fix: repair a broken comment line in .env.example`（`f9b15e8..c7e279a`） |
| `eb46507` | 10/8 11:41 | `docs: add comments and type hints to create_tables`（`c7e279a..eb46507`） |
| `dac3d3c` | 10/8 13:50 | `feat: add a run entry point to create_tables`（`eb46507..dac3d3c`） |

10/8 的三筆，commit 前都以 `git status`、`git diff` 確認只有預期的那一個檔。

---

## E90. 步驟 6：API Key 驗證（2026-10-08 14:02 定案；14:15～21:04 實作）

**依據：** 決策書 2.2 流程圖 [2]（驗證失敗回 401）、3.2 的 `api_keys` 表（`key_hash` → `user_id`、狀態）、D3（只存 SHA-256 雜湊）、8.2 M2（API Key 錯誤只回「驗證失敗」，不透露是不存在還是已停用；fail-closed）、10.3 第 1、7、8 點；D10（重試與逾時要自己設）；E88 定案 4（驗證失敗的請求不寫稽核）。對應驗收 S01。

**範圍：** 請求帶著 API Key 進來，Gateway 查出是誰；查不到回 401，資料庫讀不到回 503。`user_id` 目前只是被查出來，還沒有用在額度（步驟 7）與稽核（步驟 9）。Key 的產生在步驟 10。

**生活比喻：** 演唱會入口的驗票口。票不對的人在門口就被擋下，走不到座位區；裡面的工作人員遇到的都是驗過票的人。

### 定案 1：開工前（10/8 14:02 本人決定）

| # | 決定 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 1 | Key 放哪個標頭 | `Authorization: Bearer gw_…` | `X-API-Key`：解析最簡單，但它是自訂標頭，客戶端與工具不認得它是機密。`Authorization` 是 HTTP 的標準位置 |
| 2 | `api_keys` 的 `status` 欄位 | 要；值是 `active` 才放行，其餘（`disabled`、欄位不存在、不認得的值）一律拒絕 | 不加、要停用就刪掉那一筆：刪掉後查不到這把 Key 原本屬於誰 |
| 3 | Key 的格式 | `gw_` 加 `secrets.token_hex(32)`，共 67 個字元 | `uuid4`：設計來當編號，不是當密碼。不加前綴：一串亂數看不出是哪個系統的 |
| 4 | 放哪個檔 | `app/auth.py`；測試分三個檔（見下） | 放進 `main.py`：純計算的部分就無法單獨測試 |
| 5 | `Bearer` 的大小寫 | 只認開頭剛好是 `Bearer `（B 大寫、後面一個空格） | 不分大小寫：HTTP 規範的寫法，但常見的客戶端都送 `Bearer`；先做嚴格版，記為限制 |

### 定案 2：接進 `main.py` 時（10/8 16:42 本人決定）

| # | 決定 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 6 | 驗證寫在哪 | FastAPI 的相依 `get_user_id()`，與既有的三個「領用窗口」同一個做法；`chat_endpoint` 把它列為參數 | 寫在 `chat_endpoint` 裡面：失敗的請求可能已經做了遮罩、準備了稽核。寫成相依，沒通過的請求進不了 `chat_endpoint`，E88 定案 4（不寫稽核）與「不碰模型」由結構保證 |
| 7 | 既有的 9 個 `test_chat` 測試 | `make_test_client` 把 `get_user_id` 換成直接交回 `"alice"`；驗證另寫新測試、走真的流程、連考場 | 9 個都先放 Key 再帶上：`test_chat` 整個檔變成要 Docker。代價：這 9 個測試不再經過驗證 |
| 8 | 401 的標頭 | 附 `WWW-Authenticate: Bearer` | 不附：HTTP 規範要求 401 用這個標頭說明驗證方式 |

### 定案 3：資料庫讀不到時（10/8 19:58 本人決定，量測之後）

| # | 決定 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 9 | 多久放棄 | 連線逾時 2 秒、讀取逾時 5 秒、總共試 2 次（含第一次）、重試模式 `standard` | 只試 1 次：一次瞬間的連線問題就變成 503。維持預設：實測要等 48 秒 |
| 10 | 回什麼 | **503**，`{"detail": "Service temporarily unavailable"}`；驗證與額度（步驟 7）共用這一個訊息 | 驗證與額度各用一個訊息：對外透露內部哪一塊壞了，而兩者其實是同一個資料庫 |

**定案 10 修訂了 E88：** E88 寫「額度資料讀不到回 503 `Quota service unavailable`」。資料庫連不上時，最先出錯的是驗證（查 `api_keys`），請求走不到額度檢查；S03 的示範實際上會先撞到驗證。步驟 7 實作時改用共用的訊息。E88 的字串當時尚未實作，只改文件。

**不管哪一種都一樣：** 不能回 401（有效的使用者會以為自己的 Key 壞了），更不能放行；這種請求不寫稽核，因為還不知道是誰。

### 做法：分六小段，先寫測試、看它失敗，再寫功能

| 段 | 內容 | 結果 |
|---|---|---|
| 1 | `hash_api_key()`：Key 算成 SHA-256 | `ModuleNotFoundError` → `2 passed`（共 73） |
| 2 | `extract_bearer_token()`：從標頭取出 Key | `ImportError` → `2 failed, 4 passed` → `6 passed`（共 77） |
| 3 | `find_user_id()`：拿雜湊查 `user_id`、檢查 `status` | `ImportError` → `4 failed` → `4 passed`（共 81） |
| 4 | `get_user_id()` 接進 `main.py`，回 401 | `4 failed, 1 passed` → `5 passed`；全部 `9 failed, 77 passed` → `86 passed` |
| 5 | 連線設定：快點放棄 | 量到 48.1 秒 → `1 failed, 2 passed` → `87 passed`，再量 6.7 秒 |
| 6 | 資料庫讀不到回 503 | `2 failed, 5 passed` → `7 passed`（共 89） |

### 第 1 段：`hash_api_key()`（14:15～14:31）

**生活比喻：** 果汁機。同一種水果打出來的果汁每次都一樣，但拿著果汁變不回水果。資料庫只放果汁，整張表被搬走也拿不到能用的 Key。

**為什麼不像 `hash_prompt()` 那樣用 HMAC：** 使用者的問句很短、很好猜，把常見問句逐一算雜湊就比對得出來，所以要多加一把金鑰（D4）。API Key 是 256 位元的亂數，沒有人猜得完，直接算 SHA-256 就夠（D3；LiteLLM 也是這樣存，E18）。

**測試（`tests/test_auth.py`，不需容器）：**

| 測試（開頭皆為 `test_hash_api_key`） | 檢查 | 在守什麼 |
|---|---|---|
| `…_matches_known_sha256` | `hash_api_key("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"` | 算出來的真的是 SHA-256；`abc` 的雜湊是公開的標準答案 |
| `…_gives_different_hashes_for_different_keys` | `hash_api_key("gw_aaa") != hash_api_key("gw_aab")` | 函式有用到傳進來的 Key |

先寫測試：`ModuleNotFoundError: No module named 'app.auth'`。寫完一次 `2 passed`，所以做破壞實驗：

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| A | `hashlib.sha256(bytes_text)` 改成 `hashlib.sha256(b"abc")`（不理會輸入） | `1 failed, 1 passed` | `assert 'ba7816bf…' != 'ba7816bf…'` |
| B | `sha256` 改成 `sha1` | `1 failed, 1 passed` | `+ a9993e364706816aba3e25717850c26c9cd0d89d`（40 個字元，預期是 64 個） |

**判讀（實驗 A）：** 兩把不同的 Key 算出同一串，等於拿任何一把 Key 都查到同一個人。**「標準答案」那個測試這時是綠的**：寫死的剛好是 `abc`，和它的輸入相同。只有一個測試的話這個錯會過關，兩個測試各守一個方向才夾得住（與 E81「對任何輸入都回 `False`」同類）。

### 第 2 段：`extract_bearer_token()`（14:31～15:49）

**生活比喻：** 信封上寫「王小明 收」。收發室要的是名字，先確認格式對、再把固定的字拿掉；信封空白或格式不對，就當成收件人不明。

**測試（4 個，同一個檔）：**

| 測試（開頭皆為 `test_extract_bearer_token`） | 輸入 | 預期 | 在守什麼 |
|---|---|---|---|
| `…_returns_key_after_prefix` | `"Bearer gw_abc"` | `"gw_abc"` | 拿得到 Key，前綴拿得乾淨 |
| `…_returns_none_without_header` | `None` | `None` | 沒帶標頭不能讓程式當掉 |
| `…_rejects_other_scheme` | `"Basic gw_abc"` | `None` | 不是 `Bearer` 開頭的不收 |
| `…_rejects_empty_key` | `"Bearer "` | `None` | 不能交回空字串去查資料庫 |

**新語法：** `str | None`（可能是文字，也可能沒有）；`startswith()`；`[n:]`（從第 n 個位置取到最後，與做摘要的 `[:50]` 方向相反）。前綴長度用 `len(BEARER_PREFIX)` 算，不寫死成 7。

**破壞實驗（各 `1 failed, 5 passed`）：**

| # | 改了什麼 | 紅的是 | 失敗訊息 |
|---|---|---|---|
| A | 拿掉「標頭是 `None`」的檢查 | 沒帶標頭 | `AttributeError: 'NoneType' object has no attribute 'startswith'` |
| B | 拿掉前綴的檢查 | 別的驗證方式 | `assert 'w_abc' is None` |
| C | 拿掉空字串的檢查 | 空 Key | `assert '' is None` |

加上第一版的失敗（見挫折 1），四個斷言都看過失敗。

**判讀（實驗 A）：** 沒帶標頭的請求會讓程式當掉，使用者拿到的是 500 而不是 401。

### 第 3 段：`find_user_id()`（15:50～16:40）

**生活比喻：** 健身房櫃檯刷會員卡。查無此卡不給進；查到了但會籍是「停權」也不給進；會籍那一欄是空白的，櫃檯不會自己當成有效。

**測試（`tests/test_auth_db.py`，4 個，`integration`）：** 道具 `put_key(client, key_hash, user_id, status)` 往 `api_keys` 放一筆，`status` 給 `None` 就不寫這個欄位。

| 測試（開頭皆為 `test_find_user_id`） | 準備 | 查 | 預期 |
|---|---|---|---|
| `…_returns_user_for_active_key` | 放 `hash-a`／`alice`／`active` | `hash-a` | `"alice"` |
| `…_returns_none_for_unknown_key` | 同上 | `hash-b` | `None` |
| `…_rejects_disabled_key` | 放 `hash-a`／`alice`／`disabled` | `hash-a` | `None` |
| `…_rejects_key_without_status` | 放 `hash-a`／`alice`，不寫 `status` | `hash-a` | `None` |

測試裡的 `hash-a` 只是代號：這個函式只負責「拿一串字去查」，算雜湊是 `hash_api_key()` 的事。

**破壞實驗（各 `1 failed, 3 passed`）：**

| # | 改了什麼 | 紅的是 | 失敗訊息 |
|---|---|---|---|
| A | 回傳時忘了剝型別標籤（`item["user_id"]`） | 有效的 Key | `assert {'S': 'alice'} == 'alice'` |
| B | 拿掉「回應沒有 `Item`」的檢查 | 查無此 Key | `KeyError: 'Item'` |
| C | 拿掉狀態的比對 | 被停用的 Key | `assert 'alice' is None` |
| D | 拿掉「沒有 `status` 欄位」的檢查 | 沒有狀態欄 | `KeyError: 'status'` |

**判讀：**

- **實驗 C 是四個裡最危險的：** 程式不會當掉、沒有任何錯誤，停用的 Key 照樣查得到人，停用功能安靜地失效。與 E85 實驗 3、E89 實驗 B 同類
- 實驗 B、D 停在函式裡（`KeyError`），不是停在測試的斷言。這兩個測試要守的就是「遇到這種資料不能當掉、要安靜地拒絕」，所以算數
- 實驗 D：一筆資料少一欄，就讓持有那把 Key 的人每次都拿到 500

**本人撰寫（`app/auth.py`，`96278fd` 的版本）：**

```python
import hashlib

from botocore.client import BaseClient

from app.db import API_KEYS_TABLE

# Authorization 標頭的固定開頭；結尾的空格是前綴的一部分
BEARER_PREFIX = "Bearer "


# 資料庫只存 Key 的雜湊：整張表被搬走也拿不到能用的 Key；Key 是長亂數，不用另外加金鑰
def hash_api_key(key: str) -> str:
    """Return the SHA-256 hex digest of an API key, the only form the key is stored in."""
    bytes_text = key.encode("utf-8")
    result = hashlib.sha256(bytes_text)
    return result.hexdigest()


# 格式不對一律交回 None，由呼叫的人統一回 401；不在這裡分辨是哪一種不對
def extract_bearer_token(header: str | None) -> str | None:
    """Return the key from an Authorization header, or None when it is missing or malformed."""
    if header is None:
        return None
    if not header.startswith(BEARER_PREFIX):
        return None
    token = header[len(BEARER_PREFIX):]
    if token == "":
        return None
    return token


# 查不到、被停用、狀態欄不存在，一律交回 None：呼叫的人分不出是哪一種，也就不會透露給外面
def find_user_id(client: BaseClient, key_hash: str) -> str | None:
    """Return the user id for an active API key hash, or None when the key must not be used."""
    response = client.get_item(TableName=API_KEYS_TABLE, Key={"key_hash": {"S": key_hash}})
    if "Item" not in response:
        return None
    item = response["Item"]
    if "status" not in item:
        return None
    if item["status"]["S"] != "active":
        return None
    return item["user_id"]["S"]
```

### 第 4 段：`get_user_id()` 接進 `main.py`（16:42～19:45）

**新觀念：**

| 寫法 | 白話 |
|---|---|
| `authorization: str \| None = Header(default=None)` | 請 FastAPI 從請求的標頭裡找 `Authorization`，把值放進這個參數；沒帶就給 `None` |
| `dynamodb: BaseClient = Depends(get_dynamodb)` | 窗口也能向別的窗口領東西：驗票口自己先領一條資料庫連線 |
| `app.dependency_overrides.clear()` | 「換窗口」的設定是全域的，上一個測試換過的會留著；要測真的驗票口，先全部清掉再重設 |

**測試（`tests/test_chat_auth.py`，5 個，`integration`）：** 道具 `make_auth_test_client(tmp_path, dynamodb)` 把模型、HMAC 金鑰、稽核檔換成假的，資料庫換成考場，**驗證走真的**；並在 `api_keys` 放一把 `alice` 的有效 Key（存的是雜湊）。測試用的 Key 是 `"gw_" + "a" * 64`。

| 測試（開頭皆為 `test_chat`） | 請求 | 檢查 |
|---|---|---|
| `…_accepts_valid_key` | 帶正確的 Key | 200 |
| `…_rejects_missing_key` | 不帶標頭 | 401；`{"detail": "Authentication failed"}`；`WWW-Authenticate` 是 `Bearer` |
| `…_rejects_unknown_key` | `Bearer gw_wrong_key` | 401；回應內容同上 |
| `…_rejects_disabled_key` | 先把那把 Key 改成 `disabled`，再帶正確的 Key | 401；回應內容同上 |
| `…_rejected_request_reaches_neither_model_nor_audit` | 不帶標頭 | 401；假的 OpenAI 沒被呼叫（`last_request is None`）；稽核檔沒有被建立 |

第 2、3、4 個的回應內容完全相同：外面的人分不出是沒帶、查不到，還是被停用。

**未完成時的推送（18:18，`bcad448`）：** 測試寫好、驗票口還沒寫時要先推送。沿用 E88 的做法：`get_dynamodb()` 先進 `main.py`（它本身是完整的），5 個測試掛 `skip`，`81 passed, 5 skipped`。回來第一步是撕掉標記、先看到紅：

```
FAILED …::test_chat_rejects_missing_key - assert 200 == 401
FAILED …::test_chat_rejects_unknown_key - assert 200 == 401
FAILED …::test_chat_rejects_disabled_key - assert 200 == 401
FAILED …::test_chat_rejected_request_reaches_neither_model_nor_audit - assert 200 == 401
4 failed, 1 passed
```

**判讀：** 沒帶 Key、帶錯的 Key、帶被停用的 Key，全部回 200。這就是「還沒有驗證」的樣子。有效 Key 那個是綠的：門沒鎖，拿對鑰匙的人當然進得去。

**本人撰寫（`app/main.py` 的驗票口，`87f6f7c` 的版本，含第 6 段的 503）：**

```python
# 領用窗口：資料庫連線（測試時會換成考場的）
def get_dynamodb() -> BaseClient:
    return make_dynamodb_client()


# 驗票口：通過才交出「這個請求是誰」；沒通過在這裡就結束，進不了對話入口
def get_user_id(
    authorization: str | None = Header(default=None),
    dynamodb: BaseClient = Depends(get_dynamodb),
) -> str:
    """Return the caller's user id, or stop the request with 401 or 503."""
    token = extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    key_hash = hash_api_key(token)
    # 資料庫讀不到時不放行，也不說成是 Key 的問題：回 503，請對方稍後再試
    try:
        user_id = find_user_id(dynamodb, key_hash)
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
```

`chat_endpoint` 的參數最後加上 `user_id: str = Depends(get_user_id)`。函式內目前用不到它，但列在參數裡，驗票口就會先執行。

**接上之後，既有的 9 個測試全部變紅：**

```
FAILED tests/test_chat.py::test_chat_returns_reply - KeyError: 'DYNAMODB_ENDPOINT_URL'
（其餘 8 個相同）
9 failed, 77 passed
```

**判讀：** 這 9 個測試沒有換資料庫窗口，驗票口去領真的連線；沒有設定要連哪裡，`make_dynamodb_client()` 就拒絕連（E89 定案 2 第 1 項）。測試沒說要連哪個資料庫，程式沒有偷偷去連別的地方。照定案 7 在 `make_test_client` 加一行覆寫後 `86 passed`；驗票口被換掉後，它底下的資料庫窗口也不會被呼叫，這 9 個測試仍然不需要 Docker。

**破壞實驗：**

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| A | `key_hash = hash_api_key(token)` 改成 `key_hash = token`（忘了算雜湊） | `1 failed, 4 passed`：有效的 Key | `assert 401 == 200` |
| B | 第二個 `raise` 的 `detail` 改成 `"Key not found"` | `2 failed, 3 passed`：查無此 Key、被停用 | `{'detail': 'Key not found'} != {'detail': 'Authentication failed'}` |
| C | 第一個 `raise` 拿掉 `headers=` | `1 failed, 4 passed`：沒帶 Key | `KeyError: 'WWW-Authenticate'` |

**判讀（實驗 A）：** 拿 Key 本身去查，資料庫存的是雜湊，永遠查不到，**所有人都進不來**。五個測試裡四個是「該擋的有擋」，本來就預期 401，所以是綠的；只有「該放的有放」那一個抓得到。少了它，一個把所有人都擋掉的驗票口也會全綠（與 E77「只測該遮的有遮」同類）。

### 第 5 段：資料庫連不上時，先量再決定（19:51～20:29）

**先觀察現況：** 叫程式去連一個沒有任何東西在聽的埠（8003），用 PowerShell 的 `Measure-Command` 計時。

| | 設定前（boto3 預設） | 設定後（定案 9） |
|---|---|---|
| 花的時間 | **48.1 秒** | **6.7 秒** |
| 最底層的錯誤 | `ConnectionRefusedError: [WinError 10061]`（目標電腦拒絕連線） | `TimeoutError: timed out` |
| 程式實際拿到的錯誤 | `botocore.exceptions.EndpointConnectionError: Could not connect to the endpoint URL: "http://127.0.0.1:8003/"` | `botocore.exceptions.ConnectTimeoutError: Connect timeout on endpoint URL: "http://127.0.0.1:8003/"` |

**48 秒是怎麼來的：** 對方是立刻拒絕，照理一秒內就該知道。boto3 預設的重試模式是 `legacy`，連線類的錯誤會自動重試，每次之間的等待加倍；連線與讀取的逾時預設各 60 秒（官方文件）。Claude 以同版本的 boto3 在 Linux 上重現，預設值花 25.57 秒，幾乎等於 9 次等待的總和（0.05 秒起每次加倍，合計 25.55 秒），也就是**總共試了 10 次**；套用定案 9 後是 0.8 秒。Windows 上每次被拒絕要多等約 2 秒，10 次約 20 秒，兩邊對得起來。

**6.7 秒的組成：** Python 啟動約 2 秒，加上連兩次、每次等滿 2 秒就放棄，中間再等一小段。

**錯誤的類型變了：** 在 Windows 上，連一個沒人聽的埠要 2 秒多才收到「拒絕」，設定 2 秒就不等之後，「等到逾時」先發生。同一種故障在不同的設定與作業系統上，會以不同的錯誤類型出現；所以第 6 段接錯誤時接的是它們共同的上一層。

**生活比喻：** 打電話給一家已經歇業的店，是空號，一撥就知道。但手機設定成「打不通就自動重撥，每次多等一下」，結果拿著手機站了快一分鐘才放棄。

**與 D10 是同一個想法：** M1 把 OpenAI SDK 的重試調成 1 次、逾時 30 秒（預設是重試 2 次、逾時 10 分鐘，E70）。預設值是為了「盡量成功」，不是為了「快點告訴使用者失敗」；閘道要自己決定等多久。

**`app/db.py` 的改動（宣告式設定，骨架由 Claude 提供）：**

```python
# 多久放棄：DynamoDB 正常是毫秒等級，連不上就該快點讓使用者知道，而不是默默重試
CONNECT_TIMEOUT_SECONDS = 2
READ_TIMEOUT_SECONDS = 5
# 總共試幾次（含第一次）：留一次重試，網路瞬間抖一下不會直接變成失敗
TOTAL_MAX_ATTEMPTS = 2
```

```python
    config = Config(
        connect_timeout=CONNECT_TIMEOUT_SECONDS,
        read_timeout=READ_TIMEOUT_SECONDS,
        retries={"total_max_attempts": TOTAL_MAX_ATTEMPTS, "mode": "standard"},
    )
```

`boto3.client(…)` 多帶一格 `config=config`。用 `total_max_attempts` 而不是 `max_attempts`：前者含第一次，後者不含，官方文件建議用前者。

**測試（`tests/test_db.py`，1 個，不需容器）：** `test_make_dynamodb_client_gives_up_quickly` 檢查 `client.meta.config` 的 `connect_timeout == 2`、`read_timeout == 5`、`retries == {"total_max_attempts": 2, "mode": "standard"}`。

| 程式的狀態 | 結果 | 失敗訊息 |
|---|---|---|
| 還沒加設定 | `1 failed, 2 passed` | `assert 60 == 2` |
| 破壞 A：拿掉 `read_timeout` | `1 failed, 2 passed` | `assert 60 == 5` |
| 破壞 B：拿掉 `retries` | `1 failed, 2 passed` | `{'mode': 'legacy'} != {'mode': 'standard'}` |

三個斷言都看過失敗。**這個測試只檢查設定有被帶進連線，不會真的去等；** 實際的秒數是上表手動量的那兩次。

### 第 6 段：資料庫讀不到時回 503（20:31～21:04）

**boto3 的錯誤有兩個家族：**

| 家族 | 發生了什麼 | 生活比喻 | 例子 |
|---|---|---|---|
| `BotoCoreError` | 根本沒拿到回覆 | 電話打不通 | 連不上、等到逾時（第 5 段量到的兩種都是） |
| `ClientError` | 接通了，但對方說辦不到 | 電話接通，總機說「沒有這個部門」 | 表不存在、沒有權限 |

**測試（`tests/test_chat_auth.py`，2 個；請求都帶正確的 Key）：**

| 測試 | 怎麼讓資料庫出問題 | 檢查 |
|---|---|---|
| `test_chat_returns_503_when_database_is_unreachable` | 資料庫窗口換成替身 `BrokenDynamoDB`，它的 `get_item` 一律丟 `EndpointConnectionError` | 503；`{"detail": "Service temporarily unavailable"}`；沒碰模型；沒寫稽核 |
| `test_chat_returns_503_when_key_table_is_missing` | 真的把考場的 `api_keys` 表刪掉 | 503；回應內容同上 |

用替身的理由：不必真的停掉容器，也不用每次等逾時。第二個測試的錯誤是 DynamoDB Local 親口回的。

寫功能前：

```
FAILED …::test_chat_returns_503_when_database_is_unreachable - botocore.exceptions.EndpointConnectionError: Could not connect to the endpoint URL: "http://127.0.0.1:8002"
FAILED …::test_chat_returns_503_when_key_table_is_missing - botocore.errorfactory.ResourceNotFoundException: An error occurred (ResourceNotFoundException) when calling the GetItem …
2 failed, 5 passed
```

把查資料庫的那一行用 `try / except (BotoCoreError, ClientError)` 包起來（程式見第 4 段），`7 passed`，全部 `89 passed`。這一段以填空版（提示二）完成。

**生活比喻（`try / except`）：** 請同事去倉庫拿東西，先交代一句：「門打不開的話不要硬撬，回來跟我說暫時拿不到。」

**破壞實驗：**

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| A | 只接 `BotoCoreError` | `1 failed, 6 passed`：表不存在 | `ResourceNotFoundException … Cannot do operations on a non-existent table` |
| B | 只接 `ClientError` | `1 failed, 6 passed`：連不上 | `EndpointConnectionError: Could not connect to the endpoint URL` |
| C | `503` 改成 `500` | `2 failed, 5 passed` | `assert 500 == 503` |

**判讀：** 兩個測試各守一個家族，少接哪一個，就是哪一個測試紅。

### 挫折 1：取單一位置與切片（第 2 段）

第一版的 `header[len(BEARER_PREFIX)]` 少了冒號：

```
AssertionError: assert 'g' == 'gw_abc'
IndexError: string index out of range
2 failed, 4 passed
```

- **原因：** 沒有冒號是「拿第 7 個位置的那一個字」，所以只拿到 `g`；`"Bearer "` 剛好 7 個字（位置 0～6），沒有第 7 個，所以空 Key 那個測試是 `IndexError`
- **生活比喻：** 一排 7 個座位，編號 0～6。「7 號座位」不存在，會被擋下；「7 號以後的所有座位」是合法的問法，答案是沒有人。取單一位置會報錯，切片不會
- 本人依訊息自行修正。第一個測試是為了對的原因紅的；空 Key 那個紅的原因是 `IndexError`，不算，另以實驗 C 補做

### 挫折 2：`get_item() only accepts keyword arguments`（第 3 段）

第一版寫成 `client.get_item({"key_hash": {"S": key_hash}})`：

```
TypeError: get_item() only accepts keyword arguments.
4 failed
```

- **原因：** boto3 的每個動作都只收有寫名字的參數（`TableName=…`、`Key=…`），不收只照位置排的
- 四個測試全紅、訊息完全相同、都停在同一行：那一行之後的程式還沒有被走到（E88 學到的），所以這次的紅不算看過斷言失敗
- 本人依訊息自行修正

### 挫折 3：推送前逐行讀測試抓到的六處

這六處都不會自己報錯，測試結果是綠的或被別的錯誤蓋住，是讀程式才看到的。

| # | 寫成 | 問題 | 為什麼沒有自己露出來 |
|---|---|---|---|
| 1 | 測試名稱 `…_rejects_other_schema`、`token__rejects`（雙底線） | `schema` 是「結構」，這裡要的是 `scheme`「方式」 | pytest 只看名稱是不是 `test_` 開頭 |
| 2 | `API_KEY_TABLE`（少一個 `S`） | 常數名稱不存在 | 上一行的 `ImportError` 先發生，蓋住了它 |
| 3 | 「查無此 Key」的測試放的和查的是同一把（`hash-b`） | 正確的函式反而會讓這個測試紅 | 函式還沒寫，測試停在收集階段 |
| 4 | 網址 `"/V1/chat"`（四處） | 路徑分大小寫，會得到 404 | 同上 |
| 5 | `TEST_KEY = "gw_ " + …`（多一個空格） | 與註解「格式和真的一樣」不符 | 存和查用的是同一串，測試照過 |
| 6 | 「不碰模型、不寫稽核」的測試沒有檢查狀態碼 | 配上第 4 項打錯的網址，請求在 404 就結束，**不管有沒有做驗證都會通過** | 它的兩個斷言在 404 時也成立 |

- **第 6 項的修正：** 在那兩個斷言之前加 `assert response.status_code == 401`，先確認請求真的是被驗證擋下的。這個斷言在撕掉 `skip` 之後確實變紅（`assert 200 == 401`）
- **生活比喻（第 6 項）：** 要檢查「沒票的人進不了場」，派去的人走錯棟樓。他確實沒進場，但這不能證明驗票口有在運作
- **學到的：** 「某件事沒有發生」的斷言，要先確認請求走到了預期的那一步；否則任何提早失敗都會讓它通過。與 E85「更正」（對字典用 `in` 永遠通過）同類
- 常數名稱打錯會直接報錯（第 2 項），字串打錯不會（第 4 項）；這是 E89 把表名寫成常數的理由

### 挫折 4：撕掉 `skip` 之後仍然是 `5 skipped`

回來接著做時，第一次重跑的結果列是 `sssss`、`5 skipped`，修改沒有生效。以 `Select-String "skip" tests\test_chat_auth.py` 確認檔案裡已經沒有 `skip` 之後才看到紅。

- **學到的：** E88 記過「跳過的測試不會提醒自己還在跳過」。這次是實例：以為撕掉了，結果是綠的。撕標記之後要看結果列有沒有 `s`，不能只看有沒有 `F`

### 挫折 5：量測指令在別的資料夾執行

第一次量測得到 `ModuleNotFoundError: No module named 'app'`、1.9 秒。那個終端機不在專案資料夾，Python 從目前所在的資料夾找 `app`，在第一行就停了，還沒走到連線。回到專案資料夾重做才得到 48.1 秒。與 E89「為什麼用 `python -m`」是同一件事。

### 限制（誠實記錄）

- **`user_id` 查出來之後還沒有被使用。** 額度（步驟 7）與稽核（步驟 9）尚未接上；目前的效果只有「沒有有效 Key 的人進不來」
- **既有的 9 個 `test_chat` 測試不經過驗證**（定案 7 的代價）；驗證壞了只有 `test_chat_auth.py` 的 7 個會發現
- **「不碰模型、不寫稽核」的兩個斷言沒有做破壞實驗。** 要讓它們變紅，得把驗證搬進 `chat_endpoint`、排在呼叫模型之後，那是結構的改寫，不是改一行；目前由「驗證在 `chat_endpoint` 之外」的結構保證
- 503 兩個測試的 `detail` 斷言沒有單獨看過失敗（實驗 C 停在前一個斷言）
- **每個請求都新建一條 boto3 連線**（`get_dynamodb()` 沒有重複使用）。建立連線的成本沒有量測；步驟 12 量延遲與記憶體時評估
- **`get_item` 沒有指定強一致讀取。** 雲端上剛被停用的 Key 可能在短時間內仍然通過；DynamoDB Local 看不出這個差異。是否加 `ConsistentRead=True` 尚未定案
- **驗證失敗沒有任何紀錄與計數**（E88 定案 4 的代價）。有人大量嘗試 Key 時目前看不到；限速不在本專題範圍（7.9）
- `bearer` 小寫會被拒絕（定案 5）；`Bearer` 後面多個空格時，取出的 Key 帶著空格，查不到而回 401
- Key 的格式（`gw_` 開頭、長度）沒有檢查，任何字串都會被拿去算雜湊再查一次資料庫
- 連不上資料庫時，使用者仍要等約 4～5 秒才拿到 503（6.7 秒扣掉 Python 啟動）；這個數字只在 Windows 的本機量過一次，雲端的情況要到 M4 才知道
- 逾時與重試的數字（2 秒、5 秒、2 次）是依「DynamoDB 正常是毫秒等級」定的，沒有壓力測試佐證
- `BrokenDynamoDB` 是替身，只模擬 `EndpointConnectionError`；真的停掉容器的情況留到步驟 11 的驗收（S03）
- 503 沒有附 `Retry-After`
- 只接了 `find_user_id` 的錯誤。`get_dynamodb()` 本身出錯（例如沒設定網址）仍是 500
- `hash_api_key()` 用未加鹽的 SHA-256，前提是 Key 夠長夠亂；步驟 10 產生 Key 時要守住定案 3 的格式
- 只驗證假的 OpenAI 與考場；真實呼叫留到步驟 11（S01）

### 面試可用的說法

- 「API Key 我只存 SHA-256 雜湊。稽核的指紋我用 HMAC，因為問句很短、猜得到；API Key 是 256 位元的亂數，猜不完，所以不需要另外加金鑰。兩個地方用不同的做法，依據是被雜湊的東西好不好猜。」
- 「驗證我寫成 FastAPI 的相依，放在對話入口之外。沒通過的請求進不了主流程，所以不會碰到模型、也不會寫稽核，這是結構保證的，不是靠每個地方記得檢查。」
- 「沒帶 Key、Key 不存在、Key 被停用，三種我回完全相同的 401。我做過一個實驗，把其中一種的訊息改掉，兩個測試立刻變紅。外面的人不該能從訊息分辨一把 Key 存不存在。」
- 「我有一個測試是『被拒絕的請求不碰模型、不寫稽核』。推上去之前我讀到自己把網址的大小寫打錯了，請求其實是 404，那個測試照樣是綠的。所以我在它前面加了一行，先確認狀態碼是 401。『某件事沒發生』的測試，要先確認請求真的走到了該被擋的地方。」
- 「資料庫連不上時會怎樣，我是先量的：boto3 預設花了 48 秒才報錯，因為它默默重試了十次。我改成 2 秒逾時、最多試兩次，同樣的情況變成 6.7 秒。預設值是為了盡量成功，不是為了快點告訴使用者失敗；閘道要自己決定等多久。」
- 「資料庫讀不到的時候我回 503，不是 401。那個人帶的可能是正確的 Key，只是我們沒辦法確認；回 401 會讓他以為自己的 Key 壞了。不確認就不放行，這是 fail-closed。」
- 「boto3 的錯誤有兩個家族：連不上，和連上了但對方說辦不到。我各寫一個測試，也實際把其中一個家族拿掉，看到對應的測試變紅。」

---

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `04202c3` | 14:31 | `feat: add hash_api_key for API key lookup` |
| `0ba5841` | 15:49 | `feat: add extract_bearer_token for the Authorization header` |
| `96278fd` | 16:40 | `feat: add find_user_id to look up active API keys` |
| `bcad448` | 18:18 | `feat: add the DynamoDB dependency and skipped authentication tests` |
| `8d90c4a` | 19:45 | `feat: require an API key on POST /v1/chat` |
| `9a0957e` | 20:29 | `feat: make the DynamoDB client give up quickly` |
| `87f6f7c` | 21:04 | `feat: return 503 when the key lookup cannot reach the database` |

每一筆 commit 前都以 `git status` 確認只有預期的檔案，破壞實驗已還原。

---

## 目前進度（2026-10-08 21:05）

- 開工前待辦 1 ✅（E76）；待辦 2（digest 複查）✅（E89）
- 步驟 1-1（Email）✅（E77，已推送）
- 步驟 1-2（手機）✅（E78，已推送）
- 10/5 老師回饋已記錄（E79）
- 步驟 1-3（身分證字號）✅（E80，已推送）
- 步驟 1-4（信用卡號與 Luhn）✅（E81，已推送）
- 步驟 1-5（跨第 50 字的邊界測試）✅（E82，已推送）
- 步驟 1-6（兩個去處都已遮罩）✅（E83，已推送）
- **步驟 1 全部完成**
- 期末簡報 v1 已記錄（E84），已推送（簡報 `8508164`；紀錄 `docs: record final presentation v1 evidence`，`8508164..b33144c`，10/6 02:08）
- 交接說明為 `docs/handoff/m2-step6-handoff.md`（接在 `m2-step5-part2-handoff.md`、 `m2-step5-handoff.md`、`m2-step3-handoff.md` 之後；後者的第 3、4、5、9、10 節仍有效）
- **步驟 2（個資類別進稽核）✅（E85，程式已推送 `53a4491`）；目前 `45 passed`**
- **步驟 3（`period_of()`：台北時間切月）✅（E86）；已推送 `249921d`**
- **步驟 4（`cost_micro_usd()`：最小成本函式）✅（E87，已推送 `3491977`）**
- **步驟 7 的純邏輯（超額回應五項定案、`is_over_quota()`、`seconds_until_next_period()`）✅（E88）。** 接線（429、`Retry-After`、503、稽核）尚未做
- **步驟 5（DynamoDB Local、boto3 連線、建表）✅（E89，程式已推送 `dac3d3c`）**
- **步驟 6（API Key 驗證：401、資料庫讀不到回 503、連線逾時設定）✅（E90，程式已推送 `87f6f7c`）；目前 `89 passed`（其中 16 個是 `integration`，要 `dynamodb-test` 容器開著）**
- 下一步：步驟 7 的接線（額度檢查、429、`Retry-After`、被擋的請求寫稽核）；開工前要先定「沒有額度紀錄的人怎麼處理」；下一筆是 E91
- 目標 10/10 結案；10/8 評估後，10/11 較為實際（仍在 W2 內）

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| ~~`python:3.12-slim` digest 複查（E74 的冷卻期例外）~~ | ✅ 10/7 完成：digest 仍存在且未變；未掃弱點（E89） | — |
| ~~API Key 從哪個標頭來；`api_keys` 要不要 `status` 欄位；Key 的格式與長度~~ | ✅ 10/8 定案：`Authorization: Bearer`、要 `status`、`gw_` 加 `token_hex(32)`（E90） | — |
| 這個人這個月沒有額度紀錄時，擋還是放（E89） | 與「資料庫讀不到」（503）是兩種情況；步驟 7 開工時定 | 步驟 7 |
| 既有 9 個 `test_chat` 測試怎麼提供**額度**（身分已定案：覆寫 `get_user_id`，E90） | 步驟 7 接線時定；傾向比照身分的做法，把額度檢查也做成可覆寫的相依 | 步驟 7 |
| `get_item` 要不要強一致讀取（`ConsistentRead=True`）（E90） | 雲端上剛停用的 Key 可能短暫仍可用；查證成本與延遲後定 | M4 前 |
| 每個請求新建一條 boto3 連線的成本（E90） | 步驟 12 量延遲與記憶體時評估是否改為重複使用 | 步驟 12 |
| 503 要不要附 `Retry-After`（E90） | D10 對供應商限流的 503 有附；資料庫故障的 503 尚未決定 | 步驟 7 |
| CI 怎麼跑 `integration` 測試（E89） | 預設在 CI 起 `dynamodb-test` 容器；不行才用 `-m "not integration"` | 10/12 那週 |
| M4 上雲時 `app/db.py` 怎麼表示連真的 AWS（不給網址、不帶假帳密，用 Fargate 的 IAM 角色）（E89） | 保留「沒講清楚要連哪裡就報錯」的性質 | M4 |
| 雲端 DynamoDB 的計費模式（E89） | 查證免費額度適用哪一種後定 | M4 |
| ~~超額回應的狀態碼、錯誤類型、是否附 `Retry-After`（決策書 12.5）~~ | ✅ 10/7 定案：429、固定字串、附 `Retry-After`（E88） | — |
| `Retry-After` 長達 31 天時，客戶端 SDK 的行為（E88） | 查 OpenAI SDK 等常見客戶端對很大的 `Retry-After` 怎麼處理；步驟 11 真實驗收時觀察一次 | 步驟 7 接線或步驟 11 |
| `pii_types` 在 DynamoDB 的型別（E85） | 預計用 List（要能存空值）；查證官方文件後定案 | 步驟 9 |
| 輸出 token 數是否已包含思考 token（E87） | 對照 OpenAI 官方文件與 `app/providers/openai_client.py`，確認 `cost_micro_usd()` 不會漏算或重複計算 | 步驟 8 |
| 沒有單價時的錯誤類型（E87） | 目前是通用的 `ValueError`；評估是否改為專用的錯誤類型，並把單價搬到設定檔 | M3 |
| 本人尚未回覆：決策書 11.1 的 6 分鐘配置、D33～D40 是否符合理解 | 10/4 開場已問一次，不再重複詢問 | 本人回覆時 |
| `protect-main` 加「CI 通過才能合併」、CodeQL | 沿用 M1 | 10/12 那週 |
| `/docs`、`/openapi.json` 是否關閉 | 沿用 M1 | M4 前 |
| `m1-gateway` 金鑰 11/2 到期後的接續 | 沿用 M1 | M4 前 |
| `m1-evidence-log.md` 與 M0 紀錄中對三張未存檔截圖的引用（E79 更正） | M2 結案整理文件時，把引用處改成「截圖未存檔」 | M2 結案 |
| M7 是否開工（E79） | 看三個時段的條件 | 10/16、10/30、11/1 |
| 簡報計時試講、用 PowerPoint 桌面版確認版面（E84） | 素材到齊前至少試講一次主影片 | 10/18 前 |
| M2 結案時更新簡報：主影片 04 面板 2（月額度 503 畫面） | 用步驟 11 的 S03 截圖與錄影，版號 +0.1 | M2 結案 |
