# 交接說明：M7 小型 agent 寫到一半，換個人電腦繼續（10/27 16:55，公司電腦 → 個人電腦）

> 給下一個對話看。開新對話時貼第 6 節那段。跟本人說話不用 E 編號。下一個證據編號 **E157**（M7 的記在 `docs/evidence/m7-evidence-log.md`；M6 上雲的記回 `m6-evidence-log.md`）。
> 先讀：**決策書 v2.11.1**（唯一事實來源）→ 本檔 → `docs/evidence/m7-evidence-log.md`（E155 定案、E156 進度）。M6 上雲的清單看 `docs/handoff/m6-s16-done-handoff.md` 第 4 節。

## 1. 目前狀態

| 項目 | 狀態 |
|---|---|
| `main` | `305fe54`（M6：CD、S16 都已合併；剩上雲一次） |
| 分支 `feat/m7-agent` | 本人在公司電腦 commit＋push 一次 WIP（第 2 節），內容：`scripts/agent_tools.py`（已比對一致）、`tests/test_agent_tools.py`、`tests/test_agent_demo.py`、`docs/evidence/m7-evidence-log.md`。**若本人沒推到，個人電腦拿不到**，再請 Claude 把 Project 的草稿放進去 |
| 還沒打 | `scripts/agent_demo.py`（完整版在 Project `claude/m7-agent-draft/agent_demo.py`，Claude 已驗證）、`scripts/seed.py` 加 carol（`claude/m7-agent-draft/seed.py.diff`） |
| 測試 | 驗證複本 444 個全綠（415＋29）；在 `agent_demo.py` 打完之前，`tests/test_agent_demo.py` 會 import 失敗，正常 |
| 不要 `git add` | `docs/handoff/`（本機複本） |
| Project 指示 | 第一行「唯一事實來源」還寫 v2.10，要由本人改成 v2.11.1 |

## 2. 本人在公司電腦離開前（若還沒做）

```
git add scripts/agent_tools.py tests/test_agent_tools.py tests/test_agent_demo.py docs/evidence/m7-evidence-log.md
git commit -m "wip: add the agent tools and their tests"
git push -u origin feat/m7-agent
```
（分支推送不會觸發 CI；CI 只跑 PR 與 `main`）

## 3. 個人電腦接著做（M7）

1. `git fetch` → `git switch feat/m7-agent`
2. 本人照打 `scripts/agent_demo.py`（Claude 從 Project 草稿貼完整版；**全形 `｜`、`→`、`strip("\"'「」")`、`r"..."` 是易錯點**），再改 `seed.py`
3. Claude 逐行比對（`device_stage_files` 拉回來 `diff`，比截圖準）
4. `docker compose up -d` → `uv run pytest -q` → **444 passed**
5. 實跑（花真錢，每步約 2,000～4,000 micro-USD）：
   - 起本機 Gateway（`uv run --env-file .env uvicorn app.main:app` 或 compose 的 gateway profile）→ `uv run python -m scripts.create_tables`／`python -m scripts.seed`（印出 alice、bob、carol 三把 Key，只在當下 PowerShell 用）
   - **驗收①**：`uv run python -m scripts.agent_demo`，貼 bob 的 Key → 預期約 6 步、`停止：完成`；`python -m scripts.show_audit` 看每一步各一筆、單號對得上
   - **驗收②**：`uv run python -m scripts.agent_demo --max-steps 0 --budget 0`，貼 carol 的 Key → 預期約 4 步後 `停止：被 Gateway 擋下：額度用完（429）`；audit 最後一筆 `quota_exceeded`
   - 兩段都**錄影**（每段 30～60 秒）；畫面不能出現 Key
6. 實跑後看結果再定：模型若常不照格式（invalid 很多），調 `RULES` 文字（測試有釘住 `CALL 工具名(參數)`）
7. commit、PR（中文）、合併；練習本**先問本人**（M6、M7 一起整理）

## 4. 定案（細節在 E155）

- 工具 A+：`route`、`price`、`calc`（不用 `eval`）；任務約 6 步
- 煞車：8 步、30,000 micro-USD；Gateway 429；停止理由 `final`／`max_steps`／`budget`／`quota`
- 驗收②用 carol（10,000）
- `urllib`、網址寫死、`getpass` 問 Key
- 每步都會走 sol（含「設計」、規則＋歷史長）：誠實寫進報告與簡報

## 5. 今晚的順序建議（Claude）

M6 上雲那一段要建每日層、錄 Console、Grafana、告警、對帳、拆光，大約 3～4 小時；M7 剩下約 2～3 小時。兩個都要用個人電腦。
- **建議先做 M6 上雲**：金鑰 11/2 到期、上雲是 M6 唯一剩下的驗收、雲端開著就在計費，精神好的時候做；M7 是本機、不花雲端錢，晚一點或明天做都可以
- 若先做 M7：注意本機 Gateway（8000 埠）與上雲時的 Prometheus 抓本機 compose 會不會衝突

## 6. 給本人：開新對話時貼這段

> 我在做 LLM Gateway 專題，M6 只剩上雲一次（main = 305fe54），M7 小型 agent 寫到一半（分支 feat/m7-agent：agent_tools.py 與測試已推，agent_demo.py 還沒打）。今晚在個人電腦要做【M6 上雲／M7 收尾】。請先讀決策書 v2.11.1、docs/handoff/m7-agent-wip-handoff.md、docs/evidence/m7-evidence-log.md（E155、E156），M6 上雲另看 docs/handoff/m6-s16-done-handoff.md。我在【個人電腦】。工作方式照 Project 指示，時間緊，程式請給完整版讓我照打。跟我說話不用 E 編號。
