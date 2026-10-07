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

## 目前進度（2026-10-07 14:55）

- 開工前待辦 1 ✅（E76）；待辦 2（digest 複查）已可執行，尚未做
- 步驟 1-1（Email）✅（E77，已推送）
- 步驟 1-2（手機）✅（E78，已推送）
- 10/5 老師回饋已記錄（E79）
- 步驟 1-3（身分證字號）✅（E80，已推送）
- 步驟 1-4（信用卡號與 Luhn）✅（E81，已推送）
- 步驟 1-5（跨第 50 字的邊界測試）✅（E82，已推送）
- 步驟 1-6（兩個去處都已遮罩）✅（E83，已推送）
- **步驟 1 全部完成**
- 期末簡報 v1 已記錄（E84），已推送（簡報 `8508164`；紀錄 `docs: record final presentation v1 evidence`，`8508164..b33144c`，10/6 02:08）
- 交接說明為 `docs/handoff/m2-step3-handoff.md`（取代 `m2-step2-handoff.md`）
- **步驟 2（個資類別進稽核）✅（E85，程式已推送 `53a4491`）；目前 `45 passed`**
- **步驟 3（`period_of()`：台北時間切月）✅（E86）；已推送 `249921d`**
- **步驟 4（`cost_micro_usd()`：最小成本函式）✅（E87）；目前 `55 passed`**
- 下一步：步驟 5（DynamoDB Local：docker-compose、boto3、建表）；步驟 6、7 中不需要資料庫的純邏輯（API Key 雜湊、額度判斷）可先做；下一筆是 E88
- 預計 10/10 結案（原訂 10/11）

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| `python:3.12-slim` digest 複查（E74 的冷卻期例外） | 10/5 05:50（台北時間）起已滿 3 天，尚未執行；步驟 5 開 Docker 時一併確認 digest 仍可拉取 | 步驟 5 |
| 超額回應的狀態碼、錯誤類型、是否附 `Retry-After`（決策書 12.5） | 步驟 7 開工前列選項比較 | 步驟 7 |
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
