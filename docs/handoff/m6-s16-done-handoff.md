# 交接說明：CD 試跑與 S16 都做完，下一步上雲一次（10/27 15:40，公司電腦）

> 給下一個對話看。開新對話時貼第 7 節那段。跟本人說話不用 E 編號。下一個證據編號 **E155**（`docs/evidence/m6-evidence-log.md`）。
> 先讀：**決策書 v2.11.1**（唯一事實來源）→ 本檔 → `docs/evidence/m6-evidence-log.md` 的 **E150～E154** → 上雲清單另看 `m6-cd-wip-handoff.md` 第 5、6 節與 `m6-console-done-handoff.md` 第 5 節。

## 1. 目前狀態

| 項目 | 狀態 |
|---|---|
| `main` | **`305fe54`**（PR #40：S16 截圖與 E154）；之前 PR #37 CD、#38 CD 試跑紀錄 |
| 測試 | 415 個 |
| environment `deploy` | 只准 `main`、取消管理員略過；secret `AWS_DEPLOY_ROLE_ARN`、`ADMIN_CIDR`＝`192.0.2.1/32`（**上雲那天改成家裡的 IP**） |
| CD 試跑 | `main`：建映像、Trivy、推 ECR 綠，`plan` 42 to add → 守門擋下、apply 沒開始；別的分支：environment 擋 |
| Worker zip | Windows（公司電腦）與 Linux runner 的 `source_code_hash` 相同：`1z50L1kGoXaNff0iTZQ9eSbwx4gAKPbZOjKwNr8Q6k4=` |
| S16 | 完成：PR #39（草稿、已關閉）舊基底 Image scan 紅（pcre2 CVE-2026-103111 HIGH，有修補版）；main 綠。截圖 `docs/screenshots/s16-trivy-block.png`、`s16-trivy-pass.png` |
| ECR | 多了 `llm-gateway:8bcc043`（CD 試跑推的） |
| 每日層 | 拆著 |
| 長期層 | PR #35 那次 apply 後沒變 |
| 不要 `git add` | `docs/handoff/`（本機複本） |
| 可以清的 | 遠端分支 `docs/m6-s16`、`docs/m6-cd-trial`、`feat/m6-deploy-workflow`；公司電腦 `.git\stale-maintenance-lock-claude`、`.git\stale-tmp-obj-claude`（Claude 跑 `git fetch` 留下、已改名移開，可刪） |
| Project 指示 | 第一行「唯一事實來源」還寫 v2.10，要由本人改成 v2.11.1 |

## 2. 10/27 做完的（11:55～15:40，公司電腦）

1. PR #37 合併（CD）
2. environment `deploy` 設定與兩個 secret（Claude 讀設定頁核對）
3. deploy #1、#2 試跑（E153）
4. Worker zip 跨系統：公司電腦 `terraform -chdir=infra/daily plan` 指紋對上（E153）
5. S16（E154）：Claude 改 `Dockerfile` 的兩個 digest（只在測試分支），本人開草稿 PR；截圖由 Claude 用 Chrome 擷取
6. 撞到的：在 repo 最上層跑 `terraform plan` → `No configuration files`，改用 `-chdir=infra/daily`；Claude 在本人電腦跑 `git fetch` 留下鎖檔（已移開；之後 Claude 在本人電腦只讀 git，不跑會寫入的 git 指令）

## 3. 定案與要記得的

- CD 範圍＝整份 `plan`＋守門（10/26 定案 A）；兩道門：environment 只准 `main`、守門只准「任務定義換新＋服務更新」
- 擋下的只有「有修補版」的 HIGH、CRITICAL；沒修補版的 3 個 HIGH 照樣帶著上雲
- 練習本：M6 整段做完後**先問本人**再整理；待整理清單在 Project `claude/m6-console-draft/practice-book-todo.md`，還要加 `disallowed_changes()`、deploy 角色、`daily_read.tf`、`deploy.yml`
- 公司電腦：VS Code 只給 Claude「看＋點」，Chrome 用 Claude in Chrome 讀；權限 30 分鐘沒用會過期

## 4. 下一步：上雲一次（10/29 或 10/30 晚，**個人電腦**，約 3～4 小時）

順序（Claude 建議，開工前跟本人確認）：
1. `disable_key.py --user` 的事前準備（照 `m6-console-done-handoff.md`）；`m1-gateway` 金鑰 **11/2 到期**
2. 個人電腦：`git switch main && git pull`；`terraform -chdir=infra/daily plan -no-color | sls source_code_hash` 確認還是 `1z50L1k…Q6k4=`
3. 個人電腦建每日層（`TF_VAR_admin_cidr` 用家裡 IP、`TF_VAR_image_tag` 用當下 `main` 的前 7 碼；映像要先推過，或先按一次 CD 讓它推）
4. GitHub 把 `ADMIN_CIDR` secret 改成家裡 IP（跟 `TF_VAR_admin_cidr` 一樣，否則安全群組要改 → 守門擋）
5. 換一個新 commit 進 `main`（例如小文件改動），按 deploy：**預期守門放行**、只換任務定義＋服務、`wait_for_steady_state` 成功。若紅在 `plan` 的 `AccessDenied` → deploy 角色讀的權限缺，補 `daily_read.tf`
6. `/metrics` 驗收：不帶／帶錯 → 403；帶對 → 200；`/metrics/` → 403；`/health`、`/` 200
7. Console 三章錄影（節費、個資、額度；額度用 alice）
8. Grafana 抓雲端（S15；Prometheus 讀通行證檔用 `Set-Content -NoNewline -Encoding ascii`）
9. 告警響一次（`charge_queue_failed` 或新的兩組其中之一）
10. 與 OpenAI 後台對帳
11. destroy workflow 拆光，直接問 AWS 確認

## 5. 之後

| 時間 | 做什麼 |
|---|---|
| 10/28 | 空出來（S16 提前做完）：可以先寫上雲當天的逐步清單、或簡報 v5 的 CD 與 S16 頁 |
| 10/29 或 10/30 晚 | 上雲一次 |
| 10/31～11/1 | M6 結案：`m6-report.md`、決策書 v2.12、練習本（先問） |
| 11/2～11/6 | 簡報 v5、講稿砍回 10 分鐘、6 分鐘影片、口說與面試 |
| 11/7 | 截止 |

## 6. 簡報要記得

- 「CD 的兩道門」一頁：別的分支 3 秒被 environment 擋＋每日層沒建時守門列出 42 個 `create`、apply 沒開始；證據頁用 deploy #1、#2 的 Actions 畫面（本人截，或請 Claude 用 Chrome 截）
- S16 一頁：`s16-trivy-block.png`（pcre2 HIGH、有修補版 → 紅）對照 `s16-trivy-pass.png`（同一個 debian 13.7、弱點 0）；一句話：「同一個專案只差基底指紋，一個進不了 main」

## 7. 給本人：開新對話時貼這段

> 我在做 LLM Gateway 專題，M6 進行中（main = 305fe54；CD 已合併並試跑過、守門照預期擋下；S16 已拍）。下一步是上雲一次（CD 真的換版、/metrics 驗收、Console 錄影、Grafana、告警、對帳、拆光）。請先讀決策書 v2.11.1、docs/handoff/m6-s16-done-handoff.md 和 docs/evidence/m6-evidence-log.md 的 E150～E154。我在【個人電腦／公司電腦】。工作方式照 Project 指示，時間緊，程式請給完整版讓我照打。跟我說話不用 E 編號。
