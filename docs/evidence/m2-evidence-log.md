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

## 目前進度（2026-10-04 20:24）

- 開工前待辦 1 ✅（E76）；待辦 2 待 10/5 05:50 之後執行
- 步驟 1-1（Email）✅（E77，已推送）
- 步驟 1-2（手機）✅（E78，待 commit）；目前 `24 passed`
- 下一步：步驟 1-3（身分證字號）

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| `python:3.12-slim` digest 複查（E74 的冷卻期例外） | 10/5 05:50（台北時間）滿 3 天後，確認 digest 仍可拉取；需先啟動 Docker Desktop，做完再關 | 10/5 開工時 |
| 送往 OpenAI 的內容是否經過 `mask()`（E77） | 看 `app/main.py`；補一個 `test_chat` 測試 | 步驟 1 的四類做完後 |
| 超額回應的狀態碼、錯誤類型、是否附 `Retry-After`（決策書 12.5） | 步驟 7 開工前列選項比較 | 步驟 7 |
| 個資類別怎麼從 `mask()` 帶到稽核紀錄 | 步驟 2 開工前列選項比較；`mask(text) -> str` 的介面先維持不變 | 步驟 2 |
| M2 的最小成本函式放哪裡、單價寫在哪 | 步驟 4 開工前決定；需與 D30（單價放 repo 設定檔）一致 | 步驟 4 |
| 本人尚未回覆：決策書 11.1 的 6 分鐘配置、D33～D40 是否符合理解 | 10/4 開場已問一次，不再重複詢問 | 本人回覆時 |
| `protect-main` 加「CI 通過才能合併」、CodeQL | 沿用 M1 | 10/12 那週 |
| `/docs`、`/openapi.json` 是否關閉 | 沿用 M1 | M4 前 |
| `m1-gateway` 金鑰 11/2 到期後的接續 | 沿用 M1 | M4 前 |
| 結案簡報時長 | 沿用 M1 | 與老師討論後 |
