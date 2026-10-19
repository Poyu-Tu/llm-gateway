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
| `b0bbf21` | 10/15 01:45 前後 | 本筆補上破壞實驗與三句，隨容器驗證的 commit 一起推（見 E115） |

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
| `c0bdaca` | 10/15 15:4x | `Merge pull request #5 from Poyu-Tu/fix/openai-timeout-60s`（逾時改動與本筆） |

---

## E116. 第 2 項：稽核搬進 `audit` 表；寫不進去時印一行日誌（2026-10-15 15:54～20:51）

**依據：** 決策書 3.2（`audit` 表）、7.10（扣額度）、D7（摘要與 HMAC 不外流）、D43（`pii_types` 的意義與順序）、D51（模型回答後照樣交出去）、D52（稽核搬家）；E114（容器重建就丟失的稽核檔）。

**目的：** 稽核原本寫在容器裡的 `data/audit.jsonl`，容器重建就消失，Fargate 上也是一樣。改寫進 DynamoDB 的 `audit` 表；資料庫寫不進去時，使用者照樣拿到回應，那一筆的中繼資料印成一行日誌，M4 由 CloudWatch 告警。

**生活比喻：** 收銀機的流水帳原本寫在店裡的筆記本，店一裝潢就丟了。現在改寄回總公司的帳本；郵差送不到時，店員在白板寫一行「幾號單、誰、多少錢、有沒有收到錢」，客人的餐照樣給，白板上不抄客人點了什麼。

### 定案（15:54，本人「照建議」）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | 稽核寫不進資料庫時，那一筆放哪裡 | **印一行 JSON 日誌到 stderr**（Fargate 上進 CloudWatch Logs），只有中繼資料：`request_id`、`user_id`、`timestamp`、`status`、`cost_micro_usd`、`charged`、`error_type`；**不放摘要與 HMAC**（D7） | 容器內檔案：容器重建就消失，等於沒記。另開 SQS／S3：等於提前做 M5 | 補收要手動、還原不出完整紀錄；日誌也寫不出去時那一筆就沒了 |
| 2 | 稽核寫不進去時，使用者拿到什麼 | **照原本的回應**：成功照給、429 照 429、502 照 502，只多一行日誌 | 回 503：成功那條路錢已經付了，違背 D51 | 使用者端完全看不出稽核失敗，只能靠告警 |
| 3 | `pii_types` 的型別 | **清單（`L`）** | String Set（`SS`）：DynamoDB 不收空的 Set、Set 不保留順序；D43 要求空清單代表「檢查過、沒找到」，順序固定 `EMAIL`、`CARD`、`PHONE`、`TW_ID` | — |
| 4 | 測試怎麼改 | **稽核改走領用窗口 `get_audit_writer()`**；既有測試把窗口換成「寫暫存檔」的替身，約 110 處斷言不用改；另寫連 DynamoDB Local 的測試 | 所有測試改讀 DynamoDB：全部要連資料庫、改動上百處 | 大部分對話測試走替身，不走真的資料庫 |

### 程式（本人撰寫，填空 11 格）

`app/audit.py`：

| 函式 | 做什麼 |
|---|---|
| `write_audit(client, record)` | `TypeSerializer` 把每個值轉成 DynamoDB 格式，`put_item` 加 `ConditionExpression="attribute_not_exists(request_id)"`：同一個 `request_id` 已存在就拒絕，不覆蓋 |
| `report_audit_failure(record, error)` | 從白名單 `FAILURE_LOG_FIELDS`（6 欄）用 `record.get()` 挑欄位（被額度擋下的紀錄沒有成本欄，拿不到給 `None`），加上 `event`、`error_type`，`print(json.dumps(...), file=sys.stderr, flush=True)` |
| `save_audit(client, record)` | 先 `write_audit()`；只接 `BotoCoreError`、`ClientError`，交給 `report_audit_failure()`；程式自己的錯（例如 `TypeError`）照樣往外丟 |

舊的 `append_audit()` 刪除（搬到 `tests/fakes.py`，只剩測試在用）。

`app/main.py`：刪除 `get_audit_path()` 與 `Path` 的 import；新增領用窗口 `get_audit_writer()`（向 `get_dynamodb()` 拿連線，交出「收到紀錄就交給 `save_audit()`」的函式）；`chat_endpoint()` 的參數改成 `write_audit_record = Depends(get_audit_writer)`，四處 `append_audit(record, audit_path)` 改成 `write_audit_record(record)`。

**填空時的錯（都在本機改正）：**

| 格 | 寫成 | 應該是 | 沒改的話 |
|---|---|---|---|
| ⑤ | `record.get(name) \| None` | `record.get(name)` | `TypeError: unsupported operand type(s) for \|: 'str' and 'NoneType'`：`\|` 不是「拿不到就給預設值」，`.get()` 本身就會給 `None` |
| ⑥ | `type(ClientError).__name__` | `type(error).__name__` | 日誌永遠寫 `"type"`（類別的類別），看不出這次是什麼錯 |
| ⑦ | `file=sys` | `file=sys.stderr` | `sys` 是整個模組，`print` 要的是裡面那條錯誤輸出 |
| ⑪ | `Depends(get_dynamodb)` | `Depends(get_audit_writer)` | `77 failed`，全部是 `TypeError: 'FakeDynamoDB' object is not callable`（或 `'DynamoDB'`）：對話入口領到的是資料庫，不是寫稽核的函式 |

- ①～④（`write_audit()`）、⑧～⑩ 一次就對
- 這次的寫法照 `python -c "import ..."` 逐支確認能載入；`report_audit_failure()` 另外用只有 `request_id` 的紀錄實際印一行，看到其餘欄位是 `null`、`error_type` 是 `ValueError`

**Claude 的步驟順序錯誤（兩次，同一類）：** 先叫本人拿掉 `from pathlib import Path`，`append_audit()` 卻還在用它（`NameError: name 'Path' is not defined`）；之後又叫本人在 `app/main.py` 的 import 保留 `append_audit`，但它已經從 `app/audit.py` 刪掉（`ImportError`）。之後改成「先把用到舊東西的地方都換掉，最後才刪舊東西」。

### 測試（Claude 整份提供；測試數 290 → 308）

| 檔案 | 內容 |
|---|---|
| `tests/test_audit_store.py`（新檔，13 個） | 不連資料庫 7 個：日誌只有一行 JSON、欄位剛好是允許的 8 個（沒有摘要與指紋）、被額度擋下的紀錄也印得出來（成本欄 `null`）、寫得進去時不印、資料庫拒絕或連不上時印、程式的錯（`float` → `TypeError`）不吞。連 DynamoDB Local 6 個：讀得回來、清單順序不變、空清單存得進去、沒值存成 NULL、同一個 `request_id` 第二次被拒（`ConditionalCheckFailedException`）且留下第一筆、表不存在時印日誌（`ResourceNotFoundException`） |
| `tests/test_chat_audit_store.py`（新檔，5 個，`integration`） | 用真的窗口：成功與被額度擋下的請求都進 `audit` 表；只有寫稽核失敗時回答照給、429 照 429 且附 `Retry-After`；扣額度與寫稽核同時失敗時，日誌記下 `cost_micro_usd: 7`、`charged: false` |
| `tests/fakes.py` | 新增 `make_file_audit_writer(path)`：寫暫存檔的替身，**寫之前先用 `TypeSerializer` 轉一次**，紀錄混進 DynamoDB 收不下的值時在測試就紅；`append_audit()` 搬來這裡 |
| 6 個既有測試檔 | `test_chat.py`、`test_chat_auth.py`、`test_chat_routing.py`、`test_chat_fallback.py`、`test_chat_truncation.py`、`test_demo_fallback.py`：`get_audit_path` 換成 `get_audit_writer`，覆寫值換成替身；斷言一行都沒改。另外 4 個檔（`test_chat_quota.py`、`test_chat_charge.py`、`test_message_limit.py`、`test_seed.py`）借用前面的道具，自動跟著換 |
| `tests/test_audit.py` | `append_audit` 改從 `tests.fakes` import |

**過程（本人執行）：**

| 時間點 | 結果 |
|---|---|
| 只套用測試 | `12 errors during collection`，全部是 `ImportError: cannot import name 'get_audit_writer'`（11 個）或 `'report_audit_failure'`（1 個）。有 4 個檔沒改也紅，是借用了紅的檔的道具 |
| 寫完 `app/audit.py` 三支函式 | `tests/test_audit_store.py`：`13 passed` |
| ⑪ 填錯 | `77 failed, 231 passed`（78 秒） |
| 改正 ⑪ | `308 passed`（17 秒） |

### 破壞實驗（本人執行，四個，DynamoDB Local；每個做完 `git restore app\audit.py`；只跑兩個新測試檔）

| # | 改了什麼 | 結果 | 失敗訊息 |
|---|---|---|---|
| 1 | 拿掉 `ConditionExpression` | `1 failed, 17 passed` | `test_write_audit_never_overwrites_a_record - Failed: DID NOT RAISE ClientError` |
| 2 | `FAILURE_LOG_FIELDS` 加 `"summary"` | `1 failed, 17 passed` | `test_report_audit_failure_leaves_out_summary_and_hash - AssertionError`（欄位集合不相等） |
| 3 | `write_audit()` 裡把 `pii_types` 改成 `set(value)` | `5 failed, 13 passed` | `stores_the_record`（讀回來是 Set）；`keeps_pii_types_as_an_ordered_list`：`{'SS': ['CARD', ..., 'TW_ID']}`；`keeps_an_empty_pii_types_list`：`ClientError ... (ValidationException) ... PutItem`；`test_chat_writes_the_audit_record_to_the_audit_table`：`{'EMAIL'} == ['EMAIL']`；`test_chat_writes_the_blocked_request_to_the_audit_table`：`assert 0 == 1` |
| 4 | `except` 改成 `except Exception` | `1 failed, 17 passed` | `test_save_audit_does_not_hide_programming_errors - Failed: DID NOT RAISE TypeError` |

四個的數字都與 Claude 事先在試跑環境（替身伺服器 moto）跑的相同。

**判讀：**

- **實驗 1：** `put_item` 預設遇到同一個主鍵直接覆蓋、不報錯。擋住「稽核被改寫」的只有這個條件與這個測試
- **實驗 2：** 白名單的好處：新欄位要進日誌一定得改白名單，改了測試就紅，逼人想「這欄該不該出去」
- **實驗 3：** 三種壞法都看得到。**`SS` 以 `CARD` 開頭**，證明 Set 不保留順序；**空 Set 被 DynamoDB Local 以 `ValidationException` 拒收**；最隱密的是 `0 == 1`：被額度擋下的請求（`"Say hi"`，沒有個資，所以是空清單）寫不進去，`save_audit()` 接住、印一行日誌，**使用者照樣拿到 429，但那一筆沒進表**。退路讓服務不倒，也可能把問題藏起來，所以 M4 一定要有告警
- **實驗 4：** 什麼都接的話，寫錯的程式會被偽裝成「資料庫寫不進去」，值班的人去查好好的資料庫，而每一筆稽核都進不了表

### 查詢工具與 `Dockerfile`（20:15～20:32）

- **`scripts/show_audit.py`**（Claude 提供，查詢用的工具）：`read_audit(client, request_id)` 強一致讀取那一筆、翻回 Python 的值，查不到回 `None`；`main()` 一行一欄印出，查不到印 `No audit record for ...`、結束碼 1。取代 `demo.ps1` 讀容器裡 `data/audit.jsonl` 的 `last`／`clast`
- **`tests/test_show_audit.py`**（2 個，`integration`）：`write_audit()` 寫、`read_audit()` 讀，內容一模一樣；查不到回 `None`。測試數 308 → **310**
- **`Dockerfile`**：刪除 `RUN mkdir data && chown appuser:appuser data` 與它的註解。程式已經不在容器裡寫檔，不需要任何「一般使用者寫得進去」的資料夾；M4 的 ECS 可以設 `readonlyRootFilesystem`

### 容器驗證（20:38～20:47）

`docker compose --profile gateway up -d --build`：

| 檢查 | 結果 | 證明了 |
|---|---|---|
| `docker compose ps` | `gateway` `Up` | 拿掉 `data` 後映像照樣建得起來 |
| `irm .../health` | `status: ok` | 服務正常 |
| `docker compose exec gateway ls` | 只有 `app` | `data` 資料夾真的沒了 |
| `docker compose exec gateway touch x.txt` | `touch: cannot touch 'x.txt': Permission denied` | 容器裡的 `appuser` 在工作資料夾寫不進任何東西，Gateway 照常回應 |

真實對話（種子腳本重建開發用資料庫，bob 的新 Key 以 `Read-Host` 收進變數）：訊息 `Say hi in one short sentence. My email is amy@example.com`（假信箱）。

- 回應：`200`、`gpt-6-luna`；回答提到「請不要分享信箱」：模型收到的是 `My email is [EMAIL]`，看得出原本有個信箱，看不到信箱本身
- `uv run --env-file .env python -m scripts.show_audit $r.request_id`：

| 欄位 | 值 | 證明了 |
|---|---|---|
| `user_id`、`status`、`charged` | `bob`、`ok`、`True` | 容器裡的 Gateway 把稽核寫進 `audit` 表，扣額度成功 |
| `input_tokens`、`output_tokens`、`cost_micro_usd` | 19、14、**9** | 手算 19 × 0.1 ＋ 14 × 0.5 ＝ 8.9 → 9 ✅ |
| `pii_types` | `['EMAIL']` | 清單存進去、讀得回來 |
| `summary` | `Say hi in one short sentence. My email is [EMAIL]` | 個資沒進資料庫 |
| `prompt_hash` | 64 個十六進位字元 | HMAC 指紋照記 |
| `route_reason`、`routed_model`、`model`、`provider_model` | `default`、`gpt-6-luna` ×3 | 路由與計費模型一致 |

- `docker compose logs gateway --tail 5`：只有 `GET /health 200`、`POST /v1/chat 200`，**沒有 `audit_write_failed`**：寫得進去時退路不出聲

### 容器破壞實驗：資料庫裡沒有 `audit` 表（20:50～20:51）

模擬 M4 漏建 `audit` 表或表被誤刪。只動開發用資料庫（8001）。

| 步驟 | 結果 |
|---|---|
| `delete_table(TableName='audit')` | 無輸出 |
| 同一題再問一次 | **`200`**，`request_id` `7485e35d-…`，回答正常 |
| `docker compose logs gateway --tail 5` | `{"event": "audit_write_failed", "request_id": "7485e35d-…", "user_id": "bob", "timestamp": "…", "status": "ok", "cost_micro_usd": 9, "charged": true, "error_type": "ResourceNotFoundException"}` |
| `scripts.create_tables` 建回來後 `show_audit` 那個單號 | `No audit record for 7485e35d-…` |

**判讀：**

- 使用者照樣拿到回答（錢已經花了，定案 2）；日誌一行，單號與回應相同、成本 9、`charged: true`，**沒有摘要與指紋**（定案 1、D7）；表建回來後查不到，證明那一筆**真的只留在日誌**
- 日誌那一行出現在這次請求的 `POST /v1/chat 200` **之前**：稽核在回應交出前就寫（或失敗），uvicorn 的請求紀錄在回應送出後才印
- 這行就是 M4 告警要抓的東西：`{ $.event = "audit_write_failed" }`

### 限制（誠實記錄）

- **大部分對話測試走替身，不走真的資料庫。** 靠 `test_chat_audit_store.py` 的 5 個與容器驗證補；替身會先轉 DynamoDB 格式，擋得住型別問題，擋不住「資料庫行為不同」
- **補收是手動的：** 看日誌、自己補扣額度；日誌只有中繼資料，還原不出完整紀錄。正式做法是 M5 的 SQS
- **日誌也寫不出去時，那一筆就沒了**
- **CloudWatch 的指標篩選與告警還不存在**，要 M4 的 Terraform 建；本機只在 `docker compose logs` 看得到
- `user_id` 進日誌：是內部帳號名，補收時要知道扣誰；仍是識別資訊，日誌群組要設保存期限與存取權限（M4）
- 條件寫入只防「用 `put_item` 覆蓋」；要讓稽核不可竄改，M4 的 IAM 只給 Gateway 對 `audit` 表 `PutItem`，不給 `UpdateItem`、`DeleteItem`
- 真實對話只做了兩次（成功一次、表不存在一次）；雲端 DynamoDB 的條件寫入與錯誤種類要上雲後確認
- `readonlyRootFilesystem` 只證明了「不需要寫」，還沒有真的在 ECS 設定

### 面試可用的說法

- 「稽核原本寫在容器裡的檔案，容器一重建就沒了。我改寫進 DynamoDB，寫入時加條件：同一個請求單號已經存在就拒絕。DynamoDB 的 put_item 預設會直接覆蓋、不報錯，我把條件拿掉做過實驗，只有『寫兩次』那個測試會紅。」
- 「資料庫寫不進稽核時，回答照樣給使用者，因為錢已經付給供應商了。那一筆只印一行 JSON 日誌，用白名單挑欄位，摘要和指紋不會出去。我在容器裡把 audit 表刪掉實測：回應 200、日誌多一行、表建回來後查不到那一筆。M4 會對這行設告警。」
- 「我只接資料庫的錯，不接所有錯。改成全部都接的話，寫錯的程式會被偽裝成資料庫問題，值班的人會去查一個好好的資料庫。這也有一個破壞實驗守著。」
- 「pii_types 我用清單不用 Set。實驗把它改成 Set，順序亂了、空的直接被 DynamoDB 拒收，而且被額度擋下的那筆根本沒進表，使用者端什麼都看不出來。」
- 「程式不再寫檔之後，我把 Dockerfile 裡那個可寫的資料夾也拿掉，在容器裡試著建檔案會被拒絕。上雲可以把容器設成唯讀。」

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `96c0658` | 10/15 19:07 前後 | `feat: write audit records to the audit table and log when that fails`（分支 `feat/audit-table`，12 個檔） |
| `3924348` | 10/15 20:32 | `feat: add show_audit script and drop the writable data folder`（3 個檔） |
| `f3624cb` | 10/15 20:55 | `docs: record moving the audit log into the audit table`（本筆證據紀錄） |
| `8e2ce32` | 10/15 21:01 | `Merge pull request #6 from Poyu-Tu/feat/audit-table`（`c0bdaca..8e2ce32`；5/5 檢查綠） |

---

## E117. M4 本體開工：四項定案與施工順序（2026-10-15 21:13～21:25）

**依據：** 決策書 8.2（M4）、3.5、4.1、4.4、5.1、6.4、D13、D20、D40；`m4-body-start-handoff.md`。

### 開工前檢查

| 項目 | 結果 |
|---|---|
| 本機同步 | `git pull` → `c0bdaca..8e2ce32`（PR #6）；`git branch -d feat/audit-table`；`docker compose --profile gateway down` 後 `docker compose ps` 為空 |
| PR #6 的 CI 附註（本人截圖） | `CodeQL` 2 則通知（notice）：`ubuntu-latest` 自 10/19 起改指 Ubuntu 26。`ci` 1 則警告：已知的 Node.js 20（Trivy Action 內部的 `actions/cache`，見 E115） |
| 判讀 | `ci.yml` 的 `Tests`、`Image scan` 都鎖 `ubuntu-24.04`，不受影響；CodeQL 預設設定的機器由 GitHub 管理，10/19 後看第一次結果；M4 新增的 workflow 一樣鎖 `ubuntu-24.04` |

### 定案（21:25，本人四題都選 A）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | Terraform State 的鎖 | **只用 S3 本身的鎖檔（`use_lockfile = true`），不建 DynamoDB 鎖表** | 照決策書 5.1 另建 DynamoDB 鎖表：Terraform 官方文件已標示 DynamoDB 鎖為淘汰（deprecated），未來的小版本會移除 | 需要較新的 Terraform；修訂決策書 5.1 與 PART 9 |
| 2 | 拆幾層 | **兩層：長期層**（State bucket、GitHub OIDC、ECR、DynamoDB 四張表）平常不拆；**每日層**（VPC、子網、安全群組、Gateway Endpoint、NAT、DNS 防火牆、ALB、ECS、告警）測完就 destroy，destroy workflow 只拆這層 | 全部一層、一鍵全拆：每次都要重建表、重跑種子腳本、所有 Key 換新 | 兩層分開 apply；長期層的東西要另外記得清（結案時） |
| 3 | M4 從哪裡執行 | **本人電腦**（`aws login`）跑 `terraform plan`／`apply`、`docker push`；GitHub OIDC 角色先只給 destroy workflow 用，CD 留到 M6（D20） | M4 就全部走 GitHub Actions：每次除錯都要推、等 CI，M4 會慢很多 | M4 期間部署是手動的 |
| 4 | ALB 開給誰 | **安全群組只放行本人的公開 IP**（Terraform 變數）；HTTP 80（7.8） | 開給全世界：誰掃到都能打 Gateway，灌日誌、吃 ALB 費用 | 換網路要改變數再 apply；公開 IP 屬 11.5 的遮蔽項目，變數值不進 repo |

**生活比喻（第 2 項）：** 搬家時，戶籍和存摺（State、表、映像）放在固定的保險箱；冷氣和保全（NAT、ALB、Fargate）按小時計費，出門就關。

### 施工順序（Claude 提出，本人同意）

| 段 | 內容 | 費用 |
|---|---|---|
| A | 長期層的地基：State bucket（加密、封鎖公開、版本控制）、GitHub OIDC 角色 | 幾乎免費 |
| B | 長期層的住戶：ECR、DynamoDB 四張表（隨需計費） | 閒置幾乎免費 |
| C | 每日層的骨架：VPC、公有子網 × 2 AZ、私有子網 × 1、安全群組、Gateway Endpoint（含 Endpoint Policy） | 免費 |
| D | 每日層會跳錶的：NAT（單 AZ）、DNS 防火牆（先告警後阻擋）、ALB、ECS Fargate | 約 US$2.8／天，測完當天 destroy |
| E | 驗收 S08～S11、錄影、destroy workflow 實測 | 同 D |

---

## E118. 長期層骨架（State bucket、ECR、三張表）與 CI 的 Trivy 設定掃描（2026-10-15 21:46～10-16 16:03）

**依據：** E117（兩層、施工順序 A、B 段）；決策書 3.2、3.6、5.1、D19、D62；E104、E110、E115（Trivy 升級與 PR #4）。

**範圍：** 只寫檔、`terraform init`／`validate`／`fmt`、推分支、跑 CI。**沒有登入 AWS、沒有 `plan`／`apply`**，AWS 上還沒有任何東西。

### 1. 工具版本（冷卻期：上架滿 3 天）

| 工具 | 版本 | 理由 |
|---|---|---|
| Terraform | **1.16.5**（10/2 發佈）；`required_version = "~> 1.16.5"` | 1.16.6 是 10/14 發佈，未過冷卻期。winget 安裝檔 SHA256 `01700102…38ef` 與 HashiCorp 官方 `terraform_1.16.5_SHA256SUMS` 一致（GPG 簽章沒驗） |
| AWS provider | **6.68.0**（10/7 發佈）；`version = "= 6.68.0"` | 6.69.0 是 10/14 發佈。查發佈頁時看到 6.57.0 曾因嚴重 bug 被下架，佐證冷卻期 |
| trivy-action | **v0.36.0**（`ed142fd…`，2026-04 發佈） | 與 Dependabot PR #4 相同；以 `git ls-remote` 確認 `refs/tags/v0.36.0^{}` = `ed142fd0673e97e23eac54620cfb913e5ce36c25` |
| Trivy | **v0.74.0**（2026-08-14 發佈），兩個掃描工作都明寫 | 不寫會用 action 內建的 v0.70.0；10/16 CI 提示 0.76.0 已出，未過冷卻期，不升 |

### 2. 長期層 `infra/persistent/` 的內容（Claude 給骨架、本人建檔）

| 檔 | 內容 |
|---|---|
| `versions.tf`、`providers.tf` | 版本如上；東京區；`default_tags`：`Project`、`Layer = persistent`、`ManagedBy = terraform`；不寫任何帳密 |
| `state_bucket.tf` | `bucket_prefix = "llm-gateway-tfstate-"`、`prevent_destroy`；封鎖公開四開關；版本控制；`AES256` 加密；bucket 政策 Deny 非 HTTPS（`aws:SecureTransport = false`，用 `data "aws_iam_policy_document"` 組），`depends_on` 封鎖公開 |
| `ecr.tf` | 倉庫 `llm-gateway`：`IMMUTABLE`、`scan_on_push`、`AES256`；生命週期：沒標籤 1 天後刪、全部最多留 10 個 |
| `dynamodb.tf` | `api_keys`（`key_hash`）、`quotas`（`user_id` + `period`）、`audit`（`request_id`）；表名對齊 `app/db.py`、主鍵對齊 `scripts/create_tables.py`；`PAY_PER_REQUEST`、`deletion_protection_enabled = true`、PITR 開啟 |
| `outputs.tf` | `tfstate_bucket`、`ecr_repository_url`、`dynamodb_table_arns`（三張表的 ARN 對照） |
| `.terraform.lock.hcl` | `init` 產生，16 組 `zh:` 平台指紋，進 Git |
| `.gitignore` | 加 `.terraform/`、`*.tfstate`、`*.tfstate.*`、`*.tfvars`、`crash.log`；**在第一次 apply 之前**加 |

**定案（Claude 提出、本人照做）：**

| # | 決定 | 定案 | 不選的選項與理由 |
|---|---|---|---|
| 1 | 雲端先建幾張表 | **三張**（`api_keys`、`quotas`、`audit`），`usage` 等 M5 的 Worker | 現在建四張：`usage` 的欄位 M5 才定。代價：Endpoint Policy 與 IAM 之後要補一張 |
| 2 | 表的防刪 | `deletion_protection_enabled`（AWS 層級，主控台與 CLI 也刪不掉） | 只用 `prevent_destroy`：只擋 Terraform，擋不住主控台 |
| 3 | 映像標籤 | `IMMUTABLE`，之後用 git commit 編號當標籤 | `MUTABLE` 加 `latest`：出事時查不到當時跑的是哪一份 |

### 3. 本機檢查

| 指令 | 結果 |
|---|---|
| `terraform init` | `Installed hashicorp/aws v6.68.0 (signed by HashiCorp)`；產生 `.terraform.lock.hcl` |
| `terraform validate`（bucket 時、加 ECR 與表後各一次） | `Success! The configuration is valid.` |
| `terraform fmt -check` | 加 ECR 與表後印出 `ecr.tf`（生命週期規則的等號沒對齊）；`terraform fmt` 自動修正後再檢查無輸出 |
| `git status`（init 後） | 只多出 `.terraform.lock.hcl`，`.terraform/` 有被擋 |

### 4. CI 加 Config scan（Trivy `config`）

**發現：** Claude 在試跑環境用 Trivy v0.74.0（內建規則）掃分支：HIGH 1 個 `AWS-0132`（State bucket 沒用自管 KMS 金鑰）；LOW 5 個（三張表與 ECR 沒用自管金鑰 `AWS-0025`×3、`AWS-0033`；bucket 沒開存取日誌 `AWS-0089`；Dockerfile 沒有 `HEALTHCHECK` `DS-0026`）。CI 只擋 HIGH、CRITICAL。

**定案（本人照建議選 B）：**

| 選項 | 做法 | 評估 |
|---|---|---|
| A | State bucket 改用自管 KMS 金鑰 | 每月約 US$1；所有讀寫帳本的角色都要多給 KMS 權限；金鑰刪除有 7～30 天等待期 |
| **B（採用）** | 刻意接受：`state_bucket.tf` 的加密資源上方加 `#trivy:ignore:AWS-0132:exp:2026-12-31`，上面兩行寫理由 | 帳本沒有密碼；存取由 IAM 與 HTTPS-only 政策管住；理由與程式碼放一起；**到期日過了豁免自動失效** |
| C | CI 只擋 CRITICAL | 為了過關降低門檻 |

- 試跑環境實測：加註解 → HIGH 0 個；把到期日改成過去 → `AWS-0132` 又出現、Trivy 失敗。`#` 後面不能有空格、要緊貼 `resource` 那行
- 不另開 `.trivyignore`：理由跟程式碼放在一起，改到這段的人一定看得到

**`ci.yml` 的修改：** `Image scan` 的 trivy-action 換成 v0.36.0、Trivy 升到 v0.74.0；新增工作 `config-scan`（名稱 `Config scan`，`scan-type: config`、`scan-ref: .`、HIGH／CRITICAL、`exit-code: "1"`）。Claude 以 YAML 解析確認三個工作都在。

### 5. CI 結果（草稿 PR #7）

| 檢查 | 結果 |
|---|---|
| `ci / Config scan` | ✅ 19 秒；log 的表列出 `Dockerfile`、`infra/persistent`、`dynamodb.tf`、`ecr.tf`、`state_bucket.tf`，全部 0（真的掃到檔案，不是空掃）；CI 下載了最新規則包（234.57 KiB） |
| `ci / Image scan` | ✅ 50 秒；**Summary 沒有 Annotations**：PR #3 起一直出現的 Node.js 20 警告（`actions/cache@0400d5f…`）消失，E115 的推定成立 |
| `ci / Tests` | ✅ 25 秒 |
| CodeQL ×3 | ✅ |

### 6. 破壞實驗：拿掉豁免（草稿 PR #8，分支 `ci-break-test-trivy`，`c4f689b`）

只刪 `#trivy:ignore:AWS-0132:exp:2026-12-31` 一行（兩行中文註解留著）：

| 檢查 | 結果 |
|---|---|
| `ci / Config scan` | ❌ 20 秒：`state_bucket.tf` 1 個，`AWS-0132 (HIGH): Bucket does not encrypt data with a customer managed key.`、`infra/persistent/state_bucket.tf:33-40`、`Error: Process completed with exit code 1` |
| 其他 5 個 | ✅ |

- 行號 33-40（試跑環境是 30-37）：兩行註解把資源往下推了 3 行，對得上
- CI 用最新規則包仍只抓到這一個 HIGH，與試跑環境（內建規則）一致
- **所以證明了：** 豁免靠的就是那一行，拿掉就擋；Config scan 會擋
- 收尾：PR #8 關閉（未合併），本機與 GitHub 上的 `ci-break-test-trivy` 刪除

### 7. `protect-main` 加第三個必要檢查（本人截圖）

- Rulesets → `protect-main` → Required status checks 加 `Config scan`（來源 GitHub Actions）→ **Ruleset updated**
- 必要檢查變成 `Tests`、`Image scan`、`Config scan`；PR #7 的 `ci / Config scan` 旁出現 **Required**

### 8. 分支整理

- GitHub 上刪除已合併的 `feat/audit-table`、`fix/openai-timeout-60s`（PR #5、#6 合併後沒刪）
- Dependabot 的 PR #4 保留：PR #7 合併後應會自動關閉（未驗證）

### 限制（誠實記錄）

- **全部沒有上雲：** `plan` 預期 `10 to add`（bucket 5、ECR 2、表 3），要 `aws login` 後才知道；表名、ECR 名稱有沒有撞到既有資源、權限夠不夠都還不知道
- 豁免 `AWS-0132` 是接受風險，不是解決：State bucket 沒有「誰能用金鑰」這一層；12/31 到期要重新檢討
- LOW 的 5 個沒有處理，CI 也不擋
- `trivy config .` 掃整個 repo：之後若有範例或實驗用的設定檔（例如 `scripts/litellm-lab/`）被抓到，要決定排除還是修
- Config scan 擋得住「寫錯的設定」，擋不住「設定沒錯、但用法錯」（例如政策給太多權限但符合規則）；IAM 的最小權限要人審
- Terraform 安裝檔的 GPG 簽章沒驗；provider 的簽章由 `init` 自動驗（`signed by HashiCorp`）

### 面試可用的說法

- 「Terraform 的 State 我放在 S3：封鎖公開、版本控制、加密、只准 HTTPS，加上 prevent_destroy。資料表用的是 AWS 自己的刪除保護，因為 prevent_destroy 只擋 Terraform，擋不住有人在主控台按刪除。」
- 「CI 加了 Trivy 掃 Terraform，第一次就抓到 State bucket 沒用自管 KMS 金鑰。我評估後選擇接受：帳本裡沒有密碼，存取已經由 IAM 和只准 HTTPS 的政策管住，自管金鑰要多付錢、所有角色都要多一組權限。我把理由寫在那一行旁邊，還設了到期日，過期 CI 會自己變紅、逼我重新檢討。」
- 「我做了破壞實驗：把豁免拿掉開一個測試 PR，Config scan 20 秒內就紅了，其他檢查照樣綠，證明它真的會擋。之後才把它加進 main 的必要檢查。」
- 「綠燈我也會打開 log 看一次，確認它真的掃到我的檔案，不是掃了一個空資料夾。」

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `7a9ca6f` | 10/16 02:08 | `feat: add the Terraform state bucket skeleton for the persistent layer` |
| `a0f714b` | 10/16 12:05 前後 | `chore: lock the AWS provider for the persistent layer` |
| `8aad4de` | 10/16 15:3x | `feat: add the ECR repository and DynamoDB tables to the persistent layer` |
| `11d5925` | 10/16 15:4x | `ci: add a Trivy config scan and upgrade Trivy to v0.74.0` |
| （草稿 PR #7） | 10/16 15:4x | 分支 `feat/m4-persistent-layer`；apply、帳本搬進 S3 之後才轉正式 PR |

---

## E119. 長期層上雲：apply、帳本搬進 S3、卡鎖與解鎖、兩個防刪的破壞實驗（2026-10-17 09:39～10:24）

**依據：** E117（兩層、State 鎖用 `use_lockfile`）、E118（長期層骨架、`plan` 預期 10 個）；決策書 5.1、3.2、3.6。

**目的：** 把長期層真的建在 AWS 上；帳本（State）從本機搬進自己建的 bucket；證明鎖、`prevent_destroy`、DynamoDB 刪除保護都會擋。

### 1. 登入方式

- Terraform 1.16.5 加 AWS provider 6.68.0 直接讀 `aws login` 的快取，不用另外匯出憑證（Terraform 1.15 起支援，查證來源：[Classmethod 實測](https://dev.classmethod.jp/articles/terraform-s3-backend-aws-login/)；1.14 會 `No valid credential sources found`）
- 先 `Get-ChildItem Env:AWS_*` 確認沒有 E113 那次留下的環境變數（環境變數比登入狀態優先，而且會過期）

### 2. plan 與 apply

| 步驟 | 結果 |
|---|---|
| `terraform init`（這台第一次） | 照鎖檔下載 `hashicorp/aws v6.68.0`，沒有新建鎖檔 |
| `terraform plan` | 剛好 10 個 `will be created`；`Plan: 10 to add, 0 to change, 0 to destroy.`，與 E118 的預測一致 |
| 費用說明（apply 前） | bucket、三張表（隨需）、PITR、空的 ECR 閒置合計每月不到 US$0.01；會跳錶的 NAT、ALB、Fargate 都在每日層 |
| `terraform apply` → `yes` | `Apply complete! Resources: 10 added, 0 changed, 0 destroyed.` |
| outputs | `tfstate_bucket = "llm-gateway-tfstate-629ceebfae70aa842b70303422"`；`ecr_repository_url = "<account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/llm-gateway"`；三張表的 ARN（`arn:aws:dynamodb:ap-northeast-1:<account-id>:table/...`） |
| 本機帳本 | `terraform.tfstate` 21,692 bytes；`git status` 仍是 `working tree clean`（`.gitignore` 擋住了） |

### 3. 帳本搬進 S3

`infra/persistent/backend.tf`：`backend "s3"`，`bucket` = 上面的名字（直接寫進 repo：名字裡沒有帳號 ID；bucket 已封鎖公開、只准 HTTPS；之後 destroy workflow 也要知道去哪讀）、`key = "persistent/terraform.tfstate"`、`region`、`encrypt = true`、`use_lockfile = true`。

| 步驟 | 結果 |
|---|---|
| `terraform init -migrate-state` → `yes` | `Successfully configured the backend "s3"!` |
| `aws s3 ls s3://<bucket>/persistent/` | `terraform.tfstate` 21,691 bytes（10:05:36） |
| `terraform state list` | 10 個資源加 1 個 `data`（試算單，不是資源） |
| `terraform plan` | `No changes. Your infrastructure matches the configuration.` |
| 本機剩下的 | `terraform.tfstate` 0 bytes（搬家後被清空）、`terraform.tfstate.backup` 21,692 bytes（搬家前的副本，有帳號 ID 與 ARN）→ 兩個都刪；刪後（解鎖後）`plan` 仍 `No changes`，證明帳本是從 S3 讀的 |

**一個小錯（Claude 的範例）：** 範例寫「`llm-gateway-tfstate-貼上第5步的名字`」，而印出的名字本身已含前綴，照字面貼成 `llm-gateway-tfstate-llm-gateway-tfstate-629ce…`，`aws s3 ls` 得到 `NoSuchBucket`。`backend.tf` 本人寫對（前綴一次），重打指令後正常。

### 4. 卡鎖與解鎖（意外，但剛好證明鎖有效）

| 時間（台北） | 發生的事 |
|---|---|
| 10:12:58 | 一次 `plan` 開始，在 S3 放了鎖檔 `terraform.tfstate.tflock`（263 bytes），之後沒有正常跑完（什麼都沒印），鎖沒收回 |
| 之後兩次 `plan` | `Error: Error acquiring the state lock`；`S3: PutObject … StatusCode: 412 … PreconditionFailed: At least one of the pre-conditions you specified did not hold`；Lock Info：`Operation: OperationTypePlan`、`Who: <user>@<host>`、`Version: 1.16.5`、`Created: 2026-10-17 02:12:59 UTC` |
| 解鎖前檢查 | `Get-Process terraform` 無輸出（沒有背景程序）；`aws s3 ls` 看到 `terraform.tfstate.tflock` |
| `terraform force-unlock 8ae18006-…` → `yes` | `Terraform state has been successfully unlocked!`；`.tflock` 消失；`plan` 恢復 `No changes` |

**判讀：**
- **`412` 就是鎖：** Terraform 寫鎖檔時用「只有不存在才寫入」的條件；檔已存在，S3 拒絕。這就是不需要 DynamoDB 鎖表也能鎖的原理（E117 定案 1）
- **中斷的操作會留下鎖**，要 `force-unlock` 收拾；收拾前要確認鎖的主人、沒有程序在跑。之後有 GitHub Actions 碰帳本時，還要先確認 Actions 沒有工作在跑
- 那次 `plan` 為什麼沒跑完，沒有查到原因（推定是中途被打斷）

### 5. 破壞實驗（本人執行，兩個）

| # | 做了什麼 | 結果 | 證明了 |
|---|---|---|---|
| 1 | `terraform destroy` | 先算出完整計畫 `Plan: 0 to add, 0 to change, 10 to destroy.`，接著 `Error: Instance cannot be destroyed`、`on state_bucket.tf line 2`、`Resource aws_s3_bucket.tfstate has lifecycle.prevent_destroy set, but the plan calls for this resource to be destroyed.`；**沒有問 yes、10 個一個都沒拆**；事後 `aws s3 ls` 沒有殘留 `.tflock` | 只要計畫裡有一個受保護的資源，整份拆除計畫作廢 |
| 2 | 先 `describe-table --query "Table.DeletionProtectionEnabled"` → `true`；再 `aws dynamodb delete-table --table-name audit` | `An error occurred (ValidationException) when calling the DeleteTable operation: Resource cannot be deleted as it is currently protected against deletion. Disable deletion protection first.` | 刪除保護是 AWS 層級的，連 CLI 都擋；`prevent_destroy` 只擋 Terraform（E118 定案 2） |

**順帶看到的（destroy 的計畫印出了每個資源的完整屬性）：**
- PITR：`recovery_period_in_days = 35`
- State bucket 的加密設定多了 `blocked_encryption_types = ["SSE-C"]`：AWS 對新 bucket 的預設（禁止用戶自帶金鑰加密），不是我們寫的
- **計畫輸出裡的 ARN、ECR 網址都有完整帳號 ID**：存日誌或截圖時要遮

### 限制（誠實記錄）

- `prevent_destroy` 只要有人把那一行刪掉再 apply 就失效；刪除保護有 `dynamodb:UpdateTable` 權限的人可以先關掉再刪。兩者擋的是「手滑」，不是「有權限的惡意」
- bucket 名字寫在公開 repo：知道名字也進不去，但等於公開了它存在
- 卡鎖那次沒查到原因；`force-unlock` 是手動判斷，判斷錯（別人真的在跑）會讓兩個操作同時寫帳本
- 還沒有 OIDC 角色，destroy workflow 還不存在；長期層之後若要改，目前只有本人電腦能 apply
- 沒有用 CloudTrail 確認 apply 呼叫了哪些 API

### 面試可用的說法

- 「Terraform 的帳本先放本機建出 S3 bucket，再用 init -migrate-state 搬進去。.gitignore 在 apply 之前就擋好 tfstate，帳本在本機那幾分鐘 git status 是乾淨的。」
- 「State 鎖我用 S3 的條件寫入，不用 DynamoDB。我真的遇過一次中斷的 plan 留下鎖，下一個 plan 被 412 擋下。我先確認鎖是我自己留的、沒有程序在跑，才 force-unlock。」
- 「我做了兩個防刪實驗：terraform destroy 會先算出拆 10 個，但因為 State bucket 有 prevent_destroy，整份計畫作廢、一個都沒拆；用 AWS CLI 直接刪表，被 DynamoDB 的刪除保護擋下。前者只擋 Terraform，後者連主控台都擋。」

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `23e190b` | 10/17 10:2x | `feat: store the persistent layer state in the S3 bucket`（`11d5925..23e190b`） |
| `763634e` | 10/17 10:3x | `docs: record the persistent layer, the config scan and the first apply`（本筆與 E117、E118） |
| `92b7aa4` | 10/17 10:40 | `Merge pull request #7 from Poyu-Tu/feat/m4-persistent-layer`（`8e2ce32..92b7aa4`；6 個檢查全綠） |

---

## E120. A 段後半：GitHub OIDC 與 destroy 角色（定案、`sub` 新格式、apply、權限模擬器、GitHub 端驗證）（2026-10-17 11:02～16:12）

**依據：** E117（OIDC 角色先只給 destroy workflow；施工順序 A～E）、E119；決策書 4.2（CI/CD 層）、5.1、6.4、D20；11.4 的 S11。

**生活比喻：** 拆除組要進工地收東西，不發他萬用鑰匙。他每次到門口出示「拆除組、從正門進來」的工作證（GitHub 開的身分證明），警衛核對後給一張一小時的臨時通行證（AWS 的臨時憑證），通行證上寫明哪些房間能進、哪些房間（長期層）絕對不准進。

### 定案（本人：設計題 AAA，10/17 11:02；追加兩題「11」，14:21）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | 誰能借 destroy 角色 | **A：GitHub environment `destroy`**；environment 只准 `main`；`sub` 與 `aud`（`sts.amazonaws.com`）都用完全相等比對；不設審核人（拆是省錢的動作，不該卡住） | B：只限 `main` 分支（`sub` 結尾 `ref:refs/heads/main`）：`main` 上任何 workflow 的任何工作都借得到，包括 CI | 掛了 environment 之後，證明上**只寫 environment、不寫分支**，「只准 `main`」完全靠 GitHub 的 environment 設定，那個設定不在 repo 裡、沒有版本紀錄；能在 `main` 手動觸發的人就能拆 |
| 2 | 權限怎麼給 | **A：分批長出來。** 這次只建 OIDC 提供者、角色、讀寫每日層帳本；刪除權限跟每日層一起寫（標籤條件只准刪 `Layer=daily`）。帳本只開兩個檔：`daily/terraform.tfstate` 與 `daily/terraform.tfstate.tflock`（比交接寫的 `daily/*` 更窄） | B：現在照文件猜一整份刪除權限：猜錯的要到每日層才知道，猜多了就是多給 | 每加一批刪除權限都要 apply 一次長期層 |
| 3 | destroy workflow 第一次實測 | **A：C 段（免費的 VPC、子網、安全群組、Gateway Endpoint）建好就實測**，驗過才開 D 段會跳錶的東西 | B：照原順序到 E 段：第一次拆就是在跳錶的時候 | — |
| 4 | 追加：先做一支只驗身分的 workflow | **要。** 手動觸發、掛 environment `destroy`；向 GitHub 要一張證明，**只印 `sub`、`aud` 等欄位，不印證明本身**；再用 AWS CLI 借一次角色、跑 `aws sts get-caller-identity`；不用第三方 Action | 不做：C 段第一次 destroy 失敗時，「`sub` 寫錯」和「刪除權限不夠」兩種原因混在一起 | 多一個 workflow 檔 |
| 5 | 追加：明文 Deny 什麼時候寫 | **這次就寫**：護欄比權限先到，之後每加一條允許都已經有 Deny 墊著；用 AWS 的權限模擬器就能驗證，不用真的刪東西 | 等刪除權限一起寫 | Deny 只擋列出來的動作；漏列的靠「沒給就沒有」（目前除了帳本兩個檔，什麼都沒給） |

### 發現：GitHub 2026/7/15 之後建立的 repo，`sub` 改成「名字@編號」的新格式

- **官方文件（Claude 查證）：** 7/15 之後建立的 repo，`sub` 改為 `repo:OWNER@OWNER-ID/REPO@REPO-ID:...`；之前建立的維持舊格式（可自行改用新格式）。理由：舊格式只有名字，帳號或 repo 名稱被別人重新註冊後，對方可以做出一模一樣的 `sub`。來源：[GitHub Docs〈OpenID Connect reference〉](https://docs.github.com/en/actions/reference/security/oidc)
- **本 repo（本人以瀏覽器查 `https://api.github.com/repos/Poyu-Tu/llm-gateway`）：** `created_at` `2026-09-29T07:32:30Z` → 新格式；repo 編號 `1394630828`、帳號編號 `62129723`（公開資訊，寫進 Terraform）
- **交接檔原本寫的 `repo:Poyu-Tu/llm-gateway:environment:destroy` 是舊格式：** 照寫的話角色永遠借不到，錯誤只會是「沒有權限」，很難查
- **推定的新寫法：** `repo:Poyu-Tu@62129723/llm-gateway@1394630828:environment:destroy`。官方只示範了分支的新格式，**environment 的新格式是照推的、未證實**，由定案 4 的 workflow 實際印出來確認

**生活比喻：** 門禁卡以前只印「公司名／部門名」，公司倒了、別人註冊同名公司，就能做出一樣的卡；現在卡上加印統一編號。警衛的名單要照新卡的樣子寫。

### 開工前檢查（本人執行）

| 指令 | 結果 | 證明了 |
|---|---|---|
| `Get-ChildItem Env:AWS_*` | 無輸出 | 沒有會過期的舊憑證蓋過 `aws login` |
| `aws login` | `Updated profile default to use arn:aws:iam::<account-id>:user/terry-admin credentials.` | 已登入 |
| `aws iam list-open-id-connect-providers` | `"OpenIDConnectProviderList": []` | 帳號裡沒有 GitHub 的 OIDC 提供者，apply 不會撞名（同一個網址一個帳號只能有一個） |

### 設計（`infra/persistent/github_oidc.tf`，Claude 給骨架；`outputs.tf` 加 `destroy_role_arn`）

| 資源 | 內容 |
|---|---|
| `aws_iam_openid_connect_provider.github` | `https://token.actions.githubusercontent.com`、`client_id_list = ["sts.amazonaws.com"]`；不寫 `thumbprint_list`（AWS 驗證 GitHub 的證明已改用自己信任的憑證機構） |
| `aws_iam_role.destroy` | 名稱 `llm-gateway-destroy`；信任政策只有一條 `sts:AssumeRoleWithWebIdentity`，條件 `aud`、`sub` 都是 `StringEquals`；一次最多 1 小時 |
| `aws_iam_role_policy.destroy`（inline） | 允許 3 條：`s3:ListBucket`（bucket，不加前綴條件）、每日層帳本 `GetObject`／`PutObject`、鎖檔 `GetObject`／`PutObject`／`DeleteObject`。明文 Deny 6 條：三張表（刪表、`UpdateTable`、關 PITR、寫資料）、帳本 bucket 的設定、`persistent/` 帳本與鎖檔（寫、刪、刪舊版本）、ECR（刪倉庫、刪映像、改政策與生命週期、改標籤可覆蓋）、角色自己（改權限、改信任、刪除）、OIDC 提供者 |

- 政策裡**沒有任何萬用字元**（`*`）：Claude 以 HCL 解析器逐條檢查
- 帳本權限照 Terraform 官方文件：帳本本身要讀寫、不需要刪；鎖檔要讀、寫、刪。來源：[Terraform Docs〈S3 backend〉](https://developer.hashicorp.com/terraform/language/backend/s3)
- `ListBucket` 不加前綴條件：只會看到 bucket 裡的檔名（`persistent/…`、`daily/…`），不是秘密；前綴寫錯的話 `terraform init` 會失敗，而那要到 GitHub Actions 上才看得到
- 角色的 ARN 含帳號 ID：放進 GitHub 的 **repository secret** `AWS_DESTROY_ROLE_ARN`（不是 variable），GitHub 會在公開的 log 裡遮掉。原本想放 environment `destroy` 的 secret，改成 repository secret 的理由見下方「施工」第 4 節

### 限制（目前為止）

- **Claude 的試跑環境裝不了 Terraform**（HashiCorp 的下載站不在允許清單），骨架只用 HCL 解析器檢查語法與萬用字元；`fmt`、`validate`、`plan` 以本人電腦為準
- environment 的新 `sub` 格式未證實（見上）
- 信任條件只認 `sub` 與 `aud`；`sub` 裡已有 repo 與帳號編號，所以名稱被重新註冊的風險已由新格式處理

### 施工（本人執行，個人電腦，10/17 14:30～15:21）

**1. 分支與檢查**

| 指令 | 結果 |
|---|---|
| `git switch -c feat/m4-github-oidc`（`main` 已是最新） | 新分支 |
| `git status` | `modified` 兩個（`outputs.tf`、`m4-evidence-log.md`）、`Untracked` 一個（`github_oidc.tf`） |
| `terraform fmt -check` | 無輸出 |
| `terraform validate` | `Success! The configuration is valid.`：不寫 `thumbprint_list` 也通過，計畫中顯示 `(known after apply)`（由 AWS 補上） |

**2. plan 與 apply**

| 步驟 | 結果 |
|---|---|
| `terraform plan` | `Plan: 3 to add, 0 to change, 0 to destroy.`；既有 10 個只有 `Refreshing state`，沒有任何變動 |
| 計畫裡的信任政策 | `"token.actions.githubusercontent.com:sub"` = `repo:Poyu-Tu@62129723/llm-gateway@1394630828:environment:destroy`、`aud` = `sts.amazonaws.com`，兩個都是 `StringEquals` |
| 兩份政策 `will be read during apply` | 政策裡要填角色與 OIDC 提供者的 ARN，要等那兩個建好才知道，所以 Terraform 在 apply 中途才組政策 |
| `terraform apply` → `yes`（答之前確認重印的計畫仍是 `3 to add`） | 順序：OIDC 提供者（2 秒）→ 組信任政策 → 角色（1 秒）→ 組權限政策 → 角色上的權限；`Apply complete! Resources: 3 added, 0 changed, 0 destroyed.` |
| outputs | `destroy_role_arn = "arn:aws:iam::<account-id>:role/llm-gateway-destroy"` |

- 沒有用 `plan -out` 存計畫檔：計畫檔含帳本內容，而 `.gitignore` 沒有擋 `*.tfplan`；`apply` 本身會重算一次計畫並等 `yes`
- 費用：三個都是 IAM，免費

**3. 權限模擬器（`aws iam simulate-principal-policy`，只用角色身上的政策計算，不真的借角色、不真的刪東西）**

| # | 問題 | 結果 | 證明了 |
|---|---|---|---|
| 1 | `s3:PutObject` `daily/terraform.tfstate` | `allowed` | 寫得了每日層帳本 |
| 2 | `s3:PutObject` `persistent/terraform.tfstate` | `explicitDeny` | 長期層帳本被明文 Deny 擋 |
| 3 | `dynamodb:DeleteTable` `audit` 表 | `explicitDeny` | 刪 `audit` 表被明文 Deny 擋 |
| 4 | `s3:PutObject` `daily/other.tfstate` | `implicitDeny` | 只開了那兩個檔，旁邊的檔不行 |
| 5 | `s3:GetObject` `persistent/terraform.tfstate` | `implicitDeny` | 長期層帳本連讀都沒給 |

- 5 個都與 Claude 事先寫的預期相同
- **`implicitDeny` 與 `explicitDeny` 的差別：** 前者是「沒給」，之後加一條允許就會變成可以；後者是「明文禁止」，之後不管加什麼允許都照樣擋（IAM 的規則：Deny 一定贏過 Allow）
- **意外發現（打錯字）：** 第 3 題第一次打成 `sim dynamodb:Delete $audit`，結果是 `implicitDeny`，**沒有報錯**。模擬器不檢查動作名稱存不存在，不存在的動作只會得到「沒給」。反過來說：**Deny 清單裡若把動作名稱打錯，Terraform 與 AWS 都不會報錯，那一條就默默失效。** 所以 Deny 寫完一定要用模擬器逐一問一次「該擋的有沒有擋」，不能只看政策長得對不對

**生活比喻（打錯字那題）：** 問警衛「拆除組能不能進『刪』這間？」大樓根本沒有叫「刪」的房間，警衛也不會說「沒這間」，只會說「你的名單上沒有」。黑名單上的房間名寫錯，也是一樣：警衛照名單擋，名單上那間不存在，真正的房間就沒擋到。

**4. 角色 ARN 放 repository secret，不放 environment secret（Claude 修正設計）**

- 只驗身分的 workflow 要有一個「沒掛 environment」的工作，用來證明它借不到角色。environment 的 secret **只有掛了那個 environment 的工作讀得到**；放在 environment 裡，沒掛的工作拿到的是空字串，被拒的原因會變成「參數不對」，而不是「信任條件對不上」，證明不了想證明的事
- ARN 不是密碼，知道它也借不到角色（要通過信任條件）；放 secret 只是為了讓公開的 log 不露出帳號 ID

**5. GitHub 端設定（本人在主控台操作，15:30～15:45）**

| 設定 | 內容 | 截圖 |
|---|---|---|
| environment `destroy` | Required reviewers、Wait timer 不勾；Deployment branches and tags 改 **Selected branches and tags**，規則 `main`（`1 branch and 0 tags allowed`） | `m4-oidc-env-branch-rule.png` |
| 取消管理員略過 | `Allow administrators to bypass configured protection rules` 預設是勾的，**取消勾**（`Environment "destroy" updated.`） | `m4-oidc-env-no-admin-bypass.png` |
| repository secret | `AWS_DESTROY_ROLE_ARN`（Environment secrets 維持空的） | — |

**定案 6（15:45，Claude 提出、本人照做）：取消管理員略過。** 這個 repo 會按「Run workflow」的只有本人，而本人就是管理員；勾著的話，管理員可能可以繞過這個 environment 的保護規則。它會不會連「只准 `main`」也繞過，GitHub 文件寫得不夠清楚，所以不猜、直接關掉：沒有審核人與等待時間，關掉不會卡到任何事。實測結果見第 7 節。

**生活比喻：** 門口貼「只有走正門的人能領拆除證」，旁邊又貼「店長不用管上面那條」。店裡唯一會去領證的就是店長，第一條等於沒貼。

**6. PR #9 與從 `main` 執行 `oidc-check`**

| 項目 | 結果 |
|---|---|
| PR #9（`be59adf`、`c9c3b6c`、`1cd5f15`） | 6 個檢查全綠：`Config scan` 11 秒（第一次掃到 IAM 政策，沒有 HIGH）、`Image scan` 46 秒、`Tests` 27 秒、CodeQL ×3；按 Merge pull request → `e08f48e`；本機 `92b7aa4..e08f48e`、刪分支 |
| Dependabot PR #4 | `git fetch --prune` 顯示 `[deleted] origin/dependabot/github_actions/aquasecurity/trivy-action-0.36.0`：Dependabot 已自行關閉（PR #7 已含同樣的升級） |

`oidc-check #1`（從 `main` 手動觸發；截圖 `m4-oidc-check-claims-with-env.png`、`m4-oidc-check-assumed-role.png`、`m4-oidc-check-denied-without-env.png`）：

| 工作 | 印出的 `sub` | `environment` | 結果 |
|---|---|---|---|
| `Assume the destroy role (environment destroy)` | `repo:Poyu-Tu@62129723/llm-gateway@1394630828:environment:destroy` | `destroy` | ✅ 7 秒；借到 `arn:aws:sts::<account-id>:assumed-role/llm-gateway-destroy/oidc-check-39015190287` |
| `Try the destroy role without the environment (must be denied)` | `repo:Poyu-Tu@62129723/llm-gateway@1394630828:ref:refs/heads/main` | `None` | ✅ 9 秒；`An error occurred (AccessDenied) when calling the AssumeRoleWithWebIdentity operation: Not authorized to perform sts:AssumeRoleWithWebIdentity`、`Denied as expected` |

- 兩個工作的 `aud` 都是 `sts.amazonaws.com`；`repository_id` `1394630828`、`repository_owner_id` `62129723`，與瀏覽器查到的一致
- **新格式的推定成立：** environment 的 `sub` 就是 `名字@編號` 加 `:environment:destroy`，信任政策第一次就對
- **兩個工作的唯一差別是有沒有掛 environment：** 同一個 repo、同一個 `main`、同一次執行，`sub` 的結尾因此不同，AWS 只認 `environment:destroy` 那一張
- 帳號 ID 的遮罩有效：公開 log 裡只看得到 `<account-id>`

**7. 破壞實驗：從別的分支執行（16:00 前後）**

`git switch -c test/oidc-from-branch`、推上 GitHub（內容與 `main` 相同，`e08f48e`），Actions 選這個分支執行 `oidc-check #2`（截圖 `m4-oidc-check-branch-blocked.png`）：

| 工作 | 結果 |
|---|---|
| `Assume the destroy role (environment destroy)` | ❌ 2 秒，**一個步驟都沒跑**：`Branch "test/oidc-from-branch" is not allowed to deploy to destroy due to environment protection rules.` |
| `Try the destroy role without the environment (must be denied)` | ✅ 6 秒（沒掛 environment，不受這條規則管，照樣被 AWS 拒絕） |

- **所以證明了：** 「只准 `main`」在 GitHub 這一層就擋下，工作根本沒開始、拿不到身分證明，更碰不到 AWS；取消管理員略過之後，管理員本人從分支觸發也被擋
- 收尾：本機 `git branch -D`、GitHub `git push origin --delete test/oidc-from-branch`

**生活比喻：** 拆除組的人從後門進來，櫃台連工作證都不發給他，警衛那關根本不用出場。

### 證明了什麼（E120 全部）

| 想擋的情況 | 誰擋 | 證據 |
|---|---|---|
| 沒掛 environment 的工作（CI、別的 workflow）借角色 | AWS 的信任條件（`sub` 對不上） | `oidc-check #1` 第二個工作的 `AccessDenied` |
| 從 `main` 以外的分支掛 environment 借角色 | GitHub environment 的分支規則 | `oidc-check #2` 的 `not allowed to deploy` |
| 借到角色後碰長期層 | 角色上的明文 Deny | 權限模擬器 `explicitDeny`（第 3 節） |
| 借到角色後碰沒給的東西 | 沒給就沒有 | 權限模擬器 `implicitDeny` |

### 限制（誠實記錄）

- **信任條件與環境規則分屬兩個系統：** AWS 只看得到 `sub`，「只准 `main`」在 GitHub 的設定裡，不在 repo、沒有版本紀錄；有人把 environment 的分支規則刪掉，AWS 端不會知道
- 有 repo 管理權限的人可以改 environment、改 workflow，等於能拆每日層；個人專題只有本人一個管理員
- 權限模擬器只算角色身上的政策，不含 bucket 政策（只准 HTTPS 那條）；真的寫帳本要等 C 段的 destroy workflow
- 刪除權限還沒有給，「借到角色就能拆每日層」要到 C 段才成立
- `oidc-check.yml` 的 environment 新格式只在 `main` 驗過；`pull_request` 等其他觸發方式的 `sub` 沒有看
- 截圖由 Claude 遮蔽：裁掉最上方一列（頭像）、執行摘要的頭像改成灰色方塊

### 面試可用的說法

- 「destroy workflow 用 GitHub OIDC 借 AWS 的角色，repo 裡沒有任何長期金鑰。信任條件只認 environment destroy，environment 又只准 main。我做了兩個破壞實驗：沒掛 environment 的工作被 AWS 拒絕，從別的分支觸發則在 GitHub 那層就被擋，連身分證明都拿不到。」
- 「設定時我發現 GitHub 今年 7 月起，新 repo 的身分證明格式改成名字加編號，網路上大部分範例還是舊格式，照抄會永遠借不到。我先寫一支只印證明欄位、不印證明本身的 workflow，確認格式之後才去寫真的 destroy。」
- 「權限我分批給，這次只開帳本的兩個檔，但先把長期層的明文 Deny 寫好。我用 IAM 的權限模擬器逐一驗證，還意外發現打錯的動作名稱不會報錯，只會變成沒給，所以 Deny 寫完一定要用模擬器問一次。」
- 「GitHub environment 預設允許管理員略過保護規則，而這個 repo 唯一會觸發 workflow 的就是我這個管理員，所以我把它關掉，再從別的分支實測確認被擋。」

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `be59adf` | 10/17 15:4x | `feat: add the GitHub OIDC provider and the destroy role` |
| `c9c3b6c` | 10/17 15:4x | `ci: add a workflow that checks who can assume the destroy role` |
| `1cd5f15` | 10/17 15:4x | `docs: record the OIDC decisions, the apply and the policy simulator` |
| `e08f48e` | 10/17 15:5x | `Merge pull request #9 from Poyu-Tu/feat/m4-github-oidc`（`92b7aa4..e08f48e`；6 個檢查全綠） |
| `f0c2776` | 10/17 16:2x | `docs: record the GitHub side of the OIDC check`（本筆後半與 6 張截圖） |
| `8c36ed3` | 10/17 16:2x | `Merge pull request #10 from Poyu-Tu/docs/m4-oidc-results`（`e08f48e..8c36ed3`；6 個檢查全綠） |

---

## E121. C 段開工：每日層骨架與 destroy workflow 的六項定案；fmt、validate、plan（2026-10-17 18:37～10-18 11:47）

**依據：** E117（施工順序 C、兩層）、E120（定案 2 權限分批長、定案 3 C 段建好就實測 destroy）；決策書 3.5、4.1、5.1、7.1、D13、D16、D20；`m4-daily-layer-start-handoff.md` 第 4 節。

**生活比喻：** 這一段是蓋圍牆、隔間、門禁，再鋪兩條通往倉庫的專用走廊，但還不接水電。按小時計費的 NAT、ALB、Fargate 留到 D 段。蓋好就先請拆除組來拆一次：免費的東西拆壞了不心疼，等於把 D 段跳錶時才會遇到的錯誤先撞出來。

### 開工前檢查

| 項目 | 結果 |
|---|---|
| 本機同步 | `git pull` → `e08f48e..8c36ed3`（PR #10：E120 後半與 6 張截圖）；`git branch -d docs/m4-oidc-results`（`was f0c2776`）；`git push origin --delete docs/m4-oidc-results` → `[deleted]` |

### 定案（本人逐題作答，18:39～18:49）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | 每日層怎麼拿長期層的資料（表的 ARN） | **C：表名寫死，帳號 ID 用 `aws_caller_identity` 問出來** | A `terraform_remote_state`：destroy 角色要能讀整份長期層帳本（E120 模擬器驗過是 `implicitDeny` 的門）；B data source：角色要多開三張表的 `DescribeTable`。**每日層讀什麼，destroy 拆之前也要讀什麼**，多讀一處就多一項權限 | 表改名要改三處（長期層、每日層、`app/db.py`），Terraform 不會提醒 |
| 2 | destroy 角色的讀取權限 | **A：逐一列出 `Describe` 動作（先列 11 個）**；`Resource` 依 AWS 規定寫 `"*"`（EC2 的 `Describe` 不支援指定資源） | B `ec2:Describe*`：一次就過，但動作欄有萬用字元（EC2 的 `Describe` 有上百個） | 列漏的要等第一次 destroy 失敗才知道；每補一次要 apply 長期層再重跑，一輪約 5 分鐘。C 段免費，這正是定案在這裡實測的理由 |
| 3 | destroy workflow 怎麼裝 Terraform | **B：curl 下載官方 zip，比對寫死的 SHA256**（`terraform_1.16.5_linux_amd64.zip` = `2bc2fcff…a9b2a49a3294b9e49eaab5e4`，本人從官方 `SHA256SUMS` 取得） | A `hashicorp/setup-terraform`：多信任一個外部 Action，每次更新都要再審 | 指紋第一次是從官網抄的，抄的那一刻官網若已被入侵就擋不住（選 A 也擋不住）；升級時版本、指紋、`versions.tf` 三處一起改 |
| 4 | destroy workflow 怎麼借角色 | **C：只把身分證明存成檔案，設 `AWS_ROLE_ARN`、`AWS_WEB_IDENTITY_TOKEN_FILE`，讓 Terraform 自己換臨時憑證**（Terraform 官方 S3 backend 文件寫明支援這兩個環境變數） | A `aws-actions/configure-aws-credentials`：多信任一個外部 Action；B 沿用 `oidc-check.yml` 的 CLI 寫法再把三個值寫進環境變數：三個值都要自己遮，漏一行就進公開 log | 換憑證失敗時錯誤藏在 Terraform 的輸出裡，比 CLI 難讀；證明約 5 分鐘過期，所以每個 Terraform 指令前重新要一張（見設計） |
| 5 | 網際網路閘道放哪一段 | **A：C 段**（免費） | B D 段：C 段的公有子網暫時名不副實；「卸大門」要到跳錶時才第一次驗 | C 段多 3 個資源；公有子網接了大門，但裡面什麼都沒放、也不自動發公開 IP |
| 6 | destroy 時，`admin_cidr`（本人 IP）怎麼給值 | **A：workflow 填 RFC 5737 文件專用位址 `192.0.2.1/32`**；變數加檢查，只收 `/32` 單一位址（`0.0.0.0/0` 被擋） | B 存成 GitHub secret：個人 IP 多存一處、換網路要改兩處；C `alb` 安全群組留 D 段：只是把問題往後延 | workflow 裡出現假位址，要靠註解說明（拆除只照帳本拆，不會用到這個值） |

### 設計（Claude 給骨架）

**`infra/daily/`（19 個資源，全部免費）**

| 檔案 | 內容 |
|---|---|
| `versions.tf`、`.terraform.lock.hcl` | 照抄長期層：Terraform `~> 1.16.5`、AWS provider `= 6.68.0` |
| `providers.tf` | 東京；`default_tags` 的 `Layer = "daily"`：destroy 角色的刪除權限只認這張標籤 |
| `backend.tf` | 同一個 bucket，`key = "daily/terraform.tfstate"`、`use_lockfile = true` |
| `variables.tf` | `admin_cidr`，檢查只收 `/32` |
| `network.tf` | VPC `10.0.0.0/16`（開 DNS 支援與主機名稱）；公有子網 `10.0.0.0/24`（1a）、`10.0.1.0/24`（1c），`map_public_ip_on_launch = false`；私有子網 `10.0.10.0/24`（1a，與 D 段的 NAT 同 AZ）；網際網路閘道、公有路由表（`0.0.0.0/0` → 閘道）、私有路由表（沒有對外的路，NAT 那條 D 段加） |
| `security_groups.tf` | `alb`：入 80 只准 `var.admin_cidr`，出 8000 只到 `gateway`；`gateway`：入 8000 只准從 `alb`，出 443 到 `0.0.0.0/0`。每條規則一個資源（兩個群組互相參照也不會繞圈） |
| `endpoints.tf` | S3：只准 `s3:GetObject` `prod-ap-northeast-1-starport-layer-bucket/*`（AWS ECR 文件的寫法）；DynamoDB：只准 `GetItem`、`PutItem`、`UpdateItem`，範圍限三張表（`app/` 只用這三種呼叫）；兩條都只接私有路由表 |

**Trivy：** `gateway` 的出口 `0.0.0.0/0:443` 是 AWS-0104（CRITICAL），以 `#trivy:ignore:AWS-0104:exp:2026-12-31` 刻意接受，理由寫在該行上方（OpenAI 的 IP 不固定，只能用網域管，網域由 DNS 防火牆管）。公有子網不自動發公開 IP，避開 AWS-0164（HIGH）。VPC Flow Logs（MEDIUM，不擋）這次不開，S08 的證據用 D 段的 DNS 查詢日誌。IAM 的萬用字元檢查 AWS-0057 已被 Trivy 標為淘汰，預設不跑（Claude 查 `trivy-checks` 原始碼）。

**`infra/persistent/github_oidc.tf`（destroy 角色第二批權限）**

- `DescribeDailyNetwork`：11 個 `Describe` 動作，`Resource "*"`
- `DeleteDailyNetwork`：11 個刪除動作（含 `DetachInternetGateway`、`RevokeSecurityGroupIngress`／`Egress`、`DeleteVpcEndpoints`）；資源限「本帳號、東京、7 種 EC2 資源」的 ARN（`vpc/*`、`subnet/*`……ID 每次 apply 都不同，所以種類後面是 `*`），再加條件 `aws:ResourceTag/Layer = daily`
- 刻意不給任何 `Create*`、`CreateTags`：不能蓋東西，也不能把別的東西改貼成 `daily` 再刪
- 帳號 ID 用 `aws_caller_identity`（長期層新增這個 data source，不是資源）
- 多一層保險：workflow 就算被改成指向 `infra/persistent/`，角色連長期層帳本都讀不到（E120 模擬器 `implicitDeny`），寫入有明文 Deny

**`.github/workflows/destroy.yml`**

| 項目 | 內容 |
|---|---|
| 觸發與權限 | `workflow_dispatch`；`permissions: {}`，工作上才開 `id-token: write`、`contents: read`；`environment: destroy`；`runs-on: ubuntu-24.04`；`timeout-minutes: 30` |
| `concurrency` | `destroy-daily`，`cancel-in-progress: false`：第二次排隊，不取消正在拆的（拆到一半被取消，帳本會留下鎖） |
| 裝 Terraform | curl 官方 zip → `sha256sum --check --strict` → 解壓到 `$RUNNER_TEMP/bin` |
| 遮帳號 ID | 從 secret 的角色 ARN 取第 5 段，`::add-mask::`：之後每個步驟、每一行都遮成 `***`（比 `oidc-check.yml` 的 `sed` 全面） |
| 拆 | `init` → `destroy -auto-approve -var=admin_cidr=192.0.2.1/32` → `state list` 必須是空的，有剩就失敗 |
| 證明過期 | GitHub 的證明約 5 分鐘過期，而 `init`、`destroy`、`state list` 是三個各自換憑證的程式，所以每個指令前都重新要一張；同一個程式內換到的臨時憑證可用 1 小時 |

### 施工（本人執行，個人電腦，10/18 11:13～11:47）

**工作方式改變（11:23）：** 本人開啟 Claude 桌面版的 Computer use，授權 VS Code、Windows PowerShell（只能看與點擊，不能打字）、Chrome（Claude in Chrome 擴充功能），以及 repo 資料夾的存取。之後本人打指令、Claude 自己截圖讀結果，不再複製貼上；按 Merge、Run workflow 等收不回來的動作，每次都先問本人。

| 步驟 | 指令 | 結果 |
|---|---|---|
| 1 | `git switch -c feat/m4-daily-network`；`Expand-Archive`（Claude 給的 zip） | `git status`：`modified` 兩個（證據紀錄、`github_oidc.tf`）、`Untracked` 兩個（`destroy.yml`、`infra/daily/`） |
| 2 | `terraform -chdir=infra/daily fmt -check`、`-chdir=infra/persistent fmt -check` | 兩層都無輸出：Claude 手寫的排版第一次就符合 |
| 3 | `aws login` → `aws sts get-caller-identity --query Arn --output text` | `arn:aws:iam::<account-id>:user/terry-admin` |
| 4 | `terraform -chdir=infra/daily init` | `Successfully configured the backend "s3"!`；`Reusing previous version of hashicorp/aws from the dependency lock file`、`Installed hashicorp/aws v6.68.0 (signed by HashiCorp)` |
| 5 | `terraform -chdir=infra/daily validate`、`-chdir=infra/persistent validate` | 兩層都 `Success! The configuration is valid.` |
| 6 | `terraform -chdir=infra/persistent plan` | `Plan: 0 to add, 1 to change, 0 to destroy.`：只有 `aws_iam_role_policy.destroy` `updated in-place`；其他 12 個只有 `Refreshing state`；新增 `DescribeDailyNetwork`（11 個動作、`Resource = "*"`）與 `DeleteDailyNetwork`（條件 `aws:ResourceTag/Layer = "daily"`、7 種 ARN）；原本的明文 Deny 不變 |
| 7 | `$env:TF_VAR_admin_cidr = "$((irm checkip.amazonaws.com).Trim())/32"` | 見下方「定案 6 補充」 |
| 8 | `terraform -chdir=infra/daily plan` | `Plan: 19 to add, 0 to change, 0 to destroy.`；每個資源的 `tags_all` 都有 `Layer = "daily"`；S3 Endpoint 政策只有 `s3:GetObject` `arn:aws:s3:::prod-ap-northeast-1-starport-layer-bucket/*`；DynamoDB Endpoint 政策只有 `GetItem`／`PutItem`／`UpdateItem` 與三張表的 ARN（帳號 ID 由 `aws_caller_identity` 在 plan 時就算出來） |

**定案 6 補充（本人 11:42 選 A）：本機的 `admin_cidr` 用環境變數 `TF_VAR_admin_cidr`，每開一個終端機查一次當下的公開 IP，不存 `.tfvars` 檔。**

- 本人常帶著電腦換網路；DHCP 發的是內部 IP（路由器給的），ALB 看到的是電信業者給路由器的公開 IP，換網路就會變
- 硬碟上不留 IP；忘了設時 Terraform 會停下來問 `var.admin_cidr`，等於自動提醒。不選 `.tfvars`：換網路時容易拿舊 IP apply，而且不會有提醒
- `checkip.amazonaws.com` 的回應尾巴帶換行，要 `.Trim()`，否則值會是「IP、換行、/32」，被變數檢查擋下
- C 段沒有 ALB，IP 對不對不影響；D 段測試換了網路就重新 apply（只改那一條規則）。在公司網路上查到的是全公司共用的出口 IP，D 段測試要用家裡網路或手機熱點

### 限制（目前為止）

- Claude 的試跑環境裝不了 Terraform，骨架只用 HCL 解析器檢查；本人電腦的 `fmt`、`validate`、`plan` 都通過（上方「施工」）
- 11 個 `Describe` 是照 Terraform 會呼叫的 API 推的，可能漏；`DisassociateRouteTable` 等動作 AWS 會檢查哪幾種資源的標籤，也要第一次 destroy 才確定
- 權限模擬器不會去看資源上真正的標籤，標籤要用 `--context-entries` 自己餵；所以標籤條件的「真的有效」要靠 destroy 實測
- 證明約 5 分鐘過期是查證到的說法（Spacelift 支援文件），workflow 的寫法不依賴確切秒數

---

## E122. C 段完成：PR #11 合併、長期層 apply、權限模擬器、每日層 apply、destroy workflow 第一次實測（2026-10-18 12:04～13:42）

**依據：** E121（六項定案與設計）；E120 定案 3（C 段建好就實測 destroy）。

**生活比喻：** 樣品屋蓋好、請拆除組來拆一次。拆除組自己帶工具（核對過序號的 Terraform）、拿工作證去櫃台換一小時的通行證（OIDC）、只拆貼「每日」標籤的東西、拆完巡一圈確認全空。第一次進場就拆乾淨，沒有回去拿扳手。

### 推送與 PR #11（本人執行，Claude 截圖讀結果）

| 步驟 | 結果 |
|---|---|
| `git add`（`infra/daily`、`destroy.yml`、`github_oidc.tf`、證據紀錄，四次）→ `git status` | `Changes to be committed` 剛好 11 個檔：9 個 `new file`、2 個 `modified`；沒有 `.terraform/`、`.tfstate`、`.tfvars` |
| `git commit` | `4099590`，`11 files changed, 565 insertions(+), 6 deletions(-)` |
| `git log --oneline -3`、`git diff --stat origin/main...HEAD` | `4099590` 接在 `8c36ed3`（`origin/main`）之後；diff 一樣是 11 個檔、565／6 |
| `git push -u origin feat/m4-daily-network` | `[new branch]` |
| PR #11（說明由 Claude 用 Claude in Chrome 填寫，本人按 Create） | 6 個檢查全綠（`Tests`、`Image scan`、`Config scan`、CodeQL ×3）；`Config scan` 綠燈 = `#trivy:ignore:AWS-0104` 的位置與寫法有效，其他新資源沒有 HIGH／CRITICAL |
| 合併（本人按 Merge） | `main` = `6fcb525`（12:43）；本機 `8c36ed3..6fcb525`、刪本機與遠端分支 |

- 填 PR 說明時發現：GitHub 的編輯器打字換行會自動補清單符號，逐字輸入會變成 `- -`；改成整段設定欄位的值才正確
- Claude 開的 Chrome 分頁在另一個視窗，本人一開始找不到；之後要提醒「在 Claude 的分頁群組裡」

### 長期層 apply（12:50）

| 項目 | 結果 |
|---|---|
| `terraform -chdir=infra/persistent apply` | 答 `yes` 前的計畫 `0 to add, 1 to change, 0 to destroy`；`aws_iam_role_policy.destroy: Modifications complete after 2s`；`Apply complete! Resources: 0 added, 1 changed, 0 destroyed.` |
| Outputs | 5 個值與 10/17 相同（帳號 ID 遮成 `<account-id>`） |
| 費用 | IAM，免費 |

### 權限模擬器（12:59～13:06）

捷徑：`$role` = 長期層 output `destroy_role_arn`；`$vpc` = 同帳號的假 VPC ARN（`vpc/vpc-test`）；`sim 動作 資源 標籤`（標籤用 `--context-entries` 餵 `aws:ResourceTag/Layer`，不寫就是沒標籤）。

| # | 問題 | 結果 | 證明了 |
|---|---|---|---|
| 1 | `sim ec2:DeleteVpc $vpc daily` | `allowed` | 貼 `daily` 的拆得掉 |
| 2 | `sim ec2:DeleteVpc $vpc persistent` | `implicitDeny` | 標籤不對拆不掉 |
| 3 | `sim ec2:DeleteVpc $vpc` | `implicitDeny` | 沒標籤（例如帳號預設 VPC）拆不掉 |
| 4 | `sim ec2:CreateTags $vpc daily` | `implicitDeny` | 不能把別的東西改貼成 `daily` 再拆 |
| 5 | `sim ec2:DescribeVpcs "*"` | `allowed` | 拆之前看得到現況 |

- 5 題都與 Claude 事先寫的預期相同
- 第 2～4 題是 `implicitDeny` 不是 `explicitDeny`：EC2 沒有寫 Deny，是 Allow 的條件不符合
- **限制：** 模擬器不看資源身上真正的標籤（標籤是參數餵的）；標籤條件「真的有效」靠下方 destroy 實測

### 每日層 apply（13:10）

| 項目 | 結果 |
|---|---|
| 確認 `$env:TF_VAR_admin_cidr` | 有值（`/32`） |
| `terraform -chdir=infra/daily apply` | 計畫 `19 to add`；VPC 3 秒 → 子網、大門、路由表、安全群組同時建 → 路由、綁定、規則 → 兩條 Gateway Endpoint 各 9 秒；`Apply complete! Resources: 19 added, 0 changed, 0 destroyed.` |
| 費用 | 全部免費 |

**主控台資源地圖（本人截圖，13:19～13:22）：** `m4-daily-resource-map-private.png`（私有子網 → `llm-gateway-private` → 只連 S3、DynamoDB 兩條 Endpoint）、`m4-daily-resource-map-public.png`（公有子網 1a、1c → `llm-gateway-public` → 網際網路閘道；大門底下寫「網際網路路由至 2 個公有子網路，0 個私有子網路路由至網際網路」）。兩張只有資源 ID，沒有帳號 ID。

**發現：路由表有 3 張，多一張沒有名字的 `rtb-…`。** 那是 AWS 建 VPC 時自動附送的**主路由表**：只有「本機」一條路、沒有子網關聯（三個子網都明確關聯了自己的路由表）。不是 Terraform 建的，所以沒有 `Name`、`Layer` 標籤；刪 VPC 時 AWS 一起刪，destroy 不需要額外權限。同樣附送的還有預設安全群組（`default`）與預設網路 ACL。

**生活比喻：** 建商在管理室放的預設指路牌，哪一棟沒掛自己的指路牌就照它走。三棟都掛了自己的，所以它沒人用；而且它只寫「社區內部」，有人忘了掛也只會出不去，不會意外通外面。

### destroy workflow 第一次實測（13:25～13:28，`destroy #1`）

本人在 Actions 的 `destroy` 頁面按 Run workflow（`main`）；Claude 用 Claude in Chrome 讀 log。截圖 `m4-destroy-first-run.png`。

| 步驟 | 結果 |
|---|---|
| 整體 | `Success`，51 秒（工作 44 秒）；`6fcb525`、`main`、`Manually triggered` |
| `Install Terraform and check its fingerprint`（2 秒） | `/home/runner/work/_temp/terraform.zip: OK`、`Terraform v1.16.5 on linux_amd64`；另印 `The latest version is 1.16.6` |
| `Hide the account ID` | 之後所有帳號 ID 都是 `***`（例如 `arn:aws:ec2:ap-northeast-1:***:internet-gateway/…`、`data.aws_caller_identity.current: Read complete after 0s [id=***]`） |
| `Destroy with Terraform`（37 秒） | `init` → 19 個 `Refreshing state`（**11 個 `Describe` 一個都沒漏**）→ 計畫 19 個 `destroy` → 拆：路由、規則、綁定 → 子網、安全群組、大門 → 兩條 Endpoint（各 11 秒）→ 私有路由表 → VPC；`Destroy complete! Resources: 19 destroyed.`、`The daily state is empty` |

**本人電腦再確認（13:42）：** `aws ec2 describe-vpcs --filters Name=tag:Layer,Values=daily --query "Vpcs[].VpcId"` → `[]`。

### 證明了什麼（C 段全部）

| 想證明的 | 證據 |
|---|---|
| repo 裡沒有長期金鑰，destroy 用 GitHub OIDC 借一小時的角色 | `destroy #1` 從 `main` 借到角色並完成拆除 |
| 安裝的 Terraform 是原廠的 | `sha256sum --check` 印 `OK` |
| 臨時憑證與帳號 ID 不出現在公開 log | log 裡帳號 ID 全是 `***`；workflow 沒有任何一步印出憑證 |
| 角色的讀取權限夠拆每日層 | 19 個 `Refreshing state` 沒有 `UnauthorizedOperation` |
| 刪除只限 `Layer=daily` | 模擬器 5 題；實際拆掉 19 個（含「卸大門要大門與 VPC 兩邊都有標籤」的 `DetachInternetGateway`） |
| 拆完沒有殘留 | workflow 自我驗收 `The daily state is empty`；本人 CLI 查 `Layer=daily` 的 VPC 為 `[]` |

### 限制（誠實記錄）

- 這次只拆了 C 段的 7 種資源；D 段的 NAT、彈性 IP、DNS 防火牆、ALB、ECS、CloudWatch 告警，要再加刪除權限，第一次拆時一樣可能缺權限
- 「標籤條件擋得住不該拆的東西」只用模擬器驗過，沒有在真的資源上做破壞實驗（例如手動建一個沒標籤的 VPC 讓 workflow 去拆）
- 公有子網、私有子網沒有被任何東西使用就拆了，C 段沒有驗證「網路通不通」；要到 D 段 Fargate 拉映像才證明 Endpoint Policy 寫對
- 主路由表、預設安全群組、預設 ACL 沒有被 Terraform 認領，沒有名字與標籤；預設安全群組的規則也沒有清空（見待決）
- Terraform 1.16.6 已發佈，這次沒升級（冷卻期與三處要一起改）

### 面試可用的說法

- 「我的 destroy workflow 從頭到尾不用第三方 Action：自己下載 Terraform、比對寫死在 repo 裡的 SHA256，再把 GitHub 的 OIDC 證明存成檔案，讓 Terraform 自己去換一小時的臨時憑證，憑證本身從來不出現在環境變數或 log 裡。」
- 「拆除角色的刪除權限只認 `Layer=daily` 這張標籤，而且刻意不給 `CreateTags`，否則就能把長期層的東西改貼標籤再刪。我先用 IAM 權限模擬器問了 5 題，再拿免費的網路骨架真的拆一次，第一次就拆乾淨，最後 workflow 自己檢查帳本是空的。」
- 「我把會跳錶的 NAT、ALB、Fargate 留到驗過拆除之後才建，所以如果拆除有問題，是在不花錢的地方撞到。」

**推送：**

| commit | 時間 | 訊息 |
|---|---|---|
| `4099590` | 10/18 12:05 | `feat: add the daily network skeleton and the destroy workflow` |
| `6fcb525` | 10/18 12:43 | `Merge pull request #11 from Poyu-Tu/feat/m4-daily-network`（`8c36ed3..6fcb525`；6 個檢查全綠） |
| `c791bd4` | 10/18 13:55 | `docs: record the C-stage apply and the first destroy run`（本筆與 3 張截圖） |
| `dfc49f8` | 10/18 14:0x | `Merge pull request #12 from Poyu-Tu/docs/m4-daily-results`（`6fcb525..dfc49f8`；6 個檢查全綠） |

---

## E123. D 段開工：九項定案（2026-10-18 14:23～15:02）

**依據：** E117（施工順序 D）、E120（權限分批長）、E121、E122；決策書 3.5（五個必踩的坑）、4.1、4.5、5.1、6.4、7.1、7.9、11.4（S08～S11）、D13、D14、D16、D20、D25；`m4-body-start-handoff.md` 第 4 節（寫 Terraform 時要記得的 11 項）。

**範圍：** NAT（單 AZ 1a）＋彈性 IP、私有路由表 `0.0.0.0/0 → NAT`、Route 53 Resolver DNS 防火牆（先 ALERT 後 BLOCK）＋查詢日誌、ALB（兩個公有子網、閒置逾時 120 秒、HTTP 80 只准本人 IP）、ECS Fargate（叢集、任務定義、服務）、CloudWatch 日誌群組與 `audit_write_failed` 指標篩選＋告警；`get_client()` 改用身分聯盟；雲端三張表的種子資料；OpenAI 端的 Fargate 角色對應；destroy 角色第三批權限。

**生活比喻：** C 段蓋好圍牆、隔間、門禁與兩條專用走廊；D 段接水電（NAT）、請一位拿名單的總機（DNS 防火牆）、開店門（ALB）、讓店員上班（Fargate）。

**花費估算（決策書 6.2 的東京單價）：** 全部開著約每小時 US$0.12（NAT 0.062、ALB 0.0243、公開 IPv4 × 3 共 0.015、Fargate 0.0154，其餘幾乎 0）；apply 到 destroy 預估 3～4 小時，約 US$0.4～0.5。

### 沿用的定案（不再問）

ALB 閒置逾時 120 秒（E115）；ALB 健康檢查打 `/health`、開部署斷路器並自動退回（E114）；`readonlyRootFilesystem: true`（E116）；任務角色對 `audit` 只給 `PutItem`、`api_keys` 只讀、`quotas` 讀＋`UpdateItem`（E116）；`DYNAMODB_TARGET=aws`（E111）；NAT 與私有子網都在 1a（D13）；ALB 只收本人 IP（E117）。

### 定案（本人逐題作答，14:51～15:02）

| # | 決定 | 定案 | 不選的選項與理由 | 弱點 |
|---|---|---|---|---|
| 1 | 上雲節奏 | **A：一次全上。** DNS 防火牆的「其他全部」規則先 ALERT；Gateway 跑起來後用真實對話與一次性任務製造查詢，從查詢日誌整理放行清單 → 改 BLOCK 再 apply（只改一條規則）→ 重跑一輪確認 → 當天 destroy | B 拆兩次：臨時任務本身就要 ECR、日誌、任務定義，D1 等於大半都要建，多一輪 apply／destroy。C 直接 BLOCK：漏一個網域就卡在 `CannotPullContainerError`（決策書 3.5 坑 2） | ALERT 那段時間出口只有紀錄、沒有擋（ALB 只收本人 IP） |
| 2 | Gateway 的兩個 IAM 角色放哪一層 | **A：執行角色與任務角色都放長期層。** 政策裡指到每日層的東西（日誌群組、SSM 參數）用寫死的名字；信任條件限 `ecs-tasks.amazonaws.com` 與本帳號 | B 放每日層：destroy 角色要多拿 `iam:DeleteRole` 等「註銷身分」的權限，與 C 段連 `CreateTags` 都不給的原則相反。C 拆開放：兩邊的缺點都拿到 | 每日層拆掉後角色還在（沒有任務在跑就沒人借得到） |
| 3 | HMAC 金鑰怎麼交給 Fargate | **A：本人用 AWS CLI 建 SSM SecureString `/llm-gateway/audit-hmac-key`**（值用 Python `secrets` 當場產生、不顯示；雲端用新的一把，與本機 `.env` 分開）。Terraform 只寫名字：任務定義的 `secrets` 指過去、執行角色只准讀這幾個參數；用 AWS 預設的 `aws/ssm` 金鑰加密 | B Terraform 用 write-only 參數建：要多引入 `random` provider（鎖版本、冷卻期），功能較新。C 明文環境變數：違反 D14 | 唯一不歸 Terraform 管的東西，誤刪要手動重建；放行清單要多 `ssm.ap-northeast-1.amazonaws.com` |
| 4 | `get_client()` 怎麼切換金鑰與身分聯盟 | **A：新環境變數 `OPENAI_AUTH`，一定要明講**：`api_key`（本機）／`workload_identity`（雲端）；沒設或寫錯 → 啟動就報錯。整個程式共用一個連線物件。身分提供者 ID、服務帳號 ID 也由本人用 CLI 存進 SSM（證據紀錄一直遮蔽它們，不進 repo）；audience `llm-gateway-capstone` 直接寫在 Terraform | B 自動判斷：程式自己猜，殘留的環境變數會讓本機悄悄換路（E111 的 43 個測試連錯資料庫就是這類問題）。C 本機也用身分聯盟：每次開發要 `aws login` 再匯出會過期的憑證，而且讓管理員帳號當 OpenAI 的身分 | `.env`、`.env.example`、`compose.yaml` 都要加一行；測試要配合「共用一個連線」 |
| 5 | 映像從哪一版建、標籤怎麼取 | **A：程式與 Terraform 同一個 PR → 本機 `fmt`／`validate`／`plan` → CI 全綠 → 合併 → 從 `main` 建映像，標籤 = 合併 commit 的編號 → 推 ECR → apply。** 之後要改程式：小 PR → 新標籤 → 只改變數 `image_tag` 再 apply。任務定義寫明 `X86_64` | B 從分支建：雲上跑過的那一份可能不在 `main`。C 固定標籤：`IMMUTABLE` 不准覆蓋 | apply 前多等一輪 CI（還沒跳錶） |
| 6 | S08 怎麼證明「清單外被擋」；ECS Exec | **A：一次性任務**：同一個任務定義與映像，臨時把啟動指令換成一小段 Python，查 `api.openai.com` 與 `example.com` 並試連 443，結果進 CloudWatch 日誌，DNS 查詢日誌出現 BLOCK；換指令的設定放 JSON 檔，外面包一支短的 PowerShell 腳本。**ECS Exec 不做** | B ECS Exec：放行清單要加 `ssmmessages` 等網域、任務角色多權限、本機裝 Session Manager 外掛，唯讀根目錄下還要另外掛可寫的資料夾（社群實測），與「出口管很緊」反方向。C 兩個都做：還是要付 B 的複雜度 | 決策書 8.2 M4 驗證列的「`enable_ecs_exec` 改成 `true` 後能進入容器」留白 |
| 7 | destroy 權限碰到不能限標籤的動作 | **B：先找「根本不需要這個權限」的做法。** 任務定義 `skip_destroy = true`（destroy 只從帳本移除、不註銷；任務定義不收費，留著當版本紀錄）；之後再遇到別的，真的沒辦法才寫 `Resource "*"` 並附理由 | A 直接給 `ecs:DeregisterTaskDefinition` 的 `Resource "*"`：範圍是整個帳號的任務定義，換來的只是撕掉不花錢的東西。C 讓本人電腦拆：workflow 拆不乾淨 | 「state 為空」不再代表 AWS 上一點不剩，任務定義會一版一版累積（每次改設定多一版） |
| 8 | `audit_write_failed` 告警通知誰 | **A：SNS 主題放長期層、訂閱本人 Email**（確認一次）；每日層的告警用名字指過去。Trivy AWS-0095（SNS 沒加密，HIGH）以 `trivy:ignore` 刻意接受、12/31 到期：用 AWS 預設金鑰加密的主題，CloudWatch 告警發不過去，要自管 KMS 金鑰（每月約 US$1）；主題裡只有告警名稱與狀態，沒有使用者資料 | B 不接通知：沒人聽得到的警報器。C 主題放每日層：每天要重點確認信、destroy 角色多 SNS 刪除權限 | 多一筆刻意接受的豁免 |
| 8-2 | AWS 附送的預設資源 | **A：只認領預設安全群組**（`aws_default_security_group`）：規則清空、貼名字與 `Layer=daily`；主路由表、預設網路 ACL 不動 | B 三個都認領：網路 ACL 規則寫錯會擋死整個子網。C 都不動：忘了指定安全群組的東西會套用「對外全開」的預設 | destroy 時只從帳本移除，靠刪 VPC 一起消失 |

**題 8 的 E 段驗證方式：** 本人用 CLI 往日誌群組寫一行假的 `audit_write_failed`，看告警變 `ALARM` 並收到信；證明「篩選 → 指標 → 告警 → 通知」這條鏈。Gateway 自己寫失敗的那一段已在本機刪表實驗證明（E116），兩者分開記。

**查到、寫進設計的事：**

- S3、DynamoDB 雖然走 Gateway Endpoint，容器仍要先經 VPC 的 DNS 查網域，所以 `dynamodb.ap-northeast-1.amazonaws.com` 與 ECR 映像層 bucket 的網域也要在放行清單裡；切成 BLOCK 時漏了就連資料庫都查不到
- Route 53 Resolver 的刪除動作（規則群組、網域清單、關聯、查詢日誌設定）都支援 `aws:ResourceTag`（AWS Service Authorization Reference）；NAT、彈性 IP、ALB、ECS、日誌、告警寫 Terraform 時逐一查並用模擬器驗

### 寫程式與 Terraform 時多做的安排（依定案推出，15:05～15:25 告知本人）

| # | 安排 | 依據 |
|---|---|---|
| 1 | **兩個日誌群組（`/ecs/llm-gateway`、`/llm-gateway/dns-queries`）、DNS 查詢日誌設定、`audit_write_failed` 指標篩選與告警都放長期層**；每日層只把查詢日誌「接上 VPC」 | 定案 7：刪查詢日誌設定要 `logs:DeleteLogDelivery`（只能寫 `*`）；日誌在每日層拆掉後仍查得到；日誌群組保存 30 天並開 AWS 層級的防刪（`deletion_protection_enabled`） |
| 2 | SNS 的 Email 訂閱由本人用 CLI 建 | 信箱是個人資料，同定案 3 的做法：不進 repo、不進帳本 |
| 3 | `tests/conftest.py` 開頭強制 `OPENAI_AUTH=api_key`（用 `=` 不用 `setdefault`） | 定案 4：視窗殘留雲端設定時，測試也不會去向 AWS 要證明 |
| 4 | 任務角色的信任條件加 `aws:SourceAccount` 與 `aws:SourceArn`（本帳號東京的 ECS）；執行角色只加 `aws:SourceAccount` | ECS 文件建議的防冒用條件 |
| 5 | 放行規則設 `TRUST_REDIRECTION_DOMAIN` | 預設會連 CNAME 指過去的名字也拿去比，切 BLOCK 時會被擋 |

**查到的：** AWS 文件寫明 `GetWebIdentityToken` 證明的 `sub` 是呼叫者的 IAM ARN，用角色時是角色的 ARN（不是每次不同的 session），所以 OpenAI 對應 `llm-gateway-task` 一次就好（AWS IAM〈Understanding token claims〉）。OpenAI 文件建議任務角色以 `sts:IdentityTokenAudience`、`sts:DurationSeconds ≤ 300` 限制（OpenAI〈Configuring workload identity federation for AWS〉）。

### 程式：`app/openai_auth.py`（新檔）與 `app/main.py`（本人填空 11 格，15:27～15:47）

| 函式 | 做什麼 |
|---|---|
| `read_openai_auth()` | 讀 `OPENAI_AUTH`，只收 `api_key`、`workload_identity`；沒設 → `KeyError`，其他 → `ValueError` |
| `get_aws_identity_token()` | 用東京 STS 地區網址（`https://sts.ap-northeast-1.amazonaws.com`）要一張 audience 為 `OPENAI_WIF_AUDIENCE`、ES384、300 秒的證明 |
| `make_openai_client(auth, max_retries, timeout)` | 金鑰模式交給 SDK 讀 `OPENAI_API_KEY`；身分聯盟模式把 `get_aws_identity_token` **本身**交給 SDK（不加括號），兩個 ID 從環境讀 |
| `app/main.py` | 模組層級 `OPENAI_AUTH = read_openai_auth()`（啟動就檢查）；`get_client()` 加 `@lru_cache(maxsize=1)`、改呼叫 `make_openai_client()` |

**填空第一次交出時（`4 failed, 15 passed`）：**

| 格 | 寫成 | 應該是 | 訊息 |
|---|---|---|---|
| ⑥ | `return auth` | `return OpenAI(max_retries=max_retries, timeout=timeout)` | `AttributeError: 'str' object has no attribute 'api_key'` |
| ⑨ | `read_openai_auth` | `read_openai_auth()` | 3 個 `ValueError: Unknown OpenAI auth mode: <function read_openai_auth at 0x...>`：存進去的是函式本身 |
| ⑩ | `@lru_cache` | `@lru_cache(maxsize=1)`（建議） | 能跑：沒有參數的函式只會有 1 個結果；寫明讓人一眼看出「只建一個」 |

改正後 Claude 取回兩個檔逐字比對，與參考版相同。

### 測試（Claude 整份提供；測試數 310 → 325）

- `tests/test_openai_auth.py`（新檔，14 個，不連資料庫）：兩種模式、5 種錯誤寫法、金鑰模式、身分聯盟模式（`get_token` 用 `is` 比對是不是同一支函式）、身分聯盟模式無視環境裡的金鑰（SDK 把 `api_key` 放成佔位字 `workload-identity-auth`）、缺 ID、未知模式、STS 用 botocore `Stubber` 檢查地區網址、audience、ES384、300 秒
- `tests/test_production_settings.py`（4 → 5 個）：加 `test_openai_client_is_shared`；加道具 `fresh_client`，每個測試前後 `get_client.cache_clear()`
- `tests/conftest.py`：開頭 `os.environ["OPENAI_AUTH"] = "api_key"`

| 時間點 | 結果 |
|---|---|
| 只放測試 | `ImportError: cannot import name 'openai_auth' from 'app'`，`1 error during collection` |
| 填空第一次 | `4 failed, 15 passed` |
| 改正 | 兩個檔 `19 passed`；整套 `325 passed`（23.97 秒，含 DynamoDB Local） |

（Claude 事先說「預期 20 passed」是算錯：`test_production_settings.py` 是 5 個不是 6 個。）

### 破壞實驗（本人執行，三個；每個做完改回，Claude 比對檔案大小確認）

| # | 改了什麼 | 結果 | 失敗訊息 | 證明了 |
|---|---|---|---|---|
| 1 | `get_token` 改成 `get_aws_identity_token()`（加括號） | `2 failed, 12 passed`：`test_workload_identity_mode_uses_the_aws_token`、`..._ignores_an_api_key` | 本人電腦：`botocore.exceptions.MissingDependencyException: Missing Dependency: Using the login credent...`；Claude 試跑：`KeyError: 'OPENAI_WIF_AUDIENCE'` | 加括號會在建連線那一刻就去要證明。本人的終端機留著 10/14 的 `OPENAI_WIF_AUDIENCE`，壞版本真的往下跑去找 `aws login` 的登入身分（同 `make_dynamodb_client()` 拿掉假帳密那次）；若那個套件剛好有裝，就會用本人真的 AWS 身分向 STS 開證明。正確版本建連線時不會去要證明 |
| 2 | 拿掉 `@lru_cache(maxsize=1)` | `5 errors` | `AttributeError: 'function' object has no attribute 'cache_clear'` | 共用連線被拿掉，整個檔停下來。限制：紅在測試前的準備動作，`is` 判斷本身沒有單獨看到紅（改 `maxsize=0` 才會），沒做 |
| 3 | `STS_ENDPOINT` 改 `https://sts.amazonaws.com` | `1 failed, 13 passed` | `assert 'https://sts.amazonaws.com' == 'https://sts....amazonaws.com'` | 改成全球網址擋得下來 |

**練習本：** 程式對照新增 `app/openai_auth.py` 一節（常數、`read_openai_auth()`、`get_aws_identity_token()`、`make_openai_client()`），`get_client()` 升為核心並寫 10/18 改動；測試索引新增 14 列、改 1 檔；進度總表加一列；基礎觀念補強加「函式名稱加不加括號」「`@lru_cache`」；設定檔分頁新增「M4 D 段的設定檔」一節。四個分頁開頭的 commit 編號合併後再改。

### 放檔與本機設定（16:05～16:20）

- 16 個檔由 Claude 放進 repo、核對大小；**`.github/workflows/destroy.yml` 是遠端工具的受保護路徑，寫不進去**，改放根目錄 `destroy.yml.new`，本人 `Move-Item -Force` 搬過去（第一次打成 `.github\workflow\`，`DirectoryNotFoundException`，沒有任何檔案被動）
- **`.env` 加一行時踩到的坑：** `Add-Content .env "OPENAI_AUTH=api_key"`，但 `.env` 最後一行沒有換行，`Add-Content` 不會先補換行，新的一行黏在 `DYNAMODB_TARGET` 的值後面（`...8001OPENAI_AUTH=api_key`）。Claude 以一行 `sed` 只在該位置補換行，全程只看變數名稱與行數、不印任何值；修正後 4 行、CRLF 不變、`DYNAMODB_TARGET` 結尾仍是 `8001`。之後往檔案尾巴加行，先確認最後一行有換行

### SSM 參數（本人，16:30～16:46）

- 兩個 OpenAI ID 的位置（OpenAI 文件沒寫）：身分提供者 ID（`idp_` 開頭）在組織設定 → Security → Workload Identity Provider 列表的 PROVIDER ID 欄；服務帳號 ID 是 `gateway-wif` 的 **User ID（`user-` 開頭）**，在專案設定 → Members，或對應頁 `gateway-wif` 旁的 ⓘ。本人找不到時，由 Claude 用 Claude in Chrome 在自己的分頁群組裡找到
- **推定、未證實：** SDK 要的服務帳號 ID 就是這個 `user-` 開頭的值；填錯的話 Gateway 第一次呼叫 OpenAI 會 `OAuth authentication error`，改 SSM 的值即可
- 10/14 探測時用 `$env:` 設的兩個 ID 以明文留在 PowerShell 歷史檔；這次改用 `--value (Read-Host)`，輸入的值不進歷史檔
- `put-parameter` 三次（HMAC 金鑰由 `secrets.token_hex(32)` 當場產生，雲端專用、與本機 `.env` 不同把），之後 `cls`
- `describe-parameters`（不列值）：3 個都是 `SecureString`、版本 `1`。中間兩次打錯：`describe-parameter`（印說明）、`--query "Parameter[]..."`（**沒有報錯、什麼都不印**：欄位名稱打錯只會回空的）

### fmt／validate／plan 與長期層 apply（16:46～17:05）

| 步驟 | 結果 |
|---|---|
| 兩層 `fmt -check`、`validate` | 都沒印東西、都 `Success!`（Claude 事先以 OpenTofu 1.10.6 加同版 AWS provider 檢查過） |
| 長期層 `plan`（`Select-String` 只留摘要） | `Plan: 10 to add, 1 to change, 0 to destroy.`：兩個角色與兩份政策、SNS 主題、兩個日誌群組、查詢日誌設定、指標篩選、告警；`aws_iam_role_policy.destroy` 原地更新 |
| **順序調整** | 每日層 `dns_firewall.tf` 要用名字查長期層的查詢日誌設定，設定沒建之前每日層 plan 跑不起來；所以長期層先 apply（10 個都不計費），每日層等合併、建好映像才 apply |
| 長期層 `apply` | `Apply complete! Resources: 10 added, 1 changed, 0 destroyed.`；新 output：`alerts_topic_arn`、`dns_query_log_config_id`、`task_execution_role_arn`、`task_role_arn` |
| 每日層 `plan -var=image_tag=0000000`（試算） | `Plan: 36 to add, 0 to change, 0 to destroy.`（C 段 19 ＋ 網路 4 ＋ DNS 防火牆 7 ＋ ALB 3 ＋ ECS 3） |

### OpenAI 端的對應（本人，17:10）

- 新增 `gateway-task-role`：服務帳號 `gateway-wif`、專案 `llm-gateway-capstone`、`sub` = `arn:aws:iam::<account-id>:role/llm-gateway-task`、權限 Restricted，ⓘ 只有 `api.model.chat_completions.request`（Claude 讀頁面逐字核對）
- `terry-admin-probe` 保留，Fargate 打通 OpenAI 後再刪

### SNS Email 訂閱（本人，17:14～17:22）

- `aws sns subscribe --topic-arn (terraform -chdir=infra/persistent output -raw alerts_topic_arn) --protocol email --notification-endpoint (Read-Host)`，之後 `cls`；本人點信裡的確認連結
- 確認（不印信箱）：`list-subscriptions-by-topic --query "Subscriptions[].[Protocol,SubscriptionArn=='PendingConfirmation']"` → `email   False`

### 推送與 PR #13（本人執行，Claude 截圖與讀頁面，17:25～17:43）

| 步驟 | 結果 |
|---|---|
| commit | `fc06c61` `feat: add NAT, DNS firewall, ALB and Fargate to the daily layer`（22 個檔、`1203 insertions(+), 6 deletions(-)`，父 `dfc49f8`） |
| `git push -u origin feat/m4-daily-runtime` | `* [new branch]`、追蹤設好 |
| PR #13 | Claude 在自己的分頁填標題與說明，本人按 Create；6 個檢查全綠（`Config scan`、`Image scan`、`Tests` 三個必要＋CodeQL 三個），沒有衝突 |
| 合併 | 本人按 Merge（merge commit），`main` = **`b259965`**；本機 `git switch main`、`git pull`（`dfc49f8..b259965` Fast-forward）、本機與遠端分支刪除 |
| PR 說明的規則（本人 17:31 提出） | PR 說明一律中文；PR 與 commit 都不附 Claude 署名或對話連結。查過：署名從 PR #11 開始出現（#11、#12、#13），commit 都沒有。三個 PR 的說明由 Claude 在編輯框改好、本人按 Update comment，改後重讀確認沒有署名。已寫進 Project 指示 |

**D 段的程式與設定到此全部進 `main`，但每日層的 D 段資源還沒 apply**（會計費的 NAT、ALB、Fargate、DNS 防火牆都還沒建）。剩下：建映像推 ECR → 每日層 apply → 驗證 → S08～S11 → destroy。

**10/19 01:25 討論：** 本人問能否在公司電腦做剩下的步驟。照 D34（登入 AWS 與 `plan`／`apply` 只在個人電腦）維持在個人電腦；理由之一是 ALB 只開給 `admin_cidr`，在公司電腦會變成全公司共用的對外 IP。

## E124. D 段上雲與 E 段驗收：映像、apply、身分聯盟、DNS 防火牆、S08～S11、告警、模擬器、destroy（2026-10-19 19:40～22:45）

**依據：** E123（D 段九項定案與程式）；決策書 3.5、4.1、4.5、6.4、7.1、11.4、11.5。

**目的：** 把 D 段真的建在 AWS 上，證明「雲端跑通與本機相同的流程」與「受控出口」，拍 S08～S11，測告警，當天拆掉。

**結果一句話：** 36 個資源上雲；雲端沒有 OpenAI 金鑰也叫得到模型；容器實際查的網域剛好是放行清單 9 個；切 BLOCK 後名單外的網域連地址都查不到，查詢日誌留下紀錄；S08～S11 到齊；告警 1 分鐘內寄信；destroy workflow 拆掉 35 個、卡在 EIP（權限設計漏洞），本機補拆，AWS 確認拆光。計費約 1 小時 50 分。

### 0. 簡報 PR #15（19:40～19:48，本人執行，Claude 填 PR 說明）

| 步驟 | 結果 |
|---|---|
| 分支 `docs/slides-v3`，只 add 三個檔 | `d89737b`（`3 files changed, 87 insertions(+)`）：10 分鐘簡報 v3（2,132,078 bytes）、`slides-changelog.md`、重截的 `s06-cost-savings.png`；證據紀錄與多餘的 v2.1 沒有加 |
| PR #15（中文說明、不附署名） | 6 個檢查全綠。10/19 之後第一個 PR：CodeQL（python）49 秒正常；途中出現一次灰色的「Code scanning results：1 configuration not found」，跑完變成「No new alerts」，是過渡狀態 |
| 合併 | `main` = **`90ed268`**；本機與遠端分支刪除；多餘的 `llm-gateway-slides-10min-v2.1.pptx` 刪除 |

### 1. 映像與 ECR（19:51～20:29）

| 步驟 | 結果 |
|---|---|
| 標籤 | 用當下 `main` 的 `90ed268`（`git rev-parse --short HEAD` 存進 `$tag`，不手打）。`app/` 與 `b259965` 相同，#14、#15 只動了文件與 `scripts/` 的標籤字 |
| 第一次建置 | `docker build --platform linux/amd64` 成功，但結尾有 `exporting attestation manifest`、`exporting manifest list`：Docker 預設多附出廠證明，推上去會是「目錄（image index）」格式；子層沒有標籤，可能被 ECR「沒標籤 1 天」的清理規則清掉 |
| 重建 | 加 `--provenance=false --sbom=false`，結尾只剩 `exporting manifest`、`exporting config`（全部快取，幾秒） |
| ECR 登入第一次 | `aws ecr get-login-password … \| docker login --password-stdin` 兩次都 `login attempt … failed with status: 400 Bad Request` |
| 查原因 | `$PSVersionTable.PSVersion.Major` = **5**；密碼存進變數後長度 **2252**（正常）→ 壞在 PowerShell 5 把一個程式的輸出經管線交給另一個程式時會重新編碼 |
| ECR 登入第二次 | `docker login --username AWS --password $pw …` → `Login Succeeded`（黃字警告 `--password` 不安全；權杖 12 小時、只能拉推映像）；`Remove-Variable pw` |
| 推送 | 8 層 `Pushed`；`90ed268: digest: sha256:96c54173…`，與本機相同 |
| 格式 | `imageManifestMediaType` = `application/vnd.oci.image.manifest.v1+json`（單一映像） |
| 掃描 | `describe-images` 的掃描欄位是 `null`，但 `describe-image-scan-findings` 是 `COMPLETE`；帳號層級 `BASIC`、沒有規則 → 靠倉庫的 `scan_on_push`，有運作 |
| 掃描結果 | **HIGH 3、MEDIUM 9、LOW 3**，沒有 CRITICAL |

**三個 HIGH（Claude 查 Debian 安全追蹤頁）：**

| CVE | 套件 | Debian 13 狀態 | 會不會碰到 Gateway |
|---|---|---|---|
| CVE-2026-85091 | zlib `1.3.dfsg+really1.3.1-1` | 沒有修補版 | 漏洞在 `gzprintf()`；Gateway 不寫 `.gz` |
| CVE-2026-5435 | glibc `2.41-12+deb13u4` | 沒有修補版，`<no-dsa>`（Minor issue） | 漏洞在印 DNS TSIG 紀錄的舊函式；不呼叫 |
| CVE-2026-19499 | glibc `2.41-12+deb13u4` | 沒有修補版，`<no-dsa>`（Minor issue） | 漏洞在 `strfmon()`；Gateway 算錢用整數 |

**決定：** 上雲。三個都是上游沒有修補、換指紋也修不掉，且卡在用不到的函式；與 CI 只擋「有修補版的 HIGH、CRITICAL」一致（D62）。等 Debian 出修補再換基底映像指紋。

### 2. 每日層 apply（20:42～20:49）

| 步驟 | 結果 |
|---|---|
| `admin_cidr` | `$env:TF_VAR_admin_cidr = "$((Invoke-RestMethod http://checkip.amazonaws.com).Trim())/32"`：查到就存，不印 IP（本人打成 `http://`，一樣查得到） |
| `plan -var="image_tag=$tag"` | `Plan: 36 to add, 0 to change, 0 to destroy.`，與 E123 的試算相同 |
| `apply` | `Apply complete! Resources: 36 added`；ALB 2 分 32 秒；**ECS 服務 1 分 8 秒穩定**（等於：經 NAT 拉到映像、三個 SSM 參數交給容器、唯讀根目錄下啟動、ALB 健康檢查通過）；任務定義 `llm-gateway:1`；**計費約 20:49 開始** |

### 3. 跑通（20:50～21:13）

| 步驟 | 結果 |
|---|---|
| `/health` | `HTTP/1.1 200 OK`、`{"status":"ok"}`、`server: uvicorn`（20:50:53）；只放行本人 IP 的 ALB 連得進去 |
| 灌雲端資料 | 專案的 boto3 讀不了 `aws login` 的登入狀態（同 E123 破壞實驗 1）→ `aws configure export-credentials --format powershell \| Out-String \| Invoke-Expression` 把臨時憑證放進環境變數；`DYNAMODB_TARGET=aws` 跑 `scripts.seed`，輸出整段收進變數，alice、bob 的 Key 各存一個變數，只印長度 `67`、`67` |
| **真的聊天** | `Say good morning in French` → `reply : Bonjour !`、`model : gpt-6-luna`（request_id `7edb67af-…`）。**雲端沒有 OpenAI 金鑰**：任務角色向東京 STS 要 5 分鐘的身分證明、換 OpenAI 通行證；**SSM 放 `user-…` 這個服務帳號 ID 是對的**（E123 的假設成立） |
| 雲端稽核（第一次） | `RuntimeError: Credentials were refreshed, but the refreshed credentials are still expired.`：20:55 匯出的臨時憑證約 15 分鐘就過期，Python 不會自己續期 |
| 重新登入也失敗 | `aws login` 之後再匯出仍 `still expired`：**環境變數比 `aws login` 優先**，CLI 先拿到的是過期的那組 |
| 定下的做法 | 跑 Python 查雲端前 `Get-ChildItem Env:AWS_* \| Remove-Item` → 匯出 → 跑 → 再清掉，讓 `aws`、`terraform` 用回 `aws login` |
| 雲端稽核 | `status: ok`、`user_id: bob`、`charged: True`、**`cost_micro_usd: 4`**（12 × 0.1 ＋ 5 × 0.5 = 3.7 → 4）、`model`／`routed_model`／`provider_model: gpt-6-luna`、`route_reason: default`、`fallback: False`、`finish_reason: stop`、`pii_types: []`、64 字 `prompt_hash`、`summary`、`timestamp: 2026-10-19T13:01:32Z` |

### 4. DNS 防火牆：先告警、後阻擋（21:26～21:55）

**ALERT 一小時的查詢日誌（`/llm-gateway/dns-queries`）：**

| 次數 | 網域 |
|---|---|
| 160 | `logs.ap-northeast-1.amazonaws.com` |
| 各 2 | `dynamodb…`、`prod-ap-northeast-1-starport-layer-bucket.s3…`、`auth.openai.com`、`sts.ap-northeast-1…`、`<account-id>.dkr.ecr…`、`ssm…`、`api.openai.com`、`api.ecr…` |

- **容器查過的網域剛好就是放行清單 9 個，一個不多、一個不少**；不用改清單
- 1 筆轉不成 JSON：CloudWatch 建立紀錄時寫的測試訊息（`Permissions are set correctly…`），不是 DNS 查詢
- 整段沒有任何一筆帶 `firewall` 欄位：放行規則判定通過的查詢不記防火牆欄位，只有 ALERT／BLOCK 才記 → 這段時間沒有查詢落到清單外

**切 BLOCK：**

| 步驟 | 結果 |
|---|---|
| 第一次 `apply -var="dns_firewall_action=BLOCK"` | 計畫 `3 to change`，比預期多 2 個 → 本人先答 `no` |
| 查原因（計畫寫進 `infra\daily\block.tfplan`，`*.tfplan` 被 `.gitignore` 擋；Claude 讀完、本人刪掉） | 放行清單 9 個網域、全部網域清單的 `*`：**AWS 存網域時會在結尾補一個點**（`api.openai.com.`、`*.`），Terraform 拿程式裡沒有點的版本比，以為被改過；內容相同、無害，但每次 plan 都會出現 |
| 第二次 apply | `Apply complete! Resources: 0 added, 3 changed, 0 destroyed.` |
| BLOCK 後再聊天 | `Say thank you in Japanese` → `gpt-6-luna`、`(Arigatō)`（日文在 PowerShell 5 顯示成亂碼）→ **放行清單在 BLOCK 下是完整的** |

**出口檢查（S08）：**

| 步驟 | 結果 |
|---|---|
| 第一次 `.\scripts\egress_check.ps1` | `Error handling -chdir option: chdir $tf: The system cannot find the file specified` ×4、`--cluster: expected one argument`：**PowerShell 不會展開 `-chdir=$tf` 裡的變數**（`-` 開頭的字串被當成參數名稱原樣交出）。沒有建出任何東西 |
| 修正 | Claude 把四行改成 `terraform "-chdir=$tf" output …`（1,243 → 1,251 bytes，BOM 保留）；之前給的指令都是寫死 `-chdir=infra/daily`，所以沒踩到 |
| 第二次（先不錄） | `EGRESS api.openai.com: DNS answered and TCP 443 connected`；`EGRESS example.com: DNS lookup failed (gaierror: [Errno -5] No address associated with hostname)` |
| 查詢日誌 | 13:53:44Z 4 筆 `BLOCK`、`NOERROR`：`example.com.` 的 A、AAAA，與 `example.com.ap-northeast-1.compute.internal.` 的 A、AAAA（Linux 查不到時自動接 VPC 內部網域再試，`*` 一起擋）→ **證明防火牆真的在運作並留紀錄**（回答 ALERT 階段「沒看到 firewall 欄位」的疑問） |
| 錄影（終端機的 PowerShell） | 先 `function prompt {"PS> "}`、`$since`、兩個查詢包成 `Show-Egress`、`Show-DnsBlocked`、`cls`；錄 `m4-s08-egress-control.mp4`（本人電腦，不進 repo）：任務 `2cf4e901…`、同樣兩行 `EGRESS`、同樣 4 筆 `BLOCK` |

### 5. S08～S11 截圖（本人 `Win`+`Shift`+`S` 貼給 Claude，Claude 裁掉空白、放進 `docs/screenshots/`、核對尺寸）

| # | 檔名 | 內容 |
|---|---|---|
| S08 | `s08-egress-control.png` | 兩行 `EGRESS` ＋ 4 筆 `BLOCK`／`NOERROR` |
| S09 | `s09-no-public-ip.png` | 服務 `assignPublicIp` = `DISABLED`；正在跑的任務網卡 `PublicIp` = `None`；子網 `llm-gateway-private-a`、`AutoAssignPublicIp` = `False` |
| S10 | `s10-endpoints.png` | 新腳本 `scripts/show_egress_controls.ps1`：DynamoDB 走廊只准 `GetItem`／`PutItem`／`UpdateItem` 三張表；S3 走廊只准 `GetObject` ECR 映像層 bucket；DNS 防火牆 100 `ALLOW`、200 `BLOCK`／`NODATA`；9 個網域（帳號 ID 換成 `<account-id>`） |
| S11 | `s11-part1-task-role.png`、`s11-part2-execution-role.png` | 新腳本 `scripts/show_gateway_roles.ps1`：任務角色 4 條、執行角色 4 條；**`Resource: *` 只有兩條，都是 AWS 規定不能指定資源的動作**：`ecr:GetAuthorizationToken`、`sts:GetWebIdentityToken`（後者有 audience `llm-gateway-capstone` 與 `DurationSeconds ≤ 300` 兩個條件） |

- 傳到本人資料夾的 PNG 會被重新壓縮（大小不同），Claude 逐像素比對 S08：完全相同
- 同一個暫存路徑第二次傳檔會送出舊內容（`show_egress_controls.ps1` 第一次是 2,031 的舊版），換新檔名重傳後 2,060、指紋一致

### 6. 告警測試（22:20～22:27）

- 新日誌串流 `alarm-test/<時間>`，寫一行 `{"event":"audit_write_failed","request_id":"alarm-test"}`（JSON 先寫進暫存檔，用 `file://` 交給 `put-log-events`，避開 PowerShell 5 的引號問題）→ `rejectedLogEventsInfo: null`
- **22:21:18（14:21:18 UTC）`OK -> ALARM`**，約 1 分鐘；SNS 寄信到本人信箱
- 22:27:18 `ALARM -> OK`（缺資料當成沒越線）
- 信件截圖遮掉帳號 ID、告警與主題 ARN，存 `docs/screenshots/m4-alarm-email.png`（佐證，不佔 S 編號）

### 7. destroy 角色模擬器第三批（22:26）

新腳本 `scripts/simulate_destroy_role.ps1`（只印題目與結果，不印帳號 ID 與 ARN）：10 題全部符合預期，截圖 `docs/screenshots/m4-destroy-role-simulator.png`。

| # | 題目 | 結果 |
|---|---|---|
| 1、2、4 | 拆 NAT、ALB、ECS 叢集（`daily`） | `allowed` |
| 3、5 | 拆 ALB（沒標籤）、DNS 防火牆規則群組（`persistent`） | `implicitDeny` |
| 6～9 | 刪 Gateway 任務角色、告警 SNS 主題、Gateway 日誌群組、DNS 查詢日誌設定 | `explicitDeny` |
| 10 | 把查詢日誌從 VPC 拆開 | `allowed` |

**限制：** 沒有出 `ec2:DisassociateAddress` 這一題 → 下面第 9 節的漏洞沒有被抓到。

### 8. 延遲與記憶體（決策書 12.5「上雲後量一次」）

| 項目 | 結果 |
|---|---|
| `/health` 5 次（台灣 → 東京 ALB → 容器） | 113、41、41、42、42 ms |
| 聊天 3 次（`Say hi`） | 3,538、1,956、1,747 ms；多數時間在等 OpenAI |
| 容器記憶體（ECS `MemoryUtilization`，兩小時最高） | 約 14.8%（512 MiB 的 14.8% ≈ 76 MiB）；平均值被畫面上的其他視窗擋住，沒有記到 |

### 9. 拆除（22:32～22:41）

| 步驟 | 結果 |
|---|---|
| destroy workflow（本人從 `main` 按 Run workflow，`destroy #2`） | **3 分 31 秒失敗**。ECS 服務 2 分 36 秒（先等任務停）、網際網路閘道 1 分 33 秒、ALB 17 秒、**VPC 拆掉了**（NAT 已不在）；最後 `Error: disassociating EC2 EIP (eipassoc-…): … not authorized to perform: ec2:DisassociateAddress on resource: arn:aws:ec2:ap-northeast-1:***:*/*` |
| 原因 | NAT 先拆、EIP 最後拆；帳本裡還記著 EIP 掛在 NAT 上，Terraform 先呼叫 `DisassociateAddress`（其實已自動脫離，只是過場）。**AWS 先檢查權限、再檢查東西在不在**；這個動作的資源是 `*/*`，沒有標籤，而 destroy 角色把它放在「限 `Layer=daily`」那一條 → 條件永遠不成立 |
| 本機補拆 | `state list` → `destroy`：`Plan: 0 to add, 0 to change, 1 to destroy`（`aws_eip.nat`）→ `Destroy complete! Resources: 1 destroyed.`（約 22:38） |
| 確認拆光（問 AWS） | 每日層帳本空；`daily` 標籤的 NAT、EIP、VPC 都沒有；`llm-gateway` 的 ALB、DNS 防火牆規則群組沒有；ECS 叢集 `INACTIVE` |
| 修法（下一個 PR） | destroy 角色把 `ec2:DisassociateAddress` 從限標籤那一條移出，另寫一條、`Resource "*"`、不加標籤條件（跟 `ecr:GetAuthorizationToken` 同類：AWS 沒辦法指定資源）。代價：destroy 角色可以把帳號裡任何一個公開 IP 從機器上拔下來，但**刪不掉**（`ReleaseAddress` 仍限 `daily`）；帳號裡只有這個專題的 IP。套用後模擬器補一題 |
| 實測限制 | 修好之後，要等下一次真的 apply 每日層再按 destroy，才算實測過「一鍵拆光」；M5 開工時順便驗。在那之前每次 destroy 完都要問 AWS 確認 |

### 10. 收尾

- OpenAI 端：10/14 探測用的對應（`sub` 是本人的 IAM 使用者）刪除（本人按，22:44）；Claude 重讀頁面確認只剩 `gateway-task-role`
- **計費：** 約 20:49～22:38，約 1 小時 50 分，估約 US$0.22（Cost Explorer 隔天才準）
- **OpenAI 呼叫：** bob 5 次（`Bonjour`、`Arigatō`、`Say hi` 3 次；第一次打錯參數的那次沒有送出）；出口檢查只連 TCP，不呼叫模型

### 證明了什麼（D、E 段）

- 雲端跑通與本機相同的流程：驗 Key、讀額度、遮罩、路由、呼叫、扣額度、寫雲端稽核
- **OpenAI 工作負載身分聯盟在 Fargate 上可用**：雲端不放 OpenAI 金鑰
- **受控出口成立**：容器實際只查 9 個網域；BLOCK 後名單內的照通、名單外的連地址都查不到，查詢日誌留下 `BLOCK` 紀錄
- 容器沒有公開 IP、在私有子網；兩條走廊只准特定動作與資源；兩個角色的權限都指定資源（兩個例外有理由）
- 稽核寫不進去的告警會寄信
- destroy 角色的 Deny 保護長期層（模擬器）；但「一鍵拆光」這次沒有成功

### 限制（誠實記錄）

- 三個 HIGH 弱點沒有修補版，帶著上雲
- DNS 防火牆只管 DNS：程式直接用 IP 連線擋不到（7.9 的殘餘風險，這次沒有測）
- ALERT 只觀察了約一小時、一種流量（啟動＋聊天）；強模型、降級、限流的路徑沒有走過
- 延遲只量了幾次、從台灣量；記憶體只有最高值
- 告警測試用的是手寫的假日誌，不是 Gateway 真的寫不進稽核
- destroy workflow 第二次實測失敗，修正後還沒實測
- 雲端的 alice、bob Key 只存在當時的 PowerShell 變數裡；表在長期層，Key 的雜湊還在 `api_keys` 表

### 面試可用的說法

- 「我的 Gateway 在雲端沒有放 OpenAI 的金鑰。容器用自己的 IAM 角色向 AWS 要一張 5 分鐘的身分證明，拿去跟 OpenAI 換通行證；角色的權限只准開給 OpenAI 那個對象、最多 300 秒。」
- 「DNS 防火牆我先開告警模式跑了一小時，整理容器實際查過的網域，剛好就是我放行的 9 個，才切成阻擋。切完我故意去連 example.com：DNS 連地址都不給，查詢日誌記下了 BLOCK。」
- 「一鍵拆除第二次實測失敗了。原因是拆公開 IP 前要先把它從 NAT 上拔下來，這個動作 AWS 沒辦法指定資源，而我把它放在『只能動 daily 標籤的東西』那一條，條件永遠不成立。模擬器 10 題全對，但沒出到這一題。我在本機補拆、問 AWS 確認拆光，再把這個動作改成不限標籤，代價是它能拔任何 IP、但刪不掉。」
- 「AWS 會在網域結尾自動補一個點，Terraform 以為被改過，每次都想改回去。內容一樣、無害，但我把程式改成跟 AWS 一樣的寫法，讓 plan 乾淨，真的改動才不會被淹沒。」


## E125. 修正 PR：destroy 角色拔公開 IP、DNS 網域結尾加點、模擬器補到 12 題（2026-10-20 00:40～）

**依據：** E124 第 4 節（網域結尾的點）、第 7 節（模擬器沒出到的題目）、第 9 節（destroy #2 卡在 `ec2:DisassociateAddress`）。

**目的：** 把 E124 找到的兩個問題改進程式，長期層套用 destroy 角色的新權限，模擬器補考，連同 E124 的截圖、腳本、證據一起走一個 PR。

**結果一句話：** destroy 角色多一條 `DisassociateAnyAddress`（`Resource "*"`、不加標籤條件），長期層 apply 1 個改動；模擬器 12 題全對；DNS 網域改成結尾有點。「一鍵拆光」要等下一次 apply 每日層才實測得到。

### 1. 改了什麼（分支 `fix/m4-destroy-eip`）

| 檔案 | 改動 | 為什麼 |
|---|---|---|
| `infra/persistent/github_oidc.tf` | `ec2:DisassociateAddress` 從 `DeleteDailyRuntime`（限 `Layer = daily`）移出，另寫 `sid = "DisassociateAnyAddress"`、`resources = ["*"]`、不加條件，附註解（代價：能把帳號裡任何一個公開 IP 從機器上拔下來，但刪不掉，`ReleaseAddress` 仍限 `daily`） | AWS 檢查這個動作時資源是 `*/*`，沒有標籤可比，限標籤的條件永遠不成立（E124 第 9 節） |
| `infra/daily/dns_firewall.tf` | 放行清單 9 個網域結尾加點（`api.openai.com.`；ECR 那個也是），全部網域清單 `*` 改 `*.`，附註解 | AWS 存成結尾有點，Terraform 每次 plan 都以為被改過（E124 第 4 節） |
| `scripts/simulate_destroy_role.ps1` | 加第 11 題（`ec2:DisassociateAddress` 對 `*`、沒標籤 → `allowed`）、第 12 題（`ec2:ReleaseAddress` 對 `elastic-ip/eipalloc-test`、沒標籤 → `implicitDeny`） | 補考 E124 漏掉的題目；第 12 題證明「拔得掉、刪不掉」 |

### 2. 檢查（00:43～00:47，個人電腦）

- `terraform fmt -check -recursive infra`：什麼都沒印（Claude 也在自己的環境用格式檢查工具確認兩個改過的檔，exit 0）
- `terraform -chdir=infra/persistent validate`、`terraform -chdir=infra/daily validate`：都是 `Success! The configuration is valid.`

### 3. 長期層 plan → apply（00:48～00:51；`aws login`，先清 `AWS_*` 環境變數）

| 步驟 | 結果 |
|---|---|
| plan | 只有 `aws_iam_role_policy.destroy` 原地更新（`~`）：`DeleteDailyRuntime` 的動作清單少了 `ec2:DisassociateAddress`（`ReleaseAddress`、`DeleteNatGateway` 還在）；新增 `DisassociateAnyAddress`（`Action = "ec2:DisassociateAddress"`、`Resource = "*"`）；`Plan: 0 to add, 1 to change, 0 to destroy.` |
| apply | `Modifications complete after 1s`；`Apply complete! Resources: 0 added, 1 changed, 0 destroyed.`（免費：IAM 不收錢） |

### 4. 權限模擬器補考（00:52）

`scripts/simulate_destroy_role.ps1`：**12 題全部 `O`**（截圖 `docs/screenshots/m4-destroy-role-simulator.png` 覆蓋舊的 10 題版）。

| # | 題目 | 預期 | 結果 |
|---|---|---|---|
| 1～10 | 同 E124 第 7 節 | — | 跟上次相同，全對 |
| 11 | 把公開 IP 從機器上拔下來（`ec2:DisassociateAddress`、資源 `*`、沒標籤） | `allowed` | `allowed` |
| 12 | 刪公開 IP（`ec2:ReleaseAddress`、沒標籤） | `implicitDeny` | `implicitDeny` |

### 5. 每日層

- 帳本是空的（E124 拆光），plan 看不出「點」修好沒；下一次 apply 每日層時，切 BLOCK 的 plan 應該只剩動作那一個改動
- 「一鍵拆光」同樣要等下一次 apply 再按 destroy workflow 才算實測（M5 開工時）

### 6. PR

（合併後補：PR 編號、檢查結果、`main` 的新 commit、Config scan 對 `Resource "*"` 有沒有意見）

### 證明了什麼

- destroy 角色現在「拔得掉任何公開 IP、刪不掉沒標籤的公開 IP」（模擬器第 11、12 題）
- 長期層的保護沒有被這次改動打開（第 5～9 題照舊 `implicitDeny`／`explicitDeny`）

### 限制（誠實記錄）

- 模擬器只問「這張卡刷這扇門會不會開」，不是真的拆；真的拆要等下一次 apply
- 第 11 題的資源用 `*`：模擬器這樣問跟 AWS 真的檢查時一樣，但沒有用真的 EIP 測
- DNS 結尾加點只確認語法；實際有沒有消除假改動要等下一次 apply

### 面試可用的說法

- 「模擬器 10 題全對，真的拆還是卡住，因為我沒出到那一題。修好之後我補了兩題：一題證明拔得掉，一題證明沒標籤的刪不掉，讓放寬的那條權限有邊界。」


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
| 11 | 3.2（`audit` 表）、D52、D7、D43、D51、PART 4 應用層 | 稽核寫進 `audit` 表：`write_audit()` 條件寫入（`attribute_not_exists(request_id)`）、`pii_types` 存清單（`L`）；寫不進去時 `save_audit()` 只接資料庫的錯，`report_audit_failure()` 以白名單印一行 JSON 到 stderr（不含摘要與 HMAC），回應不變；領用窗口 `get_audit_writer()` 取代 `get_audit_path()`；12.5 與 D52 該列劃掉（E116） |
| 12 | D22（repo 結構）、PART 9 安全、4.1 | `scripts/show_audit.py`；`tests/` 加上 `test_audit_store.py`、`test_chat_audit_store.py`、`test_show_audit.py`；`Dockerfile` 不再建可寫的 `data` 資料夾，ECS 設 `readonlyRootFilesystem`；IAM 只給 Gateway 對 `audit` 表 `PutItem`；CloudWatch 指標篩選 `{ $.event = "audit_write_failed" }` ＋告警；日誌群組設保存期限與存取權限（E116） |
| 13 | 5.1（State 管理）、PART 9「IaC」 | State 鎖改用 S3 鎖檔（`use_lockfile`），不建 DynamoDB 鎖表（DynamoDB 鎖已被 Terraform 標為淘汰）（E117） |
| 14 | 5.1、6.1、D20 | Terraform 分兩層：長期層（State、OIDC、ECR、四張表）與每日層（網路、NAT、DNS 防火牆、ALB、ECS）；destroy workflow 只拆每日層；M4 由本人電腦 apply，OIDC 角色先只給 destroy workflow（E117） |
| 15 | 4.4、7.8 | ALB 安全群組只放行本人公開 IP（Terraform 變數，值不進 repo）（E117） |
| 16 | D19、D62、5.1、PART 10 第 11 環節 | CI 第三個工作 `Config scan`（`trivy config .`，HIGH／CRITICAL 擋），已列入 `protect-main` 必要檢查；trivy-action v0.36.0、Trivy v0.74.0（兩個掃描都明寫）；刻意接受的項目用 `#trivy:ignore:<ID>:exp:<日期>` 寫在該行上方並附理由（目前只有 `AWS-0132`，12/31 到期）（E118） |
| 17 | 3.2、3.6、D16、D19 | 雲端 DynamoDB 先建三張表（`usage` 留 M5）：`PAY_PER_REQUEST`、`deletion_protection_enabled`、PITR；ECR `llm-gateway`：`IMMUTABLE`、`scan_on_push`、生命週期（沒標籤 1 天、最多 10 個）；State bucket：`bucket_prefix`、`prevent_destroy`、封鎖公開、版本控制、`AES256`、只准 HTTPS；Terraform 1.16.5、AWS provider 6.68.0（E118） |
| 18 | 5.1（State 管理）、PART 9「IaC」 | 實作：State 放 `llm-gateway-tfstate-<亂碼>` bucket 的 `persistent/terraform.tfstate`，`use_lockfile`；本機用 `aws login`（Terraform 1.15 起支援）；中斷的操作會留下 `.tflock`，以 `force-unlock` 收拾前要確認主人與沒有程序在跑（E119） |
| 19 | 4.2（CI/CD 層）、5.1、D20、11.4 的 S11 | GitHub OIDC 提供者與 `llm-gateway-destroy` 角色放長期層；只有 environment `destroy`（只准 `main`）借得到，`sub` 用 2026/7/15 後的新格式（`repo:Poyu-Tu@<owner-id>/llm-gateway@<repo-id>:environment:destroy`）；權限分批長，第一批只有每日層帳本兩個檔，並先寫明文 Deny 擋長期層；environment 取消管理員略過；`oidc-check.yml` 實測：沒掛 environment 被 AWS 拒、從分支觸發被 GitHub 擋（E120） |
| 20 | 3.5、D13、D16、5.1、PART 9「IaC」 | 每日層骨架：VPC `10.0.0.0/16`、公有子網 1a／1c（不自動發公開 IP）、私有子網 1a、網際網路閘道放 C 段；安全群組 `alb`（80 只准本人 IP）、`gateway`（8000 只准從 ALB、出 443）；AWS-0104 以 `trivy:ignore` 刻意接受（12/31）；Endpoint Policy：S3 只准 ECR 映像層 bucket 的 `GetObject`、DynamoDB 只准三張表的 `GetItem`／`PutItem`／`UpdateItem`；跨層資料用寫死的表名加 `aws_caller_identity`；destroy workflow 下載官方 zip 比對 SHA256、證明存檔交給 Terraform 換憑證、`admin_cidr` 填 RFC 5737 位址；destroy 角色第二批：逐一列出的 `Describe` 與限 `Layer=daily` 標籤的刪除（E121） |
| 21 | 5.1、D20、6.4、11.4 的 S11 | destroy workflow 實測：從 `main` 手動觸發，51 秒拆光每日層骨架 19 個資源，`state list` 為空；Terraform 不用第三方 Action（官方 zip＋SHA256）、OIDC 證明存檔交給 Terraform 換憑證、帳號 ID 以 `::add-mask::` 遮罩；destroy 角色的刪除權限限 `Layer=daily`，模擬器 5 題（E122） |
| 22 | 3.5、4.1、4.5、5.1、6.4、7.1、7.9、D13、D16、D20、D25 | D 段設計（E123）：長期層加執行角色與任務角色（任務角色只 `PutItem` 稽核、`sts:GetWebIdentityToken` 限 audience `llm-gateway-capstone` 與 300 秒）、兩個日誌群組（30 天、防刪）、DNS 查詢日誌設定、`audit_write_failed` 告警與 SNS；每日層加 NAT（單一 AZ 1a）、DNS 防火牆（9 個網域放行、其他 `*` 預設 ALERT、可切 BLOCK＋NODATA）、ALB（閒置 120 秒、`/health`、HTTP 80 只開 `admin_cidr`）、Fargate（0.25 vCPU／0.5 GB、根目錄唯讀、斷路器回滾、沒有公開 IP、沒有 ECS Exec、任務定義 `skip_destroy`）；`app/openai_auth.py`：`OPENAI_AUTH` 分 `api_key`／`workload_identity`；SSM 三個參數由本人用 CLI 建；destroy 角色第三批；Trivy 豁免加 AWS-0053、AWS-0054、AWS-0095（12/31）；測試 325 個（E123）。**實測結果待 D 段 apply 後補**（實測見第 23 項） |
| 23 | 3.5、4.1、4.5、6.4、7.9、8.2 的 M4、11.4（S08～S11）、12.5 | D、E 段實測（E124）：映像 `90ed268` 單一 OCI 格式（`--provenance=false --sbom=false`）、ECR 掃描 HIGH 3（都沒有修補版、用不到的函式，帶著上雲）；36 個資源、ECS 1 分 8 秒穩定；身分聯盟在 Fargate 可用、服務帳號 ID 是 `user-…`；ALERT 時容器只查 9 個放行網域、BLOCK 後名單外 `NODATA` 並記 `BLOCK`（含 `.compute.internal` 搜尋網域）；S08～S11 截圖與 S08 錄影；告警約 1 分鐘寄信；延遲 `/health` 約 41 ms、聊天 1.7～3.5 秒、記憶體最高約 14.8%（12.5 該列劃掉）；destroy workflow 卡在 `DisassociateAddress`，改為不限標籤、`Resource "*"`（E125：長期層 apply、模擬器 12 題）；網域改寫成結尾有點；新增 `scripts/show_egress_controls.ps1`、`show_gateway_roles.ps1`、`simulate_destroy_role.ps1`；本機操作規則：PowerShell 5 不用管線交 ECR 密碼、Python 查雲端前後清 `AWS_*` 環境變數、`-chdir` 加引號 |
| 24 | 11.6、2.1、2.2、8.3、11.4 的 S06、12.5 | 簡報 v3 的改動：照 `docs/handoff/slides-v3-done-handoff.md` 第 3 節（10 分鐘版 v3 37 頁、版面規則補「概念頁 → 驗收畫面」與框線、錄影不嵌進報告版、2.1 架構圖對齊簡報第 7 頁、2.2 加一句對應簡報第 8 頁、S06 右下重截、12.5 加 PR #14 一列） |

---

## 目前進度（2026-10-20 00:55）

**M4 開工前準備全部完成**（10/14～10/15）：

- 第 0 步：分支流程 ✅（E108；PR #3 改用按鈕合併 ✅，E115）
- 第 1 項：容器驗證 ✅（E114）；逾時改成 60 秒 ✅（E115，PR #5）
- 第 2 項：稽核搬進 `audit` 表 ✅（E116，PR #6）
- 第 3 項：`DYNAMODB_TARGET`、強一致讀取、隨需計費 ✅（E111）
- 第 4 項：停用 Key 的腳本 ✅（E112）
- 第 5、6 項：說明頁關閉、資料庫 503 不附 `Retry-After`、SDK 不重試 ✅（E109）
- 第 7、8 項：身分聯盟探測成功、Dependabot 運作中 ✅（E110、E113、E115）
- `main` = `8e2ce32`（PR #6）；Dependabot 的 PR #4（Trivy Action v0.36.0）留到 M4
- `310 passed`
- **M4 本體開工（E117）：** 四項定案、施工順序 A～E
- **長期層骨架與 Config scan（E118）：** State bucket、ECR、三張表寫好並 `validate`；CI 加 `Config scan` 並列為必要檢查；草稿 PR #7 6 個檢查全綠
- **長期層上雲（E119）：** 10 個資源 apply、帳本在 S3（`use_lockfile`）、`destroy` 被 `prevent_destroy` 擋、CLI 刪表被刪除保護擋；`23e190b`
- **PR #7 合併（10/17 10:40）：** `main` = `92b7aa4`，6 個檢查全綠
- **A 段後半開工（E120）：** OIDC 與 destroy 角色五項定案；發現 GitHub 新 repo 的 `sub` 改成「名字@編號」；帳號裡沒有既有的 OIDC 提供者
- **A 段完成（E120）：** OIDC 提供者與 destroy 角色上雲（免費）；權限模擬器 5 題、`oidc-check` 從 `main` 借到角色、沒掛 environment 被拒、從分支觸發被擋；PR #9 合併，`main` = `e08f48e`
- **E120 後半與截圖進 repo：** PR #10 合併，`main` = `8c36ed3`
- **C 段開工（E121）：** 六項定案；`infra/daily/` 骨架、`destroy.yml`、destroy 角色第二批權限寫好（HCL 解析器檢查通過）
- **C 段完成（E122）：** PR #11 合併（`main` = `6fcb525`）；長期層 apply（角色第二批權限）；模擬器 5 題；每日層 apply 19 個；`destroy #1` 51 秒拆光、帳本為空；**AWS 上只剩長期層 13 個資源，沒有在跳錶的東西**
- **C 段紀錄進 repo：** PR #12 合併，`main` = `dfc49f8`
- **D 段開工（E123）：** 九項定案；`app/openai_auth.py`、ECS 角色、日誌與告警、NAT、DNS 防火牆、ALB、Fargate 寫好；`325 passed`；長期層 apply（免費資源）；SSM 三個參數、OpenAI 對應 `gateway-task-role`、SNS 訂閱完成
- **PR #13 合併（10/18 17:40）：** `main` = **`b259965`**，6 個檢查全綠；**每日層 D 段還沒 apply，AWS 上沒有在跳錶的東西**
- **簡報 PR #15 合併（10/19 19:48）：** `main` = `90ed268`
- **D、E 段上雲與驗收（E124，10/19 19:51～22:45）：** 36 個資源、身分聯盟可用、受控出口成立（ALERT 收網域 → BLOCK → 出口檢查）、S08～S11 到齊、告警寄信、模擬器 10 題；destroy workflow 卡在 EIP，本機補拆，**AWS 確認拆光，沒有在跳錶的東西**
- **修正 PR 開工（E125，10/20 00:40～）：** destroy 角色加 `DisassociateAnyAddress`、長期層 apply（1 個改動）、模擬器 12 題全對、DNS 網域結尾加點
- 下一步（不花錢）：
  1. **修正 PR（個人電腦）：** commit、push、PR、合併；E125 第 6 節補 PR 結果
  2. **M4 結案：** `docs/milestones/m4-report.md`（問本人時數與 Cost Explorer 實際花費）、決策書 v2.10（本表 24 項）、練習本 `.tf` 各節第 3 句補實測、`slides-v2.1-start-handoff.md` 第 3 節（M4 成果、24.8% → 25.3%）
- 下一筆證據是 **E126**

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| ~~稽核搬進 `audit` 表；扣額度失敗的紀錄與告警；`pii_types` 的型別（D52）~~ | ✅ 10/15 寫不進去印一行日誌、回應不變、清單（E116） | — |
| 稽核寫不進去的告警與補收（E116） | CloudWatch 指標篩選 `{ $.event = "audit_write_failed" }` ＋告警；補收手動 | M4 寫 Terraform 時；正式解法 M5（SQS） |
| Gateway 對 `audit` 表的權限、容器唯讀（E116） | IAM 只給 `PutItem`；ECS `readonlyRootFilesystem: true` | M4 寫 Terraform 時 |
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
| ~~CI 加 `trivy config`（E104）~~ | ✅ 10/16 `Config scan`，必要檢查；trivy-action v0.36.0 已包含 PR #4 的升級，Node.js 20 警告消失（E118） | — |
| ~~Dependabot 的 PR #4~~ | ✅ 10/17 Dependabot 自行關閉（分支已刪，E120） | — |
| ~~environment 的新 `sub` 格式（E120）~~ | ✅ 10/17 `oidc-check` 印出 `repo:Poyu-Tu@62129723/llm-gateway@1394630828:environment:destroy`，與推定相同 | — |
| ~~每日層的 destroy 要不要讀長期層的資料（E120）~~ | ✅ 10/17 表名寫死、帳號 ID 用 `aws_caller_identity`，角色不多開權限（E121） | — |
| 主路由表、預設網路 ACL（E122） | 預設安全群組已在 D 段認領並清空規則（E123）；主路由表、預設網路 ACL 仍不認領，不影響 destroy | — |
| Terraform 1.16.6（E122） | 過冷卻期後一起升：兩層 `versions.tf`、`destroy.yml` 的 `TF_VERSION` 與指紋 | M4 內 |
| D 段的 destroy 權限（E122） | 第三批已套用、模擬器 10 題（E124）；**`ec2:DisassociateAddress` 不能限標籤**，10/20 改為 `Resource "*"` 並套用、模擬器 12 題（E125）；修正後的「一鍵拆光」待下一次 apply 實測 | M5 開工時實測 |
| 映像的三個 HIGH（E124） | zlib CVE-2026-85091、glibc CVE-2026-5435、CVE-2026-19499：Debian 13 沒有修補版；等修補出來換基底映像指紋 | 每次建映像時看 ECR 掃描 |
| DNS 防火牆網域結尾的點（E124） | 10/20 程式改寫成結尾有點（`api.openai.com.`、`*.`）（E125）；有沒有消除假改動待下一次 apply 看 plan | M5 開工時實測 |
| `AWS-0132` 豁免（E118） | 12/31 到期，到期前決定改用 KMS 或延長 | 12/31 前 |
| `usage` 表（E118） | M5 建；Endpoint Policy、IAM 要補 | M5 |
| 供應商預算用完的告警（D32、E100） | M3 只記稽核的 `error_code` | M4～M6 |
| 預扣（7.10） | M3 不做 | M5 |
| PR #6 的 CI 附註（10/15 21:18 本人截圖） | `CodeQL` 2 則是通知（notice）：`ubuntu-latest` 自 **10/19** 起改指 Ubuntu 26；`ci` 1 則是已知的 Node.js 20 警告（Trivy Action 內部的 `actions/cache`）。`ci.yml` 兩個工作都鎖 `ubuntu-24.04`，不受影響；CodeQL 預設設定的機器由 GitHub 管，10/19 後看第一次 CodeQL 結果有沒有變；M4 新增的 workflow（destroy）也鎖 `ubuntu-24.04` | 10/19 後第一個 PR |
| A 能不能擋住「沒進 PR、但有綠勾的 commit」（E108） | 目前的 `ci.yml` 做不出這種 commit；不另外測 | — |
