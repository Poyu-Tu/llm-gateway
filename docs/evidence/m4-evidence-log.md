# M4 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID；個人帳號名稱（含終端機提示字元與路徑中的使用者資料夾名稱，一律寫成 `<user>`）。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`（檔名以 `m4-` 開頭，正式清單照決策書 11.4 的 S 編號），日誌另存於 `docs/logs/`。
> E 編號接續 `m3-evidence-log.md`（E94～E107），M4 從 E108 開始。
> 紀錄日期：2026-10-14 建立（M3 於 10/13 結案；M4 開工前準備 10/14～10/16，M4 本體 10/17 起，檢查點 10/25）

---

## 紀錄規則（沿用 M3）

| # | 東西 | 規則 |
|---|---|---|
| 1 | 證據紀錄 | 本檔；每完成一組步驟就更新，回傳完整新版 |
| 2 | 里程碑報告 | 整關驗證通過後寫 `docs/milestones/m4-report.md`，格式同 M3；只向本人確認花費時間與實際花費 |
| 3 | 決策書 | M4 結案時出 v2.10；期間的新定案先記在本檔，待改項目列在本檔的「決策書 v2.10 待改項目」表 |
| 4 | 截圖、日誌、錄影 | 收到就改名、遮蔽、回傳；只截 11.4 清單（S08～S11）與出錯、決策、驗證的關鍵畫面；每個驗收條件錄一段，影片不進 repo；錄 AWS 主控台時框選範圍不含最上面那一列（帳號名稱、帳號 ID） |
| 5 | 存放 | 所有回傳的文字檔也存一份到 Project |
| 6 | 個資測試 | 只用假資料（假身分證字號、假手機、`example.com` 信箱、測試用卡號） |
| 7 | 收錄範圍 | 只收與專題本身有關的內容；不記本人的預測、不寫責任歸屬、不寫個人環境的事 |
| 8 | 推送 | 從 E108 起 `main` 不能直接推送：一律開分支、開 PR、`Tests` 與 `Image scan` 綠了才合併（D67） |

---

## M4 步驟規劃（2026-10-14，粗排）

**開工前的本機準備（10/14～10/16；決策書 8.2 M4 的「開工前」與 12.5 列「M4 前」的項目）**

| # | 項目 | 需要金鑰 | 來源 |
|---|---|---|---|
| 0 | 分支流程試一次（本筆 E108） | 否 | D67 |
| 1 | `compose.yaml` 加上 Gateway，容器實際跑一次：讀得到 `app/config.toml`、對話流程完整 | 最後一次對話要 | M2 報告、E95 |
| 2 | 稽核搬進 `audit` 表；扣額度失敗的紀錄放哪裡、怎麼補收與告警；`pii_types` 的型別 | 否 | D52 |
| 3 | `app/db.py` 怎麼表示連真的 AWS（IAM 角色、不給網址、不帶假帳密、沒講清楚要連哪裡就報錯）；強一致讀取；DynamoDB 計費模式 | 否 | E89、E90 |
| 4 | 停用 Key 的腳本 | 否 | E91 |
| 5 | 決定：`/docs`、`/openapi.json` 是否在正式環境關閉；資料庫故障的 503 要不要附 `Retry-After` | 否 | 12.5 |
| 6 | 決定：便宜模型那次 SDK 可能等 120 秒，與 ALB 預設 60 秒閒置逾時的衝突 | 否 | E100 |
| 7 | 查證：OpenAI 工作負載身分聯盟能不能用；`m1-gateway` 金鑰 11/2 到期，M4 另開金鑰放 SSM | 開新金鑰時要 | 4.5、12.5 |
| 8 | Trivy 升級與 Action 的更新方式 | 否 | E104 |

**M4 本體（10/17 起）：** Terraform（遠端 State、OIDC、最小權限、VPC、NAT、DNS 防火牆、Gateway Endpoint）→ ECR → Fargate → ALB；驗收 S08～S11；`terraform destroy` workflow。細節照決策書 8.2、3.5、4.1、7.1，開工時再拆。

---

## E108. 第 0 步：分支流程第一次實測（2026-10-14 09:08～09:29）

**依據：** 決策書 D21、D67；`m3-evidence-log.md` E107 第 6 節（`protect-main` 加「CI 通過才能合併」，但截圖沒拍到加進去的檢查項目）。

**目的：** 證明 `main` 真的不能直接推送；第一次走「分支 → PR → CI 綠 → 合併」；順便把 E107 末尾 `19f87da` 的推送紀錄送進 repo（寫在 `main` 鎖住之後，只能走 PR）。

**生活比喻：** 以前廚師可以直接把菜端上桌。現在規定菜要先放到出餐口，品管試吃過才能上桌。第一次先故意直接端，確認門口真的有人擋。

### 起點

- 本機的 `main` 停在 `dff05ed`，GitHub 已是 `19f87da`（落後 6 個 commit）
- 新版 `m3-evidence-log.md` 在 `git pull` 之前就蓋進 repo，`git pull` 因此停下：`error: Your local changes to the following files would be overwritten by merge`
- 處理：先 `git restore` 還原該檔，`git merge --ff-only origin/main` 追上 `19f87da`，再蓋一次新檔。`git diff --stat`：`1 file changed, 10 insertions(+), 1 deletion(-)`，與 repo 版只差 E107 結尾的推送紀錄

**學到的：** 開分支之前，本機的 `main` 要先追上 GitHub；不然分支是從舊版長出來的，送審時要和新版拼接。`--ff-only` 只允許直接往前追，要拼接就拒絕。

### 1. 直接推 `main`：被擋

```
git push origin HEAD:main
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - 2 of 2 required status checks are expected.
 ! [remote rejected] HEAD -> main (push declined due to repository rule violations)
```

- commit `cd9abf6`（`docs: record the push of decision book v2.9`）還沒有跑過任何 CI，所以被擋
- **「2 of 2」證明規則裡確實加了兩個必要檢查**，補上 E107 截圖沒拍到的部分

### 2. 推分支、開 PR #2：5 個檢查全綠

| 檢查 | 結果 | 必要 |
|---|---|---|
| `ci / Image scan (pull_request)` | ✅ 39 秒 | Required |
| `ci / Tests (pull_request)` | ✅ 27 秒 | Required |
| `Code scanning results / CodeQL` | ✅ 3 秒，No new alerts | — |
| `CodeQL / Analyze (actions) (dynamic)` | ✅ 37 秒 | — |
| `CodeQL / Analyze (python) (dynamic)` | ✅ 49 秒 | — |

- 只改文件的 PR 也會跑 CI：`ci.yml` 的 `pull_request` 沒有設 `paths`，不會因為只改 `docs/` 就跳過、卡在「等待檢查」

### 3. 定案：規則加上「要走 PR」（09:19，本人選 A）

**發現：** 被擋的訊息只列「必要檢查」，沒有列「要走 PR」。規則集當時只要求「檢查要通過」，沒有明文要求經過 PR。

| 選項 | 做法 | 評估 |
|---|---|---|
| **A（採用）** | `protect-main` 加「Require a pull request before merging」，核准數 **0** | 「一定要經過 PR」由規則明文保證；一個人開發，核准數 0 不會卡住自己（GitHub 不讓作者核准自己的 PR） |
| B | 維持現狀 | 靠自己記得開 PR |

- 其他子選項（Dismiss stale approvals、Code Owners、most recent push、conversation resolution）都不勾；「unattributed Copilot pull requests」維持預設勾選（核准數 0 時不影響）
- Bypass list 為空：本人的帳號也不能略過
- 本人截圖：「Ruleset updated」、Active

### 4. 規則改完後再推一次 `main`：成功，是在終端機合併了 PR #2

```
git push origin HEAD:main
   19f87da..cd9abf6  HEAD -> main
```

- PR #2 隨即變成 **Merged**：「Poyu-Tu merged commit `cd9abf6` into `main`」、「5 checks passed」
- **原因：** `cd9abf6` 正是 PR #2 最新的 commit，而且 PR 已滿足所有條件（2 個必要檢查綠、核准數 0）。GitHub 把這次推送當成在終端機合併這個 PR（PR 頁面上「You can also merge this with the command line」那條路），所以放行
- `main` 直接前進到 `cd9abf6`，沒有另外的合併 commit

**更正（Claude 的判斷錯誤）：** Claude 在選項 A 之前說「commit 在分支上跑過 CI，就能繞過 PR 直接推進 `main`」，並預期這次推送會被擋。回頭看 `ci.yml` 的觸發條件：

```yaml
on:
  push:
    branches: [main]
  pull_request:
```

CI 只在推到 `main` 與開 PR 時跑，單純推分支不會跑。一個 commit 要有綠勾，一定得先進 PR；所以那個「漏洞」在目前的設定下幾乎不存在，這次推送也證明不了 A 的效果。A 仍保留：它讓「要經過 PR」由規則明文保證，不依賴 `ci.yml` 剛好的觸發條件。

### 5. 收尾

```
git switch main
git pull                                   # dff05ed..cd9abf6，Fast-forward
git branch -d docs/m3-push-record          # Deleted branch docs/m3-push-record (was cd9abf6).
git push origin --delete docs/m3-push-record   # - [deleted] docs/m3-push-record
```

### 證明了什麼

- 沒跑過 CI 的 commit 不能進 `main`（GH013，2 個必要檢查）
- 走 PR 時，`Tests`、`Image scan` 會自動跑，而且是合併的必要條件
- 已滿足條件的 PR，從終端機推它的 commit 等於合併它，GitHub 會記成 PR 已合併

### 限制（誠實記錄）

- **A 能不能擋住「沒進 PR、但有綠勾的 commit」沒有測到。** 在目前的 `ci.yml` 下做不出這種 commit，要另外造情境才能測
- PR #2 是在終端機合併的，不是按「Merge pull request」；之後的 PR 改用按鈕合併，流程比較好說明
- 規則集的完整設定（必要檢查的名稱、PR 規則）只有截圖與錯誤訊息，沒有匯出設定檔

### 面試可用的說法

- 「我的 main 分支要 CI 通過才能進。我實測過：沒跑過 CI 的 commit 直接推，被 GitHub 擋下，訊息寫兩個必要檢查都還沒跑。」
- 「我另外加了『一定要經過 PR』。老實說，在我的設定下 CI 只對 PR 跑，所以本來就繞不過去；我加它是讓這件事寫在規則裡，不靠 CI 設定剛好成立。我也發現 GitHub 會把『推一個已經合格的 PR 的 commit』當成合併那個 PR，所以那次推送沒被擋，這是正常行為。」

**推送：** 隨 M4 開工前準備的第一個 PR 進 repo。

| commit | 時間 | 訊息 |
|---|---|---|
| `cd9abf6` | 10/14 09:23 前後 | `docs: record the push of decision book v2.9`（PR #2，`19f87da..cd9abf6`） |

---

## E109. 上 ALB 之前的三項定案：說明頁關閉、資料庫 503 不附 `Retry-After`、SDK 不重試（2026-10-14 12:05～13:25）

**依據：** 決策書 12.5 的三列（`/docs` 是否關閉、資料庫故障的 503 要不要附 `Retry-After`、SDK 的等待與 ALB 閒置逾時）；D10、D48、D59；E53、E90、E100。

**範圍：** `app/main.py` 兩處、`app/fallback.py` 一行註解；新測試檔 1 個、改 5 個既有測試檔。容器與真實呼叫都沒有用到。

### 定案（10/14 12:10，本人「照建議」）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | `/docs`、`/redoc`、`/openapi.json`、`/docs/oauth2-redirect` | **一律關閉**：`FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` | 環境變數控制本機開、正式關：多一個設定，忘了設就是開著。只在 ALB 擋：要等 Terraform，而且容器本身仍開著、只剩一層防線 | 想看 API 規格的人要讀程式碼或 README |
| 2 | 資料庫故障的 503 | **不附 `Retry-After`**（維持現狀），並用測試釘住 | 附固定秒數：多久恢復無從得知；所有客戶端被叫到同一秒重試，資料庫剛恢復又被打垮 | 客戶端要自己決定多久後重試 |
| 3 | SDK 的重試與 ALB 的 60 秒閒置逾時 | **所有 OpenAI 呼叫都不讓 SDK 重試**（`OPENAI_MAX_RETRIES` 1 → 0）；被限流時直接回 503 與 `Retry-After`，由使用者決定要不要等 | 保留重試、ALB 調到 180 秒：使用者最多等 3 分鐘、連線佔得久。Gateway 自己分配整個請求的剩餘時間：要寫新邏輯，時程不划算 | 便宜模型遇到網路瞬間抖動或偶發的 5xx，直接回 502；修訂 D10 的「SDK 重試 1 次」 |

**生活比喻（第 3 項）：** 外送平台 60 分鐘沒送到就自動取消訂單，但廚房不知道，照樣把菜煮完、照樣結帳。改法是廚房不再「卡住就自己再煮一次」，忙不過來就直接告訴客人「大約多久後再點」。

**第 3 項的推算（依 SDK 原始碼與 E100 的實測，不是量測）：**

| 情況 | 改之前 | 改之後 |
|---|---|---|
| 只走便宜模型，連續兩次逾時 | 30 秒 → SDK 稍等重試 → 30 秒，約 61～68 秒，超過 60 | 30 秒後回 502 |
| 強模型被限流、降級後便宜模型也被限流，供應商給 `retry-after: 120` | SDK 在背後等 120 秒再試，最多約 150 秒 | 立刻回 503，`Retry-After` 照抄（1～120） |

- 理論上的最長等待變成「強模型 30 秒 + 便宜模型 30 秒」，只會發生在強模型的 429 本身就花了 30 秒才回來；正常的 429 是立即回應
- `app/fallback.py` 對強模型的 `with_options(max_retries=0)` 保留：即使之後有人把 `OPENAI_MAX_RETRIES` 改回 1，強模型那次仍不重試

**查證（Claude 在試跑環境，FastAPI 0.141.1，與 `uv.lock` 相同）：** 預設 4 個說明頁都回 200；三個參數都設 `None` 後全部 404，`/health` 照樣 200。只設 `openapi_url=None` 也會讓 4 個頁面都 404（其他兩頁依賴它），但三個都寫比較清楚。

### 程式的修改（本人撰寫）

```python
# OpenAI 連線設定：重試和逾時都調小，避免重複花錢、卡住連線（D10）
# 不讓 SDK 自己重試：被限流時直接回 503 與 Retry-After，不在背後等到負載平衡器先斷線
OPENAI_MAX_RETRIES = 0
OPENAI_TIMEOUT_SECONDS = 30

# 說明頁（/docs、/redoc、/openapi.json）一律關閉：使用者用不到，只會把 API 的地圖交給想攻擊的人
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
```

`app/fallback.py` 便宜模型那一段的註解，由「保留 SDK 自己的那一次重試」改為「照連線本身的重試設定（main.py 的 OPENAI_MAX_RETRIES）」。三處都不是函式，沒有三句。

### 測試（Claude 整份提供；測試數 267 → 271）

**`tests/test_production_settings.py`（新檔，4 個）：**

| 測試 | 檢查 |
|---|---|
| `test_api_docs_pages_are_turned_off` | 4 個說明頁都回 404 |
| `test_health_check_still_answers` | `/health` 照樣 200、`{"status": "ok"}`（ALB 靠它判斷容器還活著） |
| `test_openai_client_does_not_retry` | `get_client()` 的 `max_retries` 是 0 |
| `test_openai_client_gives_up_after_30_seconds` | `get_client()` 的逾時是 30 秒 |

- 後兩個用 `monkeypatch` 設一個假的 `OPENAI_API_KEY`：建立連線物件需要有值，但不會真的連線

**既有測試：**

- `tests/test_chat_auth.py`（2 個）、`tests/test_chat_quota.py`（1 個）、`tests/test_chat_charge.py`（1 個）：4 個資料庫 503 的測試各加一行 `assert "retry-after" not in response.headers`。原本「不附」只是剛好沒寫，沒有測試守著
- `tests/test_fallback.py` 2 個、`tests/test_chat_fallback.py` 1 個測試改名：「保留 SDK 的重試」改成「照連線本身的重試設定」（`test_cheap_route_uses_the_client_retry_setting`、`test_fallback_call_uses_the_client_retry_setting`、`test_chat_uses_the_client_retry_setting_for_the_cheap_model`）。內容不變；不改的話名字和行為對不上

**過程（本人執行）：**

| 時間點 | 結果 |
|---|---|
| 只換測試檔 | `2 failed, 269 passed`：`test_api_docs_pages_are_turned_off - AssertionError: /docs`、`test_openai_client_does_not_retry - assert 1 == 0` |
| 改完 `main.py`、`fallback.py` | `271 passed` |

- 4 行「不附 `Retry-After`」在改之前就是綠的（現狀本來就不附），由破壞實驗 B 證明它們會紅

### 破壞實驗（本人執行，三個；每個做完改回，最後 `271 passed`；結果與 Claude 事先給的預期相同）

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| A | 只拿掉 `, openapi_url=None` | `1 failed, 270 passed` | `test_api_docs_pages_are_turned_off - AssertionError: /openapi.json` |
| B | 驗票口的資料庫 503 加上 `headers={"Retry-After": "5"}` | `2 failed, 269 passed` | `test_chat_auth.py` 的兩個 503 測試：`assert 'retry-after' not in Headers({'retry-after': '5', …})` |
| C | `OPENAI_MAX_RETRIES` 改回 1 | `1 failed, 270 passed` | `test_openai_client_does_not_retry - assert 1 == 0` |

**判讀：**

- **A：** `/docs` 頁面關了，`/openapi.json` 還開著。說明頁只是把這份 JSON 畫成網頁，真正交出 API 地圖的是 JSON 本身；只關頁面等於只拆招牌、門還開著
- **B：** 只紅驗票口那兩個；額度讀不到、加 0 寫不進去的兩個 503 在別的位置，這次沒有加標頭，所以沒紅。四個位置各有測試守著
- **C：** 失敗訊息的 `1 == 0` 直接說出設定被改回去

### 限制（誠實記錄）

- **全部是推算與單元測試，沒有在 ALB 後面量過。** 最長等待時間要等 M4 上雲後實測
- **ALB 的閒置逾時要在 M4 的 Terraform 明寫**（預設 60 秒）。理論上的最長等待剛好是 2 × 30 = 60 秒，沒有餘裕；寫 Terraform 時決定要不要設成 75 之類的值。原本考慮寫一個測試釘住「2 × 逾時 ≤ ALB 逾時」，但 ALB 的設定還不存在，測試裡的數字跟真的設定沒有連在一起，所以沒有加
- **30 秒的逾時夠不夠，沒有量過。** M3 的 20 題裡強模型最長寫了 1,372 個 token，但那次工具的逾時是 120 秒，沒有記錄花了幾秒。長回答若超過 30 秒，會變成 502，而供應商可能已經收錢
- 說明頁的測試只測這 4 個路徑；FastAPI 之後若新增別的預設頁面，不會被抓到
- 4 個資料庫 503 的測試是 `integration`，要 DynamoDB Local 才會跑

### 面試可用的說法

- 「FastAPI 預設會公開 API 說明頁。我做過實驗：只關掉 /docs 頁面，測試照樣紅，因為 /openapi.json 還開著，那才是真正的 API 地圖，說明頁只是把它畫出來。」
- 「SDK 預設會在背後自己重試，遇到限流還會照供應商說的等最多兩分鐘。放到 ALB 後面，ALB 60 秒就切斷連線，但 Gateway 還在背後呼叫模型、扣錢。所以我關掉 SDK 的重試，被限流就直接回 503 加 Retry-After，讓使用者自己決定要不要等。代價是網路抖一下就直接失敗，我把它寫進限制。」
- 「資料庫掛掉時的 503 我刻意不附 Retry-After。多久恢復我不知道，隨便給一個數字，等於叫所有客戶端在同一秒一起重試。原本只是剛好沒寫，所以我補了測試把它釘住。」

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `3864f57` | 10/14 13:25 前 | `feat: turn off the API docs and SDK retries before going behind the ALB`（分支 `feat/compose-gateway`，`b0b0d9c..3864f57`；PR 待容器驗證後一起開） |

---

## E110. 第 7、8 項定案：OpenAI 改用工作負載身分聯盟、Dependabot 只追 Action 與基底映像（2026-10-14 14:00～14:36）

**依據：** 決策書 4.5（OpenAI 端的防線）、12.5（`m1-gateway` 金鑰 11/2 到期；Trivy 升級與 Action 的更新方式）；E104。

### 查證（Claude 以工具讀取官方文件，並在試跑環境確認套件）

| 項目 | 結果 | 來源 |
|---|---|---|
| OpenAI 支援 AWS 的身分聯盟 | 支援：AWS STS `GetWebIdentityToken` 開出 JWT，到 `https://auth.openai.com/oauth/token` 換成存取權杖，最多 1 小時，沒有更新權杖（到期就再換一次） | OpenAI〈Configuring workload identity federation for AWS〉、〈Workload identity token exchange〉 |
| AWS 端 | 帳號層級開啟「對外身分聯盟」（`aws iam enable-outbound-web-identity-federation`）；呼叫者要有 `sts:GetWebIdentityToken`，可用 `sts:IdentityTokenAudience`、`sts:DurationSeconds` 限制；**一定要用地區的 STS 網址** | 同上；AWS IAM〈Controlling access with IAM policies〉（IAM 使用者與角色都能呼叫） |
| OpenAI 端 | 組織設定建立身分提供者（Issuer 與 Audience），再建服務帳號對應：`sub` 等於呼叫者的 ARN → Project 與服務帳號 | 同上 |
| 套件 | `openai` 3.19.2 的 `OpenAI()` 有 `workload_identity` 參數，可自訂取得 JWT 的函式；SDK 會在到期前 20 分鐘自動重換。`boto3` 1.43.103 有 `get_web_identity_token`（必填 `Audience`、`SigningAlgorithm`） | 試跑環境讀套件原始碼與服務定義 |
| 不確定 | 文件寫「有些端點不接受這種權杖」，範例只示範 `responses`，沒有說 `chat.completions`；文件沒有提到 ECS／Fargate | — |

**生活比喻：** 不再發一把萬用鑰匙給員工，改成每次刷員工證（AWS 的身分證明），警衛確認後給一張最多一小時的臨時通行證（OpenAI 的存取權杖）。

### 定案（14:36，本人）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | OpenAI 金鑰怎麼交給 Fargate | **A：M4 直接用工作負載身分聯盟，SSM 不放 OpenAI 金鑰** | B（Claude 建議）：M4 先用 SSM 放新金鑰、驗收後再升級。C：只寫進決策書 | M4 是風險最大的一關，再加兩個未知數（`chat.completions` 收不收、Fargate 有沒有問題）；DNS 防火牆要多放行 `auth.openai.com` 與 `sts.ap-northeast-1.amazonaws.com` |
| 2 | 版本更新 | **A：`.github/dependabot.yml`，只開 GitHub Action 與 Dockerfile 基底映像的版本更新**，每週、冷卻 7 天、一次最多 3 個 PR；Python 套件只收安全性更新 | B：加上 Python 套件：11/7 前每週都可能換 `openai`、`fastapi` 的版本，專題期間風險高。C：維持手動：版本停在原地 | 鎖了指紋的基底映像能不能被更新，官方頁面沒寫清楚；`compose.yaml` 的 DynamoDB Local 映像不在範圍內；Trivy 本身的版本（設定裡的文字）不會被更新 |

**第 1 項的退路（Claude 提出，與定案一起記錄）：** 今晚在個人電腦先做一次探測（`scripts/probe_wif.py`），把最大的未知數提前到 M4 開工前：

| 探測結果 | 處理 |
|---|---|
| `[1]`、`[2]` 都成功 | M4 照 A 做 |
| `[2]` 失敗，錯誤指出 `chat.completions` 不接受這種權杖 | 立刻改回 B（SSM 放新金鑰，到期日設在 11/7 之後），A 記成「試過、不支援」 |
| 設定卡住，前後超過 2 小時 | 改回 B，A 留到 M4 驗收後再試 |

**第 1 項對程式的影響（M4 要改）：** `get_client()` 現在每個請求建一個新的 `OpenAI()`。改用身分聯盟後，每個請求都會重新向 AWS 與 OpenAI 換一次權杖，多兩趟網路。要改成啟動時建一次、之後共用，權杖才會被重複使用到快到期才換。

### 交付（Claude 提供，進同一個分支）

- `scripts/probe_wif.py`：先向 AWS 要身分證明，只印 `iss`、`aud`、`sub` 與有效秒數（**不印 token 本身**）；再用身分聯盟建 `OpenAI()`，以 `gpt-6-luna` 打一次 `chat.completions`（輸出上限 50）。偵測到 `OPENAI_API_KEY` 有值就直接停下，避免不小心用金鑰而誤判成功
  - 試跑環境：用假的 STS 回應確認參數與回應欄位、解開 JWT 內容、偵測到金鑰時停下、`OpenAI(workload_identity=…)` 建得起來；**沒有真的連 AWS 與 OpenAI**
- `.github/dependabot.yml`：兩個項目（`github-actions`、`docker`），試跑環境以 YAML 解析確認格式

這兩個是設定檔與探測工具，沒有本人寫的函式，不用三句。

### 限制（誠實記錄）

- 探測用的是本人電腦登入的 AWS 身分（IAM 使用者），不是 Fargate 的角色；`sub` 會不同，Fargate 上要另外對應一次
- 「對外身分聯盟」是整個 AWS 帳號的設定；可以用對應的 `disable` 指令關掉
- Dependabot 只有合併進 `main` 之後才會開始運作

---

## E111. 第 3 項：`make_dynamodb_client()` 能連真的 AWS、三個讀取改成強一致（2026-10-14 14:51～15:42）

**依據：** 決策書 12.5「`app/db.py` 怎麼表示連真的 AWS；計費模式；要不要強一致讀取」；E89、E90（M2）；D49（資料庫逾時與重試）。

### 定案（14:51，本人「照建議」）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | 怎麼表示連真的 AWS | 環境變數改名 **`DYNAMODB_TARGET`**：`aws` → 東京區真的 DynamoDB（不給網址、不給帳密，身分交給 IAM 角色）；`http://`、`https://` 開頭 → 那個網址的練習場（假帳密 `local`）；沒設 → `KeyError`；其他值 → `ValueError` | 名稱不變、`DYNAMODB_ENDPOINT_URL=aws`：「網址」變數裝的不是網址。加第二個變數：兩個設定可能互相矛盾。沒設就當成雲端：忘了設定時會用這台電腦的 AWS 身分去改雲端資料 | `aws` 要寫對（大寫也報錯）；改名要同步 `.env`、`.env.example`、`compose.yaml`、`tests/conftest.py` |
| 2 | 強一致讀取 | 查 Key（`find_user_id`）、查額度（`read_limit`）、查已用量（`read_used`）都加 `ConsistentRead=True` | 只有查 Key：額度仍可能多放行一次。都不用：剛停用的 Key、剛扣完的錢可能讀到舊的 | 讀取費用 2 倍（每 1,000 個請求約多 US$0.0002，美東價）；練習場不管這個參數，測試只能檢查「有沒有帶」 |
| 3 | 雲端 DynamoDB 計費模式（M4 Terraform 用） | **隨需（`PAY_PER_REQUEST`）**，與練習場相同 | 預置容量吃免費額度（25 讀、25 寫單位）：要自己估容量，Demo 時可能被 `ProvisionedThroughputExceeded` 擋下 | 免費額度用不到；估算 1,000 個請求合計不到 US$0.002（美東價；東京價官方頁面未列） |

**試算（美東官方價：寫 $0.625、讀 $0.125 每百萬單位）：** 每個請求約讀 3 次、寫 2 次；1,000 個請求 = 3,000 讀單位（強一致每次 1 單位）≈ $0.0004、2,000 寫單位 ≈ $0.0013。來源：[Amazon DynamoDB on-demand pricing](https://aws.amazon.com/dynamodb/pricing/on-demand/)。

### 程式的修改（本人撰寫）

`app/db.py`（填空 6 格，一次全對）：

```python
# DYNAMODB_TARGET 寫這個字，就是連上 AWS 上真的 DynamoDB
AWS_TARGET = "aws"


# 要連哪裡一定要明講：寫 aws 連雲端、寫網址連練習場，沒寫或寫錯就報錯（不讓 boto3 自己猜）
def make_dynamodb_client() -> BaseClient:
    """Return a DynamoDB client for the target named in the environment."""
    target = os.environ["DYNAMODB_TARGET"]
    config = Config(
        connect_timeout=CONNECT_TIMEOUT_SECONDS,
        read_timeout=READ_TIMEOUT_SECONDS,
        retries={"total_max_attempts": TOTAL_MAX_ATTEMPTS, "mode": "standard"},
    )

    # 雲端：不給網址、不給帳密，boto3 就會連東京的 DynamoDB，身分用 Fargate 的 IAM 角色
    if target == AWS_TARGET:
        return boto3.client("dynamodb", region_name=REGION, config=config)

    # 練習場：網址照給，帳密用假的（不能讓 boto3 拿這台電腦上真的 AWS 身分）
    if target.startswith("http://") or target.startswith("https://"):
        return boto3.client(
            "dynamodb",
            endpoint_url=target,
            region_name=REGION,
            aws_access_key_id=LOCAL_ACCESS_KEY,
            aws_secret_access_key=LOCAL_SECRET_KEY,
            config=config,
        )

    raise ValueError(f"DYNAMODB_TARGET must be 'aws' or a URL, got: {target!r}")
```

`app/auth.py` 的 `find_user_id()`、`app/quota.py` 的 `read_limit()`、`read_used()`：`get_item(…)` 結尾加 `ConsistentRead=True`，上面各加一行註解。`compose.yaml` 的 `gateway` 改用 `DYNAMODB_TARGET: http://dynamodb:8000`；`.env.example` 改名並補兩行說明。

### 測試（Claude 整份提供；測試數 271 → 282）

| 檔案 | 內容 |
|---|---|
| `tests/test_db.py`（改寫，3 → 11 個） | 沒設 → `KeyError`；網址 → 連那個網址、帳密是 `local`；`aws` → `https://dynamodb.ap-northeast-1.amazonaws.com`、身分是環境裡的那一組（不是 `local`）；`AWS`、空字串、`dynamodb`、`127.0.0.1:8001`（沒有 `http://`）→ `ValueError`；兩種目標都是 2 秒連線、5 秒讀取、最多 2 次。每個測試用假的 AWS 身分，並清掉 boto3 記住的身分 |
| `tests/test_consistent_reads.py`（新檔，3 個） | 用會記錄參數的假資料庫，確認三個讀取都帶 `ConsistentRead=True` |
| `tests/conftest.py` | 考場改設 `DYNAMODB_TARGET` |

### 挫折：舊的環境變數把 43 個測試導到練習場，還清空了資料表

| 時間點 | 結果 |
|---|---|
| 換好測試與設定檔後第一次跑 | `11 failed, 271 passed`：連資料庫的 43 個測試**全部通過**，與預期（43 個 `ERROR`）不同；`test_make_dynamodb_client_uses_url_from_target` 的訊息出現沒有任何測試設定的 `http://127.0.0.1:8001` |
| 查 `$env:DYNAMODB_ENDPOINT_URL` | `http://127.0.0.1:8001`：之前跑種子腳本時在這個 PowerShell 視窗設的 |
| `Remove-Item Env:DYNAMODB_ENDPOINT_URL` 後重跑 | `13 failed, 226 passed, 43 errors`，全部是 `KeyError: 'DYNAMODB_ENDPOINT_URL'`，與預期相同 |
| 改完三個程式檔 | `282 passed` |

- **發生了什麼：** 新的 `conftest.py` 已經改設 `DYNAMODB_TARGET`，舊的 `db.py` 卻還在讀 `DYNAMODB_ENDPOINT_URL`，結果讀到視窗裡留下的 8001（開發用的練習場），而不是 8002（考場）。考場道具每次會刪掉所有資料表，所以練習場的 alice、bob 被清空
- **影響：** 只有本機的假資料，重跑種子腳本即可；但它證明了舊寫法的漏洞：**只要電腦上留著一個舊變數，測試就會連到別的資料庫，而且全部綠燈**
- **改名剛好把這條路斷掉：** 新的 `db.py` 只讀 `DYNAMODB_TARGET`；`tests/test_db.py` 的 `requires_target` 測試在被污染時的訊息是 `DID NOT RAISE KeyError`，也顯示了同一件事
- **生活比喻：** 消防演習的地址寫在便利貼上，桌上剛好留著上週另一張便利貼，煙霧彈就放到了正在上班的辦公室，演習報告還寫「一切順利」

### 破壞實驗（本人執行，三個；做完改回，最後 `282 passed`）

| # | 改了什麼 | 結果 | 證明了 |
|---|---|---|---|
| 1 | 練習場那段拿掉 `aws_access_key_id`、`aws_secret_access_key` | `1 failed, 238 passed, 43 errors`：`uses_dummy_credentials_for_a_url`（`assert 'AKIA-FROM-THE-ROLE' == 'local'`），另外 43 個連資料庫的測試全部 `MissingDependencyException: Using the login credential provider requires an additional dependency` | 沒有假帳密時，boto3 **真的去找這台電腦上 `aws login` 的登入身分**。這正是假帳密要擋的事 |
| 2 | 最後的 `raise` 換成「當作 `aws`」 | `4 failed, 278 passed`：`rejects_unknown_target` 的 `[AWS]`、`[]`、`[dynamodb]`、`[127.0.0.1:8001]` | 設定打錯（包括忘了 `http://`）不會默默連到雲端 |
| 3 | `read_used` 拿掉 `ConsistentRead=True` | `1 failed, 281 passed`：`test_read_used_reads_the_latest_usage`（`KeyError: 'ConsistentRead'`） | 三個讀取各有測試守著 |

- **實驗 1 比預期多 43 個 `ERROR`：** Claude 的試跑環境沒有任何 AWS 登入設定，所以只看到 1 個紅；本人電腦有 `aws login`，boto3 照順序找身分時找到了它（需要額外套件才能用，所以報錯）。若那個套件剛好有裝，測試會**用本人真的 AWS 身分**去連練習場

**本人的三句與修正：** 收在「LLM Gateway 程式面試練習本」的 `make_dynamodb_client()` 與「強一致讀取」兩節。要修正的是：第 1 句「寫網址連到 8001」改成「寫網址就連那個網址」，並補「寫錯也報錯」；第 2 句兩組都在講「怎麼做」，改成講風險（boto3 會自己猜、最終一致會讀到舊資料）與代價；第 3 句補破壞實驗與「所以證明了…」，強一致那組另補「練習場證明不了雲端行為」。

### 限制（誠實記錄）

- **連真的 AWS 那條路只檢查了連線物件的設定**（網址、區域、身分來源），沒有真的連線；Fargate 上用任務角色連得到，要到 M4 才驗證
- **強一致讀取在練習場看不出差別**，測試只證明有帶參數；延遲是否增加，上雲後量
- 測試讀身分用的是 boto3 的內部欄位（`client._request_signer._credentials`），套件升級時可能要改
- `scripts/seed.py`、`scripts/create_tables.py` 在本機執行時，要改設 `$env:DYNAMODB_TARGET`；個人電腦的 `.env` 也要把那一行改名
- 計費試算用的是美東價格

### 面試可用的說法

- 「連資料庫的設定我只收兩種：寫 aws 就連雲端、寫網址就連本機。沒寫或寫錯都直接報錯，因為 boto3 什麼都不給時會自己去連真的 AWS，還會用這台電腦登入的身分。」
- 「我改這段時真的遇過：PowerShell 視窗裡留著一個舊的環境變數，43 個測試連到了我開發用的資料庫，還把資料表清空，而且全部綠燈。是預期的紅沒有出現，我才回頭查到的。所以我很重視先看到測試為了對的原因而紅。」
- 「本機練習場一定帶假帳密。我做過實驗把它拿掉，結果 43 個測試跑去找我電腦上 aws login 的身分。這個保護不是想像出來的。」
- 「三個決定放不放行的讀取我都用強一致讀取。費用是兩倍，但 Demo 的量一個月不到一分錢；預設的最終一致可能讓剛停用的 Key 再用一次。測試只能證明有帶參數，雲端行為上雲後再驗。」

**推送：** 本人修正三句後 commit（見下一則）。

---

## E112. 第 4 項：停用 Key 的腳本 `scripts/disable_key.py`（2026-10-14 15:55～17:11；破壞實驗與三句 18:40～18:48）

**依據：** E91（M2：停用 Key 只能手動改資料庫）；決策書 12.5「停用 Key 的腳本」。

### 定案（15:55，本人選 C）

| 選項 | 做法 | 評估 |
|---|---|---|
| A | 輸入要停用的那把 Key → 算雜湊 → 改成 `disabled` | 精準，只停那一把；外流時手上一定有那把 Key |
| B | 輸入使用者名稱 → 掃整張表 → 停掉他所有的 Key | 緊急時方便；`api_keys` 用雜湊當主鍵，查不到「誰有哪些 Key」，只能掃表 |
| **C（採用）** | A 與 B 都做 | 最完整；多一個函式與一組測試 |

**兩種做法共同的坑：** DynamoDB 的 `update_item` 在那一筆不存在時會**自己新建一筆**。輸入打錯一個字，不會報錯，而是多出一筆「已停用的、不存在的 Key」，真正外流的那把照樣能用。所以更新時加 `ConditionExpression="attribute_exists(key_hash)"`，不存在就丟 `KeyNotFoundError`。

**生活比喻：** 打電話掛失信用卡，卡號念錯一個數字。好的銀行說「查無此卡」；壞的銀行說「已幫您掛失」，真正的卡繼續被盜刷。

### 程式（Claude 給填空版 11 格，本人填；`main()` 由 Claude 提供）

| 函式 | 做什麼 |
|---|---|
| `disable_key_hash(client, key_hash)` | 把那一筆的 `status` 改成 `disabled`；`status` 是 DynamoDB 的保留字，用 `#status` 代稱；不存在 → `KeyNotFoundError`；其他錯誤原封不動往外丟 |
| `disable_key(client, key)` | 先 `hash_api_key()` 再交給上面那個 |
| `disable_user_keys(client, user_id, page_size=100)` | 用 `scan` 的翻頁器一頁一頁找這個人的 Key，逐一停用，回傳停了幾把 |
| `main()` | `--key`（用 `getpass` 輸入，不顯示、不留在指令紀錄）或 `--user alice` |

**填空第一次交出時（17:06）的三個錯：**

| 格 | 寫成 | 應該是 | 沒改的話 |
|---|---|---|---|
| ② | `{"#status": "client"}` | `{"#status": "status"}` | DynamoDB 會**新增**一個叫 `client` 的欄位設成 `disabled`，`status` 仍是 `active`：腳本說停用成功，Key 照樣能用 |
| ④ | （空白） | `"ConditionalCheckFailedException"` | 語法錯誤 |
| ⑩ | `item.get_item()` | `item["key_hash"]["S"]` | `item` 是已經拿到手的那一筆（字典），`get_item` 是跟資料庫要資料的功能；寫法同 `find_user_id()` 的 `item["user_id"]["S"]` |

### 測試（Claude 整份提供，`tests/test_disable_key.py`，8 個，`integration`；測試數 282 → 290）

| 測試 | 檢查 |
|---|---|
| `test_disable_key_stops_the_key_from_working` | 停用後 `find_user_id()` 查不到，`status` 是 `disabled` |
| `test_disable_key_keeps_the_owner` | `user_id` 留著，事後查得到是誰的 |
| `test_disable_key_rejects_an_unknown_key_without_creating_one` | 打錯 → `KeyNotFoundError`，表裡仍是 1 筆 |
| `test_disable_key_leaves_other_keys_working` | 別人的 Key 照常能用 |
| `test_disable_user_keys_disables_every_key_of_the_user` | alice 的 2 把都停，回傳 2 |
| `test_disable_user_keys_leaves_other_users_working` | bob 不受影響 |
| `test_disable_user_keys_returns_zero_for_an_unknown_user` | 回傳 0，表裡沒有多東西 |
| `test_disable_user_keys_reads_every_page` | 一頁只看 1 筆時，3 把都被停用（翻頁有做） |

**過程（本人執行）：** 只放測試 → `1 error during collection`（`scripts.disable_key` 還不存在）；填完、改正三格 → `290 passed`。

### 破壞實驗（本人執行，三個；每個做完 `git restore`，只跑 `tests/test_disable_key.py`；最後整套 `290 passed`）

| # | 改了什麼 | 結果 | 失敗訊息 | Claude 的試跑 |
|---|---|---|---|---|
| 1 | 拿掉 `ConditionExpression` | `1 failed, 7 passed` | `test_disable_key_rejects_an_unknown_key_without_creating_one - Failed: DID NOT RAISE KeyNotFoundError` | 相同 |
| 2 | 改成 `SET status = :disabled`、拿掉 `ExpressionAttributeNames` | `7 failed, 1 passed` | 7 個都是 `ClientError: … (ValidationException) when calling the UpdateItem`；唯一綠的是 `test_disable_user_keys_returns_zero_for_an_unknown_user` | **6 failed**（不同，見下） |
| 3 | 外圈迴圈裡、內圈結束後加 `break`（只看第一頁） | `1 failed, 7 passed` | `test_disable_user_keys_reads_every_page - assert 1 == 3` | 相同 |

**判讀：**

- **實驗 1：** 其他 7 個照樣綠。擋住「打錯字卻回報成功」的只有這個條件與這個測試
- **實驗 2 與試跑差 1 個：** 差在 `rejects_an_unknown_key`。DynamoDB Local 先檢查語法，丟 `ValidationException`，程式原封不動往外丟，不是 `KeyNotFoundError`，所以這個測試也紅；Claude 的替身伺服器（試跑環境）看來是先檢查「這筆存不存在」，變成 `KeyNotFoundError` 而剛好綠。Claude 事先在對話中提醒過這個差異，請本人照實記數字。**替身伺服器的檢查順序可能和真的不同，破壞實驗以 DynamoDB Local 的結果為準**；雲端 DynamoDB 的行為上雲後才知道
- **實驗 2 唯一綠的那個：** 沒有這個人時根本不會呼叫更新，所以碰不到壞掉的語法
- **實驗 3：** Key 少的測試一頁就裝完，看不出漏頁；只有把一頁調成 1 筆的測試抓得到。`1 == 3` 直接說出 3 把只停了 1 把

**本人的三句與修正：** 收在「LLM Gateway 程式面試練習本」的 `disable_key_hash()`、`disable_key()` 與 `disable_user_keys()` 兩節。要修正的是：兩組第 2 句都寫成步驟（「輸入 → 算雜湊 → 改成 disabled」），改成講風險（更新找不到會自己新建一筆、掃表結果一頁一頁回來）與代價；`disable_user_keys()` 的第 2 句「兩個方式都做最完整」是選 C 的理由，不是函式為什麼這樣寫；兩組第 3 句都補上破壞實驗本身、結果與「所以證明了…」。`disable_user_keys()` 第 3 句裡「為什麼只有這個測試抓得到」講得對，保留。

### 限制（誠實記錄）

- `disable_user_keys()` 用掃表：表大了會慢、按讀取量計費；之後若常用，要加以 `user_id` 為鍵的索引
- 停用不可復原（沒有「重新啟用」的指令）；沒有記錄停用時間與操作者
- 對雲端執行時，操作者需要 `dynamodb:UpdateItem`、`dynamodb:Scan` 的權限，M4 寫 IAM 時處理
- 只在練習場與 Claude 的替身伺服器上測過；兩者在實驗 2 的結果就不同，雲端行為要上雲後確認
- `disable_user_keys()` 回傳的數字包含原本就已停用的 Key（掃表只按 `user_id` 篩選）；重跑不會壞事，但數字會偏大

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `17f7be9` | 10/14 17:1x | `feat: add a script that disables one key or every key of a user`（分支 `feat/compose-gateway`，`cae6354..17f7be9`） |
| （待推） | 10/14 晚上 | 本筆補上破壞實驗與三句，隨容器驗證的 commit 一起推 |

---

## E113. 第 7 項：OpenAI 工作負載身分聯盟探測成功，`chat.completions` 收這種權杖（2026-10-14 19:00～20:12）

**依據：** E110（定案 A：M4 直接用身分聯盟；退路 B：SSM 放金鑰）；決策書 4.5。

**目的：** 把 M4 最大的未知數提前驗證：OpenAI 的 `chat.completions` 收不收 AWS 開出的身分證明（JWT）換來的存取權杖；整條路不用 API 金鑰。

**生活比喻：** 不再發萬用鑰匙。員工每次刷員工證（AWS 的身分證明，5 分鐘有效），警衛核對發證單位與用途後，給一張臨時通行證（OpenAI 的存取權杖），通行證只能進一個房間（Chat completions）。

### 設定（本人在主控台操作）

**AWS：**

| 步驟 | 結果 |
|---|---|
| `aws login`、`aws sts get-caller-identity` | 成功 |
| `aws iam enable-outbound-web-identity-federation` | 成功，取得帳號專屬的 issuer 網址（`https://<issuer>`，網域為 `tokens.sts.global.api.aws`） |

**OpenAI（組織設定 → Security → Workload Identity Provider）：**

| 項目 | 設定 |
|---|---|
| 身分提供者 | Name `aws-outbound-capstone`；Provider type `OIDC`；OIDC Issuer URL = 探測印出的 `iss`；Audience `llm-gateway-capstone`；不用自訂探索網址、不上傳 JWKS、不加屬性轉換 |
| 服務帳號對應 | Name `terry-admin-probe`；Key `sub`、Value = 探測印出的 `sub`（IAM 使用者的 ARN）；Project `llm-gateway-capstone` |
| 服務帳號 | **新建 `gateway-wif`**（不用 `m1-gateway`，見下方定案） |
| 權限 | Restricted：**只開 Model capabilities 裡的 Chat completions（`/v1/chat/completions`）**，其他全部 None |

### 定案（19:58，本人選 A）

| 選項 | 做法 | 評估 |
|---|---|---|
| **A（採用）** | 新建服務帳號 `gateway-wif` 給身分聯盟用 | 用金鑰與不用金鑰的呼叫分屬兩個身分：用量分得開，停其中一個不牽連另一個；不受 `m1-gateway` 金鑰 11/2 到期與換金鑰影響 |
| B | 沿用 `m1-gateway` | 少一步；但與 11/2 到期的金鑰綁在一起（OpenAI 刪金鑰時是否影響服務帳號，未查證） |

**權限只開 Chat completions 的理由：** Gateway 只呼叫 `chat.completions`。這個身分即使被濫用，也不能讀檔案、微調、碰 Vector Store。OpenAI 的權限頁把 `/v1/chat/completions` 列成可以單獨開的一項，比文件寫的（`api.model.request` 等）更細。

### 探測結果（本人執行，`scripts/probe_wif.py`；日誌 `docs/logs/m4-wif-probe.log`）

| 次 | 條件 | `[1]` AWS 開證明 | `[2]` OpenAI |
|---|---|---|---|
| 1 | 只設 audience | ✅ `aud: llm-gateway-capstone`、`sub: arn:aws:iam::<account-id>:user/terry-admin`、有效 300 秒 | 未執行：`KeyError: 'OPENAI_IDENTITY_PROVIDER_ID'`（預期，OpenAI 端尚未設定） |
| 2 | OpenAI 設定完成 | ✅ 同上 | ✅ **`chat.completions` 有回答**：模型 `gpt-6-luna`、結束原因 `stop`、輸入 12、輸出 12 個 token |
| 3（破壞實驗） | audience 改成 `llm-gateway-wrong` | ✅ `aud: llm-gateway-wrong`（AWS 照開） | ❌ `openai.OAuthError: OAuth authentication error.`，發生在 SDK 向 OpenAI 換存取權杖的那一步（`_fetch_token_from_exchange`），還沒送出對話請求 |

**判讀：**

- **第 2 次：** OpenAI 驗過 AWS 的簽章、audience，對上 `sub` → 服務帳號 `gateway-wif`，`/v1/chat/completions` 收下。腳本偵測到 `OPENAI_API_KEY` 有值就會停，所以這次成功**沒有用到任何 API 金鑰**
- **第 3 次：** AWS 不管證明要拿去哪裡用，要什麼 audience 就照開；擋下來的是 OpenAI 的換證口，對話端點根本沒被呼叫。所以證明了：替別的服務開出的證明，拿不到這個 OpenAI 專案的通行證
- 花費：第 2 次 24 個 token，遠低於 US$0.0001

**執行時遇到的事（與重做探測有關）：** `aws configure export-credentials` 匯出到環境變數的是**固定的臨時身分，不會自動換新**；環境變數又比 `aws login` 的登入狀態優先，28 分鐘後再跑 AWS CLI 出現 `Credentials were refreshed, but the refreshed credentials are still expired`。做法：CLI 指令用登入狀態（先 `Remove-Item Env:AWS_*`），只有在跑 Python 腳本前才匯出，匯出後馬上跑。臨時身分的確切有效期沒有查證。Fargate 不會有這個問題：任務角色的憑證由 ECS 自動換新。

### 結論：M4 照 A 做，退路 B 不需要

### 限制（誠實記錄）

- **證明的是 IAM 使用者 `terry-admin`，不是 Fargate 的角色。** M4 要在 OpenAI 另建一筆對應（`sub` = Fargate 任務角色的 ARN），Fargate 上拿不拿得到證明、DNS 防火牆放行 `sts.ap-northeast-1.amazonaws.com` 與 `auth.openai.com` 後通不通，都要 M4 才驗證
- 破壞實驗 3 的錯誤訊息只有 `OAuth authentication error.`，SDK 沒有印出 OpenAI 回的原因；推定是 audience 不符（唯一改的地方），但沒有看到原文
- 只用一個請求驗證；權杖快到期時 SDK 自動重換（E110 查到的「到期前 20 分鐘」）沒有測到
- 沒有測「權限只開 Chat completions」會不會擋下其他端點（例如 `responses`）
- `terry-admin-probe` 對應留著，M4 的 Fargate 角色對應驗證成功後刪除；帳號的對外身分聯盟保持開啟（M4 要用）

### 面試可用的說法

- 「Gateway 呼叫 OpenAI 不用 API 金鑰。容器用 AWS 的身分向 STS 要一張 5 分鐘的證明，拿去 OpenAI 換一小時的通行證。所以沒有金鑰可以外流，也不用輪替金鑰。」
- 「上雲前我先用自己的 IAM 使用者把整條路打通，因為官方文件只示範 Responses API，沒說 Chat Completions 收不收。我也事先定了退路：不通就改回 SSM 放金鑰。」
- 「我做了破壞實驗：把 audience 改成別的值，AWS 照樣開證明，但 OpenAI 在換通行證那一步就拒絕了。代表替別的服務開出的證明，拿不到我這個專案的通行證。」
- 「OpenAI 那邊我只開了 Chat completions 一個權限，還另外建一個服務帳號專門給這條路用，跟原本用金鑰的那個分開。」

**推送：** 日誌與本筆隨容器驗證的 commit 一起推。

---

## E114. 第 1 項：容器驗證（2026-10-14 20:15～20:40；破壞實驗 10/15 01:40）

**依據：** M2 報告、E95（容器裡讀得到 `app/config.toml`、對話流程完整）；E109（每次呼叫 OpenAI 的逾時 30 秒，沒量過）；E111（`DYNAMODB_TARGET`）。

**目的：** M4 要搬上 Fargate 的就是這個映像。上雲前先在本機證明：建得起來、設定檔有打包進去、說明頁關閉、連得到資料庫容器、真實對話完整、稽核寫得進去。

### 1. 建映像與基本檢查

```
docker compose --profile gateway up -d --build
```

| 檢查 | 結果 | 證明了 |
|---|---|---|
| `docker compose ps` | `gateway`（`llm-gateway-gateway`）`Up`；`dynamodb`、`dynamodb-test` `Up` | 映像建得起來、容器跑得動 |
| `irm http://127.0.0.1:8000/health` | `status: ok` | 容器裡的 Gateway 正常回應（ALB 的健康檢查靠它） |
| `docker compose exec gateway ls app` | 清單有 `config.toml` | 設定檔打包進映像，不依賴主機上的檔案 |
| `curl.exe … /docs` | `404` | 說明頁在容器裡也是關的（E109） |

### 2. 容器連得到資料庫容器

- 種子腳本（`uv run --env-file .env python -m scripts.seed`）從主機經 `127.0.0.1:8001` 塞資料；容器裡的 Gateway 經 `dynamodb:8000` 連同一個資料庫容器
- 壞 Key：`curl.exe … -H "Authorization: Bearer gw_bad"` → **`401`**（不是 `503`）。Gateway 真的查了資料庫、查不到才拒絕

### 3. 真實對話（bob 的新 Key 以 `Read-Host` 收進變數；`data\demo.ps1` 的 `ask`）

稽核改讀容器裡的檔：`docker compose exec gateway tail -n 1 data/audit.jsonl`（`demo.ps1` 原本的 `last` 讀的是主機上 M3 留下的舊檔）。

| 題目 | 回應 | 稽核 | 手算（micro-USD） |
|---|---|---|---|
| `s05-easy` | `200`、`gpt-6-luna` | `routed_model: gpt-6-luna`、`route_reason: default`、輸入 19、輸出 10、`7` | 19 × 0.1 ＋ 10 × 0.5 ＝ 6.9 → 7 ✅ |
| `s05-hard` | `200`、`gpt-6-sol` | `routed_model: gpt-6-sol`、`route_reason: keyword`、輸入 34、輸出 103、`1098` | 34 × 2 ＋ 103 × 10 ＝ 1,098 ✅ |

**所以證明了：** 容器版的 Gateway 讀得到 `.env` 的金鑰與映像裡的 `config.toml`、連資料庫容器驗 Key 與扣額度、照規則選模型、呼叫真的 OpenAI、把稽核寫進容器裡的 `data/`（`Dockerfile` 事先建好 `data` 並交給 `appuser`，非 root 也寫得進去）。

### 4. 強模型寫長回答要幾秒（E109 的待查項目）

訊息用 M3 測試集最長的 `c07`（319 字，超過字數門檻，走強模型）；`(Measure-Command { ask c07-long | Out-Host }).TotalSeconds`。

| 項目 | 結果 |
|---|---|
| 回應 | `200`；`routed_model: gpt-6-sol`、`route_reason: length` |
| 時間 | **25.6 秒**（整個請求，含查 Key、查額度、寫稽核；本機資料庫這幾步可忽略） |
| token | 輸入 281、輸出 **1,576**（比 M3 測到的最長 1,372 還長） |
| 成本 | 281 × 2 ＋ 1,576 × 10 ＝ **16,322** ✅（約 US$0.016） |
| 速度 | 約每秒 62 個 token |

**發現：30 秒的逾時不夠。** 強模型的輸出上限是 2,000 個 token；以同樣速度推算 2,000 ÷ 62 ≈ 32 秒，**寫滿上限一定逾時**：使用者拿到 502，而 OpenAI 可能已經寫完、已經收費。只有一個樣本，供應商忙碌時會更慢。

**待本人選擇（Claude 的建議是 A；10/15 本人選 A，見 E115）：**

| 選項 | 做法 | 評估 |
|---|---|---|
| **A（建議）** | `OPENAI_TIMEOUT_SECONDS` 30 → 60；M4 的 ALB 閒置逾時設 120 秒（強模型 60 ＋ 降級後便宜模型 60） | 改一個常數與一個測試；2,000 個 token 約 32 秒，近一倍餘裕。代價：最壞等 60 秒、慢請求佔連線較久 |
| B | 強模型輸出上限 2,000 → 1,500 | 不改逾時；但這次 `c07` 的 1,576 就會被截斷，回答品質直接變差 |
| C | 改成串流回應 | 大改 `chat()`、稽核、成本計算，時程不允許 |

### 5. 破壞實驗：設定檔寫錯，容器起不來（本人執行，10/15 01:40）

`app/config.toml` 的 `strong_model` 改成 `"gpt-6-xxx"`，`docker compose --profile gateway up -d --build`：

| 步驟 | 結果 |
|---|---|
| 建映像 | 只有 `COPY app ./app` 之後兩層重做（3.6 秒），其他都是 `CACHED`；`Container llm-gateway-gateway-1 Started` |
| `docker compose ps -a`（啟動後 1 秒） | `gateway` **`Up Less than a second`** |
| `docker compose logs gateway --tail 15` | `File "/app/app/main.py", line 24` → `CONFIG = load_config(CONFIG_PATH)` → `check_config(config)` → **`app.config.ConfigError: Routing uses a model with no settings: gpt-6-xxx`** |
| `git restore app\config.toml` 後重建 | **所有層都是 `CACHED`**（包括 `COPY app ./app`）；`gateway` `Up 8 seconds` |

**判讀：**

- **設定寫錯，程式在載入時就停下：** `main.py` 一載入就呼叫 `load_config()` → `check_config()`，發現路由用到的模型沒有設定，丟 `ConfigError`；uvicorn 載入不到 `app.main:app`，服務不會開始接請求。不會帶著錯的設定上線、等到第一個請求才出錯
- **改設定一定要重建映像：** 改了 `config.toml`，`COPY app ./app` 那一層就重做；`config.toml` 是打包在映像裡的，不是從主機讀
- **改回來後所有層都命中快取：** 映像內容與先前驗證過的那一版完全相同，所以不用重測對話流程
- **`docker compose` 顯示 `Started`、`ps` 顯示 `Up` 都不代表服務可用：** 容器確實啟動了，是裡面的程式載入失敗。M4 的 ECS 不能只看「任務有沒有啟動」，要靠 ALB 打 `/health` 的健康檢查與部署斷路器（deployment circuit breaker）判斷新版本有沒有起來，起不來就自動退回舊版

### 限制（誠實記錄）

- 容器裡的稽核檔沒有掛到外面，容器重建就消失；第 2 項（稽核搬進 `audit` 表）處理，Fargate 上同樣如此
- 容器讀的是 `.env` 的 OpenAI 金鑰（本機開發的方式）；不用金鑰的身分聯盟（E113）要到 Fargate 才接上
- 長回答只量了一次
- **破壞實驗沒有拍到 `Exited`：** `ps -a` 是在啟動後 1 秒打的，當時還是 `Up Less than a second`；`ConfigError` 由日誌證明，但容器之後轉成 `Exited` 的那一刻沒有記錄到。要補證時，改壞設定、重建後等 5 秒再 `docker compose ps -a`

**推送：** 與 E112 的補充、E113、`docs/logs/m4-wif-probe.log` 一起推（commit 見 E115）。

---

## E115. PR #3 合併；逾時改成 60 秒（2026-10-15 15:10～15:40）

**依據：** E108（分支流程）、E109（SDK 不重試、30 秒的逾時沒量過）、E114（強模型 1,576 個 token 花 25.6 秒）；決策書 D10、D67。

### 1. PR #3：`feat/compose-gateway` → `main`

**開 PR 前的檢查（本人執行）：**

| 檢查 | 結果 |
|---|---|
| `git status` | `On branch feat/compose-gateway`、`up to date`、`working tree clean` |
| `git log --oneline -3` | `3a9ed2b`（`docs: update the evidence log to the final version`）、`b0bbf21`（`docs: record the container check and the keyless OpenAI probe`）、`17f7be9` |
| 證據紀錄是最終版 | `git grep -c gpt-6-xxx origin/feat/compose-gateway -- docs/evidence/m4-evidence-log.md` → `:2`（只有最終版有設定檔改壞的實驗） |
| 檔案清單 | `git diff --stat origin/main...origin/feat/compose-gateway`：22 個檔、`+1,329 -39`；只有 `.env.example`、沒有 `.env`；沒有 `docs/handoff/` |

**檢查與合併：**

| 檢查 | 結果 | 必要 |
|---|---|---|
| `ci / Tests` | ✅ 24 秒 | Required |
| `ci / Image scan` | ✅ 46 秒；1 個警告（見下） | Required |
| `CodeQL / Analyze (actions)`、`Analyze (python)` | ✅ | — |

- 本人按 **Merge pull request**（Create a merge commit），GitHub 上刪除分支
- 本機：`git pull` → `cd9abf6..dcd76c2`，`Fast-forward`；`git fetch --prune` → `[deleted] origin/feat/compose-gateway`；`git branch -d` → `Deleted branch feat/compose-gateway (was 3a9ed2b)`
- `main` 現在是 `dcd76c2`（`Merge pull request #3 from Poyu-Tu/feat/compose-gateway`）
- 這次用按鈕合併，補上 E108「PR #2 是在終端機合併的」那一項

**`Image scan` 的警告：**

```
Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/cache@0400d5f644dc74513175e3c…
```

- **來源（Claude 查證）：** `ci.yml` 本身沒有用 `actions/cache`；它在 `aquasecurity/trivy-action` v0.35.0 的 `action.yaml` 裡（`actions/cache@0400d5f…`，v4.2.4，用來快取 Trivy 的漏洞資料庫）
- **Dependabot 第一個 PR（#4）：** 合併後幾分鐘內開出，把 Trivy 的 Action 升到 v0.36.0；v0.36.0 的 `action.yaml` 改用 `actions/cache@27d5ce7…`（v5.0.5）、`setup-trivy` v0.2.6。**推定合併 #4 就會消除這個警告**，尚未驗證
- 處理：#4 先不合併。它改的是擋漏洞的那一關，M4 加 `trivy config` 時一起看變更內容再決定
- 證明了 E110 的 Dependabot 設定有效：合併進 `main` 後立刻開始運作

### 2. 定案：逾時 30 → 60 秒（15:37，本人選 A）

| 選項 | 做法 | 評估 |
|---|---|---|
| **A（採用）** | `OPENAI_TIMEOUT_SECONDS` 30 → 60；M4 的 ALB 閒置逾時設 120 秒 | 只改一個常數與一個測試。2,000 個 token 只要速度不低於每秒約 33 個就不會逾時（E114 量到每秒約 62 個） |
| B | 強模型輸出上限 2,000 → 1,500 | E114 量到的 1,576 個 token 就會被截斷；供應商忙碌、速度掉到每秒 50 個時，1,500 個仍要 30 秒，一樣撞線 |
| C | 串流回應 | `chat()`、稽核、成本計算都要重寫，M4 前做不完 |
| （另一個做法） | 只給強模型 60 秒、便宜模型維持 30 秒 | 較精準，但要改 `app/fallback.py` 的函式與測試；現在不值得 |

**生活比喻：** 外送平台 30 分鐘沒送到就自動取消，但大份餐要做 32 分鐘：菜做好了、錢也扣了，客人卻收到「訂單取消」。改成等 60 分鐘。

### 3. 修改與測試（本人執行，先改測試、再改常數）

`tests/test_production_settings.py`：`test_openai_client_gives_up_after_30_seconds` 改名為 `test_openai_client_gives_up_after_60_seconds`，比對的數字改成 60。

`app/main.py`：

```python
OPENAI_TIMEOUT_SECONDS = 60
```

上方補一行註解說明理由（強模型寫滿 2,000 個 token 約 32 秒）。只改常數，沒有三句。

| 時間點 | 指令 | 結果 |
|---|---|---|
| 只改測試 | `uv run pytest tests/test_production_settings.py -q` | `1 failed, 3 passed`：`test_openai_client_gives_up_after_60_seconds - assert 30 == 60` |
| 改完常數 | `uv run pytest -q` | `290 passed`（9.35 秒，含 DynamoDB Local 的測試） |

- `assert 30 == 60`：測試先看到程式裡還是 30，紅的原因是對的；改完常數才綠

### 限制（誠實記錄）

- **60 秒是用一個樣本推出來的。** E114 只量了一次長回答；供應商忙碌時速度若低於每秒約 33 個，寫滿 2,000 個 token 仍會逾時
- **逾時後 OpenAI 仍可能已經收費**，這個風險沒有消失，只是機率變小
- **理論最長等待變成 120 秒**（強模型 60 ＋ 降級後的便宜模型 60），使用者等得久、連線佔得久；ALB 的 120 秒還不存在，要在 M4 的 Terraform 明寫並上雲實測
- 測試只確認連線物件的逾時是 60，沒有真的等 60 秒
- `Image scan` 的警告「合併 #4 就會消失」只是對照兩版 `action.yaml` 的推定

### 面試可用的說法

- 「我原本給 OpenAI 30 秒逾時，上雲前量了一次最長的回答：強模型寫 1,576 個 token 花了 25.6 秒，換算寫滿上限 2,000 個要 32 秒，一定逾時，而且供應商那邊可能已經收費。所以改成 60 秒，負載平衡器配合設 120 秒。我沒選縮短輸出上限，因為量到的那題就會被截斷，而且供應商一慢照樣撞線。」
- 「合併後 CI 出現一個警告，我追到它不是我的 workflow 用的，是 Trivy 的 Action 內部用的快取套件太舊。Dependabot 幾分鐘後就開了升級的 PR，新版剛好換掉那個套件；但它改的是擋漏洞的那一關，我刻意先不合併，上雲前一起看。」

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `b0bbf21` | 10/15 01:45 前後 | `docs: record the container check and the keyless OpenAI probe`（E112 補充、E113、E114 舊版、`docs/logs/m4-wif-probe.log`） |
| `3a9ed2b` | 10/15 01:45 前後 | `docs: update the evidence log to the final version` |
| `dcd76c2` | 10/15 15:2x | `Merge pull request #3 from Poyu-Tu/feat/compose-gateway`（`cd9abf6..dcd76c2`） |
| （待推） | 10/15 | 逾時改動與本筆，分支 `fix/openai-timeout-60s`，PR #5 |

---

## 決策書 v2.10 待改項目

| # | v2.9 的位置 | 要改什麼 |
|---|---|---|
| 1 | D21、D67、10.3 | `protect-main` 已實測：沒跑過 CI 的 commit 直接推 `main` 被擋（GH013、2 個必要檢查 `Tests`、`Image scan`）；另加「Require a pull request before merging」（核准數 0）；Bypass list 為空。已滿足條件的 PR，推它的 commit 等於合併它（E108） |
| 2 | 12.5「FastAPI 自動文件頁」、PART 9 安全 | 說明頁一律關閉（`docs_url`、`redoc_url`、`openapi_url` 都是 `None`），由 `tests/test_production_settings.py` 釘住；12.5 該列劃掉（E109） |
| 3 | 12.5「資料庫故障的 503 要不要附 `Retry-After`」、2.2 的回應對照表、D48 | 不附；4 個資料庫 503 的測試釘住；12.5 該列劃掉（E109） |
| 4 | D10、D59、3.4、12.5「SDK 的等待與 ALB 閒置逾時」 | `OPENAI_MAX_RETRIES` 由 1 改為 0：所有 OpenAI 呼叫都不讓 SDK 重試；強模型那次的 `with_options(max_retries=0)` 保留。代價：網路瞬間抖動直接 502。ALB 閒置逾時在 M4 的 Terraform 明寫（理論最長 2 × 30 = 60 秒）（E109） |
| 5 | D22（repo 結構） | `compose.yaml` 加上 `gateway` 服務（profile `gateway`）；`tests/` 加上 `test_production_settings.py`（E109；容器驗證待補） |
| 6 | 4.5、4.1、3.5、D21 | OpenAI 改用工作負載身分聯盟：Fargate 角色向地區 STS 要 JWT，換成 OpenAI 存取權杖，SSM 不放 OpenAI 金鑰；DNS 防火牆放行清單加 `auth.openai.com`、`sts.ap-northeast-1.amazonaws.com`；`get_client()` 改為共用一個連線物件。退路是 SSM 放金鑰（E110）。探測成功：`chat.completions` 收這種權杖；OpenAI 端用專用服務帳號 `gateway-wif`、權限只開 Chat completions；M4 另建 Fargate 角色的對應（E113） |
| 7 | 10.3、D19 | `.github/dependabot.yml`：GitHub Action 與 Dockerfile 基底映像的版本更新，每週、冷卻 7 天；Python 套件只收安全性更新（E110） |
| 8 | 12.5「`app/db.py` 怎麼表示連真的 AWS…」、D49、PART 4 應用層 | `DYNAMODB_TARGET`：`aws` 連雲端（IAM 角色）、網址連練習場（假帳密）、沒設或寫錯就報錯；三個讀取強一致；雲端計費模式隨需；12.5 該列劃掉（E111） |
| 9 | 12.5「停用 Key 的腳本」、D22（repo 結構） | `scripts/disable_key.py`：`--key`（`getpass` 輸入）停一把、`--user` 停一個人的全部；更新加「必須已存在」的條件；`tests/` 加上 `test_disable_key.py`（E112） |
| 10 | D10、3.4、12.5「SDK 的等待與 ALB 閒置逾時」 | `OPENAI_TIMEOUT_SECONDS` 由 30 改為 60（強模型 1,576 個 token 實測 25.6 秒，寫滿 2,000 約 32 秒）；M4 的 ALB 閒置逾時設 120 秒（E114、E115） |

---

## 目前進度（2026-10-15 15:40）

- 第 0 步：分支流程 ✅（E108；PR #3 改用按鈕合併 ✅，E115）
- 第 1 項：容器驗證 ✅（E114）；逾時改成 60 秒 ✅（E115，分支 `fix/openai-timeout-60s` 待開 PR）
- 第 3 項：`DYNAMODB_TARGET`、強一致讀取、隨需計費 ✅（E111）
- 第 4 項：停用 Key 的腳本 ✅（E112）
- 第 5、6 項：說明頁關閉、資料庫 503 不附 `Retry-After`、SDK 不重試 ✅（E109）
- 第 7、8 項：身分聯盟探測成功、Dependabot 運作中 ✅（E110、E113、E115）
- **PR #3 已合併（`main` = `dcd76c2`）**；Dependabot 的 PR #4（Trivy Action v0.36.0）留到 M4
- `290 passed`
- **剩第 2 項：稽核搬進 `audit` 表**
- 下一筆證據是 **E116**

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| 稽核搬進 `audit` 表；扣額度失敗的紀錄與告警；`pii_types` 的型別（D52） | — | 10/16 前 |
| ~~`app/db.py` 連真的 AWS 的表示法；強一致讀取；DynamoDB 計費模式（E89、E90）~~ | ✅ 10/14（E111） | — |
| ~~停用 Key 的腳本（E91）~~ | ✅ 10/14 程式、測試、破壞實驗、三句（E112） | — |
| ~~`/docs`、`/openapi.json` 是否在正式環境關閉（12.5）~~ | ✅ 10/14 一律關閉（E109） | — |
| ~~資料庫故障的 503 要不要附 `Retry-After`（12.5）~~ | ✅ 10/14 不附，測試釘住（E109） | — |
| ~~便宜模型那次 SDK 的等待與 ALB 閒置逾時（E100）~~ | ✅ 10/14 SDK 一律不重試（E109） | — |
| ALB 閒置逾時的值（E109、E114、E115） | **120 秒**（逾時已改 60 秒）；Terraform 明寫 | M4 寫 Terraform 時 |
| ~~30 秒的逾時夠不夠（E109）~~ | ✅ 10/15 不夠，改 60 秒（E114、E115） | — |
| ~~容器驗證~~ | ✅ 10/15（E114） | — |
| M4 的 ECS 部署要能判斷新版本起不來（E114） | ALB 健康檢查打 `/health`、開部署斷路器，起不來自動退回 | M4 寫 Terraform 時 |
| ~~OpenAI 工作負載身分聯盟（4.5、E110）~~ | ✅ 10/14 探測成功（E113）；Fargate 角色的對應在 M4 | — |
| `m1-gateway` 金鑰 11/2 到期（12.5） | 雲端改用身分聯盟就不需要；**本機開發與 11/2 之後的錄影仍要用金鑰**，到期前在個人電腦換一把新的 | 11/2 前 |
| ~~Trivy 升級與 Action 的更新方式（E104）~~ | ✅ 10/14 Dependabot 管 Action 與基底映像；Trivy 本身的版本在加 `trivy config` 時手動升級（E110） | M4 |
| CI 加 `trivy config`（E104） | 有 Terraform 之後；同時看 Dependabot 的 PR #4（Trivy Action v0.36.0，推定可消除 Node.js 20 警告，E115） | M4 |
| 供應商預算用完的告警（D32、E100） | M3 只記稽核的 `error_code` | M4～M6 |
| 預扣（7.10） | M3 不做 | M5 |
| A 能不能擋住「沒進 PR、但有綠勾的 commit」（E108） | 目前的 `ci.yml` 做不出這種 commit；不另外測 | — |
