# M3 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID；個人帳號名稱（含終端機提示字元與路徑中的使用者資料夾名稱，一律寫成 `<user>`）。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`（檔名以 `m3-` 開頭，正式清單照決策書 11.4 的 S 編號），日誌另存於 `docs/logs/`。
> E 編號接續 `m2-evidence-log.md`（E76～E93），M3 從 E94 開始。
> 紀錄日期：2026-10-10 建立（M2 於 10/9 結案，M3 原訂 10/12 那一週，提前開工）

---

## 紀錄規則（沿用 M2）

| # | 東西 | 規則 |
|---|---|---|
| 1 | 證據紀錄 | 本檔；每完成一組步驟就更新，回傳完整新版 |
| 2 | 里程碑報告 | 整關驗證通過後寫 `docs/milestones/m3-report.md`，格式同 M2；只向本人確認花費時間與實際花費 |
| 3 | 決策書 | M3 結案時出 v2.9；期間的新定案先記在本檔，待改項目列在本檔的「決策書 v2.9 待改項目」表 |
| 4 | 截圖、日誌、錄影 | 收到就改名、遮蔽、回傳；只截 11.4 清單（S05～S07）與出錯、決策、驗證的關鍵畫面；每個驗收條件錄一段，影片不進 repo |
| 5 | 存放 | 所有回傳的文字檔也存一份到 Project |
| 6 | 個資測試 | 只用假資料（假身分證字號、假手機、`example.com` 信箱、測試用卡號） |
| 7 | 收錄範圍 | 只收與專題本身有關的內容；不記本人的預測、不寫責任歸屬、不寫個人環境的事 |

---

## M3 步驟規劃（2026-10-10）

**原則（M2 結案報告第 4 節）：** 測試先存好、先看它紅，再寫功能；每個功能寫完跑全部測試、做破壞實驗；檢查「某件事沒發生」之前，先確認請求真的走到了該被擋的地方。

| # | 步驟 | 需要 Docker | 需要金鑰 | 對應驗收 |
|---|---|---|---|---|
| 1 | 設定檔 `app/config.toml` 與載入 `app/config.py`：先讀得進來，再加上啟動時的檢查 | 否 | 否 | — |
| 2 | 單價搬到設定檔：`cost_micro_usd()` 改讀設定、加入 `gpt-6-sol`；沒有單價時的錯誤類型 | 否 | 否 | S06 |
| 3 | 路由函式 `app/router.py`：字數、關鍵字、理由 | 否 | 否 | S05 |
| 4 | 接進 `chat_endpoint`：路由結果取代常數 `MODEL`；呼叫前確認查得到單價；輸出上限；稽核新欄位；假的模型能回報不同的模型名與 token 數 | 是 | 否 | S05、S06 |
| 5 | 降級：強模型被限流 → 便宜模型一次；便宜模型也限流 → 503 並附 `Retry-After`；供應商預算用完 → 不降級、503 | 是 | 否 | S07 |
| 6 | 思考 token 的實證：`gpt-6-sol` 的一次真實回應；順便定輸出上限的數字 | 否 | 是 | — |
| 7 | 20 題測試集：全部用強模型與智慧路由的成本比較（省下 X%）；調整 300 字與關鍵字 | 否 | 少數幾題 | S06 |
| 8 | CI：pytest（含起 DynamoDB Local 跑 `integration`）、tfsec、Trivy；`protect-main` 加「CI 通過才能合併」；評估 CodeQL | — | 否 | — |
| 9 | 真實驗收：S05、S06、S07，各錄一段 | 是 | 是 | 全部 |
| 10 | 結案：M3 結案報告、決策書 v2.9、簡報 v1.3（v1.2 已在 10/12 提前出，E99） | — | — | — |

**10/12 修訂（E101）：** 步驟 6 另用帶輸出上限的 `gpt-6-luna` 打一次；步驟 7 改為 20 題兩顆模型都真打一次；步驟 8 改為 pytest（`integration` 用 `compose.yaml` 起 DynamoDB Local）、Trivy 掃容器映像、CodeQL 預設設定，tfsec 不用，`protect-main` 的「CI 通過才能合併」等 CI 穩定後再加。

**為什麼從設定檔開始：** 單價、模型名稱、路由門檻都要從它讀，後面每一步都用得到；它是純讀檔的函式，不需要 Docker、資料庫或金鑰。

---

## E94. 開工前確認與五項定案（2026-10-10 11:04～11:11）

**依據：** 交接說明 `docs/handoff/m3-start-handoff.md` 第 2、3 節；決策書 v2.8 的 8.2（M3）、12.2（D8～D10）、12.5（待定項目）、7.10（預扣）、D30、D32、D37、D45。

**起點：** repo 最新 commit `55e5d82`（10/10 11:02，`docs: add decision book v2.8 and presentation deck v1.1`）；本人回報 `uv run pytest` 為 `119 passed`。Claude 的試跑環境（公開 repo 的副本，沒有 Docker）執行不需資料庫的部分：`74 passed, 45 deselected`，74 + 45 = 119，數目相符；45 個 `integration` 測試在這個環境沒有執行。

### 交接檔第 2 節：本人的回覆

| # | 事 | 回覆 | 後續 |
|---|---|---|---|
| 1 | 決策書 v2.8 是否讀過 | 讀過；沒有提出要修正的地方 | v2.8 視為定稿（E93 的限制第一項結案） |
| 2 | D34 要不要修訂 | 同意修訂 | 列入「決策書 v2.9 待改項目」第 1 項 |
| 3 | 簡報 v1.1 用 PowerPoint 桌面版確認 | 回覆「ok」，沒有提出要改的地方 | E84、E93 的同一項限制結案；計時試講仍未做 |
| 4 | Project 設定的版號 | Project 內已有 v2.8 決策書 | Project 的說明文字仍寫 `decision-book-v2.7.md`，但附有「有更新版以最新版為準」，讀取順序不受影響 |
| 5 | S02 的次數確認 | 稽核檔中 alice 成功的紀錄共 **10** 筆 | 見下方 |
| 6 | 四支影片改名、備份 | 已照 E92 的檔名命名並備份；不進 repo | — |

**第 5 項補上了 E93 的佐證。** E93 把 S02 更正為「成功 5 次、第 6 次被擋」，其中第 1、2 次是由已用量 444 推算的，當時沒有畫面。alice 走了兩輪（先不錄影走一遍、錄影一遍），每輪成功 5 次，合計 10 筆，與本次的計數一致。確認指令：

```
(sls 'alice.*"ok"' data\audit.jsonl).Count
```

- **這個指令的前提：** 稽核檔一行一筆，`user_id` 排在 `status` 前面；它是文字比對，不是解析欄位。訊息內容裡剛好出現 `alice` 與 `"ok"` 的紀錄也會被算進去（10/9 的訊息沒有這種情況）
- 交接說明原本列的是解析欄位的寫法（`ConvertFrom-Json` 後以 `Where-Object` 篩選），兩者預期的數字相同；這次執行的是上面較短的寫法

### 讀程式時看到、影響定案的兩件事（`55e5d82`）

| # | 現況 | 影響 |
|---|---|---|
| 1 | `chat_endpoint` 裡，`cost_micro_usd()` 排在模型回答**之後** | 模型沒有單價時，`ValueError` 發生在已經花錢之後，使用者拿到 500。M2 只有一顆模型而且寫死，所以走不到；M3 模型由路由決定，這條路就走得到 |
| 2 | `app/providers/openai_client.py` 的 `chat()` 只帶 `model`、`messages`、`reasoning_effort`，**沒有輸出上限** | 一次呼叫的成本沒有上限；超扣的幅度也就算不出上限 |

### 定案（五項，10/10 11:11 本人決定，全數照建議）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | 設定檔的格式與位置 | **TOML，一個檔，`app/config.toml`**；由 `app/config.py` 在啟動時讀一次。內容：兩顆模型的名稱、思考量、輸出上限、單價，加上路由的字數門檻與關鍵字。路由會用到的模型缺設定就拒絕啟動 | JSON：不能寫註解，單價旁邊無法註明單位與來源。YAML：要多裝一個套件，要過 D35 的冷卻期。放根目錄 `config/`：`.dockerignore` 是白名單、`Dockerfile` 只複製 `app`，兩個都要改 | 設定和程式包在同一個映像，改價要重建映像（與 D30「改價等於版本變更」一致）。容器內讀得到這個檔，要到步驟 4 之後實際建一次映像才確認 |
| 2 | 路由函式的輸入輸出與位置 | **新檔 `app/router.py`，純函式**；吃**遮罩後**的文字與路由規則，回傳一個小物件：`model`、`reasoning_effort`、`reason`（`length`、`keyword`、`default`） | 寫在 `main.py`：不能單獨測，20 題測試集也無法直接重複呼叫。只回模型名稱：思考量與理由要另外查。用原文判斷：原文多經過一個函式，而模型實際收到的是遮罩後的內容 | `len()` 把一個中文字與一個英文字母都算 1，300 個英文字母大約只有 50 個單字，中英文的門檻不一樣寬。遮罩會改變字數（10 碼手機變成 `[PHONE]` 7 個字）。`code` 會命中 `decode`。門檻與清單留到步驟 7 調整，規則的形式不變 |
| 3 | 成本用哪個名稱查單價、什麼時候查 | 用**實際拿到回答的那一次請求所指定的名稱**（沒降級是路由結果，降級了是便宜模型），沿用 D45。**路由一決定就先確認查得到單價，查不到就不呼叫模型。** 稽核的 `model` 記這個名稱，另加 `provider_model` 記 OpenAI 回報的 | 用回報的名稱：可能帶日期尾碼，查不到單價。維持現在的時機（回答之後才查）：沒有單價時錢已經花了 | 稽核 `model` 欄位的意思由「回報的」變成「指定的」，與 M2 的舊紀錄定義不同（M2 實際的值兩者相同，都是 `gpt-6-luna`） |
| 4 | 降級時稽核記什麼 | **一個請求仍然只有一筆。** 新欄位：`route_reason`、`routed_model`（路由原本選的）、`model`（實際回答並計費的）、`fallback`（走到呼叫模型的紀錄一定有，`true` 或 `false`）、`fallback_reason`（只有降級時有，只記錯誤類別名稱，同 D37）。兩顆都限流、或供應商預算用完時，`status` 為 `error` | 降級寫成兩筆：`audit` 表的主鍵是 `request_id`，會相撞；一個請求的成本也要跨筆加總。只記最後的模型：查不到曾經降級，S07 也拍不出來。記供應商的錯誤訊息：可能夾帶帳號資訊（D37） | 被額度擋下的紀錄沒有這幾欄，查詢時要知道哪些狀態才有。降級後使用者只能從回應的 `model` 看出來 |
| 5 | 預扣要不要趁 M3 做 | **M3 不做，留到 M5 一併決定。** M3 先在設定檔給每顆模型一個輸出上限（`max_completion_tokens`），讓一次最多超扣多少變成算得出來的數字；驗收時實測強模型的超扣 | M3 就做完整預扣：要改 M2 已驗收的流程（事前加 0 改成條件式預扣、失敗時退回、`test_chat_charge.py` 與 S02 的數字）；M5 扣款移交給 Worker 時還要重新設計一次；時程見下方。什麼都不做：一次呼叫的成本沒有上限 | 超扣會比 M2 明顯（見下方試算）。思考 token 也算在輸出上限裡，設太低回答會被截斷；數字要用 `gpt-6-sol` 的真實回應試（步驟 6） |

**第 5 項的試算（估算，尚未實測）：** `gpt-6-sol` 的單價是輸入 $2、輸出 $10 每百萬 token，也就是每個 token 2 與 10 micro-USD。一次 300 個輸入、500 個輸出 token 是 300 × 2 + 500 × 10 = 5,600 micro-USD。alice 的額度是 1,000；她在已用 999 時送出一個被路由到強模型的請求，檢查會放行，回來後已用量約 6,600，是額度的 6 倍多。M2 實測的超出幅度是 4%～12%（E92）。

**第 5 項的時程依據（Claude 的粗估，不是量測）：** M3 加 CI 約 20～22 小時；到 10/16（M7 第一個開工時段的條件）可投入約 25 小時；預扣含測試估 4～6 小時。

**生活比喻（第 5 項）：** 加油站的預授權刷卡機先不裝，但先把油槍設成一次最多加 50 公升。車主還是可能加超過卡裡的錢，但最多超過多少是算得出來的。

### 留到做到那一步才定的事

| 項目 | 何時定 |
|---|---|
| 沒有單價時的錯誤類型，以及對使用者的回應（決策書 12.5） | 步驟 2、步驟 4 |
| 輸出上限的數字（設定檔目前的值是暫定） | 步驟 6 |
| 怎麼分辨供應商的兩種 429（限流、預算用完） | 步驟 5 |
| 兩顆都限流時 `Retry-After` 的值 | 步驟 5 |
| SDK 自己的重試（目前 1 次）與降級疊加時，一個請求最多呼叫幾次 | 步驟 5 |
| 300 字與關鍵字清單；中英文字數的算法 | 步驟 7 |

### 限制（誠實記錄）

- **五項定案都還沒有實作。** 這一筆只有決定與理由，沒有程式與測試
- 時程的小時數是粗估，沒有依據量測；第 5 項的 5,600 是用假設的 token 數算的，不是實測
- `max_completion_tokens` 在目前鎖定的 OpenAI SDK 版本、對這兩顆推理模型的實際行為（思考 token 是否計入、被截斷時回應長什麼樣子）還沒有驗證，步驟 6 用真實回應確認
- Claude 的試跑環境沒有 Docker，45 個 `integration` 測試在本人的環境才有執行
- 交接檔第 2 節第 1、3 項只有本人的回覆，沒有逐頁的檢查紀錄；簡報仍未計時試講

### 面試可用的說法

- 「開工前我先讀自己上一關的程式，發現算成本的那一行排在模型回答之後。上一關只有一顆模型所以沒事；這一關模型由路由決定，沒設單價的模型會在花了錢之後才出錯。所以我把查單價的時機往前移到呼叫之前。」
- 「預扣我這一關決定不做。它要動到已經驗收的扣款流程，而且下一步扣款會移交給背景的 Worker，現在做有一部分要重來。我先加輸出上限，讓最多超扣多少變成算得出來的數字，並且把強模型下超扣會變大這件事寫進限制。」

---

## E95. 步驟 1：設定檔 `app/config.toml`，讀進來並檢查（2026-10-10 11:15～12:34）

**依據：** E94 定案 1；決策書 D8（規則、模型 ID、單價、思考量都放設定檔）、D28（兩顆模型與思考量）、D30（單價放 repo；沒有單價的模型拒絕）；E23（價格表缺模型時預算安靜失效）、E24（單價少一個 0 就差 10 倍）。

**範圍：** 把設定檔讀成物件，並在讀進來的當下檢查。**Gateway 還沒有用到它**：`main.py` 這一步沒有動，單價仍是 `app/pricing.py` 裡的字典常數，接線在步驟 2。

**生活比喻：** 價目表印成一張貼在牆上，不寫死在收銀機裡；開店前店長先把價目表看過一遍，有一格空白或寫錯就不開門。

### 設定檔的結構

```toml
[routing]
cheap_model = "gpt-6-luna"
strong_model = "gpt-6-sol"
min_chars = 300
keywords = ["分析", "比較", "評估", "設計", "架構", "程式碼", "除錯", "code", "debug"]

[models.gpt-6-luna]
reasoning_effort = "none"
max_completion_tokens = 1000
input_price = 100_000
output_price = 500_000

[models.gpt-6-sol]
reasoning_effort = "low"
max_completion_tokens = 2000
input_price = 2_000_000
output_price = 10_000_000
```

- **路由規則與模型設定分成兩區：** `[routing]` 只寫「用哪兩顆」，每顆模型的設定放在 `[models.名稱]`。這樣「路由指到一顆沒有設定的模型」才是一種檢查得出來的狀態；成本也可以直接用模型名稱查
- 單價的單位沿用 E87：每一百萬個 token 多少 micro-USD，全程整數
- **`max_completion_tokens` 的兩個數字是暫定的**（E94 定案 5），步驟 6 用真實回應試過再調
- 讀進來之後是字典裡再放字典，與 M2 的 `PRICES` 同一種形狀

### 做法：分兩段，先存測試、看它紅，再寫功能

| 段 | 內容 | 結果 |
|---|---|---|
| 前半 1 | 存 `tests/test_config.py`（5 個）與 `app/config.toml` | `1 error during collection`（`app/config.py` 還不存在） |
| 前半 2 | 寫 `load_config()`（填空版，7 格） | `5 failed, 119 passed`（挫折 1）→ `124 passed` |
| 前半 3 | 三個破壞實驗 | 見下表；還原後 `5 passed` |
| 後半 1 | 存新的 `tests/test_config.py`（多 9 個） | `1 error during collection`（`ConfigError` 還不存在） |
| 後半 2 | 寫 `ConfigError`、`require_positive_int()`、`check_config()`，`load_config()` 加上 `try` 與檢查（填空版，9 格） | `3 failed, 130 passed`（挫折 2、3）→ `133 passed` |
| 後半 3 | 四個破壞實驗 | 見下表；還原後 `14 passed` |

### 新觀念

| 觀念 | 白話 | 生活比喻 |
|---|---|---|
| TOML 的 `[models.gpt-6-luna]` | 讀進來是字典裡再放字典 | 文件櫃：`models` 是抽屜，`gpt-6-luna` 是裡面的一個資料夾 |
| `Path(__file__).parent` | 這個程式檔自己所在的資料夾 | 食譜上寫「醬料在這本食譜旁邊」，書架搬到別的房間也找得到 |
| `open(path, "rb")` | 以二進位讀取；`tomllib` 規定要這樣，由它自己照 UTF-8 解讀 | — |
| `字典.items()` | 一次交出「名稱、內容」兩樣，`for` 用兩個名字接 | 翻資料夾：每翻一個，同時看到標籤和裡面的文件 |
| `class ConfigError(Exception)` | 自己取名字的錯誤 | 退貨單上蓋「設定問題」的章，一看就知道不是程式壞了 |
| `type(value) is not int` | 這個值不是整數（`0.1` 是小數） | 投幣機只收硬幣，紙鈔直接退 |
| `文字.strip()` | 去掉頭尾的空白 | 把信封兩端多出來的空白邊裁掉 |
| `pytest.raises(錯誤, match="…")` | 除了要報錯，訊息還要含這幾個字 | 警報響了還要看面板亮的是哪一區 |

**為什麼用 `"rb"`：** Windows 的預設文字編碼不是 UTF-8，設定檔裡有中文的關鍵字與註解；交給 `tomllib` 自己解讀，結果就不受作業系統影響。

### 本人撰寫（`app/config.py`，`7cb56ed` 的版本；三個資料類別從略）

```python
# 設定檔有問題時丟這個錯誤：一看就知道是設定的問題，不是程式壞了
class ConfigError(Exception):
    """The config file is missing a setting or holds a value that cannot be used."""


# 單價、上限、門檻都要是大於 0 的整數：寫成小數或 0，成本會算錯，甚至變成免費
def require_positive_int(value, name: str) -> None:
    """Raise ConfigError unless the value is a whole number above zero."""
    if type(value) is not int or value <= 0:
        raise ConfigError(f"{name} must be a whole number above zero")


# 讀進來就檢查：設定有問題寧可起不來，也不要帶著錯的設定開始收錢
def check_config(config: GatewayConfig) -> None:
    """Raise ConfigError when the settings cannot be used safely."""
    routing = config.routing

    # 路由會選到的兩顆模型都要有設定，否則會選到一顆不知道多少錢的模型
    for model in [routing.cheap_model, routing.strong_model]:
        if model not in config.models:
            raise ConfigError(f"Routing uses a model with no settings: {model}")

    require_positive_int(routing.min_chars, "routing.min_chars")
    for name, model in config.models.items():
        require_positive_int(model.max_completion_tokens, f"{name}.max_completion_tokens")
        require_positive_int(model.input_price, f"{name}.input_price")
        require_positive_int(model.output_price, f"{name}.output_price")

    # 空白的關鍵字「出現在」每一句話裡：混進清單，所有請求都會被送去強模型
    for keyword in routing.keywords:
        if keyword.strip() == "":
            raise ConfigError("routing.keywords must not contain a blank keyword")


# 把設定檔讀成上面三種物件
def load_config(path: Path) -> GatewayConfig:
    """Read the TOML file at path and return the settings."""
    with open(path, "rb") as file:
        data = tomllib.load(file)

    try:
        routing = RoutingConfig(
            cheap_model=data["routing"]["cheap_model"],
            strong_model=data["routing"]["strong_model"],
            min_chars=data["routing"]["min_chars"],
            keywords=data["routing"]["keywords"],
        )

        models = {}
        for name, fields in data["models"].items():
            models[name] = ModelConfig(
                reasoning_effort=fields["reasoning_effort"],
                max_completion_tokens=fields["max_completion_tokens"],
                input_price=fields["input_price"],
                output_price=fields["output_price"],
            )
    except KeyError as exc:
        raise ConfigError(f"Missing setting: {exc}")

    config = GatewayConfig(routing=routing, models=models)
    check_config(config)

    return  config
```

**檢查寫在 `load_config()` 裡面：** 拿得到設定的人，拿到的一定是檢查過的；不靠每個呼叫的地方記得再檢查一次。與 M2 把驗證寫成相依（E90）是同一個想法。

**為什麼要擋空白的關鍵字：** Python 認為空字串出現在任何字串裡（`"" in "hello"` 是 `True`）。它混進清單的話，所有請求都會被判定為「含關鍵字」而送去強模型，成本是 20 倍，而且沒有任何錯誤。

### 測試（Claude 整份提供，`tests/test_config.py`，14 個；測試數 119 → 133）

用一份測試專用的設定（每個數字都不同：44、111、222、333、444、555、666），欄位拿反時答案才會不同；另外兩個測試讀正式的設定檔。

| 測試 | 檢查 | 在守什麼 |
|---|---|---|
| `test_load_config_reads_routing_rules` | 路由規則的四個欄位 | 欄位各自放對位置；關鍵字含中文，確認是照 UTF-8 讀的 |
| `test_load_config_reads_model_fields` | 一顆模型的四個欄位 | 輸入與輸出單價不能拿反 |
| `test_load_config_reads_every_model` | 兩顆都讀到，各拿各的設定 | 不能全部變成同一顆 |
| `test_shipped_config_has_decision_book_prices` | 正式設定檔的四個單價等於決策書的數字 | 設定檔少打一個 0，要有另一個地方對得出來 |
| `test_shipped_config_sets_models_and_reasoning_effort` | 正式設定檔的兩顆模型名稱與思考量 | 沒設思考量時 OpenAI 會用預設值，暗中多花錢（D28） |
| `…_rejects_strong_model_without_settings` | 路由的強模型沒有設定 → `ConfigError`，訊息含模型名稱 | 不會選到不知道多少錢的模型 |
| `…_rejects_cheap_model_without_settings` | 便宜模型沒有設定 | 兩顆都要檢查，不能只查一顆 |
| `…_rejects_price_written_as_decimal` | 單價寫成 `0.1` | 把 micro-USD 寫成美元 |
| `…_rejects_zero_price` | 單價是 0 | 單價 0 等於這顆模型免費 |
| `…_rejects_zero_output_cap` | 輸出上限是 0 | 模型一個字都不能回 |
| `…_rejects_zero_min_chars` | 字數門檻是 0 | 每一句話都達到門檻，全部送去強模型 |
| `…_rejects_empty_keyword` | 關鍵字清單裡有空字串 | 所有請求都會命中 |
| `…_rejects_blank_keyword` | 關鍵字只有空格 | 幾乎每一句英文都有空格 |
| `…_rejects_missing_setting` | 少了一個欄位 | 當成設定錯誤，並說出少的是哪一個 |

（後九個的名稱開頭皆為 `test_load_config`。）

**單價在測試裡再寫一次是故意的。** 設定檔少打一個 0，程式不會報錯；測試裡獨立寫著決策書的數字，兩邊對不起來才抓得到。代價：之後改價要同時改設定檔與這個測試。

**九個「要拒絕」的測試都用 `match` 對訊息。** 只檢查「有報錯」的話，設定被別的檢查碰巧擋下也會通過（M2 結案報告第 4 節的同一件事）。

### 破壞實驗（本人執行，共七個；每個做完立刻改回）

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| 前半 A | `input_price` 與 `output_price` 等號右邊對調 | `3 failed, 2 passed` | `ModelConfig(r...put_price=111) == ModelConfig(r...put_price=222)`、`assert 555 == 444`、`assert 500000 == 100000` |
| 前半 B | `strong_model` 那一行改成拿 `cheap_model` | `2 failed, 3 passed` | `RoutingConfig…` 不相等、`assert 'gpt-6-luna' == 'gpt-6-sol'` |
| 前半 C | `config.toml` 裡 Sol 的 `input_price` 改成 `200_000` | `1 failed, 4 passed` | `assert 200000 == 2000000` |
| 後半 A | `value <= 0` 改成 `value < 0` | `3 failed, 11 passed` | 單價 0、輸出上限 0、字數門檻 0，都是 `DID NOT RAISE ConfigError` |
| 後半 B | 拿掉 `type(value) is not int or` | `1 failed, 13 passed` | 單價寫成小數：`DID NOT RAISE ConfigError` |
| 後半 C | `for model in […]` 只留強模型 | `1 failed, 13 passed` | 便宜模型沒有設定：`DID NOT RAISE ConfigError` |
| 後半 D | 拿掉 `.strip()` | `1 failed, 13 passed` | 只有空格的關鍵字：`DID NOT RAISE ConfigError` |

**判讀：**

- **前半 C：** 設定檔少一個 0，五個測試只紅一個，就是把單價再寫一次的那一個。少了它，強模型會被便宜 10 倍地計費，其餘測試全部通過
- **前半 A：** 兩個單價拿反時，Luna 的輸入會以輸出的單價（5 倍）計費。測試資料的兩個單價不同才看得出來（E86、E87 學到的做法）
- **後半 A：** `<` 與 `<=` 只差在 0。寫成 `<` 時，單價 0 的模型會通過檢查，等於免費
- **後半 B：** `0.1` 大於 0，只檢查大小的話會通過；之後 `cost_micro_usd()` 的整數除法與取餘數就會出現小數
- **後半 D：** 空字串與只有空格是兩個不同的測試；拿掉 `.strip()` 只有後者變紅

### 挫折 1：`tomllib.loads(file)`，多一個 `s`

```
app\config.py:43: in load_config
    data = tomllib.loads(file)
…
    def loads(s: str, /, *, parse_float: ParseFloat = float) -> dict[str, Any]:
        """Parse TOML from a string."""
>       src = s.replace("\r\n", "\n")
E       AttributeError: '_io.BufferedReader' object has no attribute 'replace'
5 failed, 119 passed
```

- **原因：** `tomllib.load()` 收開好的檔案，`tomllib.loads()` 收一段文字（`s` 是 string）。交出去的是檔案，卻呼叫了收文字的那一個
- **怎麼讀：** 最下面 `E` 那行說「這個東西是一個開著的檔案，它沒有 `replace`」；往上第一個落在自己檔案的是 `app\config.py:43`。中間的 `def loads(s: str, …)` 與它的說明也寫著它要的是文字
- **生活比喻：** `load` 是把整份文件交給櫃檯，`loads` 是把內容念給櫃檯聽
- 七格填對六格，改掉一個字母後 `124 passed`
- 五個測試全紅、訊息相同、都停在同一行，那一行之後的程式還沒有被走到（E88 學到的），所以這次的紅不算看過斷言失敗；斷言的紅由前半的三個破壞實驗補上
- `json` 模組也是同樣的命名（`json.load`、`json.loads`）

### 挫折 2：三行檢查的都是同一個欄位

```python
require_postive_int(model.max_completion_tokens, f"{name}.max_completion_tokens")
require_postive_int(model.max_completion_tokens, f"{name}.input_price")
require_postive_int(model.max_completion_tokens, f"{name}.output_price")
```

```
FAILED …::test_load_config_rejects_price_written_as_decimal - Failed: DID NOT RAISE ConfigError
FAILED …::test_load_config_rejects_zero_price - Failed: DID NOT RAISE ConfigError
```

- **原因：** 第二、三行是照第一行改的，只改了後面的名字，沒改前面實際拿去檢查的值。輸出上限被檢查了三次，兩個單價一次都沒檢查
- **這個錯不會自己露出來：** 程式不會當掉，正式的設定檔也照樣讀得進來；只有「單價寫成小數」與「單價是 0」這兩個測試會紅
- **生活比喻：** 保全巡三個房間，簽到表上三間都打勾，實際上三次都走進同一間
- 與 E89 挫折 4（三段 `create_table` 照第一段改，`api_keys` 留著 `user_id`）同類：照上一行改的時候，每一格都要換

### 挫折 3：`except` 接錯了錯誤種類

```
FAILED …::test_load_config_rejects_missing_setting - KeyError: 'output_price'
```

- **原因：** 寫成 `except AttributeError`。少欄位時字典丟的是 `KeyError`；`except` 只接指定的那一種，接錯就等於沒接
- **兩種錯誤的差別：** 跟字典要一個它沒有的欄位（中括號）是 `KeyError`；跟物件要一個它沒有的屬性或功能（點）是 `AttributeError`。挫折 1 是後者，這裡是前者
- 失敗訊息本身就寫出實際丟出來的是哪一種

改正挫折 2、3 之後 `133 passed`。這兩次也等於多做了兩個破壞實驗：單價沒被檢查時紅兩個、`except` 接錯時紅一個，訊息都直接指到原因。

### 測試抓不到、讀程式才看到的

| # | 內容 | 為什麼沒有自己露出來 | 處理 |
|---|---|---|---|
| 1 | 函式名稱打成 `require_postive_int`（少一個 `i`） | 定義與四個呼叫的地方少的是同一個字母，程式照跑；測試沒有直接用到這個名稱 | 推送前改為 `require_positive_int` |
| 2 | `git status` 出現 `docs/slides/~$llm-gateway-slides-v1.1.pptx` | 簡報開著時 PowerPoint 產生的鎖定檔，`git add .` 會把它一起加進去 | 這次照檔名逐一加入；`.gitignore` 加上 `~$*`（`648e90b`） |

- 第 2 項：這種鎖定檔通常帶有 Office 的使用者名稱，repo 是公開的。推送後以 `git ls-tree` 確認遠端沒有任何 `~$` 開頭的檔
- **學到的：** 測試是綠的，不代表名稱沒打錯；公開 repo 的名稱與 commit 訊息一樣，推上去之前要讀一遍（E87 挫折 1 的同一件事）

### Claude 在試跑環境做過、本人沒有重做的實驗

測試檔交出去之前，在公開 repo 的副本上以參考寫法試跑並破壞過（Linux、Python 3.12；碰資料庫的測試以替身伺服器代替 DynamoDB Local）：

| 改了什麼 | 結果 |
|---|---|
| 以文字模式開檔（`"r"`） | 全部失敗：`TypeError: File must be opened in binary mode` |
| 設定檔開頭加上 BOM | `tomllib.TOMLDecodeError: Invalid statement (at line 1, column 1)` |
| 設定檔的換行改成 CRLF | 全部通過 |
| 每顆模型都拿同一顆的思考量 | 「每顆模型」那個測試失敗：`assert 'none' == 'low'` |
| 正式設定檔的思考量改掉 | 「模型名稱與思考量」那個測試失敗 |
| 拿掉 `check_config(config)` 這一行 | 8 個失敗（九個「要拒絕」的測試裡，除了少欄位的那一個） |
| `keyword.strip() == ""` 少了括號 | 2 個失敗（空字串、只有空格）；程式不會報錯，只是永遠不成立 |

推送後在同一個環境執行 `7cb56ed`：`133 passed`。

### 限制（誠實記錄）

- **Gateway 還沒有用到這份設定。** `load_config()` 目前只有測試在呼叫；「設定有問題就拒絕啟動」要到步驟 2 把它接進 `main.py` 才成立
- **容器裡讀不讀得到 `app/config.toml` 還沒有驗證。** 依據只有 `Dockerfile` 的 `COPY app ./app` 與 `.dockerignore` 的白名單；接線後實際建一次映像才算數
- **有兩個「要拒絕」的測試，本人沒有看過它們為了預期的原因而紅：** 強模型沒有設定、關鍵字是空字串。只有 Claude 的試跑環境看過（上表「拿掉 `check_config`」那一項）
- 沒有檢查的事：`reasoning_effort` 的值是否合法；便宜模型與強模型是不是同一顆；`[models]` 底下多出來、沒被路由用到的模型；設定檔裡多出來的欄位（打錯字的欄位會因為「少了正確的那一個」而被擋下，單純多出來的不會）
- 關鍵字若不是文字（例如寫成數字），`.strip()` 會丟 `AttributeError`，不是 `ConfigError`；TOML 語法錯誤丟的是 `tomllib.TOMLDecodeError`。兩種都會讓讀取失敗，只是錯誤類型不是 `ConfigError`
- 單價寫成 `true` 這類布林值，照 `type(value) is not int` 會被擋下，但沒有測試
- 輸出上限的兩個數字是暫定的；`min_chars` 與關鍵字清單照 D8，步驟 7 才調整，所以正式設定檔的這三項沒有測試固定它們
- 設定檔的單價是手動抄的，OpenAI 改價時不會自動更新（E87 的同一項限制）；測試固定的是「等於決策書的數字」，不是「等於 OpenAI 現在的價格」
- BOM 與文字模式的行為只在 Linux 的試跑環境看過

### 面試可用的說法

- 「單價和路由規則我放在 repo 裡的一個設定檔，啟動時讀進來就檢查：路由指到的模型沒有設定、單價寫成小數或 0、關鍵字清單裡混進空字串，都直接拒絕。空字串那一項是因為它出現在任何句子裡，混進去的話所有請求都會被送去貴 20 倍的模型，而且不會有任何錯誤。」
- 「正式設定檔的單價，我在測試裡又寫了一次。我做過實驗：把設定檔的單價少打一個 0，其他測試全部通過，只有這一個會紅。價格資料打錯不會讓程式當掉，要靠另一個獨立的地方對帳。」
- 「檢查函式我一開始把三行寫成檢查同一個欄位，只有後面的名字不同。程式照跑、正式設定也讀得進來，是『單價是 0』和『單價寫成小數』這兩個測試把它抓出來的。所以每個『要拒絕』的測試我都對訊息內容，確認它是為了那一項被擋下。」

---

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `648e90b` | 10/10 11:57 | `chore: ignore Office lock files` |
| `d0b866d` | 11:59 | `feat: add the gateway config file and its loader` |
| `633890f` | 11:59 | `docs: start the M3 evidence log`（`55e5d82..633890f`） |
| `7cb56ed` | 12:34 | `feat: check the gateway config when it is loaded`（`633890f..7cb56ed`） |

推送後由 Claude 讀取公開 repo 核對：`tests/test_config.py`、`app/config.toml` 與交付的版本相同（測試檔只差結尾的換行）；變更的檔案只有 `.gitignore`、`app/config.py`、`app/config.toml`、`tests/test_config.py`、`docs/evidence/m3-evidence-log.md`。

---

## E96. 步驟 2：單價改讀設定檔，查設定移到呼叫模型之前（2026-10-10 12:40～13:10）

**依據：** E94 定案 3（成本用哪個名稱查單價、什麼時候查）；E94「讀程式時看到的兩件事」第 1 項；決策書 D30（沒有單價的模型拒絕呼叫）、D45（用程式指定的名稱查單價）；E87（M2 的最小成本函式）；E95（設定檔）。

**範圍：** `app/pricing.py` 不再自己留一份價目表，改從設定拿單價，並加入 `gpt-6-sol`；`main.py` 啟動時讀設定檔，查模型設定的動作移到呼叫模型之前。**路由還沒有做：** `main.py` 的模型仍是常數 `MODEL`（`gpt-6-luna`）。

### 做法：查設定和算錢拆成兩個函式

| 函式 | 做什麼 | 什麼時候 |
|---|---|---|
| `find_model_config(models, model)` | 用名稱查這顆模型的設定（含單價）；查不到丟 `ModelNotConfiguredError` | 呼叫模型**之前** |
| `cost_micro_usd(settings, input_tokens, output_tokens)` | 照查到的設定算錢，不再自己查 | 模型回答之後 |

M2 的 `cost_micro_usd(model, …)` 是「用名稱查單價、接著算」，而且排在模型回答之後，查不到時錢已經花了。拆開之後，算錢那一步手上已經有設定，**模型回答之後不會再因為查不到單價而出錯**；這是由函式的形狀保證的，不是靠呼叫順序記得排對。

**生活比喻：** 搭計程車，上車前先確認這台車有費率表，沒有就不上車；下車時照表算，不會到了目的地才發現沒有表。

**錯誤類型定案（決策書 12.5、E87 的待決）：** 專用的 `ModelNotConfiguredError`，取代 M2 通用的 `ValueError`。查不到時**對使用者回什麼**還沒有定（見待決）。

### 本人撰寫（`app/pricing.py`，`8907063` 的版本，整份）

```python
from app.config import ModelConfig

# 一百萬：單價是以「每一百萬個 token」報價的
MILLION = 1_000_000


# 要用一顆沒有設定（也就沒有單價）的模型時丟這個錯誤
class ModelNotConfiguredError(Exception):
    """The model has no settings, so its price is unknown."""


# 呼叫模型之前先查它的設定：查不到就不該呼叫，「不知道多少錢」不能當成「不用錢」
def find_model_config(models: dict[str, ModelConfig], model: str) -> ModelConfig:
    """Return the settings for the model, or raise when it has none."""
    if model not in models:
        raise ModelNotConfiguredError(f"No settings for model: {model}")
    return models[model]


# 金額全程用整數算，避免小數誤差；額度就是靠這個數字扣的
def cost_micro_usd(settings: ModelConfig, input_tokens: int, output_tokens: int) -> int:
    """Return the cost of one call in micro-USD, rounded up to a whole number."""
    total = input_tokens * settings.input_price + output_tokens * settings.output_price
    result = total // MILLION
    if total % MILLION != 0:
        result = result + 1
    return result
```

`app/main.py` 改三處：

```python
from app.config import CONFIG_PATH, load_config
from app.pricing import cost_micro_usd, find_model_config
```

```python
# 啟動時就把設定讀進來並檢查：設定有問題，Gateway 直接起不來
CONFIG = load_config(CONFIG_PATH)
```

```python
    # 呼叫模型之前先查到這顆模型的設定（含單價）：查不到就不呼叫
    settings = find_model_config(CONFIG.models, MODEL)
    …
    cost = cost_micro_usd(settings, result.input_tokens, result.output_tokens)
```

查設定的那一行排在「對當月已用量加 0」之後、呼叫模型之前。

### 測試（Claude 整份提供，`tests/test_pricing.py`，8 個取代 M2 的 4 個；測試數 133 → 137）

| 測試 | 檢查 | 在守什麼 |
|---|---|---|
| `test_cost_uses_input_and_output_prices` | Luna，2,000,000 / 1,000,000 → `700_000` | 兩個單價各用在對的地方；沒有零頭不能多收（沿用 E87） |
| `test_cost_rounds_up_to_whole_micro_usd` | Luna，13 / 11 → `7` | D30 的例子（沿用 E87） |
| `test_cost_charges_at_least_one_for_tiny_usage` | Luna，1 / 0 → `1` | 再小也要收 1（沿用 E87） |
| `test_cost_uses_the_prices_of_the_given_model` | Sol，13 / 11 → `136` | 用的是交進來的那顆模型的單價 |
| `test_find_model_config_returns_the_named_model` | 查 Sol 拿到 Sol、查 Luna 拿到 Luna | 拿到的是指定的那一顆 |
| `test_find_model_config_rejects_model_without_settings` | 查 `gpt-6-astra` → `ModelNotConfiguredError`，訊息含模型名稱 | 沒有設定不能當成 0 元 |
| `test_shipped_config_gives_decision_book_costs` | 正式設定檔：查設定、算成本，Luna `7`、Sol `136` | 從設定檔到金額整條路 |
| `test_pricing_module_keeps_no_price_table_of_its_own` | `app.pricing` 沒有 `PRICES` | 單價只有一個來源 |

**136 的算法：** 13 × 2 + 11 × 10 = 136 micro-USD（Sol 每個輸入 token 2、輸出 10 micro-USD）。同樣的 token 數，Luna 是 6.8、進位成 7；兩顆的單價剛好差 20 倍。

### 破壞實驗（本人執行，四個；每個做完立刻改回）

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| A | `settings.input_price` 與 `settings.output_price` 對調 | `4 failed, 4 passed` | `assert 1100000 == 700000`、`assert 8 == 7`、`assert 152 == 136`、`assert 8 == 7` |
| B | `find_model_config` 固定交回 `"gpt-6-luna"` 這個名稱 | `2 failed, 6 passed` | `assert 'gpt-6-luna' == ModelConfig(reasoning_effort='low', …)`、`AttributeError: 'str' object has no attribute 'input_price'` |
| C | `main.py` 查設定時把 `MODEL` 改成 `"gpt-6-sol"` | `5 failed, 132 passed` | `assert 236 == (100 + 7)`、`assert 136 == 7`（三個）、`assert 429 == 200` |
| D | `config.toml` 的 `strong_model` 改成 `"gpt-6-xxx"`，再匯入 `app.main` | 匯入失敗 | 見下方 |

**判讀：**

- **實驗 C：** 呼叫的是 Luna、查的卻是 Sol 的單價，一次呼叫從 7 變成 136。紅的五個都在 `tests/test_chat_charge.py`：已用量多扣（100 變成 236）、稽核記的成本不對、額度 14 的人第二次就被擋下（`429 == 200`）。**呼叫的模型和計費的模型要是同一顆**，這正是 E94 定案 3 在守的事；步驟 4 接上路由與降級之後，這兩個名稱會來自同一個變數
- **實驗 A：** 極小用量那個測試沒有紅（1 個 token 用哪個單價都不到 1 micro-USD），與 E87 的觀察相同
- **實驗 B：** 交回去的不是設定物件。第二個失敗的 `AttributeError` 就是 M2 那種「查到的東西不能拿來算錢」的樣子

**實驗 D：設定有問題時 Gateway 起不來（E94 定案 1 第一次真的發生）**

```
PS C:\Users\<user>\llm-gateway> uv run python -c "import app.main"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "C:\Users\<user>\llm-gateway\app\main.py", line 27, in <module>
    CONFIG = load_config(CONFIG_PATH)
  File "C:\Users\<user>\llm-gateway\app\config.py", line 99, in load_config
    check_config(config)
  File "C:\Users\<user>\llm-gateway\app\config.py", line 59, in check_config
    raise ConfigError(f"Routing uses a model with no settings: {model}")
app.config.ConfigError: Routing uses a model with no settings: gpt-6-xxx
```

- `main.py` 第 27 行在模組一被讀進來時就執行；uvicorn 啟動時做的第一件事就是讀進 `app.main`，所以設定有問題時服務不會開始收請求
- 訊息說出是哪一顆模型沒有設定
- 還原後 `git status` 沒有 `app/config.toml`，確認已改回

### 挫折：`return ModelConfig(models)`

`find_model_config` 的最後一行第一版寫成 `return ModelConfig(models)`。

- **原因：** `ModelConfig(…)`（圓括號）是「做一個新的設定物件」，而且只給了一格，另外三格沒給；這裡要的是從字典裡把已經有的那一個拿出來，`models[model]`（中括號）
- **生活比喻：** 要的是把標籤寫著 `gpt-6-sol` 的資料夾從抽屜抽出來，不是拿整個抽屜去做一份新的
- Claude 在試跑環境重現這個寫法：只跑 `tests/test_pricing.py` 是 `2 failed, 6 passed`，訊息為 `TypeError: ModelConfig.__init__() missing 3 required positional arguments: 'max_completion_tokens', 'input_price', and 'output_price'`；跑全部是 `21 failed, 116 passed`（每個走到查設定那一行的請求都失敗）
- 改正後 `137 passed`
- 與 E91 的兩次括號問題同類（該不該加括號、用哪一種括號）：圓括號是「做」或「呼叫」，中括號是「拿」

### 這一步的順序與規劃不同（Claude 的問題，照實記錄）

規劃的順序是「存新測試 → 看它紅 → 只改 `pricing.py` → 跑全部看到 17 個紅 → 改 `main.py`」。實際上兩個檔都先改好了，新的測試檔後來才存：

- 第一次執行時 `tests/test_pricing.py` 還是 M2 的舊檔，得到 `4 failed`，都是 `AttributeError: 'str' object has no attribute 'input_price'`（舊測試還在把模型名稱交給已經改成收設定物件的函式）
- **原因：** Claude 把「順序」放在訊息的最後面，填空的程式放在前面；照著前面的內容改完，才會讀到順序
- **後果：** 新的 8 個測試沒有看過「功能還沒寫」時的紅；改以上面四個破壞實驗確認它們會為了預期的原因而紅
- **之後的做法：** 每一步的訊息把「順序」放在最前面，填空與提示放在後面

### 限制（誠實記錄）

- **查不到模型設定時，目前沒有處理：** `find_model_config` 丟出的錯誤會直接變成框架預設的 500，這個請求不會留下稽核紀錄。正常情況下走不到（常數 `MODEL` 在設定檔裡），對使用者回什麼、要不要寫稽核，還沒有定案
- **「查不到就不呼叫模型」這條路沒有測試。** 設定是在 `main.py` 讀進來時就固定的，測試換不掉它，所以沒辦法在測試裡給一份缺模型的設定；要等設定也做成領用窗口
- **設定檔裡的 `reasoning_effort` 與 `max_completion_tokens` 還沒有被用到：** 呼叫模型時用的仍是常數 `REASONING_EFFORT`，輸出上限還沒有帶給 OpenAI
- 模型仍是常數 `MODEL`；`gpt-6-sol` 的單價目前只有測試在用
- 匯入 `app.main` 就會讀正式的設定檔，所以每個匯入它的測試檔都依賴正式設定檔是合法的；設定檔寫壞時，這些測試檔會全部停在收集階段
- 實驗 D 是匯入模組，不是真的用 uvicorn 啟動；容器裡的行為也還沒有驗證
- 新的 8 個測試沒有先看過功能還沒寫時的紅（見上）；`test_pricing_module_keeps_no_price_table_of_its_own` 與 `test_find_model_config_rejects_model_without_settings` 兩個測試，本人沒有看過它們變紅，只有 Claude 的試跑環境做過（留著舊的 `PRICES`：1 個失敗；查不到時不報錯：1 個失敗）
- 沿用 E87：token 數是負數或不是整數時的行為沒有定義；輸出 token 是否已含思考 token 要到步驟 6 才實證

### 面試可用的說法

- 「上一關算成本的函式是『用模型名稱查單價，接著算』，而且排在模型回答之後。這一關我把它拆成兩步：呼叫模型之前先查到這顆模型的設定，查不到就不呼叫；回答之後拿手上的設定直接算。這樣一來，花了錢之後才發現沒有單價這種事，從函式的形狀上就不會發生。」
- 「我做過一個實驗：呼叫的是便宜模型，查價時卻拿強模型的設定。五個測試變紅，一次呼叫從 7 變成 136，額度很小的使用者第二次就被擋掉。呼叫的模型和計費的模型一定要是同一顆。」
- 「設定檔寫錯時，我的 Gateway 是起不來的。我把路由指到一顆不存在的模型試過，一匯入主程式就報錯，訊息直接說是哪一顆模型沒有設定。」

---

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `8907063` | 10/10 13:09 | `feat: read prices from the config file and look up the model before calling it` |
| `6c1c7b0` | 13:10 | `docs: record M3 step 1 evidence`（`7cb56ed..6c1c7b0`） |

推送後由 Claude 讀取公開 repo 核對：`app/main.py`、`tests/test_pricing.py` 與參考版本相同，`app/pricing.py` 只差結尾的換行；在試跑環境執行 `6c1c7b0`：`137 passed`（碰資料庫的測試以替身伺服器代替 DynamoDB Local）。

---

## E97. 步驟 3：路由函式 `choose_model()`（2026-10-10 13:15～14:09）

**依據：** 決策書 D8（路由規則 v1：輸入 ≥ 300 字或含關鍵字 → 強模型，其餘 → 便宜模型）、D9（使用者不能指定模型）；E94 定案 2；E95（路由規則在設定檔的 `[routing]`）。對應驗收 S05。

**範圍：** 一個純函式：給它一段文字與路由規則，它交回「用哪一顆模型、為什麼」。**Gateway 還沒有呼叫它**，接進 `chat_endpoint` 是步驟 4。

**生活比喻：** 診所櫃檯看掛號單決定掛一般科還是專科，並在單子上寫下原因。

### 定案（10/10 13:51 本人決定，兩項）

| # | 決定 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 1 | 呼叫前查不到模型設定時，對使用者回什麼（決策書 12.5、E96 的待決） | **回 500 與固定訊息 `Internal server error`；稽核記一筆 `status: error`、`error_type: ModelNotConfiguredError`；不呼叫模型、不扣錢** | 回 503 並沿用 `Service temporarily unavailable`：503 的意思是「稍後再試」，客戶端會白白重試，也會和資料庫故障混在一起。不處理、讓框架自己回 500：這個請求不會留下稽核紀錄（與 D37 的想法相反）。弱點：多一種狀態碼與一條要測的路 |
| 2 | 路由函式回傳什麼（修訂 E94 定案 2） | **只回 `model` 與 `reason`，不回思考量** | 照 E94 原案連思考量一起回：思考量已經在 `find_model_config()` 查到的模型設定裡（E96），路由再回一次，同一個值就有兩個來源 |

第 1 項在步驟 4 接線時實作，這一步還沒有做。

### 做法與規則

| 規則 | 做法 | 為什麼 |
|---|---|---|
| 字數 | `len(text) >= routing.min_chars` → 強模型，理由 `length` | D8 寫的是「≥」；剛好達到門檻就算 |
| 關鍵字 | 文字與關鍵字都先轉成小寫，文字裡含任何一個 → 強模型，理由 `keyword` | 使用者打 `DEBUG`、設定檔寫 `Debug`，都應該算同一個字 |
| 其餘 | 便宜模型，理由 `default` | — |
| 兩者都符合時 | 先看字數，理由記 `length` | 同一句話每次的理由要一樣，稽核才能統計 |
| 輸入 | 遮罩後的文字（由呼叫的人傳入） | 模型實際收到的是遮罩後的內容（E94 定案 2） |

`choose_model()` 只看傳進來的文字與規則，不碰網路、資料庫，也不讀設定檔；規則由呼叫的人交給它。所以測試可以用自己的一份規則（門檻 10 個字），不用把句子寫到 300 字。

### 新觀念

| 觀念 | 白話 | 生活比喻 |
|---|---|---|
| `文字.lower()` | 交回一份全部小寫的新文字，原本的不變 | 比對名字前，兩邊都先抄成小寫再對 |
| 迴圈裡的 `return` | 找到一個就直接交結果，後面的不用看 | 一串鑰匙一把一把試，開了就不試剩下的 |
| 迴圈**外面**的 `return` | 全部都試過、都沒中，才走這一行 | 整串鑰匙都試完了才去找管理員 |

### 本人撰寫（`app/router.py`，`81a87c2` 的版本，整份）

```python
"""Choose which model answers a request."""

from dataclasses import dataclass

from app.config import RoutingConfig


# 路由的結果：用哪一顆模型，以及為什麼（稽核和示範畫面都要說得出理由）
@dataclass(frozen=True)
class RouteDecision:
    """Which model to use and why it was chosen."""
    model: str
    reason: str


# 夠長或含關鍵字就用強模型，其餘用便宜模型；只看文字和規則，不碰網路和資料庫
def choose_model(text: str, routing: RoutingConfig) -> RouteDecision:
    """Return the model for the text, together with the reason."""
    if len(text) >= routing.min_chars:
        return RouteDecision(model=routing.strong_model, reason="length")

    # 英文關鍵字不分大小寫：兩邊都先轉成小寫再比
    lowered = text.lower()
    for keyword in routing.keywords:
        if keyword.lower() in lowered:
            return RouteDecision(model=routing.strong_model, reason="keyword")
    return RouteDecision(model=routing.cheap_model, reason="default")
```

填空版七格，一次寫對：先看到 `1 error during collection`（`app/router.py` 還不存在），寫完 `150 passed`。

### 測試（Claude 整份提供，`tests/test_router.py`，13 個；測試數 137 → 150）

前十個用測試專用的規則（便宜 `small`、強 `big`、門檻 10 個字、關鍵字 `分析` 與 `debug`），後三個讀正式的設定檔。

| 測試（前十個開頭皆為 `test_choose_model`） | 輸入 | 預期 | 在守什麼 |
|---|---|---|---|
| `…_uses_cheap_model_by_default` | `Say hi` | `small`、`default` | 短又沒有關鍵字 |
| `…_uses_strong_model_at_the_length_threshold` | 10 個 `a` | `big`、`length` | 剛好達到門檻 |
| `…_keeps_cheap_model_just_below_the_threshold` | 9 個 `a` | `small`、`default` | 差一個字；和上一個從兩邊夾住門檻 |
| `…_counts_each_chinese_character_as_one` | 10 個、9 個中文字 | `length`、`default` | 一個中文字算一個字 |
| `…_uses_strong_model_for_chinese_keyword` | `請分析一下` | `big`、`keyword` | 中文關鍵字 |
| `…_uses_strong_model_for_english_keyword` | `go debug` | `big`、`keyword` | 清單裡的第二個關鍵字、出現在句子中間 |
| `…_ignores_case_of_the_text` | `go DEBUG` | `big`、`keyword` | 文字要轉小寫 |
| `…_ignores_case_of_the_keyword` | 關鍵字設成 `Debug`，輸入 `go debug` | `big`、`keyword` | 關鍵字也要轉小寫 |
| `…_reports_length_first_when_both_apply` | `please debug this`（17 個字） | `big`、`length` | 兩者都符合時理由固定 |
| `…_works_without_keywords` | 關鍵字清單是空的 | 短的 `small`、長的 `big` | 空清單不能讓函式壞掉 |
| `test_shipped_rules_keep_m2_acceptance_prompts_on_the_cheap_model` | M2 驗收用過的三句話（先遮罩） | 都是 `gpt-6-luna` | S02 的示範靠便宜模型的單價連續呼叫到超額 |
| `test_shipped_keywords_do_not_match_mask_labels` | `[EMAIL] [CARD] [PHONE] [TW_ID]` | `default` | 遮罩的標籤本身不能命中關鍵字 |
| `test_shipped_rules_send_long_or_keyword_text_to_the_strong_model` | 門檻長度的文字、清單裡的每一個關鍵字 | 都是 `gpt-6-sol` | 正式規則的每一項都會生效 |

- 讀正式設定檔的三個測試不寫死 300 與關鍵字清單，而是從設定讀出來再用；步驟 7 調整門檻時不用改它們
- **遮罩標籤那一個測試連著 M2 與 M3：** 之後有人把 `id`、`card` 這類字加進關鍵字清單，所有含個資的訊息都會被送去強模型，這個測試會紅

### 破壞實驗（本人執行，四個；每個做完立刻改回）

| # | 改了什麼 | 結果 | 紅的是 |
|---|---|---|---|
| A | `>=` 改成 `>` | `4 failed, 9 passed` | 剛好達到門檻（`…son='default') == …ason='length')`）、中文字數（`'default' == 'length'`）、空清單（`'small' == 'big'`）、正式規則（`'gpt-6-luna' == 'gpt-6-sol'`） |
| B | 文字不轉小寫 | `1 failed, 12 passed` | `ignores_case_of_the_text` |
| C | 關鍵字不轉小寫 | `1 failed, 12 passed` | `ignores_case_of_the_keyword` |
| D | 最後一行 `return` 往右縮一層（變成在 `for` 裡面） | `4 failed, 9 passed` | 英文關鍵字、文字大小寫、正式規則（三個都是 `…son='default') == …son='keyword')`）、空清單（`AttributeError: 'NoneType' object has no attribute 'model'`） |

**判讀：**

- **實驗 A：** 寫成 `>` 時，剛好 300 個字的請求會被送去便宜模型，與決策書的「≥ 300」差一個字
- **實驗 B、C：** 兩個 `.lower()` 各由一個測試守著，拿掉哪一個就是哪一個紅。只轉其中一邊的話，大寫的 `DEBUG` 或設定檔裡的 `Debug` 會安靜地失效
- **實驗 D：** 最後的 `return` 在迴圈裡面時，第一個關鍵字沒中就直接交回便宜模型，清單裡後面的關鍵字永遠不會被檢查。中文關鍵字那個測試沒有紅，因為 `分析` 剛好排在清單的第一個；英文的 `debug` 排第二個，才抓得到
- **實驗 D 的第四個紅：** 關鍵字清單是空的時候，迴圈一圈都沒跑，函式走到底沒遇到 `return`，交回 `None`（E81 寫 Luhn 時看過的同一件事）

### 更正：Claude 給的兩個預期數字與做法不符（照實記錄）

| # | 內容 | 原因 |
|---|---|---|
| 1 | 實驗 D 的預期寫成 `3 failed, 10 passed`，實際是 `4 failed, 9 passed`。**本人的結果才是對的** | Claude 試跑時做的是「在迴圈裡多加一行 `return`、原本那一行留著」，與交給本人的做法（把最後一行縮進去）不是同一個實驗；少算了空清單交回 `None` 的那一個 |
| 2 | Claude 第一次試跑時，實驗 B 與 C 紅的測試一度對調 | 兩次修改的檔案大小相同、又在同一秒內完成，Python 沿用了上一次的位元組碼快取。重跑後與邏輯相符（也就是上表的結果）；之後 Claude 的試跑一律關閉快取 |

- **學到的：** 預期的數字要來自「和交出去的指示一模一樣」的實驗；實驗做得不一樣，預期就不能算數。第 2 項是試跑環境的問題，照人的速度操作不會遇到

### 限制（誠實記錄）

- **Gateway 還沒有呼叫這個函式。** 目前只有測試在用；模型仍是 `main.py` 裡的常數
- **關鍵字是「出現在文字裡就算」，不是整個單字比對：** `code` 會命中 `decode`、`barcode`。步驟 7 用測試集決定要不要處理
- **`len()` 把一個中文字與一個英文字母都算 1：** 300 個英文字母大約只有 50 個單字，中英文的門檻不一樣寬（E94 定案 2 的弱點）。步驟 7 決定
- 遮罩會改變字數（10 碼手機變成 `[PHONE]` 7 個字），門檻邊界會差幾個字
- 理由只記 `keyword`，不記命中的是哪一個關鍵字
- 文字前後的空白、換行也算進字數；全形的英文字母（例如 `ｄｅｂｕｇ`）不會被當成關鍵字
- 遮罩標籤的測試只涵蓋目前的四種標籤；之後新增標籤要記得補
- **13 個測試裡有 6 個，本人沒有看過它們為了預期的原因而紅：** 預設用便宜模型、差一個字仍是便宜模型、中文關鍵字、兩者都符合時記 `length`、M2 驗收的三句話、遮罩標籤。前五個守的是「不該送去強模型的沒有被送去」與理由的先後。Claude 的試跑環境只對其中一個做過對應的破壞（把關鍵字的檢查排到字數前面：`reports_length_first` 紅）；其餘沒有做過「讓它為了對的原因而紅」的實驗

### 面試可用的說法

- 「路由是一個純函式：給它遮罩後的文字和規則，它回模型名稱和理由。它不碰網路也不讀設定檔，所以我可以用一份門檻只有 10 個字的測試規則把每條邊界都測到，20 題測試集也能直接重複呼叫它。」
- 「我做過一個實驗，把函式最後那行 return 縮進迴圈裡。結果是只有第一個關鍵字有效，後面的全部安靜地失效；中文關鍵字的測試沒有紅，因為它剛好排在清單第一個，是排第二個的英文關鍵字把錯抓出來的。」
- 「我有一個測試是把遮罩用的四個標籤直接丟給路由，確認它們不會命中關鍵字。不然哪天有人把 id 或 card 加進關鍵字清單，所有含個資的訊息都會被送去貴 20 倍的模型。」

---

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `81a87c2` | 10/10 14:09 | `feat: add the routing function that picks the model` |
| `6eaba32` | 14:09 | `docs: record M3 step 2 evidence`（`6c1c7b0..6eaba32`） |

推送後由 Claude 讀取公開 repo 核對：`tests/test_router.py` 與交付的版本相同；`app/router.py` 與參考寫法只差一個空行與結尾的換行；在試跑環境執行 `6eaba32`：`150 passed`。

---

## E98. 步驟 4：路由接進對話入口（2026-10-11 21:27～23:37）

**依據：** E94 定案 3（計費用實際呼叫的那顆模型、呼叫前查設定）、定案 4（稽核欄位）、定案 5（輸出上限）；E97 定案 1（查不到模型設定回 500）、定案 2（路由只回模型與理由）；決策書 D8、D9、D28、D37、D45。對應驗收 S05、S06。

**範圍：** Gateway 現在依遮罩後的內容選模型，用那顆模型自己的思考量、輸出上限與單價。分四小段，一段一筆 commit。**降級還沒有做**（步驟 5）；**全部用假的模型驗證**，真實呼叫在步驟 6、9。

### 四小段與結果

| 段 | 內容 | 先看到的紅 | 完成後 | commit |
|---|---|---|---|---|
| ① | 設定做成領用窗口 `get_config()`；`choose_model()` 接進 `chat_endpoint`；稽核加 `route_reason`、`routed_model`；刪掉常數 `MODEL`、`REASONING_EFFORT` | `ImportError: cannot import name 'get_config' from 'app.main'`，`1 error during collection` | `159 passed` | `90c7281` |
| ② | 查不到模型設定：回 500、寫稽核、不呼叫模型、不扣錢（E97 定案 1） | `3 failed, 10 passed`：`ModelNotConfiguredError: No settings for model: ghost` | `163 passed` | `82517e2` |
| ③ | 輸出上限 `max_completion_tokens` 帶給 OpenAI | `7 failed, 159 passed` → 只改 `chat()` 之後 `30 failed, 136 passed` | `166 passed` | `641d004` |
| ④ | 稽核的 `model` 改記指定的名稱，另加 `provider_model`；回給使用者的也是指定的名稱 | `3 failed, 167 passed` | `170 passed` | `fda869a` |

測試數 150 → 170（其中 45 個是 `integration`）。

### 請求的順序（步驟 4 之後）

驗證（401／503）→ 讀額度（503）→ 遮罩、準備稽核 → 判斷超額（429，寫稽核）→ 加 0（503）→ **選模型、把理由記進稽核** → **查這顆模型的設定（500，寫稽核）** → 呼叫模型，帶思考量與輸出上限（502，寫稽核）→ 記 `model`、`provider_model` 與用量 → 用查到的設定算成本、加到已用量 → 寫稽核 → 回傳。

- 路由排在「加 0」之後：被額度擋下、或資料庫寫不進去的請求不會走到路由
- 查設定排在呼叫模型之前；算成本用的是同一個 `settings`，所以**呼叫的模型和計費的模型一定是同一顆**

### 稽核紀錄的新欄位

| 欄位 | 記什麼 | 哪些紀錄有 |
|---|---|---|
| `route_reason` | 為什麼選這顆：`length`、`keyword`、`default` | 走到路由的請求：成功、查不到設定（500）、模型失敗（502） |
| `routed_model` | 路由選的模型 | 同上 |
| `model` | **我們指定、也拿來計費的名稱**（M2 記的是供應商回報的名稱） | 成功的紀錄 |
| `provider_model` | 供應商回報的名稱，可能帶日期尾碼 | 成功的紀錄；兩個名稱相同時也有這一欄 |

- 被額度擋下的紀錄（`quota_exceeded`）沒有這四欄：它在路由之前就結束了
- 目前 `routed_model` 與 `model` 一定相同；步驟 5 做了降級之後才會不同
- **生活比喻：** 訂單上寫的是「雙人房」（指定的、照這個收費），入住單上寫的是「512 號房」（實際給的那一間）；兩個都留著，帳才對得起來

### 本人撰寫（`app/main.py`，`fda869a` 的版本，節錄）

```python
# 領用窗口：模型、單價與路由規則（測試時會換成測試用的設定）
def get_config() -> GatewayConfig:
    return CONFIG
```

```python
    # 依遮罩後的內容選模型，理由記進稽核；再查到這顆模型的設定（含單價）：查不到就不呼叫
    decision = choose_model(masked, config.routing)
    record["route_reason"] = decision.reason
    record["routed_model"] = decision.model
    # 查不到設定是我們自己的設定問題：記一筆失敗、回 500，不呼叫模型、不扣錢
    try:
        settings = find_model_config(config.models, decision.model)
    except ModelNotConfiguredError as exc:
        record["status"] = "error"
        record["error_type"] = type(exc).__name__
        append_audit(record, audit_path)
        raise HTTPException(status_code=500, detail="Internal server error")

    # 試著呼叫模型；OpenAI 出錯就記一筆失敗，回 502
    try:
        result = chat(
            client,
            decision.model,
            [{"role": "user", "content": masked}],
            settings.reasoning_effort,
            settings.max_completion_tokens,
        )
    except OpenAIError as exc:
        record["status"] = "error"
        record["error_type"] = type(exc).__name__
        append_audit(record, audit_path)
        raise HTTPException(status_code=502, detail="Upstream model error")

    # 成功：補上模型和用量，再寫入
    # model 記我們指定、也拿來計費的名稱；provider_model 記 OpenAI 回報的名稱，兩者可能不同
    record["model"] = decision.model
    record["provider_model"] = result.model
```

回傳給使用者的 `model` 也改為 `decision.model`。`app/providers/openai_client.py` 的 `chat()` 多收一格 `max_completion_tokens`，並交給 `client.chat.completions.create()`。

**設定為什麼也做成領用窗口：** 和資料庫、時間一樣，測試才換得掉。`chat_endpoint` 裡一律用領到的 `config`（小寫），只有 `get_config()` 交出模組讀好的 `CONFIG`（大寫）。

**查不到設定的 500 與模型失敗的 502 是同一個形狀：** 請求確實進來了，所以先記一筆失敗的稽核，再回固定的訊息；稽核只記錯誤的類別名稱（D37）。差別在出事的是誰：500 是自己的設定，502 是上游。

### 測試（Claude 整份提供）

**`tests/fakes.py`：** 假的模型回報的名稱預設改為「請求指定的那一顆」（原本固定回 `gpt-6-luna`）；要模擬回報的名稱不同時另外給 `reported_model`；另外把每一次收到的請求都記在 `requests`（步驟 5 的降級會用到）。

**`tests/test_chat_routing.py`（新檔，19 個）：** 用一份測試專用的設定，模型叫 `small` 與 `big`、門檻 18 個字、關鍵字 `debug`、輸出上限 100 與 200；主程式若偷用寫死的名稱或正式設定，馬上會被抓到。碰資料庫的地方用 `FakeDynamoDB`，不需要 Docker。

| 組 | 測試數 | 檢查 |
|---|---|---|
| 選到哪一顆 | 3 | 短句 → `small`、思考量 `none`；含關鍵字 → `big`、`low`；20 個字 → `big` |
| 稽核的理由 | 2 | `default`／`small`；`keyword` 與 `length` 分得出來 |
| 用遮罩後的內容路由 | 1 | `Call 0912345678 now` 原文 19 個字（達到門檻），遮罩後 16 個字 → 仍是 `small` |
| 成本 | 2 | 假的模型回報 13 / 11 個 token：`big` 是 136、`small` 是 7；稽核與實際扣的金額都要對 |
| 輸出上限 | 2 | `small` 帶 100、`big` 帶 200 |
| 兩個模型名稱 | 4 | 回報 `small-2026-09-01` 時：稽核 `model` 是 `small`、`provider_model` 是回報的；回給使用者的是 `small`；成本照常是 7；兩個名稱相同時 `provider_model` 也在 |
| 查不到設定 | 4 | 500 與固定訊息、回應裡沒有模型名稱；模型沒被呼叫、只有事前的「加 0」；稽核有 `status: error`、`error_type`、`routed_model`、`route_reason`；同一份壞設定下走便宜模型的請求照常 200 |
| 不留常數 | 1 | `app.main` 沒有 `MODEL`、`REASONING_EFFORT` |

- **「查不到設定」怎麼做出來：** 正式的設定檔過不了 `load_config()` 的檢查，所以測試直接組一份壞掉的設定（強模型叫 `ghost`、沒有它的設定），從領用窗口換進去
- 「沒呼叫模型、沒扣錢」那個測試先確認狀態碼是 500，再檢查兩件「沒發生」的事（M2 結案報告第 4 節）
- 這個檔的每個測試跑完都會把換掉的領用窗口還原，避免測試用的設定影響到別的測試檔

**`tests/test_openai_client.py`：** 既有 4 個測試的呼叫補上第五格，新增 1 個確認輸出上限有送出去；共 5 個。

### 破壞實驗（本人執行，十個；每個做完立刻改回）

| 段 | # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|---|
| ① | A | 路由改吃原文（`request.message`） | `1 failed, 8 passed` | `assert 'big' == 'small'` |
| ① | B | 查設定時固定拿便宜模型 | `2 failed, 7 passed` | `assert 'none' == 'low'`、`assert 7 == 136` |
| ① | C | 選模型時用大寫的 `CONFIG` | `8 failed, 1 passed` | `ModelNotConfiguredError: No settings for model: gpt-6-luna`（5 個）與 `…gpt-6-sol`（3 個） |
| ② | A | `500` 改成 `503` | `3 failed, 10 passed` | `assert 503 == 500` |
| ② | B | 那條路不寫稽核 | `1 failed, 12 passed` | `FileNotFoundError`（稽核檔沒有被建立） |
| ② | C | 訊息改成錯誤的內容（`str(exc)`） | `1 failed, 12 passed` | `{'detail': 'N...model: ghost'} == {'detail': 'I...server error'}` |
| ③ | A | `main.py` 的輸出上限寫死成 `100` | `1 failed, 165 passed` | `assert 100 == 200` |
| ③ | B | `chat()` 不把上限交給 OpenAI | `3 failed, 163 passed` | `KeyError: 'max_completion_tokens'` |
| ④ | A | 稽核的 `model` 改回記回報的名稱 | `1 failed, 169 passed` | `assert 'small-2026-09-01' == 'small'` |
| ④ | B | 回給使用者的 `model` 改回回報的名稱 | `1 failed, 169 passed` | `assert 'small-2026-09-01' == 'small'` |

**判讀：**

- **①A：** 原文有 10 碼手機時比遮罩後長 3 個字；用原文路由，這一句會被送去貴 20 倍的模型，但模型實際收到的內容並沒有那麼長
- **①B：** 呼叫的是強模型，卻用便宜模型的思考量與單價：一次少收 129 micro-USD（136 變成 7），而且沒有任何錯誤。這就是 E96 實驗 C 的另一個方向
- **①C：** 用了模組的正式設定，測試換進去的設定完全沒有作用。在正式環境看不出這個錯（兩者是同一份），只有測試抓得到
- **②B：** 使用者照樣收到 500，從外面看不出少了一筆紀錄
- **②C：** 回應裡出現 `No settings for model: ghost`，把內部的模型名稱告訴了外面的人
- **③A：** 兩顆模型的上限不同才看得出來（E86、E87 的做法）
- **④A、④B：** 兩個測試各守一個地方，改哪一邊就是哪一個紅

### 挫折與說明不清楚的地方（照實記錄）

| # | 發生什麼 | 原因 | 之後的做法 |
|---|---|---|---|
| 1 | 第 ① 段第一次執行 `2 failed, 157 passed`：`KeyError: 'routed_model'` | 欄位名稱打成 `route_model`，少一個 `d`。程式有寫入，只是寫進另一個名字的欄位；請求照樣成功 | 與 E85 的 `"PHON"` 同類：字串打錯不會讓程式當掉，要有測試去讀那一欄 |
| 2 | 第 ① 段的「第 5 處」本人表示不清楚 | Claude 只給了要換上去的新程式，沒有把「原本長什麼樣子、要刪哪兩行」放在一起 | 要換掉既有的程式時，給改之前與改之後的對照，並標出刪哪幾行 |
| 3 | 第 ② 段寫「對照 502 那一段」，本人問那一段在哪裡 | Claude 提到既有的程式卻沒有指出位置 | 提到既有的程式時附上行號範圍與那一段的原文（與 E83「給程式片段時連同位置一起給」是同一件事） |

第 1 項也等於多做了一個破壞實驗：欄位名稱打錯時紅兩個，訊息直接說出是哪一欄。

### Claude 另外核對的事

- 專案鎖定的 OpenAI SDK（`openai` 3.19.2）的 `chat.completions.create` 有 `max_completion_tokens` 這個參數（以程式讀取函式的參數清單確認）。**只確認了參數存在**，模型實際怎麼反應要等真實呼叫
- 每一段推送後都讀取公開 repo 核對：四個測試檔與交付的版本相同；`app/main.py` 與參考寫法只差空行；在試跑環境執行 `fda869a`：`170 passed`（碰資料庫的測試以替身伺服器代替 DynamoDB Local）

### 限制（誠實記錄）

- **降級還沒有做。** 強模型被限流時，目前和其他 OpenAI 錯誤一樣回 502；稽核的 `fallback`、`fallback_reason` 兩欄也還沒有（步驟 5）
- **全部是假的模型。** 真的 OpenAI 收到路由後的請求（`gpt-6-sol`、思考量 `low`、帶輸出上限）會怎麼回，還沒有驗證；步驟 6 做第一次真實呼叫
- **輸出上限的數字是暫定的**（Luna 1,000、Sol 2,000）。思考 token 也算在上限裡，設太低回答會被截斷；**回答被截斷時目前看不出來**（沒有記錄供應商回報的結束原因），步驟 6 看過真實回應再決定要不要記
- **強模型下的超扣還沒有實測**（E94 定案 5 的試算是一次約 5,600 micro-USD）；有了輸出上限之後，一次最多花多少算得出來，但數字要等上限定案
- 500 那條路在正常情況下走不到（啟動時就擋掉了），只有測試換進壞掉的設定時才會發生
- 被額度擋下的紀錄沒有路由的欄位；驗證失敗與資料庫故障的請求仍然不寫稽核（沿用 E90、E91）
- 稽核 `model` 的意思變了：M2 的舊紀錄記的是回報的名稱，這一步之後記的是指定的名稱。10/9 的真實紀錄兩者實際相同（都是 `gpt-6-luna`）
- 設定在啟動時讀一次；改了 `app/config.toml` 要重新啟動 Gateway 才會生效
- 容器裡讀不讀得到設定檔仍未驗證（E95 的同一項限制）
- 既有的 `tests/test_chat.py` 等測試檔仍用正式的設定檔（短句都會被路由到 `gpt-6-luna`）；設定檔的門檻或關鍵字改動時，這些測試可能受影響
- **有些斷言本人沒有看過它們為了預期的原因而紅：** `test_chat_sends_simple_message_to_the_cheap_model`（只在實驗 ①C 因為查不到設定而紅）、`test_chat_sends_long_message_to_the_strong_model`、`test_chat_charges_the_cheap_price_for_a_simple_message`、`test_chat_charges_normally_when_the_provider_reports_another_name`、`test_chat_still_serves_the_cheap_model_when_only_the_strong_one_is_missing`、`test_main_keeps_no_hard_coded_model`（最後一個在 Claude 的試跑環境看過：留著常數時紅）。另外「查不到設定時沒呼叫模型、沒扣錢」那個測試只看過它的狀態碼斷言變紅，後面兩個「沒發生」的斷言沒有；要讓它們紅，得把查設定排到呼叫模型之後，那是結構的改寫

### 面試可用的說法

- 「路由我是用遮罩後的內容判斷的。我有一個測試：一句含手機號碼的話，原文剛好達到長度門檻，遮罩後少 3 個字就不到。我把程式改成用原文路由，它會被送去貴 20 倍的模型，而模型實際收到的內容並沒有那麼長。」
- 「呼叫的模型和計費的模型，我讓它們來自同一個變數。我做過實驗，呼叫強模型但拿便宜模型的設定去算，一次少收一百多 micro-USD，程式完全不報錯，只有測試會紅。」
- 「稽核裡我分兩欄記模型：一欄是我指定、也拿來計費的名稱，一欄是供應商回報的名稱。供應商回報的可能帶日期尾碼，代表它換版了；計費照指定的算，換版則是重跑測試集的訊號。」
- 「設定檔我做成可以在測試時換掉的相依。所以我能在測試裡給一份『路由指到不存在的模型』的壞設定，確認 Gateway 回 500、有留稽核、沒有呼叫模型也沒有扣錢。這種狀態在正式環境啟動時就被擋掉了，不靠測試根本做不出來。」

---

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `7458a72` | 10/10 14:13 | `docs: record M3 step 3 evidence`（`6eaba32..7458a72`） |
| `90c7281` | 10/11 22:13 | `feat: route each request to the cheap or the strong model` |
| `82517e2` | 22:44 | `feat: return 500 and audit when the routed model has no settings` |
| `641d004` | 23:14 | `feat: send the output cap of the routed model to the provider` |
| `fda869a` | 23:37 | `feat: audit the requested model and the provider-reported model separately` |

---

## E99. 簡報 v1.2：照「一頁講完 → 問題 → 前後比較 → 解法提綱 → 技術實踐」重排（2026-10-12）

**依據：** 老師對簡報的建議（10/12）：讀者是未來的主管與面試官；一頁把重點全講完、一頁想解決的問題、一頁解決前後的狀態比較、一頁解法的重新提綱，後面的頁數放技術實踐。決策書 8.3 第 7 項、11.6（簡報版號 +0.1）。

**範圍：** 只改簡報（`docs/slides/llm-gateway-slides-v1.2.pptx`，由 v1.1 改出，32 頁 → 34 頁）。程式與測試不動。旁白稿同日更新為 `docs/slides/narration-v1.2.md`（見下方「旁白稿 v1.2」）。原本規劃 M3 結案時才出 v1.2（步驟 10）；這次提前出，結案時的版本順延為 v1.3。

### 頁序（v1.2）

| v1.2 的頁 | 內容 | 來源 |
|---|---|---|
| 1 | 封面 | v1.1 第 1 頁，版號與日期更新 |
| 2 | **01｜一頁講完**：一句話、三張卡（問題／解法／現況）、四個數字（170 個測試、4 個真實驗收場景、單價差 20 倍、11 個監管環節） | 新增 |
| 3 | 02｜想解決的問題 | v1.1 第 3 頁 |
| 4 | **03｜解決前後**：六個面向的「之前／之後」對照，每列附狀態 | 新增 |
| 5 | 04｜解法提綱 | v1.1 第 4 頁 |
| 6～11 | 05～09｜技術實踐（看得到的效果、成本效益、現成方案拆解、網路邊界、稽核）、10｜取捨與結語 | v1.1 第 5～10 頁 |
| 12～31 | 技術細節 01～20 | v1.1 第 11～30 頁 |
| 32～34 | 附錄：影片時間預算、素材狀態、時程 | 時間預算由 v1.1 第 2 頁移到附錄 |

### 定案（Claude 提出預設做法並告知，本人未反對）

| 項目 | 做法 | 不選的做法與原因 |
|---|---|---|
| 影片分鏡的記號（「主影片 02／09」「旁白約 N 秒」） | 從內頁拿掉；時間預算頁移到附錄 | 留在內頁：讀者是主管與面試官，這些是製作影片用的記號，會干擾閱讀 |
| 狀態標籤 | 保留，改成讀者看得懂的字（例：「已有」→ 拿掉或改「M0.5 已完成」；「圖已有／雲端 M4、M5」→「本機已實作／雲端 M4、M5」）。只有「素材已到位」意思的標籤才拿掉 | 全部拿掉：還沒做的部分會看起來像做完了 |
| 還沒有的數字 | 省下的比例維持「X%，待 M3 實測」，不放估計值 | 先放估計值：測試集（步驟 7）還沒跑，放了就是沒有依據的數字 |
| 「之前」的那一欄 | 寫成情境假設，頁面下方註明不是特定公司的現況 | 不註明：會被讀成是在描述某一家公司 |

### 跟著進度更新的內容

| 頁 | 改了什麼 |
|---|---|
| 內容防護、驗證與觀測 | 測試數 119 → 170 |
| 看得到的效果（面板 1）、路由與成本、附錄素材狀態 | 路由由「設計定案／實作 M3」改為「已實作／M3 驗收中」；畫面仍是示意文字，註明 M3 驗收時錄製 |
| 成本、附錄素材狀態 | 日期「截至 10/9」→「截至 10/12」。10/9 之後沒有真實呼叫，也沒有開 AWS 資源，金額不變 |
| 附錄時間預算 | 註明頁碼是 v1.1 的分鏡編號，新增的兩頁尚未計入 |

### 旁白稿 v1.2（同日）

| 項目 | 內容 |
|---|---|
| 檔案 | `docs/slides/narration-v1.2.md`（v1.1 保留在 repo，沒有刪） |
| 新增兩頁的旁白 | 01｜一頁講完：64 字、約 17 秒；03｜解決前後：30 字、約 8 秒 |
| 精簡 | 02｜想解決的問題 110 → 99 字（刪開頭的引導句）；04｜解法提綱 118 → 101 字（閘道的位置已在一頁講完講過） |
| 跟著進度改 | 05 的開頭改成承接解決前後；技術細節 12 的最後一句由「這部分在 M3 實作」改為「路由已經實作並通過自動測試；降級還在做」 |
| 主影片旁白合計 | 871 字、約 238 秒 → 941 字、約 257 秒（多 19 秒） |
| 技術版旁白合計 | 1828 字、約 8.3 分鐘（只多一句） |
| 頁名 | 主影片 01～09 改為封面加 01～10；「技術版 NN」改為「技術細節 NN」；檔內附 v1.1 → v1.2 的對照表 |

**新增「示範畫面怎麼接」一節（寫在旁白稿內）：**

- 示範不是獨立的一段，而是插在簡報頁中間的錄影；兩支影片用同一批片段，差別只在剪多長、插在哪一頁後面
- 每一段固定三拍：簡報頁講主張 → 錄影當證據 → 切回簡報講一句結論
- 主影片每段剪到 8～15 秒、只播結果；技術版完整播，連反向檢查一起播
- 「03｜解決前後」當示範的目錄：每一列的「之後」是主張，後面的錄影是證據
- 片段對照表：S01～S16、Demo Console、M7 各自接在主影片與技術版的哪一頁

**尚未定案：** 試講超過 6 分鐘時先拿掉什麼。旁白稿內列了建議順序（主影片的 S03 → 解決前後的旁白 → 現成方案拆解的第一個發現縮成一句），等計時試講後再定。

### 檢查（Claude 執行）

- 旁白稿的字數用程式重算：先以同一個算法核對 v1.1 的 29 頁，全部相符，再用來算 v1.2
- 以 pptx 檢查工具對照 v1.1 驗證檔案結構：通過
- 34 頁全部轉成圖片逐頁看過。發現並修正：一頁講完的摘要文字壓到卡片、四個數字的說明斷行不自然、三個狀態標籤的字超出標籤
- 全文搜尋「119」「v1.1」「主影片 0」「旁白約」：只剩附錄註解裡刻意保留的「v1.1 影片分鏡」

### 限制（誠實記錄）

- **簡報附錄的時間預算表還是 v1.1 的數字。** 簡報先定稿、旁白稿後補，所以簡報第 32 頁仍寫主影片 4.0 分鐘，並註明新增的兩頁尚未計入；實際數字以 `narration-v1.2.md` 為準，簡報 v1.3 再對齊
- **主影片的時間幾乎沒有餘裕。** 旁白 941 字、約 257 秒，加上規劃的示範片段 94 秒，合計約 5 分 51 秒，離 6 分鐘上限只剩 9 秒；而且都是用字數估的，還沒有計時試講
- **版面只在 LibreOffice 轉出的圖上檢查過。** 簡報用的字型是微軟正黑體，檢查環境沒有這個字型，實際在 PowerPoint 開啟時字寬可能略有不同，本人需要自己翻一遍
- **「解決前後」的「之後」有兩列還沒驗收：** 自動選模型（已實作、未做真實驗收）與單一出口（M4）。頁面上各自標了「驗收中」「10/19 起」
- **一頁講完的四個數字會過期：** 測試數每一步都在變，結案前要再更新

---

## E100. 步驟 5：降級（2026-10-12 09:07～16:27）

**依據：** 交接檔 `m3-step5-handoff.md` 第 4 節；決策書 D10（強模型被限流 → 便宜模型一次；便宜模型也限流 → 503 附 `Retry-After`；SDK 重試次數設小，避免和降級疊加）、D32（供應商預算用完不降級、回 503）、D37（上游失敗記稽核、只記錯誤類別）；E94 定案 3（成本用實際拿到回答的那次指定的名稱）、定案 4（稽核欄位）；M2 結案報告第 4 節（檢查「某件事沒發生」之前，先確認請求走到了該被擋的地方）。對應驗收 S07。

**範圍：** 強模型被限流時改用便宜模型一次；兩顆都被限流回 503 並附 `Retry-After`；供應商預算用完不降級、回 503、不附 `Retry-After`；其他供應商錯誤維持 502；回傳、稽核的 `model` 與成本都改用實際回答的那顆模型；稽核新增 `fallback`、`fallback_reason`、`error_code`。**全部用假的模型驗證**，沒有呼叫 OpenAI，也沒有遇到真的 429。

**起點：** repo 最新 commit `52018c3`（10/12 09:07）；`170 passed`。交接檔第 2 節的回覆：簡報 v1.2 用 PowerPoint 桌面版看過，排版沒有問題；`app/config.py` 多一個空白、`app/main.py` 少一個空行已修（`16e50d6`）；和老師討論示範影片排在 10/12 晚上，結果另記。Claude 依旁白稿 v1.2 的「示範畫面怎麼接」整理了五個要問的問題：6 分鐘是否為硬上限、示範用插在簡報頁中間的短錄影是否可以、主影片用終端機畫面是否足夠、降級只能用模擬是否可以當驗收、「省下 X%」能否用估算。

**生活比喻：** 餐廳客滿（限流）就帶客人去隔壁分店；客人的儲值卡沒錢了（預算用完），換哪一家都刷不過，就不帶去了，請他先處理儲值。

### 開工前的查證：`openai` 3.19.2 遇到 429 會怎樣（Claude 執行）

在試跑環境用專案鎖定的 SDK，對一個本機假伺服器打 7 種 429，數伺服器實際收到幾次請求。**假伺服器回的內容是 Claude 依官方文件寫的，不是真的 OpenAI 回應。**

| # | 假伺服器回的 429 | 用戶端設定 | 實際請求次數 | 花費時間 |
|---|---|---|---|---|
| A | 限流（`rate_limit_exceeded`），沒有 `retry-after` | `max_retries=1` | 2 | 0.51 秒 |
| B | 限流，`retry-after: 2` | `max_retries=1` | 2 | 2.02 秒 |
| C | `insufficient_quota` | `max_retries=1` | 2 | 0.41 秒 |
| D | `project_spend_limit_exceeded` | `max_retries=1` | 2 | 0.43 秒 |
| E | 限流，`retry-after: 2` | `with_options(max_retries=0)` | 1 | 0.00 秒 |
| F | 限流，`x-should-retry: false` | `max_retries=1` | 1 | 0.00 秒 |
| G | 限流，`retry-after: 300` | `max_retries=1` | 1 | 0.00 秒 |

- 兩種 429 丟的都是 `openai.RateLimitError`（`APIStatusError` → `APIError` → `OpenAIError` 的子類別）；`exc.code`、`exc.type` 取自回應內容裡 `error` 那一層；回應不是 JSON 時兩個都是 `None`
- `exc.response.headers` 拿得到供應商的標頭
- **SDK 對 429 會重試，連預算用完也照樣重試**（C、D）；`retry-after` 不超過 120 秒就照等（B），超過就不重試（G，SDK 原始碼的 `MAX_RETRY_AFTER_DELAY = 120`）。`timeout=30` 是每一次請求的逾時，**管不到重試前的等待**
- `client.with_options(max_retries=0)` 交回一條只改了重試次數的新連線，原本那條不變；`create()` 本身沒有 `max_retries` 參數
- 測試裡造得出同樣的例外：`RateLimitError(訊息, response=httpx2.Response(429, …), body={"code": …, "type": …})`

**官方文件（10/12 以工具讀取）：** 預算類的 429 代碼有 `credit_balance_exhausted`、`project_spend_limit_exceeded`、`organization_spend_limit_exceeded`、`organization_usage_limit_exceeded`；`insufficient_quota` 是可能同時出現的「類型」；限流另有 `slow_down`（類型 `rate_limit_error`），一般的限流沒有列固定代碼。**更正交接檔：** 交接檔寫「預算用完的代碼是 `insufficient_quota`」，依文件它主要是類型。來源：[Error codes](https://developers.openai.com/api/docs/guides/error-codes)、[Troubleshooting 429 errors](https://help.openai.com/en/articles/6614457-troubleshooting-api-rate-limits-and-429-errors)。

### 定案（10/12 09:19 本人決定，三項全數照建議）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | 兩種 429 怎麼分辨 | **排除法**：代碼是 `insufficient_quota` 或上面四個預算代碼之一、或類型是 `insufficient_quota` → 預算用完；其餘的 429 一律當限流。稽核另記供應商的代碼（`error_code`） | 只認得限流代碼才降級：官方沒有給限流固定代碼，認不得就不降級，備援安靜失效。比對錯誤訊息文字：措辭會改，也可能夾帶帳號資訊（D37） | 之後新增的預算代碼會被當成限流：多打一次便宜模型（會被拒、不花錢），最後回帶 `Retry-After` 的 503，誤導使用者「等一下就好」 |
| 2 | 兩顆都限流時 `Retry-After` 的值 | **照抄供應商的整數秒**：1～120 照抄；超過 120 回 120；沒有、看不懂、小於 1 回 30。預算用完的 503 不附 | 固定 30 秒：供應商說了要等多久，卻回一個自己編的數字 | 120 是借用 SDK 的界線，不是量出來的；HTTP 日期與 `retry-after-ms` 不解析，一律回 30 |
| 3 | SDK 重試和降級疊在一起 | **強模型那次 `with_options(max_retries=0)`，便宜模型保留 1 次**：「有備胎的那次不重撥」；最壞從 4 次呼叫降到 3 次 | 維持現狀：最多 4 次，兩顆各可能在 SDK 裡等 120 秒。兩次都不重試：一開始就走便宜模型的請求佔多數，它們遇到連線抖動也失去重試，等於推翻 M1 的設定（D10） | 強模型的 5xx、連線錯誤也不再重試，直接 502；便宜模型那次仍可能在 SDK 裡等最多 120 秒 |

- **定案 2 的修訂：** 開工前寫的是「超出範圍用 30」；第 ② 段交付測試前，Claude 改為「超過 120 回 120」，理由是供應商說 300 秒時，轉告 120 比轉告 30 接近實情；本人沒有反對
- **做的過程中再定的三件事（Claude 提出，本人照用）：**
  - 放在新檔 `app/fallback.py`，函式 `chat_with_fallback()`，結果物件 `CallOutcome`
  - **錯誤以結果交回，不往外丟**：降級過、最後還是失敗的請求，稽核仍要記得「降級過」；例外往外丟，這個資訊會跟著不見
  - `error_code` 對所有供應商回應的錯誤（`APIError`）都記，不只 429：決策書 8.2 的 M3 列有「記錄原始錯誤碼（如 `model_not_found`）」
- 兩種 503 對外的訊息相同（`Service temporarily unavailable`），不透露是哪一種；分辨靠稽核的 `error_code`

### 做法：五小段，一段一筆 commit

| 段 | 內容 | 先看到的紅 | 完成後 | commit |
|---|---|---|---|---|
| — | 交接檔第 2 節的排版 | — | `170 passed` | `16e50d6` |
| ① 前半 | `tests/fakes.py` 能依模型丟錯誤、數呼叫、記重試設定；`app/fallback.py` 的 `call_once()`、`chat_with_fallback()` | `1 error during collection`（`No module named 'app.fallback'`） | `183 passed` | `b8b548b` |
| ① 後半 | 接進 `chat_endpoint`；回傳、稽核的 `model` 與成本改用實際回答的模型 | 本人第一次執行是 `37 failed, 152 passed`（挫折 3，不是預期的紅） | `189 passed` | `bb43a9f` |
| ② | 兩顆都限流 → 503 附 `Retry-After`；`retry_after_seconds()` | 只寫函式時 `4 failed, 196 passed`（四個 `assert 502 == 503`） | `200 passed` | `4505674` |
| ③ | 預算用完 → 不降級、503 不附 `Retry-After`；`is_budget_exhausted()` | Claude 試跑：`ImportError`，接著 `3 failed, 207 passed` | `210 passed` | `f64fcde` |
| ④ | 稽核 `fallback`、`fallback_reason`、`error_code` | Claude 試跑：`5 failed, 213 passed`（`KeyError`） | `218 passed` | `c8e6570` |

### 一個請求現在可能的結局

| 情況 | Gateway 呼叫模型 | 回應 | 稽核 |
|---|---|---|---|
| 強模型成功 | 強 1 次（SDK 不重試） | 200，`model` 是強模型 | `ok`、`fallback: false` |
| 強模型被限流、便宜模型回答 | 強 1、便宜 1 | 200，`model` 是便宜模型，照便宜模型的單價收錢 | `ok`、`fallback: true`、`fallback_reason: RateLimitError`、`routed_model` 強、`model` 便宜 |
| 兩顆都被限流 | 強 1、便宜 1 | 503，`Retry-After` 照便宜模型那次的標頭 | `error`、`RateLimitError`、`error_code`、`fallback: true` |
| 供應商預算用完 | 1 次（不降級）；降級後才遇到則 2 次 | 503，不附 `Retry-After` | `error`、`error_code`（例如 `project_spend_limit_exceeded`） |
| 其他供應商錯誤 | 1 次（強模型不降級） | 502 | `error`、`error_type`、`error_code`（有代碼時） |
| 路由選便宜模型、被限流 | 便宜 1 | 503，附 `Retry-After` | `error`、`fallback: false` |

- 表中的次數是 Gateway 呼叫 `chat()` 的次數；便宜模型那一次 SDK 保留 1 次重試，所以最壞情況實際送出 3 個 HTTP 請求
- 被額度擋下（429）、查不到模型設定（500）的請求沒有走到呼叫模型，紀錄裡沒有 `fallback`

### 新觀念

| 觀念 | 白話 | 生活比喻 |
|---|---|---|
| `isinstance(東西, 類別)` | 這個東西是不是這一類（子類別也算） | 垃圾分類：寶特瓶也算塑膠類 |
| `client.with_options(max_retries=0)` | 交回一條只改了這個設定的新連線，原本那條不變 | 影印時只把這一份改成單面，機器的預設沒動 |
| 錯誤當成結果交回 | 成功、失敗都包成 `CallOutcome` | 外送員送不到時，帶著寫了原因的單子回店裡 |
| 回應的標頭 | 內容之外的一張張「名字: 值」 | 包裹外面貼的標籤 |
| `int()` 看不懂時丟 `ValueError` | 種類對（是文字），內容看不懂；`int(None)` 則是 `TypeError` | 照片上的手寫時間看不清楚就不猜 |
| OpenAI 錯誤的層級 | `OpenAIError` ⊃ `APIError`（才有 `.code`）⊃ `RateLimitError`、`NotFoundError` | 塑膠類 ⊃ 寶特瓶 |

### 本人撰寫（`app/fallback.py`，`c8e6570` 的版本，整份）

```python
"""Call the model, and fall back to the cheap model when the strong one is rate limited."""

from dataclasses import dataclass

from openai import OpenAIError, RateLimitError

from app.config import GatewayConfig, ModelConfig
from app.pricing import find_model_config
from app.providers.openai_client import ChatResult, chat


# 呼叫模型的結果：成功或失敗都用這個交回去，稽核才知道最後用的是哪一顆、有沒有降級過
@dataclass(frozen=True)
class CallOutcome:
    """What happened when we called the model."""
    result: ChatResult | None
    error: OpenAIError | None
    model: str
    settings: ModelConfig
    fallback: bool
    fallback_reason: str | None


# 呼叫一次模型：成功就帶著回答交回去，OpenAI 出錯就帶著那個錯誤交回去（不往外丟）
def call_once(client, messages: list[dict], model: str, settings: ModelConfig, fallback: bool, fallback_reason: str | None) -> CallOutcome:
    """Call the model once and return the answer or the error."""
    try:
        result = chat(client, model, messages, settings.reasoning_effort, settings.max_completion_tokens)
    except OpenAIError as exc:
        return CallOutcome(
            result=None,
            error=exc,
            model=model,
            settings=settings,
            fallback=fallback,
            fallback_reason=fallback_reason,
        )
    return CallOutcome(
        result=result,
        error=None,
        model=model,
        settings=settings,
        fallback=fallback,
        fallback_reason=fallback_reason,
    )


# 供應商「預算用完」的代碼：換成便宜模型刷的還是同一張卡，降級沒用，而且要有人去處理
BUDGET_ERROR_CODES = [
    "insufficient_quota",
    "credit_balance_exhausted",
    "project_spend_limit_exceeded",
    "organization_spend_limit_exceeded",
    "organization_usage_limit_exceeded",
]


# 這個 429 是不是「預算用完」：看代碼，也看類型；兩邊都對不上的，一律當成限流（排除法）
def is_budget_exhausted(error: RateLimitError) -> bool:
    """Return True when the 429 means the provider's budget or credit has run out."""
    if error.code in BUDGET_ERROR_CODES:
        return True
    if error.type == "insufficient_quota":
        return True
    return False


# 強模型被限流就改用便宜模型一次；便宜模型後面沒有備胎，照平常的方式呼叫
def chat_with_fallback(client, messages: list[dict], model: str, settings: ModelConfig, config: GatewayConfig) -> CallOutcome:
    """Call the routed model; when the strong model is rate limited, try the cheap model once."""
    cheap_model = config.routing.cheap_model

    # 路由選的就是便宜模型：沒有備胎，保留 SDK 自己的那一次重試
    if model == cheap_model:
        return call_once(client, messages, model, settings, False, None)

    # 強模型後面有備胎：這一次不讓 SDK 重試，被限流就直接換人
    no_retry_client = client.with_options(max_retries=0)
    first = call_once(no_retry_client, messages, model, settings, False, None)

    # 成功，或是限流以外的錯誤：都不降級，直接交回去
    if not isinstance(first.error, RateLimitError):
        return first
    # 供應商的預算用完：降級也一樣會被拒，不降級，直接交回去
    if is_budget_exhausted(first.error):
        return first

    # 強模型被限流：查到便宜模型自己的設定，用它再呼叫一次
    cheap_settings = find_model_config(config.models, cheap_model)
    reason = type(first.error).__name__
    return call_once(client, messages, cheap_model, cheap_settings, True, reason)


# 兩顆都被限流時，告訴使用者大約多久後再試：沒有標頭或看不懂時用這個
DEFAULT_RETRY_AFTER_SECONDS = 30
# 供應商說要等再久，最多也只轉告這麼久（和 SDK 自己願意等的上限相同）
MAX_RETRY_AFTER_SECONDS = 120


# 照抄供應商說的等待秒數，但不照單全收：只收整數秒，太大就壓到上限，沒有或看不懂就用預設值
def retry_after_seconds(error: RateLimitError) -> int:
    """Return how many seconds the caller should wait, based on the provider's Retry-After header."""
    value = error.response.headers.get("retry-after")
    if value is None:
        return DEFAULT_RETRY_AFTER_SECONDS

    try:
        seconds = int(value)
    except ValueError:
        return DEFAULT_RETRY_AFTER_SECONDS

    if seconds < 1:
        return DEFAULT_RETRY_AFTER_SECONDS
    if seconds > MAX_RETRY_AFTER_SECONDS:
        return MAX_RETRY_AFTER_SECONDS
    return seconds
```

**`app/main.py` 的呼叫模型那一段（節錄）：**

```python
    # 呼叫模型：強模型被限流時改用便宜模型一次；不論成功失敗，都交回一個結果（不往外丟錯誤）
    outcome = chat_with_fallback(
        client,
        [{"role": "user", "content": masked}],
        decision.model,
        settings,
        config,
    )

    # 稽核：有沒有降級；降級了才記原因（成功、失敗都記，所以寫在判斷成敗之前）
    record["fallback"] = outcome.fallback
    if outcome.fallback:
        record["fallback_reason"] = outcome.fallback_reason

    # 沒拿到回答：記一筆失敗
    if outcome.error is not None:
        record["status"] = "error"
        record["error_type"] = type(outcome.error).__name__
        # 供應商有回應的錯誤才有代碼（例如 rate_limit_exceeded、project_spend_limit_exceeded）：
        # 只記這個短代碼、不記錯誤訊息，事後才分得出是哪一種問題
        if isinstance(outcome.error, APIError):
            record["error_code"] = outcome.error.code
        append_audit(record, audit_path)
        # 供應商回 429（限流或預算用完）：回 503
        if isinstance(outcome.error, RateLimitError):
            # 供應商的預算用完：多久會恢復無從得知，要有人處理，所以不附 Retry-After
            if is_budget_exhausted(outcome.error):
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")
            # 限流（降級後的便宜模型，或路由一開始就選便宜模型）：告訴對方大約多久後再試
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable",
                headers={"Retry-After": str(retry_after_seconds(outcome.error))},
            )
        raise HTTPException(status_code=502, detail="Upstream model error")

    # 成功：補上模型和用量，再寫入
    # model 記實際回答、也拿來計費的那一顆（降級後是便宜模型）；provider_model 記 OpenAI 回報的名稱
    result = outcome.result
    record["model"] = outcome.model
```

算成本那一行改為 `cost_micro_usd(outcome.settings, …)`，回給使用者的 `model` 改為 `outcome.model`；`main.py` 不再直接呼叫 `chat()`，也不再自己接 `OpenAIError`。

- **`append_audit()` 排在兩種 `raise` 之前：** 503 與 502 兩條路都要留稽核，寫在前面只要寫一次
- **預算用完的判斷排在限流的 `raise` 之前：** `raise` 一執行後面就不跑了，順序反過來的話預算用完永遠輪不到
- **`record["fallback"]` 寫在判斷成敗之前：** 失敗的紀錄也要看得出降級過

### 測試（Claude 整份提供；測試數 170 → 218）

**`tests/fakes.py`：** 假的模型可以用 `errors` 指定「哪一顆模型丟哪個錯誤」；`models_called()` 依序列出每次請求的模型；`retry_settings` 記下每一次是用哪一種重試設定送出的（`None` 是連線原本的設定，`0` 是這一次不重試）；假連線 `FakeClient` 有和真的一樣只收具名參數的 `with_options()`；`make_rate_limit_error(code, error_type, retry_after)` 造出和 SDK 一樣的 429。既有的 170 個測試換上新的 `fakes.py` 後照樣通過。

**`tests/test_fallback.py`（26 個，直接測函式）：**

| 組 | 測試數 | 檢查 |
|---|---|---|
| 路由選便宜模型 | 3 | 只呼叫一次、保留 SDK 重試；被限流時不降級、交回錯誤 |
| 路由選強模型、正常 | 2 | 只呼叫強模型一次；那一次的重試設定是 0 |
| 強模型被限流 | 5 | 便宜模型回答；兩顆各呼叫一次、先強後便宜；便宜模型用自己的思考量與輸出上限（測試設定 `none`／100 對 `low`／200）；送出的內容相同；降級那次保留重試 |
| 其他錯誤 | 3 | 強模型遇到非 429 不降級；兩顆都限流交回便宜模型那個錯誤；降級後便宜模型出別的錯也交回，降級過不能不見 |
| `retry_after_seconds()` | 7 | 7 → 7；1 → 1；120 → 120；121、86400 → 120；沒有標頭 → 30；0、-5 → 30；`soon`、`1.5`、HTTP 日期 → 30 |
| `is_budget_exhausted()` | 5 | 五個預算代碼逐一認得；類型 `insufficient_quota` 配沒見過的代碼也算；一般限流、`slow_down`、沒有代碼也沒有類型都不算 |
| 預算用完不降級 | 1 | 強模型遇到預算用完：交回原錯誤、沒有呼叫便宜模型 |

**`tests/test_chat_fallback.py`（22 個，經過對話入口，沿用 `test_chat_routing.py` 的 `TEST_CONFIG`）：**

| 組 | 測試數 | 檢查 |
|---|---|---|
| 接線 | 6 | 強模型那次不重試、便宜模型保留重試；降級後回答與回應的 `model` 是便宜模型；照便宜模型收 7 而不是 136；稽核 `routed_model` 強、`model` 便宜；降級後便宜模型出別的錯回 502、不扣錢 |
| 兩顆都限流 | 4 | 503、固定訊息、`Retry-After` 照便宜模型那次（強模型給 50、便宜模型給 7，回 7）；沒有標頭時 30；路由選便宜模型被限流也是 503；留稽核、不扣錢 |
| 預算用完 | 4 | 強模型、便宜模型、降級後才遇到，三種都是 503 且沒有 `Retry-After`；留稽核、不扣錢 |
| 稽核欄位 | 8 | 正常與降級時的 `fallback`、`fallback_reason`；兩顆都限流、預算用完、404 `model_not_found` 的 `error_code`；`OpenAIError("boom")` 沒有 `error_code`；被額度擋下、查不到模型設定的紀錄沒有 `fallback` |

- 「沒扣錢」「沒呼叫」這類測試都先確認狀態碼與呼叫順序，再檢查沒發生的事（M2 結案報告第 4 節）
- 404 的假錯誤在測試檔裡用 `httpx2` 與 `NotFoundError` 組出來，`fakes.py` 沒有為它另加道具

### 破壞實驗（本人執行，20 個；每個做完立刻改回；結果與 Claude 事先給的預期全部相同）

| 段 | # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|---|
| ① 前半 | A | 強模型那次不用 `with_options`，直接用原本的連線 | `2 failed, 11 passed` | `assert [None] == [0]`、`assert [None, None] == [0, None]` |
| ① 前半 | B | 降級那次用強模型的 `settings` | `1 failed, 12 passed` | `assert 'low' == 'none'` |
| ① 前半 | C | 降級條件從 `RateLimitError` 改成 `OpenAIError` | `1 failed, 12 passed` | `assert None is OpenAIError('boom')` |
| ① 前半 | D | 降級那次的 `True` 改成 `False` | `3 failed, 10 passed` | 三個都是 `assert False is True` |
| ① 後半 | A | 算成本用 `settings` | `1 failed, 188 passed` | `assert 136 == 7` |
| ① 後半 | B | 稽核 `model` 用 `decision.model` | `1 failed, 188 passed` | `assert 'big' == 'small'` |
| ① 後半 | C | 回傳 `model` 用 `decision.model` | `1 failed, 188 passed` | `assert 'big' == 'small'` |
| ① 後半 | D | 錯誤分支不寫稽核 | `3 failed, 186 passed` | 三個 `FileNotFoundError`（其中兩個在既有的 `tests/test_chat.py`） |
| ② | A | 超過上限時回預設值 | `1 failed, 199 passed` | `assert 30 == 120` |
| ② | B | `except ValueError` 改成 `except TypeError` | `1 failed, 199 passed` | `ValueError: invalid literal for int() with base 10: 'soon'` |
| ② | C | 拿掉 `headers=` | `3 failed, 197 passed` | 三個 `KeyError: 'retry-after'` |
| ② | D | 503 那段搬到 `append_audit()` 前面 | `1 failed, 199 passed` | `FileNotFoundError` |
| ③ | A | 拿掉「預算用完就不降級」 | `3 failed, 207 passed` | 兩個 `assert 200 == 503`、一個 `assert None is RateLimitError('fake 429')` |
| ③ | B | 拿掉類型的判斷 | `1 failed, 209 passed` | `assert False is True` |
| ③ | C | 清單的 `project_spend_limit_exceeded` 少打 `ed` | `1 failed, 209 passed` | 訊息直接印出 `project_spend_limit_exceeded` |
| ③ | D | `main.py` 拿掉預算用完的分支 | `3 failed, 207 passed` | 三個 `assert 'retry-after' not in Headers(...)` |
| ④ | A | `fallback` 只在成功時記 | `3 failed, 215 passed` | 三個 `KeyError: 'fallback'` |
| ④ | B | 一律記 `fallback_reason` | `2 failed, 216 passed` | `assert 'fallback_reason' not in {...}` |
| ④ | C | 代碼只對 `RateLimitError` 記 | `1 failed, 217 passed` | `KeyError: 'error_code'` |
| ④ | D | 記代碼的兩行搬到 `append_audit()` 後面 | `3 failed, 215 passed` | 三個 `KeyError: 'error_code'` |

**判讀：**

- **① 前半 A：** 強模型被限流時，SDK 會先自己等、再試一次強模型，才輪到降級
- **① 前半 C：** 任何錯誤都降級時，連線斷掉、模型名稱打錯也會去叫便宜模型，原本該回 502 的問題被蓋掉
- **① 後半 A：** 便宜模型回答、照強模型的單價收錢（7 變 136），程式不報錯；呼叫的模型和計費的模型要是同一顆（E96 實驗 C 的同一件事）
- **② D、④ D：** 使用者照樣收到 503，但稽核少了那一筆或少了那一欄，從外面看不出來
- **③ A：** 預算用完時去叫便宜模型，而便宜模型在假的環境裡剛好沒錯，使用者拿到 200；從外面看起來一切正常，其實供應商帳單已經出問題
- **③ C：** 代碼打錯一個字不會報錯，那一種預算用完會被當成限流，使用者被告知「30 秒後再試」
- **④ A：** 降級過、最後還是失敗的請求，稽核裡看不出曾經降級，這正是「錯誤以結果交回」要避免的狀況

**Claude 在試跑環境做過、本人沒有重做的實驗：**

| 改了什麼 | 結果 |
|---|---|
| 降級那次又叫一次強模型 | `4 failed`（`AttributeError: 'NoneType' object has no attribute 'text'` 等） |
| 拿掉「路由選便宜模型就直接呼叫」那一段 | `2 failed`（`assert [0] == [None]` 等：便宜模型被當成有備胎） |
| `call_once()` 只接 `RateLimitError` | `2 failed` |
| 降級那次也用不重試的連線 | `1 failed`（`assert [0, 0] == [0, None]`） |
| `retry_after_seconds()` 的下限寫成 `< 0` | `1 failed`（`assert 0 == 30`） |
| 下限寫成 `< DEFAULT_RETRY_AFTER_SECONDS` | `4 failed, 196 passed`（7 秒、1 秒都被換成 30） |
| `is_budget_exhausted()` 最後一行改成 `return True` | `18 failed`（三個「不是預算」的測試，以及所有靠降級的測試） |

### 挫折與說明不清楚的地方

| # | 發生什麼 | 原因 | 之後的做法 |
|---|---|---|---|
| 1 | `client.with_options(cheap_model=0)` | 具名參數的「名字」是要改的那個設定（`max_retries`），不是模型名稱的變數。Claude 以這個寫法試跑：`10 failed`，`with_options() got an unexpected keyword argument 'cheap_model'` | 提示寫明 `名字=值` 的名字指的是什麼 |
| 2 | 最後一行寫成 `return call_once()`，本人表示寫到這裡沒有想法 | 6 個參數各要交什麼、順序為何 | Claude 給完整的一行與逐格對照表。只改第 1 處就跑的話是 `7 failed`，`call_once() missing 6 required positional arguments`，後面依序列出 6 個名字 |
| 3 | 第一次跑 ① 後半：`37 failed, 152 passed`，全部是 `cost_micro_usd() takes 3 positional arguments but 4 were given` | `outcome.settings`（點，「outcome 的 settings」）寫成 `outcome, settings.max_completion_tokens`（逗號，兩樣東西），多交一格。37 個測試同一個訊息，代表卡在同一行 | Claude 以本人的 `main.py` 重現 37 個紅；只改這一行後 `189 passed`。與 E95 的 `tomllib.loads` 是同一種讀法 |
| 4 | 第 ② 段本人問了三次：供應商回應裡標頭的名字在哪、第 3 格是什麼意思、下限是不是填 `DEFAULT_RETRY_AFTER_SECONDS` | 提示只寫「那個標頭的名字」，沒說在哪裡看得到；第 3 格的提示引用了 E 編號，違反「用檔名與函式名」的約定；「比較用的界線」和「替換用的值」沒有分開講 | Claude 用「包裹外的標籤」解釋標頭，並指出 `tests/fakes.py` 寫標籤的那一行與 `app/main.py` 回 429 時貼同一張標籤的那一行；`ValueError` 用 `uv run python -c "int('soon')"` 自己驗證；下限填 30 的後果由 Claude 試跑給出（上表） |
| 5 | 定案 2 的規格中途改了一次（超過 120：用 30 → 回 120） | Claude 開工前的寫法沒有想清楚 | 在交付第 ② 段測試前說明理由並請本人確認 |
| 6 | Claude 的試跑環境有兩次出現 43 個 `errors`（例如 `127 passed, 43 errors`） | 替身資料庫的伺服器在對話之間停掉，與 repo 無關 | 每次核對前先確認替身伺服器在跑 |

### 限制（誠實記錄）

- **全部是假的模型，沒有遇過真的 429。** 兩種 429 的代碼取自官方文件（10/12 讀）；SDK 的行為是用本機假伺服器量的，回應內容由 Claude 撰寫。真的 OpenAI 回 429 時有沒有 `retry-after`、`x-should-retry`，以及預算用完時實際的代碼與類型，都還沒有驗證
- **「最壞 3 次 HTTP 請求」是推論：** 假的模型站在 SDK 的重試之上，Gateway 層的測試只驗證「強模型那次用了 `max_retries=0`、便宜模型那次沒有」；SDK 實際送幾次，依據是 SDK 原始碼與上面的假伺服器實測
- **便宜模型那次仍可能在 SDK 裡等最多 120 秒**（供應商給 `retry-after` 時），加上兩次各 30 秒的逾時，一個請求可能拖到兩分鐘以上。M4 上雲後 ALB 的閒置逾時預設是 60 秒，連線可能先被切斷，而 Gateway 仍在背後呼叫模型、扣錢。M4 前要決定
- **強模型的 5xx、連線錯誤不再有 SDK 的重試**，直接回 502（定案 3 的代價）
- **決策書 D32 寫「回 503 並告警」，M3 只有稽核的 `error_code`，沒有告警**
- **新的預算代碼會被當成限流**（定案 1 的代價）；`Retry-After` 只認整數秒
- **降級時便宜模型查不到設定沒有處理：** `find_model_config()` 會丟 `ModelNotConfiguredError`，變成框架預設的 500、沒有稽核。正常情況下啟動時已檢查過兩顆模型，走不到
- `error_code` 可能是 `None`（供應商回應不是 JSON 時），稽核會記成 `null`
- 兩種 503 對外的訊息相同，只能從稽核分辨（設計如此）
- **「先看紅」本人只回報了 ② 的 `4 failed, 196 passed`；** ① 前半、③、④ 的先紅只有 Claude 的試跑看過，① 後半本人第一次看到的是挫折 3 的紅。每一段的破壞實驗本人都做了
- **本人與 Claude 都沒有看過變紅的測試：** `test_cheap_route_calls_the_cheap_model_once`、`test_strong_route_answers_without_fallback`、`test_fallback_sends_the_same_messages`、`test_chat_keeps_the_sdk_retry_for_the_cheap_model`、`test_retry_after_accepts_the_maximum`、`test_retry_after_uses_the_default_without_a_header`、`test_chat_audits_no_code_when_the_error_has_none`、`test_chat_audits_no_fallback_when_the_quota_is_used_up`、`test_chat_audits_no_fallback_when_the_routed_model_has_no_settings`
- 降級的驗收（S07）還沒有錄影；真實驗收在步驟 9，降級仍會用模擬的方式呈現

### 面試可用的說法

- 「OpenAI 的限流和預算用完都是 429，而且是同一個例外類別。我用錯誤代碼分辨，而且是反過來只認預算的代碼，因為官方沒有給限流固定代碼。認錯的代價是多打一次會被拒的呼叫，不花錢；如果反過來只認限流，認不得的時候備援會安靜失效。」
- 「動手前我先量了 SDK 遇到 429 的行為：它會照供應商的 retry-after 在請求裡等最多 120 秒，連預算用完也照樣重試，而且我設的 30 秒逾時管不到這段等待。所以強模型那一次我關掉 SDK 的重試，讓降級本身當作重試。」
- 「降級的函式不往外丟錯誤，而是把結果包起來交回，裡面記著有沒有降級。我做過實驗，把記錄降級的那幾行搬到成功的分支，三個測試馬上紅，因為降級過、最後還是失敗的請求在稽核裡看不出來了。」
- 「Retry-After 我照抄供應商的值，但不照單全收：只收 1 到 120 秒的整數，其餘用預設值。上游給的資料，對我來說也是不可信的輸入。」

---

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `16e50d6` | 10/12 09:39 | `style: tidy blank lines` |
| `b8b548b` | 10:39 | `feat: add the model call that falls back to the cheap model when rate limited` |
| `bb43a9f` | 11:05 | `feat: answer from the cheap model when the strong one is rate limited` |
| `4505674` | 12:16 | `feat: return 503 with Retry-After when both models are rate limited` |
| `f64fcde` | 14:27 | `feat: do not fall back when the provider budget is exhausted` |
| `c8e6570` | 16:27 | `feat: audit fallback and the provider error code` |

每一段推送後由 Claude 讀取公開 repo 核對：測試檔與交付的版本相同；`app/fallback.py`、`app/main.py` 與參考寫法只差空行、結尾換行與一行註解（`f64fcde` 的註解錯字於 `c8e6570` 修正）；在試跑環境執行 `c8e6570`：`218 passed`（不需資料庫的 173 個，加上以替身伺服器代替 DynamoDB Local 的 45 個 `integration`）。

---

## E101. 步驟 6：用真實回應確認思考 token 的計費，稽核加上結束原因（2026-10-12 16:45～20:39）

**依據：** 交接檔 `m3-step6-handoff.md` 第 2、5 節；決策書 8.2 的 M3（「用 `gpt-6-sol` 的一次真實回應實證輸出 token 已含思考 token」）、D28（兩顆模型與思考量）、D30（成本以回應的 usage 計算）；E87（思考 token 是否算在輸出裡的待決）、E94 定案 5（輸出上限）、E98 的限制（回答被截斷時看不出來）。

**範圍：**

- 16:45 先定了步驟 6～8 的做法（五項）
- 用一個探測小工具，對兩顆模型各打兩次真的 OpenAI，共 4 次
- 依結果，`chat()` 與稽核加上供應商回報的結束原因（`finish_reason`）
- 另記：老師 10/12 對期末報告與影片的回覆

**生活比喻：** 計程車的錶只有一個，司機想路線的時間也跳在同一個錶上，不是另外收（思考 token 算在輸出裡）。規定最多跑 16 公里，結果 16 公里都在繞路想路線，乘客沒到目的地，車資照算（被截斷的空回答照樣收錢）。

### 16:45 定案（本人決定，五項全數照建議）

| 步驟 | 定案 | 理由 |
|---|---|---|
| 6 | 除了 `gpt-6-sol`，也用**帶輸出上限的 `gpt-6-luna`** 打一次：確認思考 token 是 0、結束原因、回答沒有被截斷或變空 | OpenAI 討論區 2026/4 回報 `gpt-5.4` 同時設 `reasoning_effort: none` 與 `max_completion_tokens` 時思考量失效（4/20 稱已修）；另有「計費 token 多於收到的字」的後續回報未結案。Luna 正是這個組合，M1、M2 的真實呼叫都沒帶上限 |
| 7 | **20 題兩顆模型都真打一次**，存下每題每顆的 token 數（約 US$0.12）；調門檻只重算、不再呼叫 | X% 是簡報與面試的主打數字，實測比估算可信；強模型的思考 token 估不到。取代決策書 M3 的「強模型只呼叫少數幾次」 |
| 8 | CI 跑 `integration` 用 repo 的 `compose.yaml`（`docker compose up -d dynamodb-test`） | GitHub Actions 的服務容器帶不了 `-sharedDb -inMemory` 參數；用同一份設定 |
| 8 | `protect-main` 的「CI 通過才能合併」等 CI 穩定後再加，屆時改成分支流程 | 先讓 CI 跑順 |
| 8 | M3 的 CI：pytest + Trivy 掃容器映像 + CodeQL 預設設定；tfsec 不用，M4 有 Terraform 後用 `trivy config` | tfsec 已停止開發、併入 Trivy；決策書 CI 寫的 tfsec 要改 |

- 第 1、2 項的依據是討論區與第三方網站，這一筆沒有附連結；做到那一步時再對一次官方頁面
- 所有 Action 鎖 commit SHA、過 3 天冷卻期（既有規則）

### 探測：兩顆模型各兩次真實呼叫（19:42，個人電腦）

**工具：** `scripts/probe_usage.py`（Claude 提供，本人執行；交付前 Claude 先以本機假伺服器跑過一次）

- 強模型問「請比較 TCP 與 UDP，各舉兩個適合的使用情境。」（含「比較」，正式上線也會被路由到強模型）；便宜模型問「請用大約 100 個字介紹台灣的夜市文化。」
- 第 1、3 次用設定檔的輸出上限，第 2、4 次故意壓到 16
- `OpenAI(max_retries=0, timeout=60)`：不讓 SDK 重試，一次就是一次，帳才對得上
- 成本用 `cost_micro_usd()` 算，與 Gateway 計費是同一個函式
- 不印金鑰與請求編號；金鑰以 `uv run --env-file .env` 載入，不出現在指令列
- 執行 `uv run --env-file .env python -m scripts.probe_usage`；輸出存為 `docs/logs/m3-step6-usage-probe.log`（使用者資料夾遮成 `<user>`）

**結果：**

| # | 模型（思考量） | 輸出上限 | `finish_reason` | 輸入 token | 輸出 token | 其中思考 | 看得到的回答 | 成本（micro-USD） |
|---|---|---|---|---|---|---|---|---|
| 1 | `gpt-6-sol`（`low`） | 2,000 | `stop` | 24 | 229 | 0 | 306 字（以表格比較） | 2,338 |
| 2 | `gpt-6-sol`（`low`） | 16 | `length` | 24 | 16 | 16 | **0 字** | 208 |
| 3 | `gpt-6-luna`（`none`） | 1,000 | `stop` | 22 | 103 | 0 | 100 字 | 54 |
| 4 | `gpt-6-luna`（`none`） | 16 | `length` | 22 | 16 | 0 | 15 字（半句） | 11 |
| | | | | | | | 合計 | **2,611**（約 US$0.0026） |

- 四次回報的模型名稱都與指定的相同，沒有日期尾碼
- 成本手算：#1 24 × 2 + 229 × 10 = 2,338；#2 24 × 2 + 16 × 10 = 208；#3 22 × 0.1 + 103 × 0.5 = 53.7 → 54；#4 22 × 0.1 + 16 × 0.5 = 10.2 → 11。與 `cost_micro_usd()` 的結果一致

**判讀：**

| # | 看到什麼 | 代表什麼 |
|---|---|---|
| 2 | 上限 16，輸出 16、其中思考 16、回答 0 字 | **思考 token 算在輸出 token 裡。** 如果是另外算，總數會超過上限 16。`cost_micro_usd()` 用「輸出 token × 輸出單價」是對的，不用另外加思考 token；E87 起的待決結案 |
| 2 | 強模型被截斷時回答是空的，照收 208 | 新發現：使用者會拿到 200 加一個空回答，而且被扣錢；當時的稽核看不出這種情況（下面的修改） |
| 1 | 思考量 `low`，這一題的思考 token 是 0 | 這一題模型判斷不用想。只有一個樣本，不能推論強模型都不太思考 |
| 3 | 便宜模型帶上限 1,000：思考 0、100 字用 103 個 token、正常結束 | 討論區回報的那個問題沒有出現；也看不出有多收的 token（中文大約一字一個 token）。M0 第一次呼叫 Luna 時帶過 50 的上限，結果相同 |
| 4 | 便宜模型被截斷：給了半句 | 便宜模型截斷時給半句，強模型截斷時可能整個是空的，兩顆的行為不同 |

**輸出上限：維持 1,000 與 2,000，步驟 7 再定。** 只有一個樣本，而且強模型這一題沒有思考，看不出它需要多少空間。

- 設太大：一次最多可能超扣很多，2,000 個輸出 token 等於最多 20,000 micro-USD
- 設太小：強模型的回答可能整個是空的（#2）
- 步驟 7 有 20 題、兩顆共 40 個真實回應，用那批的最大值加上餘裕來定

### 定案（19:56 本人決定，照建議）：截斷記進稽核

| 選項 | 做法 | 評估 |
|---|---|---|
| **A（採用）** | `chat()` 交回的結果多帶 `finish_reason`，稽核加一欄；行為不變：照樣回 200、照樣計費 | 截斷看得到、事後能統計，補上 E98 列的限制 |
| B | A 再加上「截斷且回答是空的」時回 502、不扣使用者的錢 | 不選：錢已經付給供應商，等於 Gateway 自己吸收成本，而且會改到行為；等有真實的統計數字再說 |
| C | 不做，只記在限制裡 | 不選：問題剛被實測證實，留著不處理說不過去 |

**弱點：** 使用者端看不出被截斷（回應的 JSON 沒有這一欄），只有稽核看得到。

### 程式的修改（本人撰寫）

`app/providers/openai_client.py`：`ChatResult` 由 5 個欄位變 6 個，`chat()` 照抄供應商回報的值。

```python
    reasoning_tokens: int
    # 結束原因："stop" 是正常說完，"length" 是被輸出上限截斷
    finish_reason: str | None
```

```python
        reasoning_tokens=reasoning_tokens,
        finish_reason=response.choices[0].finish_reason,
    )
```

`app/main.py`，成功時記進稽核：

```python
    record["reasoning_tokens"] = result.reasoning_tokens
    # 結束原因：被輸出上限截斷（length）時，回答可能只有一半甚至是空的，但照樣計費
    record["finish_reason"] = result.finish_reason
```

- 只有成功的紀錄有 `finish_reason`；呼叫模型失敗的紀錄沒有回應，也就沒有這一欄
- 降級時記的是實際回答的那顆模型的結束原因（`result` 來自 `chat_with_fallback()` 交回的那一次）

### 測試（Claude 整份提供；測試數 218 → 223）

- `tests/fakes.py`：假的模型多一個 `finish_reason`（預設 `"stop"`），要模擬被截斷時給 `"length"`
- `tests/test_openai_client.py`：第一個測試的預期多一欄 `finish_reason="stop"`；新增 `test_chat_returns_the_finish_reason`（假回應給空回答與 `"length"`，強模型、上限 16，檢查原樣交回）
- `tests/test_chat_truncation.py`（新檔，4 個；用 `FakeDynamoDB`，不需要 Docker）：

| 測試 | 檢查 |
|---|---|
| `test_chat_audits_the_finish_reason_of_a_normal_answer` | 正常回答 → 稽核 `finish_reason: stop` |
| `test_chat_audits_a_truncated_answer` | 被截斷的空回答 → 200、`reply` 是空字串、稽核 `finish_reason: length` |
| `test_chat_still_charges_a_truncated_answer` | 被截斷照樣計費：稽核成本 136；資料庫依序收到事前的 0 與 136 |
| `test_chat_audits_no_finish_reason_when_the_model_fails` | 模型出錯（`OpenAIError`）→ 502，紀錄沒有 `finish_reason` |

**過程（本人執行）：**

| 時間點 | 結果 |
|---|---|
| 只存好三個測試檔 | `4 failed, 219 passed`：兩個 `KeyError: 'finish_reason'`（稽核沒有這一欄）、`TypeError: ChatResult.__init__() got an unexpected keyword argument 'finish_reason'`、`AttributeError: 'ChatResult' object has no attribute 'finish_reason'` |
| 改完 `openai_client.py` 與 `main.py` | `223 passed` |

### 破壞實驗（本人執行，三個；做完改回 → `223 passed`；結果與 Claude 事先給的預期相同）

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| A | `chat()` 的結束原因寫死成 `"stop"` | `2 failed, 221 passed` | `test_chat_audits_a_truncated_answer`、`test_chat_returns_the_finish_reason`，都是 `assert 'stop' == 'length'` |
| B | `main.py` 不記結束原因 | `2 failed, 221 passed` | 兩個 `KeyError: 'finish_reason'` |
| C | `main.py` 的結束原因寫死成 `"stop"` | `1 failed, 222 passed` | `test_chat_audits_a_truncated_answer`：`assert 'stop' == 'length'` |

**判讀：**

- **A：** 期望 `"stop"` 的 `test_chat_maps_response_fields` 沒有紅，因為寫死的值剛好等於它期望的值。**預期值等於寫死的值時，測試抓不到寫死**；所以才另外寫一個期望 `"length"` 的測試
- **C：** 只紅一個，原因同上：正常回答的那個測試期望的也是 `"stop"`
- **B：** 使用者照樣拿到 200，從外面看不出稽核少了一欄

### 限制（誠實記錄）

- **只有 4 次、各一題。** 思考量依題目而變（#1 的思考是 0）；強模型一般會想多少，要看步驟 7 的 20 題
- **輸出上限仍是暫定**（1,000、2,000）
- **使用者端看不出被截斷：** 回應只有 `reply` 與 `model`；空的回答照樣扣額度，沒有退費、提醒或重試（選項 A 的代價）
- 結束原因照抄供應商的值；`content_filter` 等其他值沒有特別處理，也沒有測試
- `test_chat_still_charges_a_truncated_answer` 與 `test_chat_audits_no_finish_reason_when_the_model_fails` 兩個測試，本人與 Claude 都沒有看過它們變紅
- 探測的四次成本沒有和 OpenAI 後台逐筆核對（M2 時後台的金額顯示為 `$0.00`，這種量級對不出來）
- 探測小工具需要金鑰，只能在個人電腦執行；沒有自動測試，也不進 CI

### 面試可用的說法

- 「思考 token 怎麼計費，我沒有用猜的。我把強模型的輸出上限壓到 16 打一次：16 個輸出 token 全是思考，回答一個字都沒有，供應商照收。這證明思考 token 算在輸出 token 裡，成本函式不用另外加；也讓我發現使用者可能拿到一個空的回答卻被扣錢，所以稽核加了結束原因。」
- 「原本就有一個期望 stop 的測試，但我做破壞實驗把結束原因寫死成 stop，它照樣是綠的。測試期望的值剛好等於寫死的值，就抓不到寫死；所以我另外寫了一個期望 length 的測試，再用同一個實驗確認它會紅。」

### 老師 10/12 對期末呈現的回覆（本人轉述，20:07）

| 項目 | 回覆 |
|---|---|
| 期末報告 | 本人報告，抓 **10 分鐘，含 Demo 的呈現**；主軸放在 Demo，等完整的 Demo 做出來時以 Demo 呈現為主 |
| 給廠商的影片 | 由報告摘要成 **6 分鐘（含 Demo）**；緯育會拿去向各家企業推廣，要放進所有精華 |
| 版本 | 兩個版本分開做：10 分鐘的期末報告版、6 分鐘的廠商影片版；主軸是 10 分鐘的報告 |

- **取代：** 10/5 的「6 分鐘主影片 + 10～15 分鐘技術版影片，一份簡報當兩支影片的共同骨架」（D41、E79、E84）
- E100 列的五個問題中，「6 分鐘是否為硬上限」由這個回覆取代；其餘四個（插在簡報頁中間的短錄影、終端機畫面、降級只能模擬、X% 能否估算）本人轉述的回覆中沒有提到
- 簡報與旁白稿的改版在另一個對話處理，不記在這一筆

---

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `4460844` | 10/12 19:46 | `chore: add the provider usage probe and its first log`（`fd5ad6c..4460844`） |
| `f67ed09` | 20:39 | `feat: audit why the model's answer ended`（`4460844..f67ed09`） |

推送後由 Claude 讀取公開 repo 核對：探測小工具、日誌與五個程式和測試檔都與交付的版本相同；在試跑環境執行 `f67ed09`：`223 passed`（不需資料庫的 178 個，加上以替身伺服器代替 DynamoDB Local 的 45 個 `integration`）。

---

## E102. 簡報 v2.0：拆成 10 分鐘報告版與 6 分鐘廠商影片版（2026-10-12 20:27～21:26）

**依據：** 老師 10/12 的呈現方式（E101、決策書 v2.9 待改項目第 20 項）；老師 10/12 對簡報 v1.2 的回饋，以及老師給同學 Katherine 的投影片建議（本人轉述，見下表）；決策書 8.3 第 7 項、11.6（簡報版號）。

**範圍：** 只改簡報、旁白稿與影片的做法，程式與測試不動。產出 `docs/slides/llm-gateway-slides-10min-v2.0.pptx`（17 頁）、`docs/slides/llm-gateway-slides-6min-v2.0.pptx`（15 頁）、`docs/slides/narration-10min-v2.0.md`、`docs/slides/narration-6min-v2.0.md`；另做一段動畫樣片（MP4，不進 repo）。v1.2 的簡報與旁白稿留在 repo，沒有刪。

**生活比喻：** v1.2 像一本說明書，什麼都寫在頁面上；v2.0 改成電影分鏡，每格只放一個畫面和一句台詞，其餘交給講的人。

### 老師與本人的意見（本人轉述）

| 時間 | 來源 | 內容 |
|---|---|---|
| 20:27 | 老師對簡報 v1.2 | 技術與品質 OK，內容沒有意見；p.12 之後的技術細節要篩選，否則老闆看了會睡著；p.7～p.8 只留環節的標題、細節用講的；p.9 只放圖；多花篇幅講個資（PII）與 AI 節費，這是現在老闆最想聽的；可參考同學 Katherine 的寫法 |
| 20:48 | 老師給同學 Katherine 的建議（本人表示同樣適用） | ① 字多的地方只留重點字，少量用一句話 ② 能改成圖或 icon 的就改 ③ 一頁不超過 3 個重點，最多 5 個 ④ 要有 Agenda ⑤ 標題要與 Agenda 一樣 ⑥ 盡量用秉鴻老師給的標題（一頁講完、想解決的問題、解決前後、解法提綱、技術實踐），說故事能力很重要。今天的簡報是模擬未來主管面試 |
| 21:06 | 本人 | Agenda 項目太多時可以加子目錄 |
| 21:08 | 本人 | 越吸睛越好；投影片簡單，字幾乎用講的；畫面要嘛動畫、要嘛 Demo、要嘛圖片 |
| 21:10 | 本人 | 希望用原生、專業的影片動畫處理之後的內容，要像很厲害的動畫，不是單純的 PPT |
| 21:26 | 老師（本人轉述） | 主管也知道大家用 AI 做簡報，用 AI 做會被認為沒掌握內容；一定要熟悉內容，面試不能用 ChatGPT。降低 AI 感的方法：① 先給 AI 一份自己手作的版本 ② 文字 14～16 pt 以上 ③ 標題用自己訂的 ④ 請第二個 AI 扮成小學生或指定的受眾看一次、給建議 ⑤ 去掉 emoji ⑥ 以圖為主，能自己做圖更好 |

**老師說的頁碼：** 對照的是 v1.2 右下角印的頁碼（7＝現成方案拆解、8＝網路邊界、9＝稽核）。v1.2 插入兩頁新頁時右下角頁碼沒有重編（第 2～4 張都印 3），所以和 PDF 頁數差一頁；照 PDF 數的話 7＝成本效益，但成本效益本來就要加大，兩種讀法的改法相同。v2.0 的頁碼由版面自動產生。

### 定案

| 項目 | 做法 | 不選的做法與原因 | 誰定 |
|---|---|---|---|
| 10 分鐘報告的 Demo | 播錄影、本人現場口述 | 現場操作：Console 的 ALB 只放行本人 IP（決策書 4.4）、雲端資源平常是關的、模型回應時間不固定，卡住就得砍別段；同一批錄影也能直接剪 6 分鐘版 | 本人 20:48 |
| 個資的 Demo | 請 AI 原樣唸一次（沿用 S04 的做法） | Console 多一格「模型收到的內容」：Gateway 的回應要多一個欄位，等於改回應格式，多一份 M6 的工作 | 本人 20:48 |
| 技術細節 20 頁 | 不上台；留在 v1.2 當 Q&A 與面試的備用 | 搬進新簡報：不符合一頁 3 個重點的規則 | Claude 提出，本人未反對 |
| 動畫 | Claude 用程式逐格算圖做成 MP4 片段，簡報頁只當放片段與 Demo 錄影的框 | 生成式影片 AI（Runway、Sora、Veo）：字與數字無法保證正確；Canva、Gamma 的自動動畫：制式，可能改寫內容；AI 虛擬主播：廠商要看本人 | 本人 21:21 |
| Demo 錄影 | 用會依點擊自動放大的錄影工具（Cap；替代方案 FocuSee） | 一般錄影：觀眾要自己找重點 | Claude 建議；工具未定（見待決） |
| 組裝 | 10 分鐘版在 PowerPoint 播放，片段嵌入頁面、換頁用「轉化（Morph）」；6 分鐘版用 CapCut 上繁中字幕與配樂 | — | Claude 建議 |
| 後續 | 簡報會隨里程碑持續更新；簡報與影片的工作交給另一個對話繼續 | — | 本人 21:21 |

### 簡報 v2.0 的頁序

- **10 分鐘報告版（17 頁）：** 封面 → Agenda → 01 一頁講完 → 02 想解決的問題 → 03 解決前後 → 04 解法提綱｜三道關 → 04 解法提綱｜放到 AWS 上 → 05 技術實踐 → 節費 ① → 節費 ② → 個資 ① → 個資 ② → 額度 → 看不到的地方 ①（拆解 LiteLLM）→ 看不到的地方 ②（網路邊界）→ 06 結語 → 謝謝聆聽
- **6 分鐘廠商影片版（15 頁）：** 開場鉤子（429）→ 封面 → Agenda → 01 想解決的問題 → 02 解法提綱｜三道關 → 02 解法提綱｜放到 AWS 上 → 03 技術實踐（節費 ①②、個資 ①②、額度、看不到的地方 ①②）→ 04 結語 → 片尾卡

### 規則怎麼套用

| 規則 | 做法 |
|---|---|
| 重點字、少量一句話 | 每頁只留標題、一句故事線（橘字）和幾個關鍵字；說明文字移到旁白稿 |
| 圖與 icon | 每頁都有圖示、示意圖或截圖；Demo 頁左邊是放錄影的框，現在先放示意或實測畫面 |
| 一頁不超過 3 個重點 | v1.2 的六關改成「管人、管錢、管資料」三組；解決前後由六列減為三列（節費、個資、額度），與 Demo 三章一一對應 |
| Agenda 與子目錄 | Agenda 是時間軸；解法提綱下有「三道關、放到 AWS 上」，技術實踐下有「節費、個資、額度、看不到的地方」 |
| 標題與 Agenda 一樣 | 每頁標題寫成「Agenda 項目｜子目錄」，左上角是 Agenda 編號，右上角的圓點標出目前在第幾段 |
| 秉鴻老師的標題 | 一頁講完、想解決的問題、解決前後、解法提綱、技術實踐全數沿用；故事線：管不住 → 裝水表 → 看它跑起來 → 看不到的地方也有把關 |
| 老師對 v1.2 的意見 | p.7 拆解只留三張卡的標題；p.8 網路邊界只留方塊名稱；p.9 稽核改放 S04 的稽核截圖並圈出重點；節費與個資各兩頁，合計約占 10 分鐘版腳本的四成（v1.2 主影片裡兩項合計約 1 分 20 秒） |

### 旁白稿 v2.0（同日）

| 項目 | 10 分鐘版 | 6 分鐘版 |
|---|---|---|
| 檔案 | `docs/slides/narration-10min-v2.0.md` | `docs/slides/narration-6min-v2.0.md` |
| 語速假設 | 每分鐘 200 字（現場報告比錄音慢；v1.x 用 220） | 每分鐘 220 字 |
| 旁白 | 1,365 字、約 410 秒 | 586 字、約 160 秒 |
| 配給時間 | 547 秒（9 分 07 秒），留約 1 分鐘給臨場 | 334 秒（5 分 34 秒），留 26 秒給轉場與片尾 |
| Demo／技術實踐 | 第 8～13 頁 275 秒，約一半 | 第 7～13 頁 220 秒，約三分之二 |

每頁另記「畫面計畫」：要配哪段動畫（A1～A11）或哪段錄影（S02、S04、S05、S08、Console、Grafana）。

### 動畫樣片

- `pii-masking-sample.mp4`（8.5 秒，1920×1080，30 fps）：掃描線掃過 → 身分證字號變亂碼 → 變成 `[TW_ID]` → 模型只收到標籤；內容取自 S04 的實測句子
- 做法：HTML 頁面依時間畫出每一格，用無頭瀏覽器逐格截圖，再以 ffmpeg 壓成 MP4；算一次約 80 秒
- 影片檔不進 repo（既有規則）；原始碼與重建腳本存在 claude.ai Project 的 `claude/slides-tools/`

### 檢查（Claude 執行）

- 兩份 PPTX 都通過 pptx 檢查工具；32 頁全部轉成圖片逐頁看過。發現並修正：標題預設置中（改靠左）、關鍵字反白造成斷行錯位、卡片文字最後一個字單獨換行、Agenda 最左邊的字貼近頁緣
- 從公開 repo（`72a5673`）重跑一次「準備素材 → 產生簡報 → 字型修正 → 檢查」：兩份都通過
- 頁面上的數字逐項對照來源：20 倍（決策書的單價表：輸入 $0.10 對 $2、輸出 $0.50 對 $10）、US$11（決策書的成本章）、S02 的 609／818／1,039 與 429（截圖原文）、S04 的原句與稽核紀錄（截圖原文）
- 字型：主題的中文字型由空白改為微軟正黑體，避免 PowerPoint 退回新細明體

### 限制（誠實記錄）

- **字還要再少一輪。** 本人 21:08 要求「字幾乎用講的、畫面只放動畫、Demo 或圖片」，v2.0 是那之前的版本；下一輪在交接的對話做
- **很多畫面還是佔位：** X%、A、B（M3 步驟 7）；S05 路由錄影（M3）；S08 網路（M4）；雲端稽核 S14（M5）；Console 與 Grafana（M6）。對應的頁面都有狀態標籤
- **動畫只做了一段樣片**，還沒放進簡報；A1～A11 是建議清單
- **時間全是估的**，兩版都還沒計時試講
- **版面只在 LibreOffice 轉出的圖上檢查過。** 檢查環境沒有微軟正黑體，本人要用 PowerPoint 自己翻一遍
- 同學 Katherine 的寫法沒有看到
- 「解決前後」的「之前」是情境假設，頁面下方有註明
- 狀態標籤在定稿時要拿掉或改寫，否則給廠商看的影片會像沒做完
- 產生簡報的程式不在 repo，只存在 Project；要不要放進 repo 由本人決定
- **v2.0 還有小於 14 pt 的字**（頁尾 10、狀態標籤 11、錄影框標籤與註腳 11～12、Agenda 子目錄 13），不符合老師 21:26 說的 14～16 pt 以上
- **標題的子目錄與每頁的故事線是 Claude 擬的**，還不是本人自己訂的；老師 21:26 要求標題用自己訂的
- **整份簡報是 AI 先產生、本人再看**，正是老師 21:26 說的「AI 感」來源；下一輪改成本人先手作、AI 再修（見交接檔）
- 動畫路線（本人 21:21 同意）在老師 21:26 的提醒之後還要再收斂：動畫只用在本人實測內容的示意，A1～A11 精簡；Demo 以本人自己的錄影為主

### 給後面階段的要求

| 階段 | 要求 | 原因 |
|---|---|---|
| M3 步驟 7 | 存下兩種總成本（全部用強模型、智慧路由） | 第 10 頁與結語的 X%、A、B |
| M6 | Grafana 要有「依使用者、依模型的花費」圖 | 節費 ② 用它回答「錢花在誰身上」 |
| M6 | Demo 錄影用兩個帳號：額度正常的錄路由與個資，額度很小的錄被擋 | 同一個帳號錄到一半額度不夠，強模型那題可能先被擋 |
| M6 | 個資那句沿用 S04 已驗證過的格式，錄之前先在本機跑一次，確認四類都被遮 | Demo 是兩版的主角 |

---

## 決策書 v2.9 待改項目

| # | v2.8 的位置 | 要改什麼 |
|---|---|---|
| 1 | D34、PART 9「開發機」 | 修訂為：金鑰、`.env` 與真實呼叫只在個人電腦（E94） |
| 2 | D30、D8、12.5「沒有單價時的錯誤類型…」、D22（repo 結構） | 設定檔定案：TOML，`app/config.toml`，由 `app/config.py` 在啟動時讀取；路由會用到的模型缺設定就拒絕啟動。repo 結構加上 `app/config.toml`、`app/config.py`、`app/router.py`（E94 定案 1、2） |
| 3 | D8、8.2 的 M3 | 路由函式 `choose_model()`（`app/router.py`）吃遮罩後的文字與路由規則，回傳模型與理由（`length`、`keyword`、`default`）；思考量由模型設定提供。先看字數、再看關鍵字；關鍵字不分大小寫（E94 定案 2、E97） |
| 4 | D45、D30、2.2 流程圖 [4]、12.5「沒有單價時的錯誤類型…」 | 成本以實際拿到回答的那次請求所指定的名稱查單價；查單價的時機移到呼叫模型之前（E94 定案 3）。實作：`find_model_config()` 在呼叫前查設定，查不到丟 `ModelNotConfiguredError`；`cost_micro_usd()` 改收設定物件；`app/pricing.py` 不再有 `PRICES`；`main.py` 啟動時讀設定檔（E96）。降級後照便宜模型的設定計費（E100） |
| 5 | 3.2 的 `audit` 表、D10、D38 | 稽核新增 `route_reason`、`routed_model`、`provider_model`（E98）與 `fallback`、`fallback_reason`、`error_code`（E100），皆已實作；`model` 改為記實際回答並計費的名稱（降級後是便宜模型）；回給使用者的 `model` 也是這個名稱（E94 定案 3、4；E98；E100）。`fallback` 只出現在走到呼叫模型的紀錄；`error_code` 只記供應商回應的錯誤（`APIError`）的短代碼，不記訊息 |
| 6 | 7.10、7.9「預扣」、12.5「預扣」那一列、3.4 | 預扣 M3 不做，留到 M5；M3 新增每顆模型的輸出上限（`max_completion_tokens`），並說明強模型下超扣的幅度（E94 定案 5）；`chat()` 已把上限帶給 OpenAI，數字仍是暫定（E98） |
| 7 | D30、4.2 應用層、8.2 的 M3 | 補上設定檔的做法：`[routing]` 指名兩顆模型，`[models.名稱]` 放各自的思考量、輸出上限、單價；`load_config()` 讀進來就檢查（路由用到的模型要有設定、數字要是大於 0 的整數、關鍵字不能是空白、不能少欄位），有問題丟 `ConfigError`（E95） |
| 8 | 11.5 截圖規範（推送前的檢查） | 新增：簡報開著時會產生 `~$` 開頭的鎖定檔，已列入 `.gitignore`；推送前照檔名逐一加入，不用 `git add .`（E95） |
| 9 | 12.5「沒有單價時的錯誤類型與對使用者的回應」、2.2 的回應對照表、D37 | 查不到模型設定時：回 500 `Internal server error`，稽核記 `status: error` 與 `error_type: ModelNotConfiguredError`，不呼叫模型、不扣錢；12.5 該列劃掉（E97 定案 1；E98 已實作） |
| 10 | 2.2 流程圖 [4] 與「M2 實作後的順序」、4.2 應用層、D22（repo 結構） | 補上步驟 4 之後的順序：加 0 → 選模型並記理由 → 查模型設定（500）→ 呼叫模型（帶思考量與輸出上限）；設定是領用窗口 `get_config()`；repo 結構加上 `tests/test_chat_routing.py`（E98） |
| 11 | PART 11（11.1 簡報結構、11.6 版號）、8.3 第 7 項 | 簡報 v1.2 的頁序：封面 → 一頁講完 → 想解決的問題 → 解決前後 → 解法提綱 → 技術實踐 → 技術細節 20 頁 → 附錄；影片分鏡的記號只留在附錄；狀態標籤改用讀者看得懂的字。旁白稿 v1.2 補上新增兩頁的旁白與「示範畫面怎麼接」（片段對照表）；11.1 的時間預算改為主影片旁白約 4.3 分鐘（E99） |
| 12 | D10、D32、2.2 的回應對照表、PART 9「供應商 429」、8.2 的 M3 | 降級的實作定案（E100）：強模型被限流 → 便宜模型一次；兩顆都被限流 → 503 附 `Retry-After`（照抄供應商 1～120 的整數秒、超過回 120、其餘 30）；供應商預算用完 → 不降級、503 不附 `Retry-After`；其他供應商錯誤 → 502；兩種 503 的訊息相同。兩種 429 用排除法分辨：代碼是 `insufficient_quota`、`credit_balance_exhausted`、`project_spend_limit_exceeded`、`organization_spend_limit_exceeded`、`organization_usage_limit_exceeded` 之一，或類型是 `insufficient_quota` → 預算用完，其餘當限流。`app/fallback.py` 的 `chat_with_fallback()` 不論成敗都以 `CallOutcome` 交回，不往外丟錯誤 |
| 13 | D10、3.4（SDK 重試與逾時） | 強模型那次 `with_options(max_retries=0)`，便宜模型保留 SDK 的 1 次重試；最壞從 4 次 HTTP 請求降為 3 次。補上 SDK 的實測（假伺服器）：對 429 會重試，連預算用完也重試；照 `retry-after` 等，最多 120 秒；每次 30 秒的逾時不含重試前的等待（E100） |
| 14 | 12.5（新增兩列） | ① 便宜模型那次 SDK 可能等最多 120 秒、加上兩次各 30 秒的逾時，與 ALB 預設 60 秒閒置逾時的衝突：M4 前決定（關掉便宜模型的重試，或調整 ALB 逾時）。② D32 的「告警」：M3 只有稽核的 `error_code`，告警機制在 M4～M6 決定（E100） |
| 15 | D22（repo 結構） | `app/` 加上 `fallback.py`（降級、兩種 429 的分辨、`Retry-After`）；`tests/` 加上 `test_fallback.py`、`test_chat_fallback.py`（E100） |
| 16 | D30、3.4、8.2 的 M3 | 思考 token 已含在輸出 token 裡（E101 實測：上限 16 時輸出 16、其中思考 16）；成本 = 輸入 × 輸入單價 + 輸出 × 輸出單價，不另加思考 token；8.2 M3 的「實證」那一句改為已完成 |
| 17 | 3.2 的 `audit` 表、D38 | 稽核新增 `finish_reason`（只有成功的紀錄有；`stop` 正常說完、`length` 被輸出上限截斷）；被截斷照樣回 200、照樣計費，使用者的回應沒有這一欄（E101 選項 A） |
| 18 | 8.2 的 M3（驗證與成本）、6.x 的 OpenAI 預估 | 20 題測試集兩顆模型都真打一次、存下每題每顆的 token 數（約 US$0.12），調門檻只重算、不再呼叫；取代「強模型只呼叫少數幾次」（E101） |
| 19 | 8.2 的 M3、M6、10.3、D22 | CI 定案：`integration` 用 repo 的 `compose.yaml` 起 `dynamodb-test`；`protect-main` 的「CI 通過才能合併」等 CI 穩定後再加，屆時改成分支流程；M3 的 CI 為 pytest + Trivy（容器映像）+ CodeQL 預設設定；tfsec 不用（已停止開發、併入 Trivy），M4 有 Terraform 後用 `trivy config`；Action 鎖 commit SHA、過 3 天冷卻期（E101） |
| 20 | D41、PART 9「呈現方式」、PART 11（11.1～11.3、11.6）、8.3 第 6、7 項、8.4 第 2 項、8.5 時程 | 呈現改為：**10 分鐘期末報告（含 Demo，主軸是 Demo）與 6 分鐘廠商影片（含 Demo，緯育推廣用），兩個版本分開做**；取代「6 分鐘主影片 + 10～15 分鐘技術版、一份簡報當共同骨架」。8.4 砍除順序第 2 項（技術版影片縮短）失效；11/4～11/6 的影片排程改寫（E101；簡報與旁白稿的改版另記） |
| 21 | D22（repo 結構） | `scripts/` 加上 `probe_usage.py`（真實用量探測，只在個人電腦執行）；`tests/` 加上 `test_chat_truncation.py`；`docs/logs/` 加上 `m3-step6-usage-probe.log`（E101） |
| 22 | PART 11（11.1、11.6）、8.3 第 7 項 | 簡報 v2.0：拆成 10 分鐘報告版（17 頁）與 6 分鐘廠商影片版（15 頁）兩份簡報、兩份旁白稿（`narration-10min-v2.0.md`、`narration-6min-v2.0.md`）；頁序、Agenda 與子目錄見 E102；每頁標題寫成「Agenda 項目｜子目錄」；技術細節 20 頁留在 v1.2 當 Q&A 備用。取代第 11 項的頁序與 11.1 的時間預算：10 分鐘版配給 9 分 07 秒（現場語速每分鐘 200 字）、6 分鐘版 5 分 34 秒（每分鐘 220 字）。補上老師 10/12 的簡報規則：一頁不超過 3 個重點（最多 5）、字 14～16 pt 以上、標題用本人訂的、去 emoji、以圖為主（E102） |
| 23 | 3.1 Demo 腳本、8.2 的 M6、PART 11（影片製作） | Demo 改為三章：節費（兩題路由、省多少、Grafana 依使用者與模型的花費）、個資（請 AI 原樣唸一次、稽核反查）、額度（用完被擋）；10 分鐘報告播錄影、本人現場口述；錄影用兩個帳號與會自動放大的錄影工具；動畫由 Claude 以程式算圖成 MP4、只用在本人實測內容的示意；10 分鐘版用 PowerPoint 的轉化（Morph）組裝，6 分鐘版用 CapCut 上繁中字幕（E102） |

---

## 目前進度（2026-10-12 21:26）

- 交接檔第 2 節的事項已回覆（E94、E100）
- M3 開工前五項定案 ✅（E94）
- 步驟 1（設定檔、讀取與檢查）✅（E95，已推送 `7cb56ed`）
- 步驟 2（單價改讀設定檔、加入 `gpt-6-sol`、查設定移到呼叫模型之前）✅（E96，已推送 `8907063`）
- 步驟 3（路由函式 `choose_model()`）✅（E97，已推送 `81a87c2`）
- 步驟 4（路由接進對話入口：領用窗口、500、輸出上限、兩個模型名稱）✅（E98，已推送 `fda869a`）
- 簡報 v1.2（照老師建議的結構重排，34 頁）與旁白稿 v1.2 ✅（E99）
- 步驟 5（降級：限流降級一次、兩顆都限流回 503 附 `Retry-After`、預算用完不降級、稽核 `fallback`／`fallback_reason`／`error_code`）✅（E100，已推送 `c8e6570`）
- **步驟 6（真實回應：思考 token 算在輸出 token 裡、被截斷的空回答照樣計費；稽核加 `finish_reason`）✅（E101，已推送 `f67ed09`）；目前 `223 passed`（其中 45 個是 `integration`）**
- 步驟 7、8 的做法已定案（E101 的 16:45 定案）
- 老師 10/12 回覆：10 分鐘期末報告（含 Demo）與 6 分鐘廠商影片，兩個版本分開做（E101）；簡報改版在另一個對話
- 簡報 v2.0（10 分鐘 17 頁、6 分鐘 15 頁）、旁白稿 v2.0 與一段動畫樣片 ✅（E102）；字再少一輪、本人手作版與動畫片段，交給另一個對話繼續
- 下一步：步驟 7（20 題測試集，兩顆模型都真打：算省下的比例 X%、調整 300 字與關鍵字、定輸出上限；**要金鑰，只在個人電腦做**）
- 下一筆證據是 **E103**

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| ~~查不到模型設定時對使用者的回應（決策書 12.5、E87、E96）~~ | ✅ 10/10 定案：回 500、固定訊息、寫稽核（E97）；步驟 4 實作 | — |
| ~~兩種 429 怎麼分辨；兩顆都限流時 `Retry-After` 的值；SDK 重試與降級的疊加~~ | ✅ 10/12 定案並實作（E100） | — |
| 輸出上限的數字 | 暫定 `gpt-6-luna` 1,000、`gpt-6-sol` 2,000；步驟 6 只有一個樣本，維持暫定，用 20 題的最大值加餘裕來定（E101） | 步驟 7 |
| ~~輸出 token 數是否已包含思考 token（E87）~~ | ✅ 10/12 實證：思考 token 算在輸出 token 裡，成本函式不用改（E101） | — |
| 被截斷的回答要不要告知使用者、要不要不扣錢（E101 選項 B） | M3 只記進稽核；等步驟 7 與驗收看到真實的截斷比例再說 | M3 結案時 |
| 路由門檻的數字（300 字、關鍵字清單）與中英文字數的算法（決策書 12.5） | 用 20 題測試集調整；規則的形式不變 | 步驟 7 |
| ~~CI 怎麼跑 `integration` 測試；CodeQL（E89、M1 報告）~~ | ✅ 10/12 定案（E101）：`compose.yaml` 起 `dynamodb-test`；pytest + Trivy + CodeQL 預設設定；步驟 8 實作 | — |
| `protect-main` 加「CI 通過才能合併」 | CI 跑穩之後再加，屆時改成分支流程（E101） | 步驟 8 之後 |
| 降級（S07）的驗收怎麼呈現（E100） | 真的限流做不出來，用假的模型模擬；畫面上是否標「模擬」待定（老師 10/12 的回覆沒有提到） | 步驟 9 |
| 降級時便宜模型查不到設定（E100） | 正常走不到（啟動時已檢查）；要處理的話與 500 那條路合併，留稽核 | M3 結案時決定 |
| SDK 在便宜模型那次的等待與 ALB 閒置逾時（E100） | 評估關掉便宜模型那次的 SDK 重試，或調整 ALB 逾時；上雲後量一次 | M4 前 |
| 供應商預算用完的告警（D32、E100） | M3 只記稽核的 `error_code`；告警的做法另定 | M4～M6 |
| 預扣（7.10） | M3 不做（E94 定案 5） | M5 |
| M7 是否開工（E79） | 第一個時段的條件：M3 與 CI 在 10/16（五）前完成 | 10/16、10/30、11/1 |
| ~~和老師討論示範影片的結果（E100）~~ | ✅ 10/12：10 分鐘期末報告（含 Demo，主軸是 Demo）與 6 分鐘廠商影片，兩個版本分開做（E101）；簡報與旁白稿的改版在另一個對話 | — |
| 簡報計時試講（E84、E102） | 10 分鐘報告版至少計時試講一次（原本是主影片）；v2.0 的配給是 9 分 07 秒 | 10/18 前 |
| 簡報下一輪（E102） | 本人先手作（標題、故事線、至少一張自己畫的圖）→ AI 再修；字 14 pt 以上、畫面只放圖、Demo 或動畫；改完請第二個 AI 扮受眾看一次 | 交接的簡報對話 |
| 動畫片段的數量與清單（E102） | 只做本人實測內容的示意；先做不需要新數字的（開場 429、三道關、架構封包、掉帳過程），X% 等步驟 7 | 交接的簡報對話 |
| Demo 錄影工具與授權（E102） | Cap（個人免費、商用一次 US$58）或 FocuSee；6 分鐘影片給緯育推廣，保守當商用 | M6 前 |
| 產生簡報的程式要不要放進 repo（E102） | 目前只存在 claude.ai Project 的 `claude/slides-tools/` | 本人決定 |
| ~~主影片超過 6 分鐘時先拿掉什麼（E99）~~ | 由 10/12 的新呈現方式取代（E101） | — |
| 從 M2 帶過來、M4 前要定的項目（稽核搬進 `audit` 表、`compose.yaml` 加 Gateway、`app/db.py` 連真的 AWS、強一致讀取、停用 Key 的腳本、`/docs` 是否關閉、`m1-gateway` 金鑰 11/2 到期） | 見 `m2-evidence-log.md` 的待決表與決策書 12.5 | M4 前 |
