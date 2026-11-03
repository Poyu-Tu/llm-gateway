# 交接說明：CD 合併、environment `deploy` 開好、第一次試跑守門擋下（10/27 14:15，公司電腦）

> 給下一個對話看。開新對話時貼第 6 節那段。跟本人說話不用 E 編號。下一個證據編號 **E154**（`docs/evidence/m6-evidence-log.md`）。
> 先讀：**決策書 v2.11.1**（唯一事實來源）→ 本檔 → `docs/evidence/m6-evidence-log.md` 的 **E152～E153**。前一份交接 `m6-cd-wip-handoff.md` 的第 6 節風險仍有效。

## 1. 目前狀態

| 項目 | 狀態 |
|---|---|
| `main` | **`8bcc043`**（PR #37 合併：`deploy.yml`＋守門 `check_deploy_plan.py`＋8 個測試，共 415 個） |
| environment `deploy` | 只准 `main`、取消管理員略過；secret `AWS_DEPLOY_ROLE_ARN`、`ADMIN_CIDR`＝`192.0.2.1/32`（**上雲那天要改成家裡的 IP**） |
| deploy #1（`main`） | 建映像、Trivy、推 ECR 綠；`plan` 42 to add → 守門列出 42 個 `create` 擋下，apply 沒開始；帳號 ID 全是 `***`、沒有 IP |
| deploy #2（別的分支） | 3 秒被 environment 擋：`not allowed to deploy to deploy` |
| ECR | 多了 `llm-gateway:8bcc043`（CD 推的） |
| 每日層 | 拆著 |
| evidence log | 公司電腦 `D:\llm-gateway` 已補 E153（**未 commit**），Project 也已更新 |
| 不要 `git add` | `docs/handoff/`（本機複本） |
| Project 指示 | 第一行「唯一事實來源」還寫 v2.10，要由本人改成 v2.11.1 |

## 2. 本人還要做的（公司電腦）

1. 開分支、commit、推 E153，開 PR，綠了合併：
   ```
   git switch -c docs/m6-cd-trial
   git add docs/evidence/m6-evidence-log.md
   git commit -m "docs: record the first deploy run blocked by the plan guard"
   git push -u origin docs/m6-cd-trial
   ```
   PR 標題：`M6：記錄 CD 第一次試跑（守門擋下、別的分支被擋）`
2. ~~Worker zip 跨系統先驗~~ **已做（14:43）**：公司電腦 Windows 算出的 `source_code_hash` 與 Linux runner 相同（`1z50L1k…Q6k4=`）。E153 補了這段，要再 commit 一次（同一個分支）：
   ```
   git add docs/evidence/m6-evidence-log.md
   git commit -m "docs: record the worker zip hash match between windows and linux"
   git push
   ```

## 3. 定案與要記得的

- CD 的 apply 範圍＝整份 `plan`＋守門（10/26 定案 A），這次在真的計畫上證明擋得住
- deploy 角色讀的權限：每日層**沒建時**夠；**建著時**要 Describe 42 個現有資源，上雲那天第一次知道。若紅在 `plan` 的 `AccessDenied` → 補 `daily_read.tf` 的動作、跑模擬器、長期層 apply
- 練習本：M6 整段做完後**先問本人**再整理；待整理清單在 Project `claude/m6-console-draft/practice-book-todo.md`（還沒加 `disallowed_changes()`、deploy 角色、`daily_read.tf`）
- 公司電腦：VS Code 只給 Claude「看＋點」，Chrome 用 Claude in Chrome 讀；權限 30 分鐘沒用會過期

## 4. 下一步

| 時間 | 做什麼 |
|---|---|
| 10/27 | 第 2 節（PR 合併） |
| 10/28 | S16 分支（舊基底映像，看 Trivy 擋） |
| 10/29 或 10/30 晚 | **上雲一次**：本人電腦建每日層（`TF_VAR_admin_cidr` 用家裡 IP）→ 改 `ADMIN_CIDR` secret → 換一個新的 `main` commit 或直接按 deploy（標籤已存在會沿用）→ 預期守門放行、只換任務定義＋服務 → `/metrics` 驗收 → Console 三章錄影 → Grafana（S15）→ 告警響一次 → 對帳 → destroy；上雲前 `disable_key.py --user` |
| 10/31～11/1 | M6 結案：`m6-report.md`、決策書 v2.12、練習本（先問） |
| 11/2～11/6 | 簡報 v5（加 CD 這一頁：守門擋下的清單、別的分支被擋）、講稿砍回 10 分鐘、6 分鐘影片 |
| 11/7 | 截止 |

**上雲那天的注意：** 每日層由本人**個人電腦**建；建之前先跑 `terraform -chdir=infra/daily plan -no-color | sls source_code_hash`，確認還是 `1z50L1k…Q6k4=`（公司電腦已對上，個人電腦同一份 `.gitattributes`，應該一樣）。不一樣的話守門會因 Lambda 要更新而擋（安全地失敗）。在 repo 最上層跑 `terraform plan` 會報 `No configuration files`，一律用 `-chdir=infra/daily`。

## 5. 簡報要記得

- 新增一頁「CD 的兩道門」：environment 只准 `main`（別的分支 3 秒被擋）＋守門（每日層沒建時列出 42 個 `create`、apply 沒開始）；證據頁放這兩次 run 的截圖（本人截，Actions 頁面不含帳號 ID）

## 6. 給本人：開新對話時貼這段

> 我在做 LLM Gateway 專題，M6 進行中（main = 8bcc043，PR #37 的 CD 已合併；environment deploy 開好，第一次試跑守門照預期擋下、別的分支被 environment 擋）。下一步是 S16 分支，然後上雲一次（CD 真的換版）。請先讀決策書 v2.11.1、docs/handoff/m6-cd-trial-done-handoff.md 和 docs/evidence/m6-evidence-log.md 的 E152～E153。我在【個人電腦／公司電腦】。工作方式照 Project 指示，時間緊，程式請給完整版讓我照打。跟我說話不用 E 編號。
