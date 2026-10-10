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
| 10 | 結案：M3 結案報告、決策書 v2.9、簡報 v1.2 | — | — | — |

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

## 決策書 v2.9 待改項目

| # | v2.8 的位置 | 要改什麼 |
|---|---|---|
| 1 | D34、PART 9「開發機」 | 修訂為：金鑰、`.env` 與真實呼叫只在個人電腦（E94） |
| 2 | D30、D8、12.5「沒有單價時的錯誤類型…」、D22（repo 結構） | 設定檔定案：TOML，`app/config.toml`，由 `app/config.py` 在啟動時讀取；路由會用到的模型缺設定就拒絕啟動。repo 結構加上 `app/config.toml`、`app/config.py`、`app/router.py`（E94 定案 1、2） |
| 3 | D8、8.2 的 M3 | 路由函式 `choose_model()`（`app/router.py`）吃遮罩後的文字與路由規則，回傳模型與理由（`length`、`keyword`、`default`）；思考量由模型設定提供。先看字數、再看關鍵字；關鍵字不分大小寫（E94 定案 2、E97） |
| 4 | D45、D30、2.2 流程圖 [4]、12.5「沒有單價時的錯誤類型…」 | 成本以實際拿到回答的那次請求所指定的名稱查單價；查單價的時機移到呼叫模型之前（E94 定案 3）。實作：`find_model_config()` 在呼叫前查設定，查不到丟 `ModelNotConfiguredError`；`cost_micro_usd()` 改收設定物件；`app/pricing.py` 不再有 `PRICES`；`main.py` 啟動時讀設定檔（E96） |
| 5 | 3.2 的 `audit` 表、D10 | 稽核新增 `route_reason`、`routed_model`、`provider_model`、`fallback`、`fallback_reason`；`model` 改為記指定的名稱（E94 定案 3、4） |
| 6 | 7.10、7.9「預扣」、12.5「預扣」那一列、3.4 | 預扣 M3 不做，留到 M5；M3 新增每顆模型的輸出上限（`max_completion_tokens`），並說明強模型下超扣的幅度（E94 定案 5） |
| 7 | D30、4.2 應用層、8.2 的 M3 | 補上設定檔的做法：`[routing]` 指名兩顆模型，`[models.名稱]` 放各自的思考量、輸出上限、單價；`load_config()` 讀進來就檢查（路由用到的模型要有設定、數字要是大於 0 的整數、關鍵字不能是空白、不能少欄位），有問題丟 `ConfigError`（E95） |
| 8 | 11.5 截圖規範（推送前的檢查） | 新增：簡報開著時會產生 `~$` 開頭的鎖定檔，已列入 `.gitignore`；推送前照檔名逐一加入，不用 `git add .`（E95） |
| 9 | 12.5「沒有單價時的錯誤類型與對使用者的回應」、2.2 的回應對照表、D37 | 查不到模型設定時：回 500 `Internal server error`，稽核記 `status: error` 與 `error_type: ModelNotConfiguredError`，不呼叫模型、不扣錢；12.5 該列劃掉（E97 定案 1；實作後補證據編號） |

---

## 目前進度（2026-10-10 14:15）

- 交接檔第 2 節的事項已回覆（E94）
- M3 開工前五項定案 ✅（E94）
- 步驟 1（設定檔、讀取與檢查）✅（E95，已推送 `7cb56ed`）
- 步驟 2（單價改讀設定檔、加入 `gpt-6-sol`、查設定移到呼叫模型之前）✅（E96，已推送 `8907063`）
- **步驟 3（路由函式 `choose_model()`）✅（E97，已推送 `81a87c2`）；目前 `150 passed`（其中 45 個是 `integration`）**
- 下一步：步驟 4（路由接進 `chat_endpoint`），分四小段：① 路由與設定的領用窗口 ② 查不到模型設定回 500 ③ 輸出上限 ④ 稽核的 `model` 與 `provider_model`。第一段的測試檔（`tests/fakes.py`、`tests/test_chat_routing.py`）已交給本人，尚未開始

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| ~~查不到模型設定時對使用者的回應（決策書 12.5、E87、E96）~~ | ✅ 10/10 定案：回 500、固定訊息、寫稽核（E97）；步驟 4 實作 | — |
| 輸出上限的數字 | 暫定 `gpt-6-luna` 1,000、`gpt-6-sol` 2,000；用真實回應試過再調 | 步驟 6 |
| 輸出 token 數是否已包含思考 token（E87） | 用 `gpt-6-sol` 的一次真實回應實證 | 步驟 6 |
| 兩種 429 怎麼分辨；兩顆都限流時 `Retry-After` 的值；SDK 重試與降級的疊加 | 做到時先看 SDK 實際丟出的錯誤再定 | 步驟 5 |
| 路由門檻的數字（300 字、關鍵字清單）與中英文字數的算法（決策書 12.5） | 用 20 題測試集調整；規則的形式不變 | 步驟 7 |
| CI 怎麼跑 `integration` 測試；`protect-main` 加「CI 通過才能合併」；CodeQL（E89、M1 報告） | 預設在 CI 起 `dynamodb-test` 容器 | 步驟 8 |
| 預扣（7.10） | M3 不做（E94 定案 5） | M5 |
| M7 是否開工（E79） | 第一個時段的條件：M3 與 CI 在 10/16（五）前完成 | 10/16、10/30、11/1 |
| 簡報計時試講（E84） | 素材到齊前至少試講一次主影片 | 10/18 前 |
| 從 M2 帶過來、M4 前要定的項目（稽核搬進 `audit` 表、`compose.yaml` 加 Gateway、`app/db.py` 連真的 AWS、強一致讀取、停用 Key 的腳本、`/docs` 是否關閉、`m1-gateway` 金鑰 11/2 到期） | 見 `m2-evidence-log.md` 的待決表與決策書 12.5 | M4 前 |
