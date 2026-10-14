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

## 決策書 v2.10 待改項目

| # | v2.9 的位置 | 要改什麼 |
|---|---|---|
| 1 | D21、D67、10.3 | `protect-main` 已實測：沒跑過 CI 的 commit 直接推 `main` 被擋（GH013、2 個必要檢查 `Tests`、`Image scan`）；另加「Require a pull request before merging」（核准數 0）；Bypass list 為空。已滿足條件的 PR，推它的 commit 等於合併它（E108） |
| 2 | 12.5「FastAPI 自動文件頁」、PART 9 安全 | 說明頁一律關閉（`docs_url`、`redoc_url`、`openapi_url` 都是 `None`），由 `tests/test_production_settings.py` 釘住；12.5 該列劃掉（E109） |
| 3 | 12.5「資料庫故障的 503 要不要附 `Retry-After`」、2.2 的回應對照表、D48 | 不附；4 個資料庫 503 的測試釘住；12.5 該列劃掉（E109） |
| 4 | D10、D59、3.4、12.5「SDK 的等待與 ALB 閒置逾時」 | `OPENAI_MAX_RETRIES` 由 1 改為 0：所有 OpenAI 呼叫都不讓 SDK 重試；強模型那次的 `with_options(max_retries=0)` 保留。代價：網路瞬間抖動直接 502。ALB 閒置逾時在 M4 的 Terraform 明寫（理論最長 2 × 30 = 60 秒）（E109） |
| 5 | D22（repo 結構） | `compose.yaml` 加上 `gateway` 服務（profile `gateway`）；`tests/` 加上 `test_production_settings.py`（E109；容器驗證待補） |
| 6 | 4.5、4.1、3.5、D21 | OpenAI 改用工作負載身分聯盟：Fargate 角色向地區 STS 要 JWT，換成 OpenAI 存取權杖，SSM 不放 OpenAI 金鑰；DNS 防火牆放行清單加 `auth.openai.com`、`sts.ap-northeast-1.amazonaws.com`；`get_client()` 改為共用一個連線物件。退路是 SSM 放金鑰（E110；探測結果待補） |
| 7 | 10.3、D19 | `.github/dependabot.yml`：GitHub Action 與 Dockerfile 基底映像的版本更新，每週、冷卻 7 天；Python 套件只收安全性更新（E110） |

---

## 目前進度（2026-10-14 14:40）

- 第 0 步：分支流程 ✅（E108，PR #2 合併為 `cd9abf6`）
- 第 1 項：`compose.yaml` 加上 `gateway` 服務（profile）已寫好並推到分支 `feat/compose-gateway`（`b0b0d9c`）；**建映像與容器驗證還沒做**（下一筆證據）
- 第 5、6 項：說明頁關閉、資料庫 503 不附 `Retry-After`、SDK 不重試 ✅（E109，`3864f57`，同一個分支）；`271 passed`（45 個 `integration`）
- 第 7、8 項：身分聯盟（今晚探測）、Dependabot 定案（E110）
- 分支 `feat/compose-gateway` 的 PR：容器驗證完成後再開
- 下一筆證據是 **E111**

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| 稽核搬進 `audit` 表；扣額度失敗的紀錄與告警；`pii_types` 的型別（D52） | — | 10/16 前 |
| `app/db.py` 連真的 AWS 的表示法；強一致讀取；DynamoDB 計費模式（E89、E90） | — | 10/16 前 |
| 停用 Key 的腳本（E91） | — | 10/16 前 |
| ~~`/docs`、`/openapi.json` 是否在正式環境關閉（12.5）~~ | ✅ 10/14 一律關閉（E109） | — |
| ~~資料庫故障的 503 要不要附 `Retry-After`（12.5）~~ | ✅ 10/14 不附，測試釘住（E109） | — |
| ~~便宜模型那次 SDK 的等待與 ALB 閒置逾時（E100）~~ | ✅ 10/14 SDK 一律不重試（E109） | — |
| ALB 閒置逾時的值（E109） | Terraform 明寫；理論最長 2 × 30 = 60 秒，考慮設 75 | M4 寫 Terraform 時 |
| 30 秒的逾時夠不夠（E109） | 用容器打一次強模型的長回答，記下花了幾秒（約 US$0.015） | 容器驗證時 |
| 容器驗證：建映像、`/health`、容器裡的說明頁 404、連得到資料庫容器、真實對話、設定檔改壞拒絕啟動 | 分支 `feat/compose-gateway` 已備好 | 10/14 晚上 |
| OpenAI 工作負載身分聯盟（4.5、E110） | 已定案用 A；`chat.completions` 收不收要靠今晚的探測 | 10/14 晚上 |
| `m1-gateway` 金鑰 11/2 到期（12.5） | 雲端改用身分聯盟就不需要；**本機開發與 11/2 之後的錄影仍要用金鑰**，到期前在個人電腦換一把新的 | 11/2 前 |
| ~~Trivy 升級與 Action 的更新方式（E104）~~ | ✅ 10/14 Dependabot 管 Action 與基底映像；Trivy 本身的版本在加 `trivy config` 時手動升級（E110） | M4 |
| CI 加 `trivy config`（E104） | 有 Terraform 之後 | M4 |
| 供應商預算用完的告警（D32、E100） | M3 只記稽核的 `error_code` | M4～M6 |
| 預扣（7.10） | M3 不做 | M5 |
| A 能不能擋住「沒進 PR、但有綠勾的 commit」（E108） | 目前的 `ci.yml` 做不出這種 commit；不另外測 | — |
