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

## 決策書 v2.10 待改項目

| # | v2.9 的位置 | 要改什麼 |
|---|---|---|
| 1 | D21、D67、10.3 | `protect-main` 已實測：沒跑過 CI 的 commit 直接推 `main` 被擋（GH013、2 個必要檢查 `Tests`、`Image scan`）；另加「Require a pull request before merging」（核准數 0）；Bypass list 為空。已滿足條件的 PR，推它的 commit 等於合併它（E108） |

---

## 目前進度（2026-10-14 09:30）

- 第 0 步：分支流程 ✅（E108，PR #2 合併為 `cd9abf6`）
- 下一步：開工前準備第 1 項，`compose.yaml` 加上 Gateway
- 下一筆證據是 **E109**

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| 稽核搬進 `audit` 表；扣額度失敗的紀錄與告警；`pii_types` 的型別（D52） | — | 10/16 前 |
| `app/db.py` 連真的 AWS 的表示法；強一致讀取；DynamoDB 計費模式（E89、E90） | — | 10/16 前 |
| 停用 Key 的腳本（E91） | — | 10/16 前 |
| `/docs`、`/openapi.json` 是否在正式環境關閉（12.5） | — | 10/16 前 |
| 資料庫故障的 503 要不要附 `Retry-After`（12.5） | 傾向不附 | 10/16 前 |
| 便宜模型那次 SDK 的等待與 ALB 閒置逾時（E100） | 關掉便宜模型那次的 SDK 重試，或調整 ALB 逾時；上雲後量一次 | 10/16 前 |
| OpenAI 工作負載身分聯盟能不能用（4.5） | 能用就不在 SSM 放 OpenAI 金鑰 | 10/16 前 |
| `m1-gateway` 金鑰 11/2 到期（12.5） | M4 另開金鑰放 SSM | M4 |
| Trivy 升級與 Action 的更新方式（E104） | 照 3 天冷卻期手動升級；評估 Dependabot | 10/16 前 |
| CI 加 `trivy config`（E104） | 有 Terraform 之後 | M4 |
| 供應商預算用完的告警（D32、E100） | M3 只記稽核的 `error_code` | M4～M6 |
| 預扣（7.10） | M3 不做 | M5 |
| A 能不能擋住「沒進 PR、但有綠勾的 commit」（E108） | 目前的 `ci.yml` 做不出這種 commit；不另外測 | — |
