# M1 文字證據紀錄

> 依決策書 11.5 遮蔽：AWS 帳號 ID、存取金鑰 ID、使用者唯一 ID、公開 IP；OpenAI 的 Project ID、金鑰 Tracking ID、金鑰末 4 碼、建立者 user ID；個人帳號名稱（含終端機提示字元中的使用者資料夾名稱）。
> 本檔收錄「文字型」證據；截圖另存於 `docs/screenshots/`，日誌另存於 `docs/logs/`。
> E 編號接續 `m0-evidence-log.md`（E1～E28），M1 從 E29 開始。
> 紀錄日期：2026-09-28 建立，收錄 9/26 開工前的定案（E29～E34）；同日補上 E33 的 uv 安裝結果，新增 E35～E38（VS Code 擴充套件與專用設定檔），步驟 1 完成

---

## 紀錄規則（2026-09-28 定案，M1 起適用）

| # | 東西 | 規則 |
|---|---|---|
| 1 | 證據紀錄 | 每個里程碑一份（本檔為 `docs/evidence/m1-evidence-log.md`），E 編號接續；每完成一組步驟就更新，回傳完整新版 |
| 2 | 里程碑報告 | 整關驗證通過後寫 `docs/milestones/m1-report.md`，格式同《M0-M0.5-里程碑結案報告》；只向本人確認花費時間與實際花費 |
| 3 | 決策書 | M1 結案時出 v2.7，放 `docs/decision-book/`；待改項目列在里程碑報告附錄（含 Bedrock 退場） |
| 4 | 截圖、日誌 | 收到就改名、遮蔽、回傳 |
| 5 | 存放 | 所有回傳的檔案也存一份到 Project |

---

## M1 工作方式與步驟規劃（2026-09-26）

**工作方式：**
- 程式碼由本人在 VS Code 親自撰寫；Claude 負責說明概念、給規格與提示、檢查程式碼與資安問題，不代寫
- 提示分三層：方向 → 關鍵語法 → 最後才看參考答案
- 建議關閉 AI 自動補全（如 Copilot），確保程式碼是自己寫的，面試被追問時答得出來

**步驟規劃：**

| # | 步驟 | 需要金鑰 |
|---|---|---|
| 1 | 開發環境：VS Code + 3 個官方擴充（Python、Pylance、Container Tools）、Python 3.12、uv | 否 |
| 2 | 專案骨架：`uv init`、`app/`、`tests/`、`.gitignore` | 否 |
| 3 | GitHub repo 設定（D21），第一次 push 前完成 | 否 |
| 4 | `GET /health` + 第一個 pytest | 否 |
| 5 | OpenAI 呼叫函式（E30）+ 用假回應的 pytest | 否 |
| 6 | HMAC 雜湊、摘要（E34）、稽核紀錄 + pytest | 否 |
| 7 | `POST /v1/chat` 串起來 | 否 |
| 8 | 開 M1 金鑰 → 真的呼叫一次 → 驗證 | 是 |
| 9 | Dockerfile，用容器跑一次 | 是 |

**為什麼金鑰排在第 8 步：** M1 金鑰依 E21 規格設 30 天到期。前 7 步都不需要呼叫模型；晚一點開，30 天的有效期就能涵蓋到更後面的里程碑，也縮短金鑰「存在但沒在用」的時間。

---

## E29. Bedrock 正式退場（2026-09-26 18:39）

**背景：**
- Bedrock 被帳號層級封鎖（E3、E5），v2.5 改用 OpenAI API（E12）
- 但 v2.5、v2.6 仍把 Bedrock 保留為「可切回的供應商」：D23、D24 的理由之一是「薄介面保留切回 Bedrock 的彈性」；3.4 有「Bedrock 的位置」一段；7.1 有「什麼時候切回 Zero Egress」一段

**定案：** Bedrock **不再當備案**。架構固定為 NAT + 受控出口（D25）+ OpenAI API（D24、D28、D29）。

**理由：**
- 保留一條「永遠不會實作、也沒驗證過」的切回路線，文件裡就同時存在兩套網路設計（受控出口與 Zero Egress），面試時容易被追問，卻拿不出證據
- 帳號封鎖的兩條路（業務例外、指導老師）都沒有結果，M1～M6 的時程不再為它預留空間
- 切回路線是薄介面設計的主要理由之一；退場後薄介面可以一起簡化（E30）

**保留的部分：** Zero Egress → 受控出口的轉折仍是專題故事的一部分（為什麼改、改了什麼、接受哪些殘餘風險），留在決策書 7.1 與 E3、E5、E12 作為歷史紀錄。E5 寫的「若開通可經由薄介面切回 Bedrock」是當時的狀態，證據紀錄不回頭修改。

**對決策書的影響（v2.7 待改）：**
- 3.4「Bedrock 的位置」一段刪除
- 7.1「什麼時候切回 Zero Egress」刪除，或改寫為歷史說明
- D23、D24 刪除「保留切回 Bedrock」的理由
- PART 9「AI 模型存取」一列；10.1 等其他提到切回的敘述

---

## E30. 薄介面簡化：一個檔案、一個函式（2026-09-26）

**背景：** D23 定案「官方 SDK + 自己包的薄介面，換供應商只改設定」。E29 之後，「換供應商」這個理由不存在了。

**選項：**

| 選項 | 做法 | 評估 |
|---|---|---|
| A | 定義介面（`Protocol`），每家供應商一個實作類別 | 為了一個不會出現的第二家供應商做抽象，屬過度設計；新手自己寫也較難 |
| **B（採用）** | 一個檔案 `app/providers/openai_client.py`、一個函式，回傳自己定義的資料格式 | 保留下面兩個仍成立的理由，寫法最簡單 |
| C | 不包，路由程式直接呼叫 OpenAI SDK | OpenAI 回應物件的解析散落各處；測試時要去模擬 SDK 內部的結構 |

**B 仍然成立的兩個理由：**
1. **測試不花錢：** pytest 用假回應取代真的 OpenAI，跑幾次都是 $0
2. **OpenAI 的細節集中在一處：** token 怎麼取（含 `reasoning_tokens`，D28）、SDK 重試次數與逾時（D10）都寫在同一個檔案；其他程式只拿到整理好的結果，不接觸 OpenAI 的物件

**回傳格式（規劃）：**

```python
@dataclass(frozen=True)
class ChatResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
```

**生活比喻：** 家裡只有一台冰箱，不需要萬國轉接頭；但插頭還是插在延長線上，要檢修時拔延長線就好，不用拆牆。

**面試講法：** 「一開始我設計了可以換供應商的抽象層，後來確定只用 OpenAI，就把它簡化成一個函式。留著它不是為了換供應商，而是讓測試不用真的呼叫 API，並且把 token 計算、重試這些細節集中管理。抽象層要有真的需求才做。」

**對決策書的影響（v2.7 待改）：** 3.4「呼叫方式」一列與 D23 的「換供應商只改設定」，改為上述兩個理由。

---

## E31. 開發機固定為第二台（個人電腦）（2026-09-26 18:43）

**背景：** M0～M0.5 在兩台電腦上進行（E1、E2 兩台都設定過 AWS CLI）。交接時第一台尚未安裝 Docker 與 cosign。

**定案：** 從 M1 起，專題**只在第二台電腦（本人的個人電腦）**進行。第一台是公司的電腦，不再用於本專題。

**理由：**
- 個人專案的 OpenAI 金鑰與程式碼，不該放在公司管理的設備上。公司電腦受公司政策管理，可能有監控或資料外洩防護軟體；兩邊的資產混在一起，對雙方都不好
- 第二台已具備 M1 需要的 Docker 29.7.2（E4）與 cosign 3.1.3，不需要補裝

**影響：** 交接文件中「第一台補裝 Docker」的待辦取消。

**面試講法：** 「這個專題我刻意只用個人電腦，不用公司配發的電腦。金鑰和程式碼屬於個人專案，放在公司管理的設備上，不論對公司的資安政策，還是對我自己的資產，都不是好的做法。」

---

## E32. 第二台電腦開發工具盤點（2026-09-26 18:43）

**指令與結果（Windows PowerShell）：**

```
> code --version
1.133.0
a5b500951314efd502d07465bd138dfbd714a960
x64

> python --version
Python 3.12.10

> uv --version
uv : 無法辨識 'uv' 詞彙是否為 Cmdlet、函數、指令檔或可執行程式的名稱。
    + CategoryInfo          : ObjectNotFound: (uv:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

> git --version
git version 2.55.0.windows.2
```

| 工具 | 版本 | 狀態 |
|---|---|---|
| VS Code | 1.133.0（x64） | ✅ |
| Python | 3.12.10 | ✅ 符合 D18 |
| Git | 2.55.0 | ✅ |
| uv | —（9/28 已安裝 0.12.19，見 E33） | ⬜ → ✅ |

- VS Code 擴充套件尚未盤點（步驟 1 後半）
- 提示字元中的使用者資料夾名稱未收錄

---

## E33. uv 以 winget 安裝（決定 2026-09-26；安裝 2026-09-28）

**uv 是什麼：** 把「裝套件」（原本的 pip）、「每個專案獨立的套件環境」（原本的 venv）、「記下每個套件確切版本與指紋的 lock 檔」三件事合成一個工具（D18）。

**安裝方式比較：**

| 選項 | 做法 | 評估 |
|---|---|---|
| A | 官網建議的安裝指令：從網路下載腳本並立即執行 | 執行前沒有人檢查腳本內容；與 E15（LiteLLM 啟動時下載未驗證的價格表）同一類風險 |
| **B（採用）** | `winget install -e --id astral-sh.uv` | Windows 11 內建；安裝前比對安裝檔的 SHA-256，與套件清單登記的不符就拒絕安裝 |
| C | `pip install uv` | 讓「管理 Python 環境的工具」反過來依附在某一個 Python 環境裡 |

**限制（誠實記錄）：** winget 驗證的是「下載的檔案與清單登記的一致」，不是「清單本身可信」。信任因此轉移到 winget 套件清單的審核流程；比直接執行網路腳本多了一道比對，但不是零風險。

**安裝結果（2026-09-28 20:33）：**

```
> winget install -e --id astral-sh.uv
找到 uv [astral-sh.uv] 版本 0.12.19
此套件需要下列相依性：
  - 套件
      Microsoft.VCRedist.2015+.x64
正在下載 https://github.com/astral-sh/uv/releases/download/0.12.19/uv-x86_64-pc-windows-msvc.zip
  17.1 MB / 17.1 MB
已成功驗證安裝程式雜湊
已成功擷取封存
新增的命令列別名: "uvx"
新增的命令列別名: "uv"
新增的命令列別名: "uvw"
已成功安裝

> uv --version
uv 0.12.19 (bea138450 2026-09-24 x86_64-pc-windows-msvc)
```

**判讀：**
- **「已成功驗證安裝程式雜湊」**：選 B 的理由得到實證。下載檔的 SHA-256 與 winget 清單登記的一致才繼續安裝
- **下載來源是 uv 官方 GitHub Releases**：winget 不另外託管檔案，只負責「指向哪裡」與「檔案指紋應該是多少」。它能防下載途中被竄改，防不了官方發佈點本身被入侵（限制見上）
- **版本發布於 2026-09-24，安裝時已上架 4 天**：符合 D27 冷卻期的「滿 3 天」門檻（D27 原為 LiteLLM 訂定，此處只作參考）。winget 預設裝最新版，這次剛好通過，不是刻意選版
- **相依套件 VC++ 可轉散發套件**：winget 先確認系統有 uv 需要的執行環境，畫面沒有出現另外安裝的過程
- **新增三個命令別名 `uv`、`uvx`、`uvw`**：winget 以「可攜式套件」安裝，在它自己的捷徑資料夾建立別名

**與預期不同：不用重開 PowerShell 就能用。** 原本預期安裝後要重開視窗才會生效，實際上同一個視窗直接執行 `uv --version` 就成功。推測原因：winget 的捷徑資料夾在這台電腦上早已加入 PATH（先前用 winget 裝過其他可攜式套件），這次只是在裡面新增別名，PATH 本身沒有變。第一次用 winget 裝可攜式套件的電腦，仍需要重開視窗。（推測，未另外查證 PATH 內容）

**截圖：** `m1-uv-install-winget.png`（提示字元中的使用者資料夾名稱已遮蔽）

---

## E34. 稽核摘要：先遮罩再截斷（2026-09-26）

**發現的缺口：** 決策書 M1 要求稽核紀錄存「遮罩摘要（前 50 字）」（D6），但個資遮罩到 M2 才實作。照原本的順序寫，M1 存下來的前 50 字其實是**未遮罩的原文**，等於偷偷存了一部分 prompt，違反 4.2 資料層「不存原文」的原則。

**定案：**
1. **程式從 M1 就寫成 `summary = mask(text)[:50]`**。`mask()` 在 M1 是空殼，M2 補上實作
2. **順序固定為先遮罩、再截斷。** 若反過來先截斷，一支手機號碼剛好被切在第 50 字，只剩一半數字，正規表示式就認不出來，那半支號碼會漏進稽核紀錄
3. **M1 只用自己編的英文測試句，不含任何個資。** 同時避開 PowerShell 5.1 送中文 JSON 的編碼問題（E22）

**已知缺口（誠實記錄）：** M1 期間 `mask()` 不做任何事，稽核摘要的安全性只靠「測試資料不含個資」這個人為約束。M2 補上遮罩實作後，才真正符合 4.2。

**帶到 M2 的待辦：** 加一條 pytest，驗證個資出現在第 50 字前後時，摘要裡不會留下被截斷的殘片。

**面試講法：** 「遮罩和截斷的順序會影響安全性。如果先截斷再遮罩，被切成一半的手機號碼就認不出來，會漏進稽核紀錄。所以我的程式一定是先遮罩、再取前 50 字，而且有測試專門驗證這個邊界。」

**對決策書的影響（v2.7 待改）：** D6 補上「先遮罩再截斷」；8.2 M1 補上 `mask()` 空殼與測試資料的限制。

---

## E35. VS Code 擴充套件盤點（2026-09-28 20:37）

**指令：** `code --list-extensions --show-versions`

**結果：** 共 27 個，分類如下。

| 類別 | 擴充套件 | 發行者 | 本專題需要 |
|---|---|---|---|
| Python | `ms-python.python`、`vscode-pylance`、`debugpy`、`vscode-python-envs` | Microsoft 官方 | ✅ |
| 語言包 | `ms-ceintl.vscode-language-pack-zh-hant` | Microsoft 官方 | 選用 |
| Jupyter | `ms-toolsai.*` × 5 | Microsoft 官方 | ✗ |
| Java | `vscjava.*` × 7（Microsoft 官方）、`redhat.java`、`oracle.oracle-java` | 官方與第三方 | ✗ |
| AI 助手 | `anthropic.claude-code` | Anthropic | ✗（理由見下） |
| 本機網頁伺服器 | `ritwickdey.liveserver@5.7.10` | 第三方 | ✗（有未修補的已知漏洞，見下） |
| 外觀與輔助 | `better-comments`、`vscode-power-mode`、`emoji`、`material-icon-theme`、`material-theme`、`code-spell-checker` | 第三方 | ✗ |
| **容器** | **`ms-azuretools.vscode-containers`（Container Tools）** | Microsoft 官方 | **✅ 缺少** |

**判讀：**
- **缺少 Container Tools**：M1 第 9 步要寫 Dockerfile，需要補裝
- **Live Server 有已知漏洞：** CVE-2025-65717，CVSS 9.1。Live Server 執行中時，若開發者造訪惡意網頁，網頁上的 JavaScript 可以從本機 `localhost:5500` 抓走檔案並送到外部。OX Security 2026/2 公告時標示「所有版本」受影響、維護者未回應、未修補；本機安裝的 5.7.10 是否已修補，未查到資料。本專題的 Demo Console 由 FastAPI 自己提供（7.7），用不到 Live Server
- **AI 助手與 `.env`：** Claude Code 這類 AI 助手可以讀取工作區內的檔案，包含 `.env`。這正是 M1 開工條件「`.env` 不在 VS Code 中開啟（避免 AI 擴充讀取）」要防的情況；另外與「程式碼自己寫」的工作方式（M1 工作方式）衝突
- **附帶觀察（E37 更正）：** 當時推測「`ms-python.python@2026.4.0` 看起來有幾個月沒更新，可能關閉了自動更新」。E37 在新設定檔全新安裝，拿到的同樣是 2026.4.0，代表這就是 Marketplace 上的最新版，**推測錯誤**。舊設定檔真正落後的只有 Pylance（2026.3.1 → 2026.4.1）與 python-envs（1.36.0 → 1.38.0）。教訓：從版本號的日期格式推論「過時」不可靠，要跟實際的最新版比對

**生活比喻：** 擴充套件像住進家裡的房客，每個都能進每個房間。清點之後發現：有幾位是為了別的事（Java、Jupyter）住進來的，有一位房客的門鎖已知有問題（Live Server），還有一位是很能幹、但什麼抽屜都能打開的助理（AI 助手）。

**截圖：** `m1-vscode-extensions-before.png`（使用者資料夾名稱已遮蔽）

**參考來源：**
- [OX Security：CVE-2025-65717 Live Server VS Code Vulnerability](https://www.ox.security/blog/cve-2025-65717-live-server-vscode-vulnerability/)
- [The Hacker News：Critical Flaws Found in Four VS Code Extensions（2026-02-18）](https://thehackernews.com/2026/02/critical-flaws-found-in-four-vs-code.html)
- [GitHub Advisory GHSA-f57j-h7qc-9fq9](https://github.com/advisories/GHSA-f57j-h7qc-9fq9)

---

## E36. 專案專用的 VS Code 設定檔（2026-09-28 20:50）

**問題：** E35 盤點出 27 個擴充套件，其中有已知漏洞的 Live Server、能讀取工作區檔案的 AI 助手，以及與本專題無關的 Java、Jupyter 套件。

**選項：**

| 選項 | 做法 | 評估 |
|---|---|---|
| A | 把不需要的擴充套件全部解除安裝 | 會影響其他課程（Java、Jupyter） |
| B | 在本專題的工作區逐一「停用（工作區）」 | 可行，但 20 多個要逐一操作，之後新裝的套件預設又是啟用 |
| **C（採用）** | 建立專用設定檔 `llm-gateway`，從空白開始，只裝需要的 | 原本的環境完全不受影響；新設定檔預設什麼都沒有，要用才裝（預設拒絕） |

**生活比喻：** 與其把家裡的房客請走，不如給這個專題另外租一間工作室，只搬進工作要用的工具。

**結果：**
- 設定檔 `llm-gateway` 建立完成，齒輪選單顯示「設定檔 (llm-gateway)」
- 已安裝只有 1 個：繁體中文語言包（Microsoft 官方）；「推薦項目」出現 GitLens、SQLTools，**不安裝**
- 規劃中的其他套件：`ms-python.python`（會一併帶入 Pylance、偵錯工具、環境管理）、`ms-azuretools.vscode-containers`
- **不放入：** Claude Code（E35：可讀取 `.env`，且與「程式碼自己寫」衝突；需要檢查程式時直接貼到對話）、Live Server（E35：CVE-2025-65717）

**附帶觀察：**
- 左下角顯示「**受限模式**」：這是 VS Code 的「工作區信任」機制，對還沒標記為信任的資料夾，會限制擴充套件與自動執行的功能。之後打開 `llm-gateway` 資料夾時，只信任這一個資料夾，不信任整個上層目錄
- 齒輪選單有「重新啟動以更新 (1)」：VS Code 有新版本待安裝，先更新再裝擴充套件

**面試講法：** 「開發環境本身也是攻擊面。我盤點 VS Code 擴充套件時發現一個有未修補漏洞的套件，還有能讀取工作區所有檔案的 AI 助手。所以我沒有直接在原本的環境寫專題，而是開一個空白的專用設定檔，只裝需要的三個官方套件。這就是最小權限，套用在開發工具上。」

**截圖：** `m1-vscode-profile-created.png`（無需遮蔽）

---

## E37. 以指令把擴充套件裝進專用設定檔（2026-09-28 21:41）

**指令：**

```
code --profile llm-gateway --install-extension ms-python.python
code --profile llm-gateway --install-extension ms-azuretools.vscode-containers
code --profile llm-gateway --list-extensions --show-versions
```

- 用指令而不是在介面上點選：`--profile llm-gateway` 明確指定裝進哪個設定檔，不會誤裝回原本有 27 個套件的設定檔；指令與輸出也能完整留下紀錄

**安裝過程：**
- 裝 `ms-python.python` 時，自動一併裝入三個相依套件：`vscode-python-envs` v1.38.0、`debugpy` v2026.6.0、`vscode-pylance` v2026.4.1
- `ms-azuretools.vscode-containers` v2.5.2 安裝成功
- 兩次都出現 `[DEP0169] DeprecationWarning: url.parse() ...`：這是 VS Code 命令列工具內部使用的 Node.js 函式被標為「即將淘汰」的提醒，來自 VS Code 本身的程式碼，不是安裝失敗，也不是本專題的程式，不需處理

**最終清單（6 個，全部為 Microsoft 官方發行者）：**

| 擴充套件 | 版本 | 用途 |
|---|---|---|
| `ms-python.python` | 2026.4.0 | Python 支援 |
| `ms-python.vscode-pylance` | 2026.4.1 | 程式碼提示與型別檢查 |
| `ms-python.debugpy` | 2026.6.0 | 偵錯 |
| `ms-python.vscode-python-envs` | 1.38.0 | 虛擬環境管理 |
| `ms-azuretools.vscode-containers` | 2.5.2 | Dockerfile 與容器（第 9 步） |
| `ms-ceintl.vscode-language-pack-zh-hant` | 1.131.2026090407 | 繁體中文介面 |

**對照：** 原本的設定檔 27 個（其中第三方 11 個）→ 專用設定檔 6 個（第三方 0 個）

**截圖：** `m1-vscode-profile-extensions.png`（使用者資料夾名稱已遮蔽）

---

## E38. 專用設定檔關閉內建 AI 功能（2026-09-28 21:46）

**背景：** 新版 VS Code 本體內建 AI 聊天與行內建議；即使專用設定檔沒有裝任何 AI 擴充套件，這些功能仍然存在。

**做法：** 在 `llm-gateway` 設定檔的使用者設定中，把 `chat.disableAIFeatures`（介面名稱「Chat: Disable AI Features」）打勾。設定說明：「停用和隱藏 GitHub Copilot 提供的內建 AI 功能，包括聊天和內嵌建議。」

**為什麼只影響這個設定檔：** 這是使用者層級的設定，而每個非預設的設定檔各自保存一份使用者設定，所以只影響 `llm-gateway`，原本的設定檔不受影響。

**達成的兩件事：**
1. **程式碼自己寫：** 沒有行內建議，寫出來的每一行都是自己打的（M1 工作方式）
2. **縮小 `.env` 被讀取的途徑：** 專用設定檔裡已經沒有任何 AI 功能會讀取工作區檔案。但 E28 的規則不變：確認 `.env` 只看行數、長度、前綴，不打開檔案截圖

**附帶觀察：** 設定頁右上角顯示「上次同步時間：2 個月前」，齒輪選單則顯示「登入以同步設定」（E36 截圖），代表設定同步功能曾經開過、目前沒有登入。維持關閉：開啟後設定與設定檔可能同步到其他登入同一帳號的電腦（E31）。

**限制（誠實記錄）：** 截圖畫面沒有顯示目前是哪個設定檔；依操作順序判斷是在 `llm-gateway` 設定檔中設定的。

**截圖：** `m1-vscode-disable-ai.png`（無需遮蔽）

**步驟 1 狀態：✅ 完成**（Python 3.12.10、uv 0.12.19、Git 2.55.0、VS Code 專用設定檔含 6 個官方擴充套件、內建 AI 功能關閉）

---

## E39. 用專用設定檔打開專題資料夾、確認版本庫狀態（2026-09-28 21:52～21:55）

**指令：**

```
cd ~\llm-gateway
code --profile llm-gateway .
```

**結果：**
- 左下角齒輪顯示 `LL` 標記：目前視窗使用 `llm-gateway` 設定檔
- 左側活動列出現 Container Tools 與 Python 圖示，與 E37 裝的套件一致
- 檔案總管只有 `docs`、`scripts` 兩個資料夾，與交接文件的 repo 結構一致
- 狀態列的「受限模式」（E36）已消失：資料夾已被信任。**信任詢問畫面沒有截到**；改用「管理工作區信任」頁面確認信任範圍（待補）
- `git status`：`fatal: not a git repository (or any of the parent directories): .git` → 專題資料夾還不是 Git 版本庫，上層資料夾也不是

**異常與排查：AI 功能看起來沒關掉**
- 現象：E38 已打勾關閉內建 AI 功能，但這個視窗的標題列仍有聊天圖示、右下角仍有 Copilot 的「登入」
- 兩個可能原因：(1) E38 的設定其實做在預設設定檔（E38 已記錄的限制）；(2) 設定需要重新載入視窗才生效
- 處理：在這個視窗確認設定並執行「重新載入視窗」
- 結果：聊天圖示與 Copilot「登入」都消失（`m1-vscode-ai-hidden.png`），齒輪仍顯示 `LL`
- 教訓：設定改完要**看得到效果**才算完成，不是打勾就算數。跟設防火牆規則一樣，要實際測一次被擋，而不是看規則存在就好

**信任範圍確認（補沒截到的信任詢問畫面）：**
- 「工作區：管理工作區信任」頁面顯示「您信任此資料夾」，工作執行、偵錯工具、工作區設定、延伸模組全部啟用（`m1-workspace-trust-enabled.png`）
- 信任清單中，本專題的項目是 `C:\Users\<使用者>\llm-gateway` 本身，**不是整個使用者資料夾**。清單依路徑排序，使用者資料夾本身若在清單中會排在最前面；實際第一筆是另一個子資料夾，代表使用者資料夾本身沒有被信任（`m1-workspace-trust-list.png`）
- 清單中原本還有十多個過去專案的資料夾（多數在 D 槽）。工作區信任是整台電腦共用的清單，不分設定檔；`m1-workspace-trust-list.png` 只保留前兩列，其餘裁掉
- **本人主動清理（21:58）：** 移除所有過去專案的信任，清單只剩 `C:\Users\<使用者>\llm-gateway` 一筆（`m1-workspace-trust-cleaned.png`）。之後打開那些舊專案會回到受限模式，需要時再逐一信任
- 意義：信任清單等於「哪些資料夾裡的程式可以自動執行」的授權清單。只留正在用的，是最小權限；長期累積、沒人回頭檢查的授權清單，跟沒清理的防火牆規則、離職員工沒停用的帳號是同一類問題

**附帶觀察：** 重新載入後，終端機分頁的 `powershell` 旁出現黃色 ⚠。通常代表擴充套件（例如 Python）變更了終端機的環境變數，要開新的終端機才會套用。處理：關閉舊終端機、開新的（待確認）

**截圖：** `m1-git-status-not-repo.png`、`m1-vscode-ai-hidden.png`（終端機中的使用者資料夾名稱已遮蔽）、`m1-workspace-trust-enabled.png`（無需遮蔽）、`m1-workspace-trust-list.png`（只保留前兩列，使用者資料夾名稱與無關路徑已遮蔽）、`m1-workspace-trust-cleaned.png`（使用者資料夾名稱已遮蔽）

---

## E40. `uv init` 建立專案骨架（2026-09-28 22:01～22:05）

**指令與結果：**

```
> uv init --python 3.12
Initialized project `llm-gateway`

> git status
On branch master

No commits yet

Untracked files:
        .gitignore
        .python-version
        README.md
        docs/
        pyproject.toml
        scripts/
        src/
```

**判讀：**
- `uv init` 同時建立了 Git 版本庫（`git status` 不再回 `not a git repository`）
- 尚未執行任何 `git add`，所有檔案都是 Untracked：在確認 `.env` 被擋住之前，不把任何東西交給 Git

**與預期不同的兩點：**
1. **建立的是 `src/` 而不是 `main.py`。** 原本預期 uv 會建立單一範例檔 `main.py`；uv 0.12.19 實際產生 `src/` 資料夾。決策書 D22 的結構是根目錄下的 `app/`，兩者不同，待檢查 `pyproject.toml` 與 `src/` 內容後決定採用哪一種
2. **預設分支叫 `master`。** GitHub 新建 repo 的預設分支是 `main`，D21 的「`main` 分支要求 CI 通過才能合併」也是寫 `main`。本機的 Git 沒有設定預設分支名稱，所以用了舊的預設值 `master`

**確認結果（22:05）：**

```
> git check-ignore -v .\scripts\litellm-lab\.env
scripts/litellm-lab/.gitignore:1:.env   ".\\scripts\\litellm-lab\\.env"

> tree /f src
└─llm_gateway
        __init__.py

> git branch -m main
（無輸出 = 成功）
```

- **`.env` 有被擋住**：規則來自 `scripts/litellm-lab/.gitignore` 第 1 行（M0.5 建立）。Git 會讀取每一層資料夾的 `.gitignore`，子資料夾的規則只管自己底下的檔案
- **但根目錄的 `.gitignore`（uv 產生）沒有 `.env` 規則**：M1 會在根目錄建立 `.env`（HMAC 金鑰、OpenAI 金鑰），在那之前必須先把 `.env` 加進根目錄的 `.gitignore`
- **分支已改名為 `main`**：還沒有任何 commit，改名不影響任何紀錄
- `pyproject.toml` 內容見 E41、E42

**截圖：** `m1-uv-init-git-status.png`、`m1-gitignore-pyproject-src.png`（使用者資料夾名稱、Email、磁碟區序號已遮蔽）

---

## E41. `uv init` 把個人 Email 寫進 `pyproject.toml`（2026-09-28 22:05）

**發現：** `uv init` 自動產生的 `pyproject.toml` 含有：

```toml
authors = [
    { name = "Terry", email = "<個人 Gmail>" }
]
```

uv 讀取了本機 Git 設定中的 `user.email`，自動填進作者欄位。

**為什麼是問題：**
- D21 定案 repo **公開**。這個檔案一推上 GitHub，個人 Email 就公開在網路上，會被爬蟲收集，成為垃圾信與釣魚信的目標
- 同一個 `user.email` 也會寫進**每一筆 commit**。就算把 `pyproject.toml` 的 Email 刪掉，commit 紀錄一樣會洩漏；而且 commit 一旦推上去，事後要清除非常麻煩
- 性質跟 E21 的「不安全預設值」相同：工具為了方便自動帶入資料，沒有提醒使用者這些資料會被公開

**處理方式：**
1. ✅（9/29）`pyproject.toml` 的作者欄位只留名字，刪除 Email（E43）
2. ✅（9/29）在 GitHub 的 Email 設定開啟「Keep my email addresses private」與「Block command line pushes that expose my email」，取得 GitHub 提供的 noreply 地址（E44）
3. ✅（9/29）**在第一次 commit 之前**，把 `user.email` 設成 noreply 地址（E44；最後決定設在整台電腦，而非只有這個 repo）

**截圖處理：** `m1-gitignore-pyproject-src.png` 中的 Email 已遮蔽

**面試講法：** 「初始化專案時，工具自動把我的 Git Email 填進設定檔。repo 要公開，所以我在第一次 commit 之前就改用 GitHub 的 noreply 地址，並開啟 GitHub 的推送保護，擋下任何含真實 Email 的 commit。個資外洩最容易發生在這種沒人注意的自動化預設值裡。」

---

## E42. 專案結構：維持 D22 的 `app/`，不採用 uv 預設的 `src/`（2026-09-28 22:05 建議，9/29 採用）

**uv 0.12.19 的預設：** 「可打包」的專案結構：`src/llm_gateway/__init__.py`，`pyproject.toml` 含 `[project.scripts]`（命令列入口）與 `[build-system]`（`uv_build`）。

| 選項 | 做法 | 評估 |
|---|---|---|
| **A（建議）：維持 D22** | 根目錄 `app/`；刪除 `src/`、`[project.scripts]`、`[build-system]` | 本專題是部署成容器的服務，不是要發佈到 PyPI 的套件，不需要打包；FastAPI 官方文件慣用 `app/`；Dockerfile 較單純；新手要理解的概念少一層 |
| B：採用 `src/` | 程式放 `src/llm_gateway/`，專案本身安裝進虛擬環境 | 是發佈套件的最佳實務：測試一定針對「安裝後的樣子」，能抓到打包漏檔。但本專題不發佈套件，這個好處用不到；還要改 D22 與決策書的路徑 |

**A 的代價（誠實記錄）：** 專案不安裝進虛擬環境，pytest 找不到 `app` 模組，需要在 `pyproject.toml` 設定 `pythonpath`（步驟 4 處理）。

**生活比喻：** `src/` 結構像是為了「上架販售」準備的包裝（外盒、條碼、說明書）；本專題是自家餐廳的菜，直接端上桌，不需要超市的包裝。

---

## E43. 改回 D22 結構並建立虛擬環境（2026-09-29 14:21）

**本人採用 E42 的選項 A。** 修改 `pyproject.toml`（本人在 VS Code 編輯）並刪除 `src/`：

```
> rm -r src
> git config --global init.defaultBranch main
> gc pyproject.toml
[project]
name = "llm-gateway"
version = "0.1.0"
description = "Enterprise LLM Gateway with cost governance"
readme = "README.md"
authors = [
    { name = "Terry" }
]
requires-python = ">=3.12"
dependencies = []

> uv sync
Using CPython 3.12.10 interpreter at: C:\Users\<使用者>\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
Creating virtual environment at: .venv
Resolved 1 package in 26ms
Checked in 0.02ms
```

**判讀：**
- `pyproject.toml` 只剩 `[project]` 一段：作者欄位沒有 Email（E41）、沒有 `[project.scripts]` 與 `[build-system]`
- `uv sync` 沒有出現 `Built llm-gateway`、也沒有安裝專案本身：uv 判定這是**不打包**的專案，符合 E42 選項 A。`Resolved 1 package` 指的是專案本身，目前沒有任何相依套件
- 建立 `.venv`（專案專用的虛擬環境）；`uv.lock` 此時內容只有專案本身
- `git config --global init.defaultBranch main`：修正本機預設值，以後新建的版本庫都用 `main`（E40 的 `master` 問題從源頭解決）

**附帶觀察：使用的是 Microsoft Store 版 Python。** 路徑在 `WindowsApps\PythonSoftwareFoundation.Python.3.12_...`。可以正常建立虛擬環境；Store 版會把寫入 AppData 的動作導向私有位置，少數工具可能因此找不到檔案。目前沒有影響，記錄備查；若之後出現路徑相關的怪問題，改用 `uv python install 3.12` 取得 uv 管理的獨立版本

**截圖：** `m1-uv-sync.png`（使用者資料夾名稱已遮蔽）

---

## E44. 第一次 commit 前的兩道防線（2026-09-29 14:57）

### 防線 1：Email 改用 GitHub noreply 地址

**GitHub 設定（Settings → Emails）：**
- 「Keep my email addresses private」：On。GitHub 在網頁上的操作改用 noreply 地址，個人資料頁不再顯示真實 Email
- 「Block command line pushes that expose my email」：On。推送時檢查最新一筆 commit，作者 Email 若是帳號的私人 Email，直接擋下
- GitHub 頁面也寫明：「Previously authored commits associated with a public email will remain public.」→ 已經推上去的 commit 救不回來，所以這一步必須在第一次 commit **之前**做

**本機 Git：**

```
> git config --global user.email "<GitHub noreply 地址>"
> git config --global user.email
<GitHub noreply 地址>
```

- 用 `--global`（整台電腦）而不是只設這個 repo：這台是個人電腦，之後的公開專案一樣會遇到。E41 的問題出在預設值，所以直接修正預設值
- noreply 地址格式為「數字 ID + GitHub 帳號 @users.noreply.github.com」，本來就會出現在每一筆公開的 commit 中；截圖仍一律遮蔽，與 11.5 遮蔽個人帳號名稱的規則一致

**兩道開關的關係：** 本機設定是「主動不帶真實 Email」，GitHub 的推送封鎖是「萬一忘了，伺服器端擋下來」。同樣是縱深防禦：一層在自己手上，一層在對方門口

### 防線 2：根目錄 `.gitignore` 加入 `.env`

本人在 VS Code 於 `.gitignore` 最後加入：

```
# Secrets
.env
.env.*
!.env.example
```

**驗證：**

```
> git check-ignore -v .env
.gitignore:13:.env       .env

> git check-ignore -v .env.example
.gitignore:15:!.env.example      .env.example
```

- `.env`：被第 13 行擋住 ✅
- `.env.example`：命中的是第 15 行的 **`!`（例外放行）規則**，代表**不會**被擋 ✅
- **與預期不同：** 原本說第二行「什麼都沒印」才代表放行。實際上加了 `-v`（顯示詳細資訊）後，Git 會把「最後命中的規則」印出來，包括 `!` 開頭的例外規則。判讀的重點是規則開頭有沒有 `!`，不是有沒有輸出。原本的說法不精確
- 根目錄還沒有 `.env` 也能檢查：`check-ignore` 檢查的是「這個路徑如果存在，會不會被擋」，不需要檔案真的存在

**截圖：** `m1-github-email-private.png`、`m1-git-email-gitignore.png`（noreply 地址與使用者資料夾名稱已遮蔽）

---

## E45. 建立 `app/` 與第一次 commit 前總檢查（2026-09-29 15:02～15:15）

**指令：** `mkdir app`、`ni app\__init__.py`（0 bytes 的空檔案，標示 `app` 是 Python 模組）；`tests/` 留到步驟 4 再建（Git 不記錄空資料夾）

**`git status -uall` 清單（共 86 個檔案）檢查結果：**

| 檢查項目 | 結果 |
|---|---|
| 任何 `.env` | ✅ 不在清單中 |
| `.venv/` | ✅ 不在清單中（uv 產生的 `.gitignore` 已排除） |
| `uv.lock` | ✅ 在清單中，應該 commit（D18：鎖定版本與雜湊） |
| `scripts/litellm-lab/` | 7 個檔案，含 `env.example`（範本檔，檔名沒有開頭的點）；待確認裡面只有欄位名稱、沒有值 |
| `docs/screenshots/` | 已存的都是遮蔽版；**尚未存入**：`m1-workspace-trust-enabled.png`、`m1-workspace-trust-list.png`、`m1-github-email-private.png`、`m1-git-email-gitignore.png`、`m0-openai-key-list-inherited.png`（E21 列出但不在清單中） |
| 中文檔名 | 顯示成 `\346\212\200...` 這類八進位碼：Git 預設把非英文字元轉成跳脫碼顯示（`core.quotepath`），不是檔案壞掉 |

**內容掃描（repo 將公開，D21；15:06）：**

```
> git config --global core.quotepath false
> gci -r docs,scripts -File | sls "sk-[\w-]{20,}" -List | % Path
C:\Users\<使用者>\llm-gateway\scripts\litellm-lab\.env
> gci -r docs,scripts -File -Include *.md,*.log,*.yml | sls "環隆|UMEC|<使用者>" -List | % Path
（11 個 docs\logs\*.log 檔案）
> (sls "=\S" scripts\litellm-lab\env.example).Count
4
```

- 掃描指令只印檔名（`-List | % Path`），**就算命中，金鑰內容也不會出現在畫面上**。同 E17 的原則：驗證的過程本身不能洩漏要保護的東西
- **金鑰：** 只有 `scripts/litellm-lab/.env` 命中，它已被 `.gitignore` 擋住（E40），不會進 Git ✅。這一行也證明掃描有效：真的有金鑰的檔案抓得到（正向對照）
- **使用者名稱：** 11 個日誌檔含本機使用者名稱（推測是終端機提示字元與路徑）。M0～M0.5 截圖都有遮蔽，但文字日誌漏了，公開前需要處理
- **公司名稱：** 沒有 `.md` 檔命中。但 Windows PowerShell 5.1 讀取沒有 BOM 的 UTF-8 檔案時，中文比對可能失效，所以「沒命中」不代表「沒有」，需要直接查看決策書 v2 的開頭確認
- **`env.example`：** 有 4 行等號後面有值。可能是非機密的預設值（例如資料庫名稱），也可能是真的密鑰，需要確認
- **`core.quotepath false`：** 讓 Git 直接顯示中文檔名

**截圖：** `m1-precommit-scan.png`（使用者資料夾名稱已遮蔽）

**追查結果（15:13）：**

| 項目 | 指令 | 結果 | 判讀 |
|---|---|---|---|
| `env.example` 有無真實密鑰 | `(sls "[0-9a-f]{32}" ...).Count` | 0 | M0.5 的真實密鑰都是 32 碼十六進位（E14、E28），範本中沒有 ✅ |
| 有值的 4 行是什麼 | 只印欄位名稱 | 1 行註解（產生 `.env` 的指令說明）＋ `LITELLM_MASTER_KEY`、`LITELLM_SALT_KEY`、`POSTGRES_PASSWORD` | 三個欄位的值不是 32 碼十六進位，也不符合 `sk-` 加 20 碼以上的格式 → 判定為佔位字 ✅ |
| 日誌中的使用者名稱 | `sls ... \| % Line \| sort -Unique` | 全部出現在終端機提示字元 `PS C:\Users\<使用者>\...` 與兩行含完整路徑的指令（`cd`、`notepad`） | 沒有 Email 或其他個資，只需把路徑中的使用者名稱換掉 |
| 決策書 v2 開頭 | `gc ...-v2.md -TotalCount 20` | 標題為「LLM Gateway 技術決策書 v2.0」，直接從 PART 1 開始 | **沒有**「協作約定」與個人背景 |

**更正：** 原本擔心 repo 裡的決策書 v2 含現職公司名稱。實際上含有「協作約定」與個人背景的，是 claude.ai Project 的專案說明（另一份文件），不在 repo 裡。仍以明確指定 UTF-8 的方式再掃一次中文關鍵字，排除 PowerShell 5.1 編碼造成的漏判

**日誌中的使用者名稱處理方式：** 只把 `\Users\<使用者>` 換成 `\Users\<user>`，其餘內容不動。與截圖遮蔽同一原則：遮蔽個人資訊，不改實驗內容

**處理與複查（15:15）：**

```
> gci docs\logs\*.log | % { $t = [IO.File]::ReadAllText($_.FullName); [IO.File]::WriteAllText($_.FullName, $t.Replace('\Users\<使用者>', '\Users\<user>')) }
> (gci -r docs,scripts -File -Include *.md,*.log,*.yml | sls "<使用者>" -List).Count
0
> gci -r docs -Include *.md | sls "技術決策書","環隆","環科" -Encoding utf8 | group Pattern -NoElement
Count Name
----- ----
    6 技術決策書
```

- 日誌中的使用者名稱已全部替換，複查為 0 ✅
- **對照組有效：** 「技術決策書」命中 6 行，證明這次指定 UTF-8 後中文比對確實有作用
- 「環隆」「環科」**沒有出現在結果中** → repo 內的 `.md` 檔沒有現職公司名稱 ✅
- 教訓：「沒找到」要搭配「確定找得到」的對照組才有意義。與 E15 用 `http://github.com` 當控制檢查、金鑰掃描以 `.env` 當正向對照是同一個方法

**截圖：** `m1-precommit-scan-fixed.png`（使用者資料夾名稱已遮蔽）

**總檢查結論：** 金鑰、`.env`、`.venv`、使用者名稱、公司名稱全部排除，可以進行第一次 commit

---

## E46. 第一次 commit（2026-09-29 15:20）

**指令與結果：**

```
> git add .
warning: in the working copy of '.gitignore', LF will be replaced by CRLF the next time Git touches it
（共 34 行同類警告）

> git diff --cached --name-only | sls "\.env$"
（無輸出）

> git commit -m "chore: initialize project skeleton"
[main (root-commit) 59c33f5] chore: initialize project skeleton
 90 files changed, 8867 insertions(+)

> git log --format="%an <%ae> | %s"
Terry <GitHub noreply 地址> | chore: initialize project skeleton
```

**判讀：**
- **封箱前最後檢查：** 暫存區的檔名清單中沒有任何以 `.env` 結尾的檔案 ✅
- **第一筆 commit `59c33f5`**，分支為 `main`（E40 的改名生效），共 90 個檔案
- **作者 Email 是 noreply 地址** ✅：E41 的問題在第一筆 commit 就沒有發生。repo 公開後，commit 歷史中不會出現個人 Email
- **commit 訊息格式：** 採用 Conventional Commits（`chore:` 雜務、`feat:` 新功能、`fix:` 修錯、`docs:` 文件），之後看歷史就能分類
- `docs/screenshots/` 中沒有 `m1-workspace-trust-enabled.png`、`m1-workspace-trust-list.png`：後者已被 `m1-workspace-trust-cleaned.png` 取代，前者可之後補進；`m0-openai-key-list-inherited.png` 仍缺（E21 列出）

**換行符號警告（LF / CRLF）：**
- 每一行文字結尾都有一個看不見的「換行符號」。Linux 與 macOS 用 LF（一個字元），Windows 慣用 CRLF（兩個字元）
- Git for Windows 預設開啟 `core.autocrlf=true`：存進版本庫時統一成 LF，但下次從版本庫取出檔案時，會在 Windows 工作資料夾中轉成 CRLF。警告就是在說這件事，**目前不影響任何內容**
- 為什麼仍要處理：本專題的程式會跑在 Linux 容器（M1 第 9 步）、Lambda 與 GitHub Actions 上。含 CRLF 的 shell 腳本在 Linux 會出錯（例如 `/bin/sh^M: bad interpreter`）。現在只有文件與設定檔，是處理的最好時機
- 處理方式見 E47

**截圖：** `m1-first-commit.png`（使用者資料夾名稱與 noreply 地址已遮蔽）

---

## E47. `.gitattributes` 統一換行符號為 LF（2026-09-29 15:26～15:30）

**做法：** 本人在 VS Code 於根目錄新增 `.gitattributes`：

```
* text=auto eol=lf
*.png binary
```

- 第一行：所有 Git 判定為文字的檔案，工作資料夾中也一律用 LF
- 第二行：`.png` 視為二進位檔，Git 不轉換換行、不做文字比對，避免圖片被當成文字「修正」而損壞
- **為什麼用 `.gitattributes` 而不是改電腦的 `core.autocrlf`：** 規則跟著 repo 走，GitHub Actions 與任何人下載 repo 都自動套用；改電腦設定只對這台電腦有效

**指令與結果：**

```
> git add --renormalize
Nothing specified, nothing added.
hint: Maybe you wanted to say 'git add .'?

> git add --renormalize .
（無輸出）

> git add .gitattributes
warning: in the working copy of '.gitattributes', CRLF will be replaced by LF the next time Git touches it

> git status
Changes to be committed:
        new file:   .gitattributes
```

**判讀：**
- **小挫折：** 第一次少打了最後的 `.`（代表「目前資料夾全部」），Git 回「Nothing specified」並提示可能要加 `.`。補上後正常執行
- `--renormalize .` 沒有產生任何變更：E46 存進版本庫的檔案本來就是 LF，與預期相同 ✅
- `git status` 只有 `.gitattributes` 一個新檔案 ✅
- **新發現：** `.gitattributes` 本身是用 CRLF 存的。VS Code 在 Windows 上新建檔案預設用 CRLF（設定 `files.eol` 為 `auto`）。Git 存進版本庫時會轉成 LF，內容不受影響；但之後在 VS Code 新增的每個檔案都會是 CRLF，所以把 `llm-gateway` 設定檔的 `files.eol` 改為 `\n`，從來源統一

**VS Code 設定與 commit（15:30）：**
- `llm-gateway` 設定檔的「Files: Eol」改為 `\n`（LF）。設定名稱旁顯示「（也在其他地方修改）」，代表同一個設定在其他範圍（例如工作區）也有值；repo 內目前沒有 `.vscode/` 資料夾，待確認是哪裡
- commit：

```
> git commit -m "chore: enforce LF line ending"
[main 858b6a6] chore: enforce LF line ending
 1 file changed, 2 insertions(+)
 create mode 100644 .gitattributes

> git log --oneline
858b6a6 (HEAD -> main) chore: enforce LF line ending
59c33f5 chore: initialize project skeleton
```

- 兩筆 commit，第二筆只有 `.gitattributes` 一個檔案 ✅

**截圖：** `m1-gitattributes-lf.png`、`m1-commit-gitattributes.png`（使用者資料夾名稱與 noreply 地址已遮蔽）、`m1-vscode-files-eol-lf.png`（無需遮蔽）

**步驟 2 狀態：✅ 完成**（`uv init`、D22 結構、`.venv`、兩道 commit 前防線、總檢查、兩筆 commit）

---

## E48. 建立 GitHub repo 並先開安全功能（2026-09-29 15:34～15:37）

**原則：先裝防線，再推程式。** 秘密掃描與推送保護對個人免費帳號只在**公開** repo 提供（私人 repo 需付費的 GitHub Advanced Security）。D21 定案公開，除了作品集，也是為了取得這兩道免費防線

**建立方式：** 新建 `Poyu-Tu/llm-gateway`，Public，**不勾選** README、`.gitignore`、license。本機已有這些檔案，GitHub 端若也建立，兩邊歷史不同源，第一次推送會被拒絕

**介面判讀：** 按鈕顯示的是「可以執行的動作」，不是目前狀態。按鈕寫「Disable」＝目前**開啟**

**Settings → Advanced Security 最終狀態：**

| 項目 | 狀態 | 說明 |
|---|---|---|
| Private vulnerability reporting | ✅ 開啟（本人手動開啟） | 發現漏洞的人可以私下回報，不必在公開 issue 寫出來 |
| Dependency graph | ✅ 開啟（預設） | 列出專案使用的套件 |
| Automatic dependency submission | 關閉 | 建置時自動偵測相依套件；本專題有 `uv.lock`，不需要 |
| Dependabot alerts | ✅ 開啟（預設） | 套件有已知漏洞時通知 |
| Dependabot malware alerts | ✅ 開啟（本人於 15:40 手動開啟） | 相依套件被偵測為惡意程式時通知。10.3 第 3 點的 litellm 1.82.7、1.82.8 被植入竊取憑證程式，正是這類情況 |
| Dependabot security updates | ✅ 開啟 | 有修補版本時自動發 PR |
| Grouped security updates | 關閉 | 把多個修補合成一個 PR；專案小，暫不需要 |
| Dependabot version updates | 關閉 | 需要 `dependabot.yml`；D19 採鎖版本策略，一般版本更新的 PR 會製造雜訊，M6 建 CI 時再評估 |
| CodeQL analysis | 未設定 | 程式碼靜態掃描。repo 目前沒有程式碼，等有 Python 程式後再評估（公開 repo 免費） |
| AI Scan for pull requests | 關閉 | 預覽功能，不使用 |
| Copilot Autofix | 開啟（預設） | 需搭配 CodeQL 才有作用，目前無效果；與「程式碼自己寫」原則有關，CodeQL 定案時一併決定 |
| **Secret Protection** | ✅ **開啟** | 掃描 repo 中的金鑰；公開 repo 偵測到的金鑰也會通知該服務商（例如 OpenAI）讓對方撤銷 |
| **Push protection** | ✅ **開啟** | 推送時發現支援格式的金鑰，直接擋下 |

**截圖：** `m1-github-advanced-security-1.png`（大頭貼已遮蔽）、`m1-github-advanced-security-2.png`、`m1-github-advanced-security-3.png`、`m1-github-malware-alerts.png`（無需遮蔽）

**截圖處理的失誤：** 第一次遮蔽大頭貼時，以畫面顯示的尺寸估算座標，但原始截圖解析度約為 1.4 倍，灰色方塊畫在錯的位置、沒有遮到，就回傳了。發現後重新遮蔽並回傳更正版。之後遮蔽一律以原始解析度計算，並放大確認後再回傳

---

## E49. 第一次推送到 GitHub（2026-09-29 15:44）

**指令與結果：**

```
> git add docs
> git status
Changes to be committed:
        modified:   docs/evidence/m1-evidence-log.md
        new file:   docs/screenshots/（8 張 M1 截圖）

> git commit -m "docs: update M1 evidence log and screenshots"
[main c9b093b] docs: update M1 evidence log and screenshots
 9 files changed, 129 insertions(+)

> git remove add origin https://github.com/Poyu-Tu/llm-gateway.git
git: 'remove' is not a git command. See 'git --help'.
The most similar command is
        remote

> git remote add origin https://github.com/Poyu-Tu/llm-gateway.git
> git push -u origin main
Enumerating objects: 117, done.
Writing objects: 100% (117/117), 6.48 MiB | 3.25 MiB/s, done.
To https://github.com/Poyu-Tu/llm-gateway.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

**判讀：**
- `git add docs` 只加入 `docs/` 底下的檔案，`git status` 確認只有證據紀錄與 8 張截圖 ✅
- **小挫折：** `remote` 打成 `remove`，Git 回報不是指令，並建議最接近的 `remote`。重打後成功
- **推送成功**：117 個物件、6.48 MiB（大部分是截圖），本機 `main` 與 GitHub 的 `origin/main` 建立追蹤關係，之後只需 `git push`
- **推送保護沒有擋下任何東西**：與 E45 的本機掃描結果一致，三筆 commit 中沒有 GitHub 支援格式的金鑰
- **沒有跳出登入視窗**：Git Credential Manager 使用了先前（其他專案）已存在 Windows 認證管理員中的 GitHub 憑證

**GitHub 上的 commit 歷史（3 筆）：**

| commit | 訊息 |
|---|---|
| `59c33f5` | chore: initialize project skeleton |
| `858b6a6` | chore: enforce LF line ending |
| `c9b093b` | docs: update M1 evidence log and screenshots |

**截圖：** `m1-first-push.png`（使用者資料夾名稱已遮蔽）

---

## E50. 保護 `main` 分支的規則集與實測（2026-09-29 15:49～15:54）

**要防的兩種操作：**

| 操作 | 生活比喻 | 後果 |
|---|---|---|
| 強制推送（force push） | 撕掉帳本的幾頁，重寫一份蓋上去 | 歷史被竄改，舊紀錄消失 |
| 刪除分支 | 整本帳本丟進碎紙機 | 全部歷史消失 |

**設定（Settings → Rules → Rulesets → New branch ruleset）：**
- Ruleset Name：`protect-main`
- Enforcement status：**Active**
- Bypass list：**空白**（連 repo 擁有者本人也不能例外；只防別人不防自己的規則，等於沒有保護）
- Target branches：**Default**（預設分支，即 `main`）
- Rules：Restrict deletions、Block force pushes（本人確認已勾選；Rules 區塊的畫面沒有截到，以下方的實測結果作為證據）

**刻意先不加的規則：** D21 的「`main` 要求 CI 通過才能合併」。CI 尚未建立，現在加上會讓每次推送都卡住；10/12 那週建好 CI（pytest、tfsec、Trivy）後回來補上（已列入待決）

**截圖：** `m1-github-ruleset.png`（大頭貼已遮蔽）

**實測前的安全檢查（15:51）：**
- 測試會用到 `git reset --hard`，事先約定：`git status` 不是 `working tree clean` 就先停下來
- 結果：沒有 `working tree clean`，只有兩張未追蹤的截圖（`m1-first-push.png`、`m1-github-ruleset.png`）。本人**依約定停下來回報**，沒有繼續執行
- 判讀：`git reset --hard` 只會丟掉「**已追蹤檔案**的未 commit 修改」，不會刪除**未追蹤**的檔案（刪除未追蹤檔案是 `git clean` 的工作）。所以兩張截圖不受影響，可以繼續
- 原本的約定比實際需要更嚴格。對會刪資料的指令，寧可條件設嚴、停下來確認，也不要讓人在不確定時繼續執行

**截圖：** `m1-ruleset-test-precheck.png`（使用者資料夾名稱已遮蔽）

**實測：故意強制推送（15:54）**

```
> git commit --amend --no-edit
[main c7101fa] docs: update M1 evidence log and screenshots
 Date: Tue Sep 29 15:42:17 2026 +0800

> git push --force
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - Cannot force-push to this branch
 ! [remote rejected] main -> main (push declined due to repository rule violations)
error: failed to push some refs to 'https://github.com/Poyu-Tu/llm-gateway.git'

> git reset --hard origin/main
HEAD is now at c9b093b docs: update M1 evidence log and screenshots

> git log --oneline -1
c9b093b (HEAD -> main, origin/main) docs: update M1 evidence log and screenshots
```

**判讀：**
- `--amend --no-edit` 只重新封裝最後一筆 commit：內容與訊息不變，編號從 `c9b093b` 變成 `c7101fa`（原始作者時間 `15:42:17` 保留）。本機歷史因此與 GitHub 分岔
- `git push --force` 被 GitHub 拒絕：**`GH013` + `Cannot force-push to this branch`** ✅。規則集確實生效，而且 bypass 清單為空，repo 擁有者本人也被擋下
- 被拒絕之前，物件其實已經上傳（`Writing objects: 100%`）；拒絕發生在最後「更新分支指標」那一步。GitHub 收下了包裹，但不准它換掉帳本
- `reset --hard origin/main` 讓本機回到與 GitHub 相同的 `c9b093b`；兩張未追蹤的截圖不受影響
- 刪除分支的規則未實測：`main` 是預設分支，GitHub 本來就不允許刪除預設分支，即使實測被擋，也分不出是規則集還是預設行為擋的

**面試講法：** 「分支保護我不是設好就算了。我故意對 `main` 做一次強制推送，確認 GitHub 回 GH013 拒絕，而且我自己也不在例外名單裡。規則要看到它真的擋下來，才算數。」

**截圖：** `m1-force-push-blocked.png`（使用者資料夾名稱已遮蔽）

**收尾推送（15:58）：** `git commit -m "docs: record GitHub setup and ruleset test"` → `570792c`（5 個檔案），`git push` 成功；第一次推送時用了 `-u`，這次只需 `git push`（`m1-push-docs.png`）

**步驟 3 狀態：✅ 完成**（公開 repo、Advanced Security 各項防線、noreply Email、第一次推送、`main` 規則集與實測）

---

## E51. 冷卻期與安裝第一批套件（2026-09-30 18:41）

**冷卻期設定：** 本人在 `pyproject.toml` 加上

```toml
[tool.uv]
exclude-newer = "2026-09-27T00:00:00Z"
```

- 把 D27「上架滿 3 天」的冷卻期規則，從 LiteLLM 映像擴大到**所有 Python 套件**。起因是 10.3 第 3 點：litellm 1.82.7、1.82.8 在 PyPI 上架數小時內就被下載，裡面藏有竊取憑證的程式
- 日期寫死而非自動滾動：每次放寬都要手動改日期並 commit，版本變更可以追查，與 D30「單價放 repo，變更 = 經過審查的版本變更」同一個思路

**指令與結果：**

```
> uv add fastapi uvicorn
Resolving despite existing lockfile due to addition of global exclude newer 2026-09-27T00:00:00Z
Resolved 14 packages / Installed 13 packages
 + fastapi==0.141.1  + starlette==1.7.0  + pydantic==2.13.5  + pydantic-core==2.46.5
 + uvicorn==0.54.0   + h11==0.16.0       + click==8.5.0      + anyio==4.15.1
 + idna==3.20        + annotated-doc==0.0.5  + annotated-types==0.8.0
 + typing-extensions==4.16.0  + typing-inspection==0.4.4

> uv add --dev pytest httpx
Resolved 23 packages / Installed 9 packages
 + pytest==9.1.1  + pluggy==1.6.0  + iniconfig==2.3.0  + packaging==26.3  + pygments==2.21.0  + colorama==0.4.6
 + httpx==0.28.1  + httpcore==1.0.9  + certifi==2026.7.22
```

**判讀：**
- 第一行「Resolving despite existing lockfile due to addition of global exclude newer」：uv 發現冷卻期設定變了，重新計算所有版本，代表設定有被讀到 ✅
- **正式執行只有 13 個套件**：要求的只有 2 個，其餘 11 個是它們的相依套件（FastAPI 靠 Starlette 處理網路請求、靠 Pydantic 檢查資料格式；uvicorn 靠 h11 處理 HTTP、靠 click 提供命令列）
- 刻意裝 `uvicorn` 而不是 `uvicorn[standard]`、`fastapi` 而不是 `fastapi[standard]`：後兩者會多帶進十幾個套件（檔案監看、模板引擎、Email 驗證等）。多一個套件就多一個可能出事的供應鏈，要用到再加
- **開發用的 9 個套件**放在 `[dependency-groups] dev`，與 `dependencies` 分開：建容器時不裝，正式環境看不到測試工具 ✅
- `colorama` 是 pytest 在 Windows 上顯示顏色用的

**`pyproject.toml` 與 `uv.lock` 的分工：**

| 檔案 | 寫的是什麼 | 生活比喻 |
|---|---|---|
| `pyproject.toml` | `fastapi>=0.141.1`：最低需求 | 採購單：「至少要這個版本以上」 |
| `uv.lock` | 每個套件的**確切版本 + SHA-256 雜湊** | 驗收單：「這一箱的批號與封條編號」 |

建容器或 CI 時照 `uv.lock` 安裝，每次拿到的一定是同一批檔案；雜湊對不上就拒絕安裝（D18）

**截圖：** `m1-uv-add-deps.png`、`m1-pyproject-deps.png`（使用者資料夾名稱已遮蔽）

---

## E52. 第一支程式 `app/main.py` 的第一版與檢查（2026-09-30 18:51）

**本人撰寫的第一版：**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("GET /health")
def healthCheck():
    return {"status": "ok"}
```

**檢查結果：**

| 項目 | 結果 |
|---|---|
| 匯入 `FastAPI`、建立名為 `app` 的物件 | ✅ |
| 裝飾器放在函式正上方、`return` 縮排 4 格 | ✅ |
| 回應只有 `{"status": "ok"}`，沒有版本號等多餘資訊（資安要求） | ✅ |
| **路徑寫成 `"GET /health"`** | ❌ HTTP 方法已經由 `.get` 表示，括號裡只放路徑 `"/health"`。照原本寫法，`/health` 這個網址不會對應到這個函式 |
| 函式名稱 `healthCheck` | ⚠️ 可以執行，但 Python 慣例（PEP 8）是小寫加底線 `health_check`。FastAPI 也會用函式名稱產生 API 文件中的識別名稱 |
| 空行 | ⚠️ PEP 8 建議最上層的函式（含裝飾器）前面空兩行；之後在 CI 加入格式檢查工具自動處理 |

**第二版（18:53）：** 路徑改為 `"/health"`、函式改名 `health_check`、裝飾器前空兩行 → 全部正確 ✅

**註解的原則（本人提問）：**
- `#` 註解寫「**為什麼**」，不寫「做了什麼」（程式本身已經說明做了什麼）
- 函式下方的 `"""..."""` 是 docstring，說明這個函式的用途；FastAPI 會把它顯示在自動文件頁 `/docs`
- 因為 `/docs` 預設公開，docstring 裡不能寫內部資訊（網址、帳號、架構細節）
- 公開作品集的註解建議用英文：業界慣例，也避免編碼問題

**第三版（19:03，加上註解）：** 檔案最上方加 docstring `LLM Gateway API service.`；`health_check` 加上多行 docstring，說明給負載平衡器使用、刻意只回傳 status 的資安理由。英文由 Claude 提供建議句與單字表，內容與結構由本人決定並自行輸入。可執行；另建議去掉 `!` 與 `...`、刪除空行上的多餘空白，讓句子完整

**觀念：** `@app.get("/health")` 拆開看，`get` 是「用什麼方法來」，`"/health"` 是「來哪個地址」。生活比喻：「外帶（方法）」和「3 號窗口（地址）」是兩件事，窗口的牌子上只寫「3 號」，不會寫「外帶 3 號」

---

## E53. 用 uvicorn 啟動服務並以瀏覽器驗證（2026-09-30 19:10）

**指令：** `uv run uvicorn app.main:app --reload`

| 片段 | 意思 |
|---|---|
| `uv run` | 在專案的 `.venv` 中執行，不需手動啟用虛擬環境 |
| `app.main:app` | 「資料夾.檔案:變數」：`app/main.py` 裡名為 `app` 的物件 |
| `--reload` | 存檔後自動重啟；只用於開發 |

**啟動訊息：** `Uvicorn running on http://127.0.0.1:8000`
- 只綁 `127.0.0.1`（uvicorn 預設值）：只有本機連得到，同網段的其他裝置連不進來。與 M0.5 讓 LiteLLM 只綁本機（E13 第 4 項）同一原則；刻意不加 `--host 0.0.0.0`
- `--reload` 會監看整個專案資料夾的變更（`StatReload`）

**瀏覽器驗證：**

| 網址 | 結果 | 伺服器日誌 |
|---|---|---|
| `/health` | `{"status":"ok"}` ✅ | `"GET /health HTTP/1.1" 200 OK` |
| `/abc` | `{"detail":"Not Found"}` ✅ | （404） |
| `/docs` | FastAPI 自動文件頁，`/health` 展開後顯示 docstring ✅ | — |

**觀察：**
- 日誌中另有一筆 `GET /favicon.ico 404`：瀏覽器會自動要分頁的小圖示，不是程式問題
- **docstring 真的公開顯示在 `/docs`**，而且頁面左上角有 `/openapi.json` 連結，任何人都能下載完整的 API 清單。E52 提到「docstring 不能寫內部資訊」的理由得到實證；正式環境是否關閉已列入待決（M4 上雲前）
- 顯示為 `purpose.Extra`，句號後少了空格，待本人確認原始碼
- 回應範例顯示為 `"string"`：函式沒有標註回傳型別，FastAPI 不知道回應的格式。之後寫 `/v1/chat` 時會用 Pydantic 定義回應格式，屆時一併處理

**截圖：** `m1-uvicorn-start.png`（使用者資料夾名稱已遮蔽）、`m1-health-ok.png`、`m1-notfound-404.png`、`m1-docs-health.png`（瀏覽器大頭貼已遮蔽）

---

## E54. 第一個測試檔 `tests/test_health.py`（2026-09-30 19:37～19:55）

**本人撰寫的第一版：**

```python
from fastapi.testclient import TestClient
from app.main import app

test_health_returns_ok = TestClient(app)

response = TestClient.get("/health")
response.status_code
response.json()

assert response == {"status": "ok"}
```

**檢查結果（新手常見的五個觀念混淆）：**

| # | 問題 | 觀念 |
|---|---|---|
| 1 | 把測試名稱 `test_health_returns_ok` 當成變數名稱 | 測試名稱是**函式**（`def test_...():`），神秘客是另一個**變數**（例如 `client`） |
| 2 | `TestClient.get(...)` | 要叫「建立出來的那一位」`client.get(...)`，不是叫類別本身。類別是職業名稱，物件才是真的那個人 |
| 3 | `response.status_code`、`response.json()` 單獨一行 | 取出來沒有拿去用就丟掉了，要放進 `assert` 裡才有檢查作用 |
| 4 | `assert response == {...}` | `response` 是整個回應（含狀態碼、標頭），要比對的是內容 `response.json()` |
| 5 | 程式沒有放在函式裡，也少了第二個測試 | pytest 只執行名稱以 `test_` 開頭的**函式**，放在最外層的程式不算測試 |

**處理：** 提供第三層提示（填空式骨架，保留關鍵處由本人填寫），第二個測試由本人照同一模式完成

**第二版（19:47）：** 骨架填空正確；第二個測試 `test_unknown_path_returns_404` 由本人照同一模式獨立完成 ✅。僅剩函式之間空一行（慣例為兩行）的格式問題

**第三版（19:55，加上註解與空行）：** 檔案 docstring `Tests for the health check endpoint.`；404 測試加上 docstring `Only routes we define should be reachable.`（說明「預設拒絕」的資安理由）；`test_health_returns_ok` 名稱已說明用途，刻意不加註解

---

## E55. 第一次執行 pytest：`ModuleNotFoundError`（預期中的失敗，2026-09-30 19:55）

**指令：** `uv run pytest`

```
rootdir: C:\Users\<user>\llm-gateway
configfile: pyproject.toml
collected 0 items / 1 error
ERROR collecting tests/test_health.py
tests\test_health.py:4: in <module>
    from app.main import app
E   ModuleNotFoundError: No module named 'app'
=== warnings summary ===
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
=== 1 warning, 1 error in 3.10s ===
```

**這是事先預告的失敗：** E42 選擇 `app/` 結構（不打包）時，已記錄代價是「pytest 找不到 `app` 模組，需要設定 `pythonpath`」。刻意先讓錯誤發生，再理解原因

**錯誤訊息的讀法（由下往上）：**
1. 最下面的 `E   ModuleNotFoundError: No module named 'app'`：**發生什麼事**，找不到叫 `app` 的模組
2. 往上一行 `from app.main import app`：**哪一行程式**觸發的
3. 再往上 `tests\test_health.py:4`：**哪個檔案第幾行**
4. `collected 0 items / 1 error`：連測試都還沒開始跑，在「收集測試」階段就失敗了

**原因：** Python 只會到一份「搜尋清單」（`sys.path`）裡的資料夾找模組。pytest 執行 `tests/test_health.py` 時，把 `tests/` 資料夾加進清單，但沒有加入專案根目錄，而 `app/` 在根目錄下。用 uvicorn 啟動時會成功，是因為 uvicorn 把「目前所在的資料夾」（根目錄）加進了清單

**生活比喻：** 在 `tests` 會議室裡廣播「app 部門的人請過來」，但廣播只在這間會議室播，app 部門在隔壁大廳，聽不到

**附帶警告：** Starlette 1.7 把 TestClient 使用的 `httpx` 標為不建議使用，改建議 `httpx2`（見 E56）

**截圖：** `m1-pytest-module-not-found.png`（使用者資料夾名稱已遮蔽）

**修正（20:09）：** 本人在 `pyproject.toml` 加上

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

- 把專案根目錄 `.` 加進 pytest 的搜尋清單
- 不選「改用 `uv run python -m pytest`」：那會自動把目前資料夾加進清單，但要每個人、每次（包括 CI）都記得用這個指令；寫在設定檔，不論怎麼執行結果都一樣（與 `.gitattributes`「規則跟著 repo 走」同一思路）

**結果：**

```
collected 2 items
tests\test_health.py ..                                  [100%]
=== 2 passed, 1 warning in 1.29s ===
```

- `collected 2 items`：兩個測試都被找到（名稱以 `test_` 開頭的規則生效）
- `..`：每個點代表一個通過的測試
- **2 passed** ✅；剩下的 1 個 warning 是 E55 提到的 `httpx` 淘汰警告，處理見 E56

**截圖：** `m1-pytest-2-passed.png`（使用者資料夾名稱已遮蔽）

---

## E56. 測試工具由 `httpx` 換成 `httpx2`（2026-09-30 20:13）

**起因：** E55 的警告 `Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

**換套件前的來源查證（名稱與熱門套件只差一個字，先排除冒名套件）：**
- Starlette 官方文件：TestClient 現以 `httpx2` 為基礎，`httpx` 仍可用但已不建議（deprecated）
- PyPI：`httpx2` 由 Pydantic 組織維護，說明為原 `httpx` 專案的延續；PyPI 上的維護者 Kludex 同時也是 Starlette 的維護者
- 最新版 2.13.1 於 2026-09-23 上架，早於冷卻期日期 9/27

**指令與結果：**

```
> uv remove --dev httpx
Uninstalled 3 packages
 - certifi==2026.7.22
 - httpcore==1.0.9
 - httpx==0.28.1

> uv add --dev httpx2
Installed 3 packages
 + httpcore2==2.13.1
 + httpx2==2.13.1
 + truststore==0.10.4

> uv run pytest
collected 2 items
tests\test_health.py ..                                  [100%]
=== 2 passed in 0.91s ===
```

**判讀：**
- 移除 `httpx` 時，只被它用到的 `httpcore`、`certifi` 也一起移除：uv 會清掉沒有人需要的相依套件，不會留下殘骸
- `httpx2` 帶入 `truststore`：改用作業系統內建的憑證清單驗證 HTTPS 連線，取代 `certifi` 自帶的清單
- **`2 passed`，警告消失** ✅（結果列由黃色變為綠色）
- 一次只改一件事：先修 `ModuleNotFoundError`（E55），確認通過後才換套件，所以警告消失可以明確歸因於這次的更換
- 為什麼處理「只是警告」：警告累積越多，真正重要的警告越容易被淹沒；與 SOC 調校告警規則、降低雜訊的道理相同

**截圖：** `m1-httpx2-no-warning.png`（使用者資料夾名稱已遮蔽）

**參考來源：**
- [Starlette: TestClient](https://starlette.dev/testclient/)
- [PyPI: httpx2](https://pypi.org/project/httpx2/)

---

## E57. 第 4 步的 commit 與推送（2026-09-30 20:29～20:40）

**commit 前檢查（`m1-step4-status.png`）：** `git status` 顯示 3 個修改（證據紀錄、`pyproject.toml`、`uv.lock`）與新檔案（`app/main.py`、`tests/`、10 張截圖）；`.env`、`.venv`、`__pycache__`、`.pytest_cache` 都沒有出現
- `__pycache__`：被 uv 產生的 `.gitignore` 排除
- `.pytest_cache`：pytest 會在這個資料夾裡自己放一個 `.gitignore`，把整個資料夾排除

**分成兩筆 commit：**

```
> git add app tests pyproject.toml uv.lock
> git diff --cached --name-only
app/main.py
pyproject.toml
tests/test_health.py
uv.lock

> git commit -m "feat: add health check endpoint and tests"
[main 27fb02f] 4 files changed, 395 insertions(+), 1 deletion(-)

> git add docs
> git commit -m "docs: record M1 step 4 evdience"
[main 583e9db] 12 files changed, 262 insertions(+)

> git push
   570792c..583e9db  main -> main
```

- 程式與文件分開：`feat:` 那筆只有程式、測試與相依套件，之後追查程式問題時可以直接略過文件的 commit
- 放進箱子後先用 `git diff --cached --name-only` 確認只有預期的 4 個檔案，才 commit

**小失誤：commit 訊息打錯字（`evdience`）而且已經推送。**
- 推送前發現，可以用 `git commit --amend` 修改訊息
- 推送後要修改，就必須強制推送，而 `protect-main` 規則集禁止強制推送（E50），連擁有者本人也不行
- 決定：保留錯字，不為一個錯字改寫公開歷史。這也是規則集的實際效果：已公開的歷史不能被改寫
- 教訓：按 Enter 前再看一次 commit 訊息

**截圖：** `m1-step4-status.png`、`m1-step4-commit-push.png`（使用者資料夾名稱已遮蔽）

**步驟 4 狀態：✅ 完成**（冷卻期 `exclude-newer`、FastAPI 與 uvicorn、`GET /health`、兩個 pytest 測試、`httpx2`、推送至 GitHub）

---

## E58. 薄介面 5-1：安裝 OpenAI 套件、定義 `ChatResult`（2026-09-30 21:07）

**安裝：**

```
> uv add openai
Resolved 27 packages / Installed 3 packages
 + jiter==0.17.0
 + openai==3.19.2
 + sniffio==1.3.1
```

**判讀：**
- **冷卻期實際擋下了新版本：** PyPI 上 openai 的最新版是 3.21.0（2026-09-29 發布），uv 裝的是 3.19.2。9/27 之後上架的版本都被排除，E51 的 `exclude-newer` 設定第一次看得到效果
- 只多了 3 個套件：openai 3.x 預設使用 **`httpx2`** 當網路連線工具（官方 README），而 `httpx2` 在 E56 已經裝過
- 連帶影響：`httpx2` 原本只是開發用套件，現在 openai 在正式執行時也需要它，所以之後建容器時它會被裝進去。這是正常的：套件是否進容器，取決於「正式執行的程式需不需要」，不是當初用什麼方式加入

**openai SDK 的兩個預設值（官方 README），與 D10 相關：**

| 設定 | 預設值 | 問題 |
|---|---|---|
| `max_retries` | 自動重試 **2 次**，包含 429 | 供應商預算用完（`project_spend_limit_exceeded`）也是 429，SDK 會白白重試；也會跟 M3 的降級邏輯疊加（D10、D32） |
| `timeout` | **10 分鐘** | 使用者要等太久；Gateway 的連線也會被佔住 |

→ 建立 OpenAI 連線物件時，明確設定較小的重試次數與逾時時間（步驟 8 建立連線時處理）

**`ChatResult`（本人撰寫）：**

```python
"""Thin wrapper around the OpenAI SDK."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatResult:
    """The fields we need from one chat call."""
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
```

- `dataclass`：有固定欄位的表單；`frozen=True`：填好就不能改，像蓋了章的收據，計費資料不會被後面的程式偷偷改掉
- 5 個欄位都正確 ✅；只差模組 docstring 與 `import` 之間慣例上空一行

**截圖：** `m1-uv-add-openai.png`（使用者資料夾名稱已遮蔽）

**參考來源：** [PyPI: openai](https://pypi.org/project/openai/)

---

## E59. 薄介面 5-2：`chat` 函式（2026-09-30 21:21）

**本人撰寫：**

```python
def chat(client, model: str, messages: list[dict], reasoning_effort: str) -> ChatResult:
    """Call the Chat Completions API and return the fields we need."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        reasoning_effort=reasoning_effort
    )
    return ChatResult(
        text=response.choices[0].message.content,
        model=response.model,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        reasoning_tokens=response.usage.completion_tokens_details.reasoning_tokens
    )
```

**檢查：** 呼叫方式、5 個欄位的對應全部正確 ✅；格式上 `class` 與 `def` 之間慣例空兩行，多行參數的最後一項慣例加逗號（之後由自動排版工具處理）

**設計重點：**
- **名稱翻譯：** OpenAI 的 `prompt_tokens`、`completion_tokens` 在這裡換成我們的 `input_tokens`、`output_tokens`；之後的程式只看得到我們的名稱
- **`client` 由外部傳入：** 函式不自己建立連線，測試時可以傳入假的連線物件，不需金鑰、不花錢（5-3）
- **`client` 不標型別：** 測試傳入的是假物件，不是真正的 `OpenAI` 型別；標成 `OpenAI` 會讓型別檢查工具誤報

**帶到後續步驟的注意事項：**
- **計費不能重複計算思考 token：** OpenAI 的 `completion_tokens` **已經包含** `reasoning_tokens`。M3 算錢時用 `output_tokens` × 輸出單價即可，`reasoning_tokens` 是明細，不能再加一次
- **可能是 `None` 的欄位：** 模型拒答或特殊情況時，`message.content` 可能是 `None`；部分情況 `completion_tokens_details` 也可能不存在。步驟 7 串接 `/v1/chat` 時決定處理方式

---

## E60. 時程評估：11/7 繳交的可行性與每週目標（2026-10-01）

**背景：** 專題最晚 11/7 繳交（含技術文件、簡報、錄影）。本人可投入時間：平日每天至少 3 小時，假日約半天，換算**每週約 25 小時**。

**估算：**

| 項目 | 時數 |
|---|---|
| 10/1～11/7 可用時間（約 5.4 週） | 約 130 小時 |
| 剩餘工作量估計 | 約 115～125 小時 |
| 餘裕 | 約 5～15 小時 |

**結論：** 可行，但餘裕小；最大風險是 M4（Terraform 上雲，新手第一次做，除錯時間難估）。

**每週目標：**

| 週次 | 日期 | 目標 | 估計時數 | 檢查點 |
|---|---|---|---|---|
| W1 | 10/1～10/4 | M1 完成（步驟 5～9）＋ M1 結案報告、決策書 v2.7 | 約 16 | 本機真實呼叫 OpenAI 成功、Docker 可執行 |
| W2 | 10/5～10/11 | M2：API Key 驗證、額度、DynamoDB Local、fail-closed、個資遮罩 | 約 25 | 超額 429、資料庫斷線 503、遮罩生效 |
| W3 | 10/12～10/18 | M3：路由、計費、降級；CI 先建（pytest、tfsec、Trivy） | 約 25 | 🚩 10/18 M3 完成 |
| W4 | 10/19～10/25 | M4：Terraform、VPC、NAT、DNS 防火牆、Fargate、ALB | 約 25～30 | 🚩 10/25 雲端跑通 |
| W5 | 10/26～11/1 | M5：SQS＋Lambda＋故障演練；M6：Demo Console、CI/CD 部署 | 約 25 | 🚩 11/1 M6 完成 |
| 緩衝 | 11/2～11/4 | 補進度、補截圖 | — | 🚩 11/4 截圖到齊 |
| 收尾 | 11/5～11/7 | 技術文件定稿、簡報、錄影 | 約 10～15 | 11/7 繳交 |

**執行方式：**
- 每週最後一天對一次進度；落後超過兩天，提早啟用決策書 8.4 的砍除順序
- 不可砍的底線：受控出口（controlled egress）、pytest、CI/CD、技術文件

**時程依賴的兩個前提（✅ 2026-10-01 19:36 本人確認兩項都採用）：**
1. 減少例行截圖：只留 11.4 清單與出錯、決策、驗證的關鍵畫面；例行 git 操作改貼文字
2. M4 的 Terraform 由 Claude 提供含註解的骨架，本人負責理解、修改、執行、除錯並能說明每個設定的理由；Python 程式維持本人自行撰寫
   - 若不採用第 2 項，W4 約多 10～15 小時，需從緩衝或 M7 扣除

**面試可用的說法：** 「我在動工前先把剩餘工作量換算成時數，跟可用時間對帳，排出每週檢查點，並事先定好落後時要砍什麼、什麼絕對不砍——這是把專案管理的範圍控制（scope control）用在自己身上。」

---

## E61. 薄介面 5-3：用假的 OpenAI 連線測試 `chat`（2026-10-01 22:53～23:18）

**做法：** 不連真的 OpenAI（不需金鑰、不花錢、不用等網路），改用假物件假扮 `client.chat.completions`：
- `FakeCompletions.create(**kwargs)`：把收到的參數整包存進 `last_request`（筆記本），再回傳一份固定的假回應
- `make_fake_client()`：同時回傳 `client`（交給 `chat`）與 `completions`（讓測試事後翻筆記本）
- 骨架由 Claude 提供（測試道具，非本步驟重點）；兩個測試由本人撰寫

**兩個測試各管一件事：**

| 測試 | 檢查什麼 | 比喻 |
|---|---|---|
| `test_chat_maps_response_fields` | 回應的 5 個欄位有沒有正確裝進 `ChatResult` | 收到的餐點有沒有正確裝盒 |
| `test_chat_sends_model_and_reasoning_effort` | 送出的請求有沒有帶對 `model` 與 `reasoning_effort` | 訂單有沒有寫對 |

**為什麼需要第二個測試：** 假回應是固定的，就算 `chat()` 漏傳 `reasoning_effort`，第一個測試照樣通過；只有檢查「送出的請求」才抓得到。

**卡關與解法：**
- 測試 1 本人在提示二（填空版）後完成，全部正確
- 測試 2 卡在 `completions.last_request[ ]` 的括號內要填什麼——原因是骨架中的 `**kwargs` 沒有事先解釋（Claude 的疏漏）。補充說明後理解：
  - `chat()` 以「名稱=值」方式呼叫 `create(model=..., messages=..., reasoning_effort=...)`
  - `**kwargs` 把這些參數收成一本字典：`{"model": "gpt-6-luna", "messages": [...], "reasoning_effort": "none"}`
  - 所以用 `last_request["model"]`、`last_request["reasoning_effort"]` 查詢
- **教訓：** 給骨架時，骨架裡的新語法也要先講清楚，不能只說「照打就好」

**註解原則（本人確認）：** 只寫「為什麼」，不寫「做什麼」（函式名稱已經說明的不重複）。補在 `make_fake_client()`（為什麼回傳兩樣東西）與測試 2（為什麼需要這個測試）。

**驗證結果：**

```
PS C:\Users\<user>\llm-gateway> uv run pytest
collected 4 items
tests\test_health.py ..                    [ 50%]
tests\test_openai_client.py ..             [100%]
4 passed in 2.34s
```

（依 E60 的截圖原則，例行驗證以文字記錄；使用者名稱已遮蔽）

**面試可用的說法：** 「呼叫外部付費 API 的程式，我用假物件做單元測試：一個測試確認回應欄位對應正確，另一個確認送出的參數正確。這樣 CI 每次執行都不需要金鑰、不花錢，也不會因為對方服務不穩而誤判失敗。」

---

## E62. 第 5 步的 commit 與推送（2026-10-01 23:20～23:26）

**推送前檢查：** `git status` 列出 7 項，全部屬於本步驟；無 `.env`、無多餘檔案。加入暫存區後再確認 `app/providers/` 只含 `__init__.py` 與 `openai_client.py`。

**兩次 commit（程式與文件分開）：**
- `feat: add OpenAI thin wrapper and tests`：`pyproject.toml`、`uv.lock`、`app/providers/`、`tests/test_openai_client.py`
- `docs: record M1 step 5 evidence`：證據紀錄（E58～E61）與兩張截圖

**推送結果：** `583e9db..066b924  main -> main`（`066b924` 為 docs commit）

**為什麼分開：** 翻歷史紀錄時能一眼區分程式與文件的變更；若程式需要退版，不會連文件一起退掉。

---

## E63. 稽核 6-1：HMAC 雜湊 `hash_prompt`（2026-10-03 09:08～09:52）

**為什麼用 HMAC 而不是一般雜湊（D4）：** prompt 常是短句，一般 SHA-256 可以被字典攻擊猜回原文（把常見問句逐一算雜湊比對）。HMAC 多了一把金鑰，沒有金鑰就算不出相同的結果。

**生活比喻：** 雜湊像全世界都買得到的同款果汁機，壞人可以把水果一個個丟進去比對；HMAC 是打果汁時加一匙只有自己知道的祕密醬料。

**本人撰寫（`app/audit.py`）：**

```python
def hash_prompt(text: str, key: bytes) -> str:
    """Return the HMAC-SHA256 of the prompt, so the audit log never stores the text."""
    bytes_text = text.encode("utf-8")
    hmac_text = hmac.new(key, bytes_text, hashlib.sha256)
    return hmac_text.hexdigest()
```

**設計重點：**
- 只用 Python 內建的 `hmac`、`hashlib`，不增加第三方套件（少一個供應鏈風險點）
- **金鑰由外部傳入**，函式不自己讀環境變數：測試時直接傳假金鑰 `b"test-key"`，與 `chat()` 的 `client` 同一個做法
- 函式本體第一次就寫對；拆成三行（轉位元組 → 計算 → 轉十六進位），比擠成一行好讀

**測試（`tests/test_audit.py`）：**

| 測試 | 檢查 |
|---|---|
| `test_hash_is_64_hex_chars` | 結果長度 64 |
| `test_same_input_gives_same_hash` | 同文字、同金鑰 → 結果相等 |
| `test_different_key_gives_different_hash` | 同文字、不同金鑰 → 結果不相等（HMAC 的核心性質） |

**卡關與解法：** 第一版測試只寫了 `client = hash_prompt()`（沒傳參數、沒有 `assert`）。原因是不確定「一個測試要包含哪些東西」。補充「準備 → 執行 → 檢查」三步驟的固定套路後，以填空版完成，全部正確。

**驗證：** `uv run pytest` → `7 passed in 0.61s`

**帶到後續：** 本機的 HMAC 金鑰用環境變數（步驟 8），雲端改從 SSM SecureString 注入（D14，M4）。這把金鑰換了舊紀錄就對不上（10.3 第 12 點）。

---

## E64. 稽核 6-2：摘要 `make_summary`，先遮罩再截斷（2026-10-03 09:34～09:52）

**依據：** D6（遮罩後內容的前 50 字）、E34（順序固定為先遮罩、再截斷）。

**本人撰寫：**

```python
SUMMARY_LENGTH = 50


def mask(text: str) -> str:
    """Placeholder for M1. M2 will mask personal data here."""
    return text


def make_summary(text: str) -> str:
    """Mask first, then cut. Cutting first could split personal data and hide it from the mask."""
    f_mask = mask(text)
    cut_summary = f_mask[:SUMMARY_LENGTH]
    return cut_summary
```

**設計重點：**
- `mask()` 在 M1 是空殼，但呼叫順序從現在就寫對；M2 只需補 `mask()` 的內容
- 長度寫成常數 `SUMMARY_LENGTH`，不在程式中直接寫 `50`

**測試（本人不靠提示完成）：**

| 測試 | 檢查 |
|---|---|
| `test_summary_keeps_short_text` | `"Say hi"` 原樣保留 |
| `test_summary_cuts_long_text_to_50_chars` | 80 個字元截成 50 |

**驗證：** `uv run pytest` → `9 passed in 0.79s`

**已知缺口（同 E34）：** M1 的 `mask()` 不做任何事，摘要的安全性只靠「測試資料不含個資」；「個資跨在第 50 字」的邊界測試留到 M2。

---

## E65. 稽核 6-3：JSON Lines 存放函式 `append_audit`（2026-10-03 09:52～10:57）

**定案：** M1 的稽核紀錄寫入 JSON Lines 檔（一行一筆 JSON），包成一個函式；M2 啟動 DynamoDB Local 時只換這個函式的實作，呼叫端不動。執行時產生的資料放 `data/`，已加入 `.gitignore`。

**為什麼選 JSON Lines：** 稽核紀錄只新增、不修改，與「接在檔案最後面寫一行」的操作吻合。不選 SQLite（關聯式，M2 全部作廢）；不選 M1 就上 DynamoDB Local（第一次成功對話前要先搞定 docker-compose、boto3、建表）。

**生活比喻：** 餐廳的出單夾：新單一律夾在最後面，前面的不動。

**本人撰寫（最終版）：**

```python
def append_audit(record: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        text = json.dumps(record)
        f.write(text + "\n")
```

**兩個資安／正確性重點：**
- **`"a"`（附加）不能寫成 `"w"`（覆寫）：** `"w"` 每次都會清空檔案，等於稽核紀錄被銷毀。`test_append_audit_keeps_earlier_records` 專門防這件事
- **明確指定 `encoding="utf-8"`：** Windows 的預設編碼不是 UTF-8，不指定的話之後的中文摘要會變亂碼（同 E22、E45 的編碼教訓）

**挫折與排查：第一次執行 2 個測試失敗**

```
>       f.write(text + "\n")
E       ValueError: I/O operation on closed file.
app\audit.py:34: ValueError
2 failed, 9 passed in 0.75s
```

- **原因：** `f.write(...)` 少縮排一層，跑到 `with` 區塊外面。`with` 區塊一結束，檔案就自動關閉；之後再寫入就是「對已關閉的檔案操作」
- **解法（本人自行排查）：** 依錯誤訊息指出的行號（`audit.py:34`）找到那一行，把它縮排進 `with` 區塊內
- **結果：** `11 passed in 0.65s`
- **意義：** 這是測試第一次抓到真正的 bug。沒有測試的話，這個錯誤要到步驟 8 真的呼叫 API 時才會發現，而且會和金鑰、網路等問題混在一起，難以判斷

**測試：**

| 測試 | 檢查 | 做法 |
|---|---|---|
| `test_append_audit_writes_one_json_line` | 寫一筆 → 檔案 1 行，讀回來等於原紀錄 | 填空版 |
| `test_append_audit_keeps_earlier_records` | 寫兩筆 → 檔案 2 行，順序正確 | 本人撰寫；第一版漏了「執行」步驟、誤用另一個測試的變數，經指出後修正 |

- 使用 pytest 內建的 `tmp_path`（用完即丟的暫存資料夾），測試不會在專案內留下檔案
- 日誌中的使用者名稱（路徑與暫存資料夾名稱）未收錄

**面試可用的說法：** 「稽核紀錄的寫入我特別測了『附加而不是覆寫』：連寫兩筆，確認兩筆都在、順序正確。開檔模式寫錯一個字母，稽核紀錄就會被整個清掉，這種錯誤要靠測試擋，不能靠小心。」

---

## E66. 第 6 步的 commit 與推送（2026-10-03 11:16）

- `feat: add audit helpers and tests`：`.gitignore`（新增 `data/`）、`app/audit.py`、`tests/test_audit.py`
- `docs: record M1 step 6 evidence`：證據紀錄 E63～E65
- 推送結果：`066b924..5888682  main -> main`

---

## E67. 串接 7-1：`POST /v1/chat` 入口（2026-10-03 11:16～13:49）

**流程（生活比喻：餐廳出餐）：**

```
POST /v1/chat  {"message": "..."}
  ① 開單號（request_id，uuid4）
  ② 個資遮罩（mask）
  ③ 呼叫模型（chat）          ← 送出的是遮罩後的內容（D5）
  ④ 寫稽核紀錄（append_audit） ← 只有指紋、摘要、用量
  ⑤ 回傳 request_id、reply、model
```

**設計決定：**

| 項目 | 做法 | 為什麼 |
|---|---|---|
| 請求格式 | `ChatRequest` 只有 `message` 一欄 | 沒有 `model` 欄位，使用者無法指定模型（D9） |
| 輸入長度 | `min_length=1, max_length=4000` | 空訊息無意義；超長輸入等於超貴的帳單。不合格由 FastAPI 自動回 422 |
| 模型 | 常數 `MODEL = "gpt-6-luna"`、`REASONING_EFFORT = "none"` | M1 尚無路由（M3 才做） |
| 相依注入 | `get_client`、`get_hmac_key`、`get_audit_path` 三個函式，以 `Depends` 注入 | 測試時用 `dependency_overrides` 換成假的，與 `chat()` 傳入假 `client` 同一思路 |
| HMAC 金鑰來源 | 環境變數 `AUDIT_HMAC_KEY` | 不寫在程式裡；雲端改由 SSM 注入（D14） |
| 指紋的輸入 | **原文**（非遮罩後內容） | 指紋用於事後比對「是否問過這句話」，比對時拿的是原句；原文本身不落地 |
| 時間 | UTC、ISO 8601 | 服務將部署在東京，統一時區避免查紀錄時算錯 |

**資安規則（D5）：** 稽核紀錄的任何欄位都不直接放 `request.message` 或 `result.text`；原文只出現在 `hash_prompt(...)`、`make_summary(...)`、`mask(...)` 的參數中。

**工作方式調整：** 本人反映一次給整段規格太多，改為「一次一小段、邊講邊做」：框架語法（`Depends`、Pydantic 模型）由 Claude 提供並解釋，函式本體分 ①②③、④⑤ 兩次由本人撰寫。

**本人寫錯並修正：** 回傳值誤寫成 `"request_id": client`（把 OpenAI 連線物件放進回應），改為 `request_id`。

---

## E68. 串接 7-2：整條流程的測試（2026-10-03 13:49～14:30）

**準備：**
- 假 OpenAI（`FakeCompletions`、`make_fake_client`）由 `tests/test_openai_client.py` 搬到共用的 `tests/fakes.py`；搬完先確認 11 個測試仍通過
- `tests/test_chat.py` 的 `make_test_client(tmp_path)`：以 `app.dependency_overrides` 把三個相依換成假連線、假金鑰 `b"test-key"`、暫存稽核檔

**測試：**

| 測試 | 檢查 | 備註 |
|---|---|---|
| `test_chat_returns_reply` | 200、`reply`、`model` | 填空版 |
| `test_chat_audit_has_hash_and_summary_but_not_the_prompt` | 指紋 64 字元、摘要為前 50 字、**完整原文不在稽核檔**、**模型回答不在稽核檔** | **M1 驗收條件的自動化**；用超過 50 字的句子，確保完整原文不會因為「摘要剛好等於原文」而出現 |
| `test_chat_rejects_empty_message` | 空字串回 422 | 本人自行撰寫 |

**驗證：** `14 passed`

**釐清的觀念：**
- `_`：函式回傳多個值時，用來接「不需要的那個」；只是慣例名稱，不是特殊語法
- 註解原則的實際應用：`test_chat_returns_reply` 不加 docstring（名稱已說明）；驗收條件那個測試加（背後有資安規則）

**本人提出的做法：** 所有函式與類別上方加一行中文 `#` 註解（英文 docstring 保留），方便自己複習與面試前回顧。已全數加上，加完後 `14 passed`。

---

## E69. 串接 7-3：特殊狀況處理（2026-10-03 14:30～17:03）

### A. 模型回應不完整

| 狀況 | 處理 | 位置 |
|---|---|---|
| `message.content` 為 `None`（拒答等） | 改用空字串：`content or ""` | `openai_client.chat()` |
| `completion_tokens_details` 不存在 | 思考 token 記 0 | 同上 |

- 假 OpenAI 增加三個可調參數：`content`、`has_details`、`error`（都有預設值，既有測試不用改）
- 本人偏好把條件式拆成 `if / else` 四行，不用單行寫法；之後提供的程式碼以拆開寫法為主

**挫折 1：測試先失敗（預期中）**

```
E   AttributeError: 'NoneType' object has no attribute 'reasoning_tokens'
app\providers\openai_client.py:31
```

- 原因：只做了 `content or ""`，還沒加「沒有明細就算 0」
- 意義：先看到測試失敗、改程式後通過，證明這個測試真的有在檢查
- 順帶修正：新測試把 `reasoning_effort` 寫成 `None`（空值），應為字串 `"none"`

### B. OpenAI 呼叫失敗

**做法：**

```python
    try:
        result = chat(client, MODEL, [{"role": "user", "content": masked}], REASONING_EFFORT)
    except OpenAIError as exc:
        record["status"] = "error"
        record["error_type"] = type(exc).__name__
        append_audit(record, audit_path)
        raise HTTPException(status_code=502, detail="Upstream model error")
```

| 決定 | 為什麼 |
|---|---|
| 失敗也寫稽核紀錄（`status: "error"`） | 使用者確實送了請求，稽核不能查不到（同 E23：失敗請求也要記） |
| 回 502 Bad Gateway | 語意正是「閘道向上游取資料，上游出錯」 |
| 稽核只記錯誤**類別名稱**，不記錯誤訊息 | 錯誤訊息可能夾帶帳號資訊或請求內容 |
| 回給使用者固定一句 `Upstream model error` | 不洩漏內部細節 |
| 紀錄分兩段組：先放共同欄位，成功／失敗再各自補欄位 | 兩條路共用單號、時間、指紋、摘要 |

**挫折 2：稽核紀錄安靜地少了四個欄位（重要）**

```
>       assert len(record["prompt_hash"]) == 64
E       KeyError: 'prompt_hash'
FAILED tests/test_chat.py::test_chat_audit_has_hash_and_summary_but_not_the_prompt
```

- **原因：** 成功路徑寫成 `record = {...}`（建立新字典，取代原本的），原有的 `request_id`、`timestamp`、`prompt_hash`、`summary` 全部遺失。應為 `record["欄位"] = 值`（在原字典上新增）
- **為什麼危險：** 使用者照樣拿得到回答，畫面上沒有任何異狀；但每筆成功請求的稽核紀錄都沒有單號、指紋、摘要，稽核形同虛設
- **誰抓到的：** E68 的 M1 驗收測試。沒有它，這個錯誤會一路帶到上線
- **Claude 的疏漏：** 只寫「你來寫 5 行」，沒有強調不能用 `record = {...}`

**挫折 3：讀不懂 `AssertionError`**

```
E   AssertionError: assert 'OpenAIError' == 'Say hi'
E     - Say hi
E     + OpenAIError
```

- 本人連試三個值（`"Upstream model error"`、`"boom"`、`"Say hi"`）都失敗
- 學到的讀法：`-` 是測試預期的值，`+` 是程式實際給的值；答案就在 `+` 那一行
- 觀念釐清：`OpenAIError("boom")` 中，`OpenAIError` 是類別（病名），`"boom"` 是訊息（備註）；稽核只記前者

**測試：** `test_chat_returns_502_and_audits_when_model_fails`——回 502、`status` 為 `error`、`error_type` 為 `OpenAIError`、`boom` 不在稽核檔也不在回應中

**驗證：** `17 passed in 1.52s`

**面試可用的說法：**
- 「我有一個測試直接對應驗收條件：稽核紀錄有雜湊與摘要、找不到原文。後來我重構錯誤處理時不小心把紀錄整個換掉，少了四個欄位，使用者端完全看不出來，是這個測試擋下來的。」
- 「上游出錯時我回 502，稽核只記錯誤類別、不記錯誤訊息，回應也只給固定字串。錯誤訊息本身就是資訊洩漏的管道。」

**留到之後：**
- OpenAI SDK 的重試次數與逾時（預設重試 2 次、逾時 10 分鐘）在步驟 8 建立真實連線時調小（D10）
- 依錯誤類型區分處理（限流降級、預算用完不降級）屬 M3（D10、D32）

---

## E70. 第 7 步的 commit；8-1 連線設定與設定檔範本（2026-10-03 17:11～23:31）

**第 7 步 commit：**
- `feat: add chat endpoint with audit and error handling`、`docs: record M1 step 7 evidence`
- 推送結果：`5888682..f629796  main -> main`

**8-1 A：OpenAI SDK 的重試與逾時（D10）**

| 設定 | SDK 預設 | 本案 | 為什麼 |
|---|---|---|---|
| `max_retries` | 2 | **1** | 每次重試都可能再花一次錢；M3 會自己寫「限流就降級」，SDK 的自動重試會與它疊加 |
| `timeout` | 10 分鐘 | **30 秒** | 平價模型數秒內回應；等 10 分鐘會讓使用者連線被卡住 |

```python
OPENAI_MAX_RETRIES = 1
OPENAI_TIMEOUT_SECONDS = 30

def get_client() -> OpenAI:
    return OpenAI(max_retries=OPENAI_MAX_RETRIES, timeout=OPENAI_TIMEOUT_SECONDS)
```

**8-1 B：`.env.example`**（進 Git，只有欄位名稱、沒有值）：`OPENAI_API_KEY`、`AUDIT_HMAC_KEY`

**放金鑰之前先驗證鎖：**

```
> uv run pytest
17 passed
> git check-ignore -v .env.example
.gitignore:15:!.env.example     .env.example
> git check-ignore -v .env
.gitignore:13:.env      .env
```

- `.env.example` 命中放行規則（會進 Git）；`.env` 命中忽略規則（不會進 Git）
- 順序是刻意的：先確認 `.env` 進不了 Git，才把金鑰放進去（同 E44 的做法）

---

## E71. 8-2：M1 專用金鑰與 `.env`（2026-10-03 23:31～23:54）

**原則（E28）：** `.env` 不在 VS Code 開、金鑰不出現在指令列與截圖、確認內容只看欄位名稱、長度、前綴。

**差點放錯位置（先問再做，避免了錯誤）：** 執行前本人先貼出目錄清單，所在位置是 `scripts\litellm-lab`（M0.5 的實驗資料夾，內有當時的 `.env`）。該檔案日期仍為 9/26，確認尚未被改動；退回專案根目錄後才執行。
- 專案內有兩個 `.env`：`scripts/litellm-lab/.env`（M0.5 實驗用）與根目錄 `.env`（M1 Gateway 用），互不相干
- 教訓：寫入密鑰檔之前先確認目前所在目錄

**HMAC 金鑰（不顯示在畫面上，直接寫入檔案）：**

```
> "AUDIT_HMAC_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" | Add-Content .env -Encoding ascii
> gc .env | % { $_.Split('=')[0] + ' ' + $_.Length }
AUDIT_HMAC_KEY 79
```

- 以 Python 內建的 `secrets` 產生 32 位元組（64 個十六進位字元）；`secrets` 是為密碼學用途設計的亂數來源
- 檢查指令只印欄位名稱與該行長度（15 + 64 = 79），不印內容
- 明確指定 `-Encoding ascii`：Windows PowerShell 5.1 的重新導向預設寫成 UTF-16，會讓其他程式讀不到

**OpenAI 金鑰 `m1-gateway`（規格同 E21）：**

| 項目 | 設定 |
|---|---|
| Project | `llm-gateway-capstone` |
| 擁有者 | Service account |
| 有效期限 | 30 天（2026-10-03 建立，2026-11-02 到期） |
| 權限 | Restricted：只有 Chat completions = Request；其餘（含 Responses、List models）皆 None |

- 到期日 11/2 早於繳交日 11/7：M4 上雲時會另開金鑰放 SSM（D14），或屆時改用工作負載身分聯盟；M1 這把只用於本機
- 列表同時可見 M0.5 的 `m0-m05-lab` 金鑰狀態為 **Revoked**，佐證 E28 的撤銷
- 兩把金鑰的 Created by 不同：每個服務帳號是獨立的機器人成員，不綁個人帳號

**寫入後的檢查：**

```
> gc .env | % { $_.Split('=')[0] + ' ' + $_.Length }
AUDIT_HMAC_KEY 79
OPENAI_API_KEY 182
> (gc .env)[1].Substring(0,26)
OPENAI_API_KEY=sk-svcacct-
> git status --short
 M app/main.py
?? .env.example
```

- 前綴 `sk-svcacct-` 證明是服務帳號金鑰；長度 182 − 15 = 167，與 M0 的金鑰長度相同（E22）
- `git status` 看不到 `.env`：金鑰放進去之後，Git 仍然看不到它 ✅
- 金鑰以記事本貼入後清除剪貼簿

**截圖：**
- `m1-openai-key-create-settings.png`（帳號頭像已遮蔽）
- `m1-openai-key-permissions.png`
- `m1-openai-key-list-restricted.png`（兩列的 Tracking ID、金鑰末 4 碼、建立者 user ID 已遮蔽，保留前綴）

---

## E72. 8-3：第一次經由 Gateway 真實呼叫 OpenAI——M1 驗收（2026-10-04 00:00）

**啟動方式：** `uv run --env-file .env uvicorn app.main:app --host 127.0.0.1 --port 8000`
- 金鑰由 `--env-file` 從檔案載入，不出現在指令列與 PowerShell 歷史紀錄
- 只綁 `127.0.0.1`，不對區域網路開放

**請求（另一個 PowerShell 視窗）：**

```
> $b = '{"message":"Please reply with only the word hello, and nothing else, because this is a connectivity test"}'
> irm http://127.0.0.1:8000/v1/chat -Method Post -ContentType 'application/json' -Body $b

request_id                           reply model
----------                           ----- -----
4bcc9256-ece1-4192-96a1-0ac9574595c9 hello gpt-6-luna
```

**稽核紀錄（`data/audit.jsonl`）：**

```json
{"request_id": "4bcc9256-ece1-4192-96a1-0ac9574595c9", "timestamp": "2026-10-03T16:00:42.553397+00:00", "prompt_hash": "c9345336006504814950591f0637b5092d41b7d7475e25f3373054ae91e8206d", "summary": "Please reply with only the word hello, and nothing", "model": "gpt-6-luna", "input_tokens": 24, "output_tokens": 4, "reasoning_tokens": 0, "status": "ok"}
```

**反向檢查：完整原文不在稽核檔**

```
> sls "connectivity test" data\audit.jsonl
（無輸出）
```

**對照決策書 8.2 的 M1 驗證條件：**

| 驗證條件 | 結果 | 依據 |
|---|---|---|
| 本機送一次 `POST /v1/chat` 拿到回應 | ✅ | `reply: hello`、`model: gpt-6-luna` |
| 稽核紀錄看得到 hash 與摘要 | ✅ | `prompt_hash` 64 字元；`summary` 為原句前 50 字 |
| 找不到完整 prompt | ✅ | 原句第 50 字之後的 `connectivity test` 搜尋無結果；模型回答 `hello` 也只出現在摘要引用的原句片段中，不是以回答欄位存入 |
| `usage` 的思考 token 有被記錄 | ✅ | `reasoning_tokens: 0`（`reasoning_effort: none` 生效） |

**判讀：**
- 回應的 `request_id` 與稽核紀錄的 `request_id` 相同：使用者拿到的單號可以對回稽核紀錄
- `timestamp` 為 UTC（16:00:42），換算台北時間為 10/4 00:00:42
- 測試句刻意超過 50 字，才能驗證「摘要截斷後，完整原文確實不落地」；若用短句，摘要會等於原文，這項檢查就失去意義
- **花費：** 輸入 24 × $0.10／百萬 ＋ 輸出 4 × $0.50／百萬 ＝ **$0.0000044**（4.4 micro-USD）

**已知限制（誠實記錄）：**
- 這次是在本機直接執行（尚未裝進容器，步驟 9）
- `mask()` 仍是空殼，送往 OpenAI 的是未遮罩內容；M1 以「測試句不含個資」作為人為約束（E34），M2 補上
- 摘要 50 字內的內容會落地，這是設計上的取捨（D6），遮罩補上前不可輸入個資

**截圖：** `m1-first-real-call-audit.png`（六處提示字元中的使用者資料夾名稱已遮蔽）

**面試可用的說法：** 「驗收時我不只看『有回應』，還做了反向檢查：用一句超過 50 字的話呼叫，再到稽核檔搜尋後半句，確認搜不到。證明『沒有存原文』要靠找不到的證據，而不是靠程式碼看起來沒寫。」

---

## E73. 第 8 步的 commit；動工前整理 Docker 環境（2026-10-04 00:09、15:43～15:50）

**第 8 步 commit：**
- `d2fb1a0 feat: set OpenAI client limits and add env example`、`5e4978a docs: record M1 step 8 evidence`
- 推送前 `git status` 確認清單中沒有 `.env` 與 `data/`（此時 `data/audit.jsonl` 已實際存在）
- 推送結果：`f629796..5e4978a  main -> main`

**整理 Docker 環境（本人提出）：** 步驟 9 開工前，先清掉先前課程練習留下的容器、映像、資料卷與建置快取；只保留 M0.5 的兩個映像（LiteLLM v1.102.0、`postgres:16`），留到繳交後再刪，以備補拍截圖。

| 項目 | 清理前 | 清理後 |
|---|---|---|
| 映像 | 20 個、9.36 GB | 2 個、2.29 GB |
| 容器 | 4 個 | 0 |
| 資料卷 | 10 個、1.29 GB | 0 |
| 建置快取 | 1.56 GB | 0 |

- 做法：先盤點（`docker system df`、`ps -a`、`images`、`volume ls`）→ 分類 → 本人確認 → 才刪除；資料卷刪除後無法復原
- 附帶發現：練習用的容器設定為隨 Docker 自動啟動，且連接埠綁定 `0.0.0.0`，等於每次開啟 Docker 就對區域網路開放。與 E13 第 4 項同類；步驟 9 的容器因此明確綁定 `127.0.0.1`
- 與本專題無關的映像名稱不收錄

---

## E74. 步驟 9：Dockerfile 與容器驗證（2026-10-04 15:39～16:42）

### 基底映像與 digest（D19）

```
> docker pull python:3.12-slim
Digest: sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
> docker pull ghcr.io/astral-sh/uv:0.12.19
Digest: sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424
> docker inspect -f "{{.Created}}" python:3.12-slim
2026-10-01T21:49:55.902225648Z
```

| 映像 | 用途 | 製作時間 | 冷卻期（滿 3 天，D27） |
|---|---|---|---|
| `python:3.12-slim` | 兩個階段的基底 | 2026-10-01 21:49 UTC | ❌ 建置當下為 2 天 10 小時，差約 14 小時 |
| `ghcr.io/astral-sh/uv:0.12.19` | 只借用 `uv` 執行檔；與本機版本相同（E33） | 9 天前 | ✅ |

**冷卻期例外（誠實記錄）：** Python 映像於 10/5 05:50（台北時間）才滿 3 天。評估後當天照做：
- 映像只在本機測試，不推送到任何倉庫；digest 已鎖定，日後使用的是同一份內容
- Docker 官方映像由官方流程定期重建以納入安全更新，風險型態不同於任何人都能上傳的 PyPI 套件
- M4 推上 ECR 時早已超過 3 天；**M1 結案時再確認此 digest 未被撤回**
- 本人未明確答覆選項即開始建置，視為採用「當天照做、記錄例外」；有異議再調整

### `.dockerignore`：白名單

```
*
!app
!pyproject.toml
!uv.lock
**/__pycache__/
```

- 預設全部排除，只放行映像需要的三樣；`.env`、`data/`、`.git`、`docs/`、`tests/` 自動被擋，之後新增的檔案預設也是擋
- **實證：** 建置輸出 `transferring context: 307B`，送進 Docker 引擎的內容只有 307 位元組

### Dockerfile：多階段建置

| 階段 | 內容 | 最後的映像裡有沒有 |
|---|---|---|
| `builder` | 借用 `uv`，`uv sync --frozen --no-dev --no-install-project` 照 `uv.lock` 安裝 | 沒有（只取走 `.venv`） |
| 執行階段 | 建立一般使用者 `appuser`（UID 10001）、複製 `.venv` 與 `app/`、建立 `data/`、`USER appuser`、以 uvicorn 啟動 | 有 |

**四個資安重點：**

| # | 做法 | 防什麼 | 依據 |
|---|---|---|---|
| 1 | 基底映像以 digest 鎖定 | 同一個標籤的內容日後被替換 | D19 |
| 2 | 照含雜湊的 `uv.lock` 安裝、不裝開發工具 | 套件被偷換；正式環境不該有測試工具 | D18 |
| 3 | 以一般使用者執行 | 程式被入侵時拿不到 root | — |
| 4 | 金鑰不進映像，執行時以 `--env-file` 提供 | 映像外流等於金鑰外流 | D14 |

- `uv` 以 `COPY --from` 自官方映像取得，不用「下載腳本後直接執行」的安裝方式（同 E33 的理由）
- 容器內監聽 `0.0.0.0` 是慣例；是否對外開放由執行時的 `-p` 決定（同 E14）

**程式由 Claude 提供含註解的骨架並逐行講解**（E60 定案的做法延伸到 Dockerfile）；本人負責理解、建立檔案、執行與除錯。

### 挫折：`invalid value 'COPY'`

```
 > [builder 5/5] RUN uv sync --frozen --no-dev --no-install-project:
error: invalid value 'COPY' for '--link-mode <LINK_MODE>'
  [possible values: clone, copy, hardlink, symlink]
```

- 原因：環境變數寫成 `UV_LINK_MODE=COPY`。`COPY`（大寫）是 Dockerfile 的指令；交給 uv 的設定值必須是小寫 `copy`
- 解法：改為小寫後建置成功（`17/17 FINISHED`，8.6 秒）
- 錯誤訊息已列出合法值；前面的步驟（digest 解析、取得 uv、建立使用者）都已通過，問題範圍一開始就很小

### 執行與驗證

```
> docker run -d --rm --name gw -p 127.0.0.1:8000:8000 --env-file .env llm-gateway:m1
> docker ps
... Up 3 seconds   127.0.0.1:8000->8000/tcp   gw
```

**功能：**

```
> irm http://127.0.0.1:8000/health
status: ok

> irm http://127.0.0.1:8000/v1/chat -Method Post -ContentType 'application/json' -Body $b
request_id                           reply model
6b5a3594-eee6-4d76-99f7-cb6acd28fb32 hello gpt-6-luna

> docker exec gw cat data/audit.jsonl
{"request_id": "6b5a3594-eee6-4d76-99f7-cb6acd28fb32", "timestamp": "2026-10-04T08:35:16.293045+00:00", "prompt_hash": "c9345336006504814950591f0637b5092d41b7d7475e25f3373054ae91e8206d", "summary": "Please reply with only the word hello, and nothing", "model": "gpt-6-luna", "input_tokens": 24, "output_tokens": 4, "reasoning_tokens": 0, "status": "ok"}
```

**資安：**

| 指令 | 結果 | 證明 |
|---|---|---|
| `docker ps` | `127.0.0.1:8000->8000/tcp` | 只對本機開放 |
| `docker exec gw whoami` | `appuser` | 不是以 root 執行 |
| `docker exec gw ls -a /app` | `.venv`、`app`、`data` | 映像內沒有 `.env` |
| `docker exec gw python -c "import pytest"` | `ModuleNotFoundError` | 開發工具未安裝（`--no-dev` 生效） |
| `docker exec gw which uv` | 無輸出 | 安裝工具未帶進執行階段 |
| `docker images llm-gateway` | 220 MB（內容 50.9 MB） | 對照 LiteLLM 映像 1.65 GB（E11） |

**附帶的驗證：指紋可重現。** 這次的 `prompt_hash` 與前一天本機直接執行時（E72）**完全相同**（`c9345336…206d`）：同一句話、同一把 HMAC 金鑰，在不同環境算出同一個指紋。這正是指紋能用於「事後比對是否問過這句話」的前提。

**過程中的小錯誤：** 設定 `$b` 時漏打等號（`$b '{...}'`），PowerShell 回報語法錯誤；本人自行補上後重做。

**刻意不執行的指令：** `docker exec gw env`、`docker inspect gw` 會把執行時注入的金鑰印出來。金鑰不在映像裡，但執行中的容器必然持有；驗證時不把它顯示在畫面上（同 E17 的原則）。

**已知限制：**
- 稽核檔寫在容器內，容器停止（`--rm`）後即消失；M2 改寫入 DynamoDB Local 後解決
- 尚未做映像弱點掃描（Trivy 於 CI 建立時加入，10/12 那週）
- 未設定容器健康檢查；M4 由 ECS 與 ALB 的健康檢查負責

**花費：** 輸入 24、輸出 4 token，$0.0000044（同 E72）

**截圖：** `m1-docker-run-ps.png`、`m1-docker-chat-audit.png`、`m1-docker-security-checks.png`（共 14 處提示字元中的使用者資料夾名稱已遮蔽）

**面試可用的說法：**
- 「我的 `.dockerignore` 是白名單：先全部排除，再放行三樣東西。建置時送進引擎的內容只有 307 位元組，`.env` 根本到不了 Docker。」
- 「映像做完我不只測功能，還逐項驗證：`whoami` 不是 root、映像裡沒有 `.env`、`import pytest` 會失敗、`which uv` 找不到。每個設計決定都有一個指令可以證明。」

---

## E75. 第 9 步的 commit、與供應商對帳、M1 結案（2026-10-04 17:07）

**第 9 步 commit：**
- `feat: add Dockerfile with pinned base images and non-root user`、`docs: record M1 step 9 evidence`
- 推送結果：`5e4978a..6d51996  main -> main`

**與 OpenAI Usage 對帳（Project `llm-gateway-capstone`，最近 7 天）：**

| 項目 | OpenAI Usage 顯示 | 本案的稽核紀錄 | 一致 |
|---|---|---|---|
| 請求數 | 2（10/3、10/4 各一） | 2 筆（E72、E74） | ✅ |
| 輸入 token | 48 | 24 + 24 | ✅ |
| 金額 | $0.00（低於顯示精度） | 計算值 $0.0000088 | — |

- 計算：每次輸入 24 × $0.10／百萬 ＋ 輸出 4 × $0.50／百萬 ＝ $0.0000044，兩次共 $0.0000088
- 這是決策書 12.5「與供應商帳單對帳」（預定 M6）的第一次手動比對：供應商記到的呼叫數與輸入 token，和 Gateway 自己記的完全相同
- 日期以 UTC 計：第一次呼叫是台北時間 10/4 00:00，在 Usage 上歸在 10/3

**M1 結案資訊（本人確認）：**
- 投入時間：約 18 小時（9/28～10/4）
- 實際花費：OpenAI $0.0000088；AWS $0
- 對照時程（E60）：W1 目標為 10/4 完成 M1，如期達成

**結案文件：**
- `docs/milestones/m1-report.md`
- `docs/decision-book/decision-book-v2.7.md`（變更對照見結案報告附錄）

**截圖：** `m1-openai-usage.png`

---

## 待決（尚未定案）

| 項目 | 目前的建議 | 何時定 |
|---|---|---|
| ~~M1 稽核紀錄的存放位置~~（✅ 10/3 定案，採用下列建議） | JSON Lines 檔，外面包一層存放函式；M2 啟動 DynamoDB Local 時只換存放函式的實作。不選 SQLite（關聯式，M2 全部作廢）；不選 M1 就上 DynamoDB Local（第一次成功對話前，要先搞定 docker-compose、boto3、建表） | 步驟 6 開工前 |
| ~~VS Code 擴充套件~~ | ✅ 已定案：專用設定檔 `llm-gateway`，6 個官方套件（E36、E37） | 步驟 1 |
| ~~專用設定檔關閉內建 AI 功能~~ | ✅ 已完成（E38） | 步驟 1 |
| `protect-main` 加上「CI 通過才能合併」（D21） | CI 建立後補上；屆時決定是否改為 PR 流程 | 10/12 那週（CI 建立時） |
| CodeQL 與 Copilot Autofix（E48） | 與 pytest、tfsec、Trivy 一起在 CI 建立時評估（M1 結案時改期，已寫入決策書 v2.7 的 12.5） | 10/12 那週（CI 建立時） |
| 結案簡報與錄影的時長（9/30 得知上限約 6 分鐘） | 主影片照 6 分鐘設計（配置已寫入決策書 v2.7 的 11.1）；向指導老師詢問能否延長，或另附詳細版影片 | 與老師討論後 |
| ~~時程的兩個前提：減少例行截圖、M4 Terraform 改用骨架~~ | ✅ 已定案：兩項都採用（E60，10/1） | 10/1 |
| FastAPI 自動文件頁 `/docs`、`/openapi.json` | 預設開啟，會公開列出所有 API；正式環境評估關閉 | M4 上雲前 |
| Gateway 待機記憶體量測（M0／M0.5 報告的待辦，M1 未執行） | `docker stats` 量一次，對照 LiteLLM 的 584 MiB（E16） | M2 開工前 |
| `python:3.12-slim` digest 複查（E74 的冷卻期例外） | 滿 3 天後確認 digest 仍可拉取 | M2 開工前 |
| `m1-gateway` 金鑰 11/2 到期（E71） | M4 另開金鑰放 SSM，或改用工作負載身分聯盟 | M4 前 |

> M1 結案後仍未定案的項目，已同步列入決策書 v2.7 的 12.5 與 M1 結案報告 Part C；M2 的證據紀錄從 E76 開始，另開 `m2-evidence-log.md`。
