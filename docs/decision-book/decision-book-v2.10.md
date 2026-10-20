# LLM Gateway 技術決策書 v2.10(M4 完成)

> **一句話說明這是什麼**
> 一個放在 AWS 上的「AI 收費櫃檯」——公司裡所有人要用 AI，都得先經過它。
> 它負責幫你挑最便宜的 AI 模型、記帳、擋超用的人、留稽核紀錄。

> **v2.10 變更紀錄(2026-10-20,M4 完成)**
> - **M4 ✅(10/20,檢查點 10/25,提前五天):** 10/14～10/15 開工前準備(本機)、10/15 晚上本體開工(Terraform 骨架)、10/17 長期層上雲、10/19 上雲驗收(D、E 段)、10/20 修正 PR #16 合併(`main` = `bd849c1`)。8.2 的 M4 補上結果,11.4 的 S08～S11 標為完成。結案說明見 `docs/milestones/m4-report.md`
> - **雲端跑通(E124):** 每日層 36 個資源上雲,ECS 服務 1 分 8 秒穩定;雲端走完與本機相同的流程(驗 Key、讀額度、遮罩、路由、呼叫、扣額度、寫雲端稽核)
> - **受控出口實測(D89,E124):** DNS 防火牆先 ALERT 約一小時,容器實際查過的網域剛好是放行清單 9 個;切 BLOCK 後 `api.openai.com` 連得上、`example.com` 連地址都查不到,查詢日誌留下 `BLOCK` 紀錄(S08)。Fargate 沒有公開 IP(S09);兩條 Gateway Endpoint 只准特定動作與資源(S10)
> - **工作負載身分聯盟(D71、D72,修訂 D14、4.5):** 雲端**不放 OpenAI 金鑰**:任務角色向東京 STS 要 5 分鐘的身分證明,換 OpenAI 的存取權杖;OpenAI 端專用服務帳號 `gateway-wif`、只開 Chat completions。本機開發仍用金鑰(`OPENAI_AUTH`)
> - **兩層 Terraform(D78～D80,修訂 5.1):** 長期層(State、ECR、三張表、IAM 角色、日誌、告警)平常不拆;每日層(網路、NAT、DNS 防火牆、ALB、ECS)測完就拆。State 鎖改用 S3 鎖檔,不建 DynamoDB 鎖表
> - **destroy workflow(D84～D86):** GitHub OIDC 借角色、repo 裡沒有長期金鑰;C 段第一次實測 51 秒拆光 19 個資源。第二次執行(`destroy #2`,D 段第一次拆)卡在彈性 IP(`ec2:DisassociateAddress` 不能限標籤),本機補拆、問 AWS 確認拆光;已修(PR #16,模擬器 12 題全對),**修正後的「一鍵拆光」待 M5 開工時實測**
> - **CI(D83,修訂 D62):** 加第三個必要檢查 `Config scan`(`trivy config`);Trivy v0.74.0;刻意接受的項目用 `#trivy:ignore` 寫在該行上方、12/31 到期
> - **開工前準備(D68～D70、D73～D77):** 說明頁關閉;資料庫 503 不附 `Retry-After`;SDK 一律不重試、逾時 60 秒、ALB 閒置 120 秒;`DYNAMODB_TARGET`;三個讀取強一致;停用 Key 的腳本;稽核搬進 `audit` 表(寫不進去印一行日誌、回應不變,告警約 1 分鐘寄信);Dependabot
> - **測試:** 267 → 325 個
> - **量測(E124):** `/health` 約 41 ms、聊天 1.7～3.5 秒(多數時間在等 OpenAI)、容器記憶體最高約 14.8%(約 76 MiB)
> - **時間與花費:** M4 實際投入約 27 小時。AWS:D、E 段那一天(10/19 約 20:49～22:38)估約 US$0.22,**Cost Explorer 實際約 US$0.29**(UTC 10/14～10/20 合計,估計值;多出來的主因是 NAT 計了 3 小時:按小時計費要算建好到拆掉整段、不滿一小時進位,M5 E129);長期層閒置幾乎不花錢(E119 估每月不到 US$0.01,當時還沒有日誌、SNS 與映像)。OpenAI:Gateway 自己算的成本加總約 17,500 micro-USD(約 US$0.018,其中 16,322 是量長回答那一次),沒有和後台逐筆對帳(E126)
> - **簡報(11.6):** 10 分鐘版改 v3(37 頁),2.1 架構圖對齊簡報第 7 頁、2.2 對應第 8 頁;S06 右下 10/19 重截
> - 新增 12.11「v2.10 追加定案」(D68～D97);修訂 D4、D7、D10、D13～D16、D19～D22、D34、D36、D43、D47～D49、D51、D52、D59、D62、D67;12.5、PART 9、PART 10、PART 11 同步
> - 證據:E108～E126(`docs/evidence/m4-evidence-log.md`)

> **v2.9 變更紀錄(2026-10-14,M3 完成)**
> - **M3 ✅(10/13,檢查點 10/18,提前五天):** 智慧路由、成本與備援在本機完成;S05～S07 以真的 OpenAI 驗收並錄影(S07 的限流是模擬);測試 119 → 267 個;CI 上線。8.2 的 M3 補上結果,11.4 的 S05～S07 標為完成。結案說明見 `docs/milestones/m3-report.md`
> - **設定檔(D54):** 單價、模型、思考量、輸出上限、路由規則放 `app/config.toml`,啟動時讀進來就檢查,有問題 Gateway 起不來。12.5「沒有單價時的錯誤類型」結案:呼叫前查設定,查不到回 500、寫稽核、不呼叫模型
> - **路由規則定案(D55,修訂 D8):** 字數門檻維持 300;關鍵字拿掉「比較」、改「請比較」「優缺點」,加英文 `design`、`architecture`、`trade-off`、`compare`、`analyze`;英文關鍵字改**字首比對**(`code` 不命中 `decode`)。20 題測試集兩顆模型都真打:**省 25.3%**(簡單題佔 65%、送對 18 題)。不選省 54% 的字數門檻 500
> - **降級定案(D59,補 D10、D32):** 只認預算用完的代碼,其餘 429 當限流;強模型那次不讓 SDK 重試;兩顆都限流回 503 附 `Retry-After`(照抄 1～120 秒)
> - **計費(D56～D58,補 D30、7.10):** 思考 token 已含在輸出 token 裡(實測);兩顆模型的輸出上限都是 2,000;預扣延到 M5;被截斷的回答照樣計費,只記進稽核(本人 10/14 確認維持)
> - **稽核新增七個欄位(D57):** `route_reason`、`routed_model`、`provider_model`、`fallback`、`fallback_reason`、`error_code`、`finish_reason`;`model` 改記實際回答並計費的名稱
> - **CI(D62,修訂 5.1、D21):** pytest(含 `integration`)+ Trivy 掃映像 + CodeQL 預設設定;tfsec 不用(已併入 Trivy);第一次就抓到基底映像的 HIGH,換指紋(修訂 D19);信箱規則改為線性時間(D63)。推送結案文件後 `protect-main` 加「CI 通過才能合併」、改走分支加 PR(D67)
> - **呈現方式(D65,修訂 D41):** 10 分鐘期末報告(本人報告,含 Demo)與 6 分鐘廠商影片(緯育推廣)分開做;取代「6 分鐘主影片 + 技術版」。Demo 播錄影、本人現場口述;錄影用 Windows 內建功能;外行版開場用情境故事(12.5 結案)
> - **時程(D66,修訂 8.2 的 M7、8.4、8.5):** 本人 10/14 決定:用 M3 省下的時間**先把 M4～M6 做完,M7 最後再做**;M7 的第一個開工時段(10/17～10/18)取消,M4 提前到 10/17 開工
> - **D34 修訂:** 金鑰、`.env` 與真實呼叫只在個人電腦
> - **量測:** M3 實際花費 US$0.065(51 次呼叫),與 OpenAI 後台的請求數對得上;約 20 小時
> - 新增 12.10「v2.9 追加定案」(D54～D67);12.5、PART 9、PART 10、PART 11 同步
> - 證據:E94～E107(`docs/evidence/m3-evidence-log.md`)

> **v2.8 變更紀錄(2026-10-09,M2 完成)**
> - **M2 ✅(10/9,原訂 10/10):** 身分、額度、個資偵測在本機完成;S01～S04 以真的 OpenAI 驗收並錄影;測試 17 → 119 個。8.2 的 M2 補上結果,11.4 的 S01～S04 標為完成
> - **額度改放使用者層級(D50,修訂 3.2、D2):** `quotas` 表多一筆固定排序鍵 `limit` 的紀錄存額度;每月一筆的只存已用量。原設計把兩者放在同一筆,換月時新的那一筆沒有人建,所有人會查不到額度
> - **扣額度的做法(D51,補 7.10、2.2):** 呼叫模型前先對當月那一筆加 0,確認寫得進去(寫不進去回 503);模型回答後原子累加實際成本;事後扣失敗時回答照給,稽核記下金額。**M2 會超扣**(實測 892 → 1120),預扣仍是升級路線
> - **稽核 M2 仍存檔案(D52,修訂 D36):** 原訂 M2 搬進 DynamoDB Local,改為 M4 上雲前搬。理由:扣額度失敗的紀錄不能和額度放在同一個資料庫
> - **超額與錯誤回應定案(D46、D48、D49):** 超額回 429 並附 `Retry-After`;驗證失敗一律回相同的 401;資料庫讀不到回 503,驗證與額度共用一個訊息;資料庫連線逾時 2 秒、讀取 5 秒、最多試 2 次(實測預設值要 48.1 秒才報錯)。12.5「超額回應的狀態碼與重試語意」結案
> - **個資遮罩規則定案(D43):** 四類(信箱、信用卡號、手機、身分證字號)、類別標籤、處理順序、信用卡號驗 Luhn;稽核欄位 `pii_types`
> - **指導老師 10/5 回饋後的定案(D41、D42):** 定位為「雲端工程師,做 LLM 上線後的治理層」;影片改為 6 分鐘主影片加一支技術版;簡報是兩支影片的共同骨架;每關驗收錄影;M7 由選配改為有條件開工、做法改為文字約定。1.3、7.9、8.1、8.3、8.4、8.5、PART 9、PART 11 同步
> - **用詞:** 不做的項目一律寫「知識檢索(RAG)」;「向量資料庫」只在講元件或成本時單獨出現
> - **3.2、4.2、D2、D3、D10、D15、D22、D30、D36、D38 補上 M2 的實際做法;** 新增 11.6「簡報與旁白稿」、12.9「v2.8 追加定案」(D41～D53);12.5 更新
> - **量測:** M2 映像待機記憶體 62.06 MiB(M1 為 56.08 MiB);M2 實際花費 US$0.002185(15 次呼叫),與 OpenAI 後台的請求數對得上
> - 證據:E76～E92(`docs/evidence/m2-evidence-log.md`);結案說明見 `docs/milestones/m2-report.md`

> **v2.7 變更紀錄(2026-10-04,M1 完成)**
> - **Bedrock 正式退場(D33,E29):** 不再保留為「可切回的供應商」。架構固定為 NAT + 受控出口 + OpenAI API。3.4、7.1、7.9、PART 9、D23、D24 同步改寫;Zero Egress → 受控出口的轉折留在 7.1 與 E3、E5、E12 作為歷史紀錄
> - **薄介面簡化(D23 修訂,E30):** 由「可換供應商的抽象層」簡化為一個檔案、一個函式(`app/providers/openai_client.py` 的 `chat()`),回傳自訂的 `ChatResult`。保留的理由只剩兩個:測試不花錢、OpenAI 的細節集中一處
> - **摘要順序(D6 修訂,E34):** 固定為**先遮罩、再截斷**。M1 的 `mask()` 是空殼,M2 補上實作
> - **M1 實作定案(12.8,D33～D40):** 開發機只用個人電腦、Python 套件冷卻期(`exclude-newer`)、M1 稽核存放用 JSON Lines、請求格式、上游失敗的處理(稽核記失敗、回 502、只記錯誤類別)、容器建置原則、工作方式
> - **D4、D10、D18、D19、D21、D22 補上 M1 的實際做法:** HMAC 金鑰來源與指紋的輸入、SDK 重試 1 次與逾時 30 秒、容器照 `uv.lock` 安裝、基底映像 digest、`protect-main` 規則集、實際的 repo 結構
> - **8.2 M1 ✅(10/4):** 補上結果;8.3 新增「寫里程碑結案報告」與截圖精簡原則;8.5 更新時程(每週約 25 小時、每週對帳一次)
> - **PART 11:** 結案簡報與錄影上限約 6 分鐘(9/30 得知),11.1 新增 6 分鐘版的配置;11.5 補遮蔽項目(個人帳號名稱、Email、頭像)與「驗證時不把金鑰印出來」
> - **12.5 新增待定:** `/docs` 是否關閉、`protect-main` 的 CI 規則、CodeQL、簡報時長、M1 金鑰到期後的接續
> - 證據:E29～E75(`docs/evidence/m1-evidence-log.md`);結案說明見 `docs/milestones/m1-report.md`

> **v2.6 變更紀錄(2026-09-26,M0、M0.5 全部完成)**
> - **模型定案(D28):** 便宜模型 `gpt-6-luna`($0.10 / $0.50 每百萬 token)、強模型 `gpt-6-sol`($2 / $10)。v2.5 的候選 GPT-5.6 Luna / Terra 仍可用,但新一代 GPT-6 更便宜。兩顆都是推理模型,思考 token 以輸出計費,分別設 `reasoning_effort` 為 `none`、`low`(E20、E22)
> - **呼叫方式(D29):** 用 Chat Completions,不用 Responses(Responses 預設把回應存在 OpenAI 30 天);金鑰權限只開 Chat completions,從權限層保證用不了 Responses(E20、E21)
> - **單價與進位(D30):** 單價放 repo 設定檔;**設定檔沒有單價的模型一律拒絕呼叫**;金額無條件進位成 micro-USD 整數。起因是 M0.5 實測 LiteLLM 內建價格表缺新模型,預算安靜失效(E23),以及浮點數誤差實證(E25)
> - **計費事件順序(D31):** 2.2 流程由「回應與送事件平行」改為「**先確認事件進 SQS,再回應**」。起因是 M0.5 實測 LiteLLM 在寫帳前當機會永久掉帳,並照出本案原設計有同樣的缺口(E26)
> - **兩種 429 分開處理(D32):** 供應商限流 → 降級;供應商預算用完(`project_spend_limit_exceeded`)→ 不降級、回 503;修訂 D10(E20、E21)
> - **D11 修訂:** alice 額度 US$0.01 → **US$0.001**(以 `gpt-6-luna` 單價約 4 次就會被擋)
> - **4.5 補完:** 資料保留政策、OpenAI 端五道防線(儲值上限、Project 硬上限、模型白名單、金鑰最小權限、服務帳號 + 30 天到期);新增 M4 前評估「工作負載身分聯盟」
> - **6.2、6.3 更新:** DNS 防火牆每個網域每月 $0.0005;OpenAI 以最低儲值 $5 計;全期總帳約 US$11
> - **PART 10 新增實測:** 10.1 LiteLLM 花費批次寫入(觀察 4)、負載記憶體;10.3 新增第 10～13 點(價格表缺新模型、寫帳前當機掉帳、SALT_KEY 不能輪替、浮點數誤差);10.5 面試講法更新
> - 8.2 M0 ✅、M0.5 ✅;8.5 時程提前約 4 天;11.4 新增 S21;12.5 更新;新增 12.7「v2.6 追加定案」(D28～D32)
> - 證據:E20～E28(`docs/evidence/m0-evidence-log.md`)

> **v2.5.1 變更紀錄(2026-09-25,M0.5 不需模型的部分完成)**
> - **更正 fail-open 的說法:** v2.2～v2.5 在 10.3、10.5、M2 寫「LiteLLM 沒接資料庫時預算會放行,所以本案反其道而行」,把「沒設資料庫」與「資料庫斷線」兩種情境混在一起。實測 v1.102.0:資料庫斷線預設回 503 拒絕,2 分鐘後仍拒絕,恢復後自動回復(E18);沒設資料庫則無法發虛擬金鑰(E19)。10.1、10.3、10.5、M2 改寫
> - **10.3 改為實測版:** 新增啟動時從 GitHub `main` 分支下載未驗證的價格表(E15)、啟動時自動改資料表結構需高權限(E14)、預算檢查順序與預算 0 的邊界值(E17)、金鑰以 SHA-256 存放(E18)、超額回 429 的重試語意(E17)
> - **10.4 成本措辭修正:** LiteLLM 待機 584 MiB 超過本案 512 MiB,需升至 1 GB,但 Fargate 記憶體便宜,只多約 18%;真正的成本差異是必須常駐 PostgreSQL(E16)
> - 8.2 M0.5 狀態、11.4 的 S19 / S20、12.5 待辦同步更新
> - 證據:E14～E19(`docs/evidence/m0-evidence-log.md`)

> **v2.5 變更紀錄(2026-09-25,供應商與網路層改版)**
> - **模型供應商:Bedrock → OpenAI API。** 帳號層級 Error 002,AWS Support 回覆需有足夠付款紀錄或由業務申請例外(證據 E3、E5),時程風險過高。呼叫模型改走「官方 SDK + 自己包的薄介面」,Bedrock 保留為可切回的供應商(D23、D24)
> - **網路層:Zero Egress → 受控出口(Controlled Egress)。** NAT Gateway(單 AZ)+ Route 53 Resolver DNS 防火牆放行清單 + 安全群組對外只開 443;不再使用 Interface Endpoint,S3、DynamoDB 仍走免費 Gateway Endpoint 並加 Endpoint Policy(D25、D26)。4.1、7.1、7.9 改寫
> - **平台層再確認:** 自建 Gateway,LiteLLM 只在 M0.5 當拆解對照(D23);10.4 刪除「接外部供應商就違背 Zero Egress」這個已不成立的理由
> - **6.2、6.3 改用 M0 實測的東京單價:** Fargate $0.0154/小時(v2.4 低估約 28%)、ALB $0.0243/小時(低估約 8%)、NAT $0.062/小時;全期總帳改為 US$8～16
> - 新增 4.5「外部供應商的風險控管」;新增 12.6「v2.5 追加定案」(D23～D27,含 LiteLLM 冷卻期規則);12.5 更新;D12～D17 修訂
> - 待查證項目(9/28):OpenAI 模型 ID 與官方單價、API 資料保留政策、最低儲值金額、DNS 防火牆每個網域的月費(v2.6 已完成,E20)

> **v2.4 變更紀錄(2026-09-21,開工前定案)**
> - 新增 PART 12「開工前定案清單」:資料模型、稽核雜湊、路由規則、部署觸發、repo 結構等 22 項一次定案,並列出刻意留到各里程碑才定的 5 項
> - 額度單位改為**美元**(原本 Console 畫面用 token,會讓智慧路由與額度脫鉤);`quotas` 表改用 `user_id + period`;新增第四張表 `api_keys`
> - 稽核雜湊改為 HMAC-SHA256,原文不進 SQS 與資料庫;CD 改為手動觸發
> - 新增 8.5 時程與檢查點(10/1 開工、11/7 截止);8.4 定案

> **v2.3 變更紀錄(2026-09-21,網路層與成本更正)**
> - 3.5 VPC Endpoint 由 4 個 Interface 補到 7 個(新增 `sqs`、`ssm`、`ssmmessages`),`ssmmessages` 預設關閉;補「不需要 Endpoint 的服務」與四個必踩的坑
> - 6.2～6.4 改用東京區域單價重算:Interface Endpoint 為 $0.014/小時(v2 誤用美東的 $0.01);全期總帳改為 US$12～22
> - 7.1 改寫:常駐成本 Endpoint 其實比 NAT 貴,選擇理由改為「安全,不是省錢」;更正 v2「NAT 流量經過公開網際網路」的不精確說法
> - 4.1、M4、7.9、PART 9 同步;7.9 新增 DNS 外洩的殘餘風險

> **v2.2 變更紀錄(2026-09-21,依指導老師回饋)**
> - 新增 PART 10:對照拆解 LiteLLM、AWS 原生服務與本專案(十一個監管環節對照、為什麼自建)
> - 新增 PART 11:外行版/內行版呈現策略與 20 張截圖清單
> - 新增 M0.5 LiteLLM 本機拆解實驗;M2 加入個資偵測與 fail-closed;M3 加入模型備援;M6 加入 Trivy 攔截實證
> - 新增 1.4、7.10;7.9 補多供應商、限速、語意快取、管理後台四項「不做」;4.2 補 fail-closed 與個資遮罩

> **v2.1 變更紀錄(2026-09-21)**
> - PART 8 由「按 AWS 服務分層」改為「按可獨立展示的里程碑」(7 個里程碑 + 前置作業),並新增 8.1 AI agent 分層定位、8.3 每關收尾清單、8.4 時間吃緊時的取捨
> - 1.3、7.9、PART 9 同步:明確列出「不做 RAG」與「選配小型 agent」
> - 4.2 「五層防護」更正為「六層防護」(表格本來就是六列)

---

# PART 1 — 這個系統在做什麼

## 1.1 解決什麼問題

某間公司讓 200 個員工都能用 AI，三個月後老闆收到帳單：

| 問題 | 具體情況 |
|---|---|
| **帳單看不懂** | 花了 30 萬，但不知道誰花的、花在哪 |
| **沒人管超用** | 某個工程師寫了個測試迴圈，一個晚上燒掉 5 萬 |
| **沒有稽核紀錄** | 有人把客戶個資貼進 AI，事後查不到 |

這三個問題，正好對應本系統的核心價值。

## 1.2 四大功能

| # | 功能 | 白話說明 |
|---|---|---|
| 1 | **智慧路由** | 問題簡單就用便宜模型，問題複雜才用貴的。像叫外送：買瓶飲料不會叫貨車 |
| 2 | **用量計費** | 每一次呼叫都記帳：誰用的、用了多少 token、換算多少錢 |
| 3 | **限流防護** | 每人每月有額度(以美元計),超過就擋。像手機吃到飽的流量上限 |
| 4 | **稽核紀錄** | 留下時間、來源、內容摘要(去識別化),供資安查核 |

## 1.3 系統邊界(什麼不做)

- **定位(v2.8,D41):** 作者的角色是**雲端工程師,做 LLM 上線之後的治理層**(額度、計費、稽核、網路邊界),不是「替企業做 AI 化」。範圍依這個定位決定
- ❌ 不自建模型、不做訓練 → 只做「調度與治理」
- ❌ 不做多租戶 SaaS → 定位是企業內部平台
- ❌ 不做知識檢索(RAG)→ 見 7.9
- ⭕ **有條件開工:極小 agent 當 Gateway 的客戶** → 見 8.2 的 M7,達到開工條件才做(v2.8,D42)
- ⭕ **對照拆解現成方案(LiteLLM、AWS 原生服務)** → 見 PART 10
- ⭕ **提供輕量 Demo Console(網頁)** → 用於展示內部運作,不是完整產品前端

## 1.4 為什麼不直接用現成的?

> 懂行的人第一個問題通常是:「LiteLLM 或 AWS 自家的服務不就做完了?」
>
> **簡答:** 正式環境我會先評估現成方案。這個專題是把 AI 閘道「拆開來」,親手做出每個環節的最小版本,並把重點放在現成工具不處理的部分:雲端出口管控、權限、稽核設計。完整對照見 PART 10。

---

# PART 2 — 架構全貌

## 2.1 系統架構圖

> **v2.10(對齊簡報第 7 頁「解法提綱｜系統架構」):** 一句話只留「**外面連不進來,出口只放行 OpenAI**」。下圖是 M4 實際建成的樣子(E121～E124);**虛線框是還沒做的** M5(SQS + DLQ、Lambda Worker、`usage` 表)、M6(本機 Grafana、Demo Console)、M7(agent 腳本)。

```
   使用者(只有本人 IP 進得來,HTTP 80)                 OpenAI API
          │                                       api.openai.com、auth.openai.com
          │                                                ▲
 ═════════│════════ AWS VPC 10.0.0.0/16(ap-northeast-1)═══│═══════════
          ▼                                                │
 公有子網  ┌──────────────────┐              ┌───────────────┴──┐
 1a、1c   │       ALB        │              │ NAT Gateway(1a) │──► 網際網路閘道
          │ 閒置逾時 120 秒   │              │  + 彈性 IP        │
          │ 健康檢查 /health  │              └────────▲─────────┘
          └────────┬─────────┘                       │ 對外只開 443
 ══════════════════│═════════════════════════════════│═════════════════
          ▼                              ┌──────────┴──────────────┐
 私有子網  ┌─────────────────────────┐      │ DNS 防火牆:只解析 9 個網域 │
 1a       │ Gateway(ECS Fargate)   │──────►│ 其他一律 BLOCK、留查詢日誌 │
          │ 0.25 vCPU / 0.5 GB      │      └─────────────────────────┘
          │ 沒有公開 IP、根目錄唯讀   │
          │ ┆ Demo Console(M6)┆     │      走 NAT 的 AWS 服務:
          └──────┬──────────┬───────┘      ECR(拉映像)、SSM(三個參數)、
                 │          │               CloudWatch Logs、STS(身分證明)
     Gateway Endpoint(免費,含 Endpoint Policy)
                 ▼          ▼
          ┌───────────┐ ┌──────────────┐
          │ DynamoDB  │ │ S3(ECR      │
          │ api_keys、 │ │ 映像層)       │
          │ quotas、   │ └──────────────┘
          │ audit     │
          └───────────┘

 長期層(平常不拆):S3 State、ECR、三張表、IAM 角色、日誌群組、告警與 SNS
 每日層(測完就拆):VPC、子網、安全群組、Gateway Endpoint、NAT、DNS 防火牆、ALB、ECS

 ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
   M5:Gateway ──► SQS ──► Lambda Worker ──► usage 表;失敗 3 次進 DLQ
 ┆ M6:本機 Prometheus / Grafana ──► ALB 的 /metrics                    ┆
   M7:agent 腳本 ──► Gateway(每一輪都過身分、額度、遮罩、稽核)
 └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

- **和簡報第 7 頁的對應:** VPC、公有/私有子網、ALB、NAT + DNS 防火牆、Fargate(+ Console M6)、DynamoDB、Gateway Endpoint、ECR、SSM、CloudWatch、S3、OpenAI 是實線;M5、M6、M7 是虛線。本人 10/19 的註記:這頁只留架構圖,最下面那行白字拿掉
- **和 v2.9 以前那張圖的差別:** 原圖把 SQS 與 Lambda Worker 畫成實線,M4 還沒有它們(記帳仍由 Gateway 同步完成,見 7.10);雲端先建三張表,`usage` 留 M5(D82)
- **9 個放行網域**見 3.5 的 v2.10 補充(D89)

**v2.9 以前的架構圖(原設計,保留作對照):**

```
                        ┌─────────────┐
                        │   使用者     │
                        │ 瀏覽器 / curl│
                        └──────┬──────┘
                               │ HTTP
    ═══════════════════════════│═══════════════════════════
     AWS VPC                   │
                               ▼
                    ┌──────────────────────┐
    公有子網         │        ALB           │  ← 唯一對外入口
    Public Subnet   │  (Application LB)    │
                    └──────────┬───────────┘
    ═══════════════════════════│═══════════════════════════
                               │
                               ▼
                 ┌───────────────────────────┐
    私有子網      │   Gateway Service         │
    Private       │   (ECS Fargate)           │  ← 沒有 Public IP
    Subnet        │                           │
                  │  ① 驗證身分                │
                  │  ② 查配額                  │
                  │  ③ 智慧路由                │
                  │  ④ 呼叫模型                │
                  │  ⑤ 丟計費事件              │
                  │                           │
                  │  + Demo Console (靜態頁)   │
                  │    FastAPI StaticFiles    │
                  └─┬────────┬────────┬───────┘
                    │        │        │
        ┌───────────┘        │        └──────────┐
        │                    │                   │
        ▼                    ▼                   ▼
  ┌───────────┐      ┌──────────────┐    ┌─────────────┐
  │ DynamoDB  │      │ NAT Gateway  │    │     SQS     │
  │ (配額表)   │      │ → OpenAI API │    │  (出單夾)    │
  └───────────┘      └──────────────┘    └──────┬──────┘
                                                 │ 觸發
                                                 ▼
                                        ┌──────────────────┐
                                        │  Metering Worker │
                                        │    (Lambda)      │
                                        │                  │
                                        │  ① 算成本         │
                                        │  ② 寫用量表       │
                                        │  ③ 寫稽核 log     │
                                        │  ④ 更新配額       │
                                        └────────┬─────────┘
                                                 │
                                    ┌────────────┴──────────┐
                                    ▼                       ▼
                            ┌───────────────┐      ┌──────────────┐
                            │   DynamoDB    │      │  CloudWatch  │
                            │ (用量/稽核表)   │      │    Logs      │
                            └───────────────┘      └──────────────┘

    ═══════════════════════════════════════════════════════
     ⚠️ 受控出口(v2.5):對外只有 NAT 一條路
        DNS 防火牆只解析放行清單內的網域,安全群組對外只開 443
        DynamoDB、S3 走免費的 Gateway Endpoint(含 Endpoint Policy)
```

## 2.2 請求流程圖(一次呼叫發生什麼事,v2.6 修正計費事件順序)

```
使用者送出「幫我摘要這段文字」
    │
    ▼
[1] ALB 收到請求 ────────────────► 健康檢查、路徑判斷
    │
    ▼
[2] Gateway 驗證 API Key ────────► 失敗 → 回 401;資料庫讀不到 → 回 503(fail-closed)
    │ 成功(查出 user_id)
    ▼
[3] Gateway 讀額度與本月已用量 ──► 讀不到 → 回 503(fail-closed)
    │
    ▼
[3.5] 個資偵測與遮罩 ─────────────► 命中就遮罩;稽核只記類別(送出 AWS 前必做)
    │
    ▼
[3.6] 判斷是否超額 ───────────────► 已用 ≥ 額度 → 寫稽核、回 429 並附 Retry-After
    │ 額度足夠
    ▼
[3.7] 對當月已用量加 0 ─────────► 寫不進去 → 回 503(還沒花錢;M2～M4,D51)
    │
    ▼
[4] 智慧路由判斷任務複雜度
    │
    ├── 簡單 ──► 便宜模型 gpt-6-luna
    └── 複雜 ──► 強模型 gpt-6-sol
    │
    │   設定檔裡沒有單價的模型 → 拒絕呼叫(D30)
    ▼
[5] 呼叫 OpenAI(遮罩後內容)──────► 經 NAT;DNS 防火牆只放行 api.openai.com 等清單網域
    │
    ▼
[6] 拿到回應(含 usage:輸入、輸出、思考 token)
    │
    ▼
[7] 丟一筆事件進 SQS ─────────────► 只有中繼資料與 HMAC,不含原文
    │ 確認 SQS 已收到(D31)
    ▼
[8] 回傳給使用者 ✅ (使用者到此結束,不用等記帳)
                    │
                    ▼   (背後非同步)
             [9] Lambda 被 SQS 觸發
                    │
                    ├─ 算成本 (token × 單價,無條件進位成 micro-USD)
                    ├─ 寫用量表
                    ├─ 寫稽核 log(寫入 Gateway 算好的 HMAC 與遮罩摘要)
                    └─ 扣減配額
                    │
                    ▼
             失敗 3 次 ──► 進 DLQ(死信佇列),不會靜靜消失
```

**關鍵設計:** 使用者不用等記帳([9] 在背後做),但**回答之前,帳一定已經進了佇列**。

**v2.6 為什麼改順序(E26):** v2.5 以前寫的是「[7a] 回傳給使用者」與「[7b] 丟事件進 SQS」平行進行。M0.5 實測 LiteLLM 在「回答已送出、帳還沒寫」時被強制終止,那筆帳永久遺失。照原設計寫程式,Gateway 在同樣的瞬間當機也會掉帳:SQS 只保護「已經進到佇列裡」的事件。改成先送 SQS 再回應,每次請求多等一次 SQS 寫入(約十幾毫秒,相對模型回應的數秒可忽略),換到「使用者拿到回答 = 帳一定在佇列裡」。

**生活比喻:** 餐廳出餐前,先把單據夾進出單夾,再把餐端給客人。多花一秒夾單,換到的是:只要客人吃到了,這筆帳就一定在出單夾裡,店員下一秒昏倒也不會漏帳。

**v2.8 補充:M2 實作後的順序與回應(E88、E90、E91)。**

| 步驟 | 失敗時的回應 | 寫不寫稽核 |
|---|---|---|
| [2] 驗證 | `401` `{"detail": "Authentication failed"}`,附 `WWW-Authenticate: Bearer`;沒帶 Key、Key 不存在、Key 被停用三種完全相同 | 不寫(沒有身分可記,也避免被假 Key 灌爆) |
| [2][3][3.7] 資料庫讀不到或寫不進去 | `503` `{"detail": "Service temporarily unavailable"}`;驗證與額度共用一個訊息,不對外透露是哪一塊壞了。**v2.10(D69,E109):不附 `Retry-After`,4 個測試釘住** | 不寫 |
| [3.6] 超額 | `429` `{"detail": "Monthly quota exceeded"}`,附 `Retry-After`(到台北時間下個月 1 號 00:00 的秒數) | 寫,`status` 為 `quota_exceeded` |
| [5] 模型失敗 | `502` `{"detail": "Upstream model error"}`(D37) | 寫,`status` 為 `error` |

- **順序為什麼是「先讀額度、再遮罩、再判斷」:** 讀額度做成 FastAPI 的相依,讀不到的請求進不了主流程;判斷超額時要寫稽核,而稽核需要遮罩後的摘要與個資類別,所以判斷排在遮罩之後。超額的請求仍然碰不到模型
- **資料庫整個連不上時,最先出錯的是 [2] 驗證,**請求走不到額度那一步(S03 的畫面就是這個情況)
- **M2～M4 的 [7]～[9] 還不存在:** 模型回答後由 Gateway 直接把成本加到已用量上、寫稽核(見 7.10、D51);M5 才改成送 SQS、由 Worker 記帳

**v2.9 補充:M3 實作後的順序與回應(E98、E100、E101、E105)。**

驗證(401／503)→ 讀額度(503)→ 遮罩、準備稽核 → 判斷超額(429,寫稽核)→ 加 0(503)→ **選模型,把理由記進稽核** → **查這顆模型的設定(500,寫稽核)** → 呼叫模型,帶思考量與輸出上限;強模型被限流時改用便宜模型一次 → 記模型、用量與結束原因 → 用查到的設定算成本、加到已用量 → 寫稽核 → 回傳。

| 情況 | 回應 | 稽核 |
|---|---|---|
| 訊息超過 4,000 字 | `422`(框架驗證;壞 Key 先回 `401`) | 不寫(沒進對話入口,D38、D64) |
| 路由選到的模型查不到設定 | `500` `{"detail": "Internal server error"}` | 寫,`status: error`、`error_type: ModelNotConfiguredError`;不呼叫模型、不扣錢(D56) |
| 強模型被限流、便宜模型回答 | `200`,`model` 是便宜模型,照便宜模型的單價收錢 | 寫,`fallback: true`、`fallback_reason: RateLimitError` |
| 兩顆都被限流 | `503` `Service temporarily unavailable`,附 `Retry-After` | 寫,`error_code` 記供應商的代碼 |
| 供應商預算用完 | `503`,同一個訊息,**不附** `Retry-After`;不降級 | 寫,`error_code`(例如 `project_spend_limit_exceeded`) |
| 其他供應商錯誤 | `502` `Upstream model error` | 寫,`error_type`、`error_code`(有代碼時) |
| 回答被輸出上限截斷 | `200`,回答可能只有一半或是空的;照樣計費 | 寫,`finish_reason: length` |

- 呼叫的模型和計費的模型來自同一個變數:查設定、呼叫、算成本用的是同一份 `settings`(降級後是便宜模型那一份)
- 兩種 503 對外的訊息相同,不透露是哪一種;分辨靠稽核的 `error_code`

**v2.10 補充:對應簡報第 8 頁;M4 實作後的順序與回應(E109、E115、E116、E124)。**

簡報第 8 頁「解法提綱｜一次呼叫發生什麼事」就是這一節的流程:編號 1～11 排成兩排,只放步驟名;紅框是會擋人的步驟,紅標籤是回的代碼(401、503、429、503、500、502);第 4 步「遮罩個資」用綠色標出(之後的內容都是遮罩後的);其餘口述;底下的虛線框寫 M5 的改法(即上方 [7]～[9],D31)。

M4 的順序與 M3 相同,差在最後兩步與上雲後的環境:

驗證(401/503)→ 讀額度(503)→ 遮罩、準備稽核 → 判斷超額(429,寫稽核)→ 加 0(503)→ 選模型 → 查設定(500,寫稽核)→ 呼叫模型(SDK 一律不重試、逾時 60 秒;強模型被限流時改用便宜模型一次)→ 用查到的設定算成本、加到已用量 → **寫稽核進 `audit` 表**(寫不進去時印一行日誌,回應不變)→ 回傳。

| 情況 | 回應 | 稽核 |
|---|---|---|
| 稽核寫不進 `audit` 表(資料庫拒絕或連不上) | **不變**:成功照給 200、超額照 429(附 `Retry-After`)、上游錯誤照 502 | 那一筆不在表裡;`save_audit()` 只接資料庫的錯,交給 `report_audit_failure()` 印一行 JSON 到 stderr(Fargate 上進 CloudWatch Logs):`event: audit_write_failed`、`request_id`、`user_id`、`timestamp`、`status`、`cost_micro_usd`、`charged`、`error_type`,**不含摘要與 HMAC**;CloudWatch 指標篩選抓這一行並告警(D77、D95) |
| 資料庫讀不到或寫不進去(驗證、讀額度、加 0) | `503`,**不附** `Retry-After`(多久恢復無從得知),4 個測試釘住(D69) | 不寫 |
| 兩顆模型都被限流 | `503`,附 `Retry-After`(照抄 1～120 秒);SDK 不在背後等(D70) | 寫,`error_code` |

- **在容器裡實測(E116):** 開發用資料庫刪掉 `audit` 表後再問一次 → `200`、日誌多一行 `audit_write_failed`(`error_type: ResourceNotFoundException`、`cost_micro_usd: 9`、`charged: true`);表建回來後查不到那個單號,證明那一筆真的只留在日誌。這一行出現在 uvicorn 的 `POST /v1/chat 200` 之前:稽核在回應交出前就寫(或失敗)
- **雲端實測(E124):** bob 一次 `Say good morning in French` → `Bonjour !`、`gpt-6-luna`;雲端稽核 `status: ok`、`charged: True`、`cost_micro_usd: 4`(12 × 0.1 + 5 × 0.5 = 3.7 → 4)、`pii_types: []`、64 字 `prompt_hash`
- **M4 的 [7]～[9] 仍不存在**,記帳仍由 Gateway 同步完成(7.10);稽核寫不進去的正式解法是 M5 的 SQS

---

# PART 3 — 每個服務負責什麼

## 3.1 運算層

### Gateway Service(ECS Fargate)
> **角色比喻:** 餐廳前台服務生

| 項目 | 內容 |
|---|---|
| **技術** | Python + FastAPI,打包成 Docker 容器 |
| **位置** | 私有子網,**無 Public IP** |
| **規格** | 0.25 vCPU / 0.5 GB(最小規格) |
| **職責** | 驗證身分 → 查配額 → 個資遮罩 → 智慧路由 → 呼叫模型供應商(OpenAI)→ 發計費事件 → 回傳 |
| **對外介面** | `POST /v1/chat`、`GET /health`、`GET /metrics`、`GET /`(Console) |

> **v2.10(M4 實作,E116、E123、E124):** 任務定義 `cpu = 256`、`memory = 512`、`X86_64`;根目錄唯讀(`readonlyRootFilesystem`,程式不再寫檔、`Dockerfile` 不建可寫的資料夾);沒有公開 IP;ALB 健康檢查打 `/health`,開部署斷路器、起不來自動退回;沒有 ECS Exec(D94)。目前實際的對外介面只有 `POST /v1/chat`、`GET /health`;說明頁 `/docs`、`/redoc`、`/openapi.json` 一律關閉(D68);`/metrics` 與 Console 在 M6。雲端實測:ECS 服務 1 分 8 秒穩定,記憶體最高約 14.8%(D15)。

### Metering & Audit Worker(AWS Lambda)
> **角色比喻:** 後台會計

| 項目 | 內容 |
|---|---|
| **技術** | Python |
| **觸發方式** | SQS 有訊息就自動觸發(事件驅動) |
| **位置** | 同樣掛在私有子網 |
| **職責** | 計算成本 → 寫用量表 → 寫稽核 log → 更新配額 |
| **失敗處理** | 重試 3 次仍失敗 → 送進 DLQ |

### Demo Console(內建靜態網頁)
> **角色比喻:** 引擎的儀表板——不只聽引擎聲,而是直接看轉速表

| 項目 | 內容 |
|---|---|
| **技術** | 單頁 HTML + 原生 JavaScript,由 FastAPI `StaticFiles` 提供 |
| **部署** | **打包在 Gateway 容器內**,不另開 S3 / CloudFront |
| **額外成本** | **$0**(共用現有 ALB 與 Fargate) |
| **路徑** | `GET /` |
| **職責** | 讓「智慧路由的判斷」「即時成本」「配額扣減」「限流被擋」這些內部行為**看得見** |

**畫面設計(重點是可視化內部運作,不是漂亮的產品官網):**

```
┌────────────────────────────────────────────┐
│  LLM Gateway Console                       │
├────────────────────────────────────────────┤
│  API Key: [________]   使用者: alice        │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ 輸入你的問題...                        │  │
│  └──────────────────────────────────────┘  │
│                          [ 送出 ]           │
├────────────────────────────────────────────┤
│  ⚙️ 路由決策                                │
│     複雜度判定:簡單 → gpt-6-luna            │
│                                            │
│  💬 回應                                    │
│     (模型輸出...)                           │
│                                            │
│  📊 本次用量                                │
│     Input 120 / Output 340 tokens          │
│     成本 US$0.000182                       │
│                                            │
│  🎫 剩餘配額                                │
│     ████████░░  US$0.00082 / US$0.00100    │
└────────────────────────────────────────────┘
```

**Demo 腳本(面試展示用):**

| 步驟 | 操作 | 觀眾看到什麼 |
|---|---|---|
| 1 | 送出簡單問題 | 路由選擇便宜模型,成本極低 |
| 2 | 送出複雜問題 | 路由改選強模型,成本上升 |
| 3 | 連續呼叫至超額 | **畫面跳出 429,配額條變紅** |
| 4 | 切到 Grafana | 剛才幾筆呼叫出現在統計曲線上 |

> **v2.9(D65):** 期末報告的 Demo 改為三章:**節費**(兩題分到不同模型、省多少、Grafana 依使用者與模型的花費)、**個資**(請 AI 原樣唸一次、稽核反查)、**額度**(用完被擋)。10 分鐘報告播錄影、本人現場口述;錄影用兩個帳號(額度正常的錄路由與個資,額度很小的錄被擋)。M3 的 S05～S07 已有終端機版本的錄影,M6 用 Console 重錄。

## 3.2 資料層

### DynamoDB(四張表,v2.4 定案)

| 表名 | 存什麼 | 主鍵 | 誰讀寫 |
|---|---|---|---|
| `api_keys` | API Key 的 SHA-256 雜湊 → `user_id`、`status`(值是 `active` 才放行,其餘一律拒絕,含欄位不存在;v2.8) | `key_hash` | Gateway 只讀;種子腳本寫入 |
| `quotas` | 額度與每月已用量(micro-USD 整數)。**v2.8:分成兩種紀錄**:`period` 為固定字串 `limit` 的那一筆存 `limit_micro_usd`(額度,跟著人);`period` 為 `YYYY-MM` 的每月一筆存 `used_micro_usd`(已用量) | `user_id` + `period` | Gateway 讀;M2～M4 由 Gateway 累加,M5 起由 Worker 累加 |
| `usage` | 每一筆呼叫的 token、模型、成本 | `user_id` + `timestamp` | Worker 寫 |
| `audit` | 時間、`user_id`、模型、內容 HMAC、遮罩摘要、個資類別(`pii_types`)、狀態(`ok`、`error`、`quota_exceeded`)、token 數、`cost_micro_usd`、`charged`(有沒有扣到額度) | `request_id` | Worker 寫(M5 起)。**v2.8:M2 仍寫本機檔案,M4 上雲前搬進這張表(D52)。v2.10:已搬(D77,E116);M4 由 Gateway 以條件寫入,只有 `PutItem` 權限** |

> **為什麼分四張表?**
> - `api_keys`、`quotas` 是「熱資料」,每次請求都要讀,需要極低延遲;`usage`、`audit` 是「冷資料」,只有查報表時才讀
> - 分開也方便做最小權限:Worker 的 IAM 角色**完全碰不到** `api_keys`
>
> **為什麼 `quotas` 用 `user_id + period`?** 換月時自然是新的一筆,不需要寫「每月重置」的排程。像每個月換一本新的記帳本,舊的留著當紀錄。
>
> **v2.8 修訂(D50,E91):這句話只對已用量成立。** v2.4～v2.7 把額度和已用量放在同一筆裡。實作時發現:換月那天新的一筆沒有人建,所有人都查不到額度,等於還是需要一支每月「開帳」的排程。改成額度放在使用者層級的固定一筆(`period = "limit"`),已用量才是每月一筆。**生活比喻:** 信用卡的額度印在卡片上,每個月換的只是帳單。
> - 查不到當月的已用量 → 當成 0,放行(這個月還沒用過)
> - 查不到額度那一筆 → 當成額度 0,回 429(只會在帳號沒設定好時發生;不能變成沒有上限)
> - 已用 **≥** 額度就擋;額度 0 是嚴格上限,不是無上限(E17、E88)
>
> **v2.9 稽核新增的欄位(D57,E98、E100、E101):**
>
> | 欄位 | 記什麼 | 哪些紀錄有 |
> |---|---|---|
> | `route_reason` | 為什麼選這顆:`length`、`keyword`、`default` | 走到路由的請求 |
> | `routed_model` | 路由選的模型 | 同上 |
> | `model` | **實際回答、也拿來計費的名稱**(降級後是便宜模型;M2 記的是供應商回報的名稱) | 成功的紀錄 |
> | `provider_model` | 供應商回報的名稱,可能帶日期尾碼;換了代表模型換版,是重跑測試集的訊號 | 成功的紀錄 |
> | `fallback`、`fallback_reason` | 有沒有降級;降級了才記原因(錯誤類別名稱) | 走到呼叫模型的紀錄 |
> | `error_code` | 供應商錯誤的短代碼(例如 `rate_limit_exceeded`),不記訊息 | 供應商回應的錯誤 |
> | `finish_reason` | `stop` 正常說完、`length` 被輸出上限截斷 | 成功的紀錄 |
>
> 被額度擋下(`quota_exceeded`)的紀錄沒有路由與降級的欄位:它在路由之前就結束了。
>
> **M2 只建三張表:** `api_keys`、`quotas`、`audit`(`audit` 已建表但 M2 尚未寫入);`usage` 於 M5 建立(E89)。
>
> **v2.10:三張表上雲(D74、D75、D77、D82,E111、E116、E118、E119、E124)。**
>
> | 項目 | 做法 |
> |---|---|
> | 雲端建幾張 | 長期層先建三張(`api_keys`、`quotas`、`audit`),`usage` 的欄位 M5 才定,留到 M5;代價是 Endpoint Policy 與 IAM 之後要補一張 |
> | 計費模式 | 隨需(`PAY_PER_REQUEST`),與練習場相同;預置容量要自己估,Demo 時可能被 `ProvisionedThroughputExceeded` 擋下。試算(美東價):1,000 個請求合計不到 US$0.002 |
> | 防刪 | `deletion_protection_enabled`(AWS 層級,主控台與 CLI 也刪不掉;實測 `delete-table` 被擋);PITR 開啟(`recovery_period_in_days = 35`) |
> | 連哪裡 | 環境變數 `DYNAMODB_TARGET`:`aws` → 東京真的 DynamoDB(不給網址、不給帳密,身分用 Fargate 的任務角色);`http://`、`https://` 開頭 → 那個網址的練習場(假帳密 `local`);沒設 → `KeyError`;其他值 → `ValueError`(D74) |
> | 強一致讀取 | 查 Key(`find_user_id`)、查額度(`read_limit`)、查已用量(`read_used`)都加 `ConsistentRead=True`;讀取費用 2 倍,Demo 的量一個月不到一分錢;練習場不管這個參數,測試只能檢查「有沒有帶」(D75) |
> | 稽核寫入 | `write_audit()`:`put_item` 加 `ConditionExpression="attribute_not_exists(request_id)"`,同一個單號已存在就拒絕、不覆蓋(`put_item` 預設會直接覆蓋、不報錯);寫不進去見 2.2 的 v2.10 補充(D77) |
> | `pii_types` 的型別 | **清單(`L`)**,不用 String Set(`SS`):DynamoDB 不收空的 Set、Set 不保留順序;D43 要求空清單代表「檢查過、沒找到」、順序固定(實驗:改成 Set 後順序亂掉、空的被拒收,被額度擋下的那筆根本沒進表)(D77) |
> | Gateway 的權限 | `audit` 只給 `PutItem`(不給 `UpdateItem`、`DeleteItem`,稽核不能被改);`api_keys` 只讀;`quotas` 讀 + `UpdateItem`(D90) |
> | 走哪條路 | DynamoDB Gateway Endpoint,Endpoint Policy 只准三張表的 `GetItem`、`PutItem`、`UpdateItem`(3.5) |
>
> **雲端種子資料(E124):** `DYNAMODB_TARGET=aws` 跑 `scripts.seed`,輸出整段收進變數,只印 Key 的長度(67)。限制:雲端的 alice、bob Key 只存在當時的 PowerShell 變數裡;表在長期層,Key 的雜湊還在 `api_keys` 表。
>
> **為什麼金額存 micro-USD 整數?** 一次呼叫可能只花 US$0.0000068,用小數容易累積誤差;存成整數(0.0000068 美元 → 6.8 → 無條件進位成 7 micro-USD,D30)再換算,算幾萬次都不會差一分。M0.5 實測 LiteLLM 以浮點數記帳,0.0000068 被存成 6.799999999999999e-06(E25),這是 v2.4 定案時的理由第一次得到實證。
>
> **時區注意(E23):** LiteLLM 以 UTC 儲存時間。本案 `period` 以台北時間切月,`timestamp` 與 `period` 的換算在 M2 寫成單一函式並加 pytest(例如台北 10/1 00:30 = UTC 9/30 16:30,應歸入 10 月)。
>
> **v2.8 實作(D44,E86、E91):** `app/quota.py` 的 `period_of(moment)`,以固定偏移 `TAIPEI_TZ`(UTC+8)換算後回傳 `YYYY-MM`;只收帶時區的時間,沒帶時區丟 `ValueError`;不使用時區資料庫與 `tzdata`(台灣沒有日光節約時間;固定偏移在 Windows、容器、Lambda 三個環境一定一致)。同一個請求裡的 `period`、`Retry-After`、稽核時間用同一個「現在」。
>
> **v2.8 個資類別欄位(D43,E85):** `pii_types` 的值是不含中括號的類別名稱清單,順序固定為 `EMAIL`、`CARD`、`PHONE`、`TW_ID`;同一類出現多次只記一次;沒有個資時是空清單(「檢查過沒找到」和「沒有這個欄位」要分得出來);成功、失敗、被額度擋下的紀錄都有這一欄。
>
> **v2.8 本機的資料庫連線(D47、D49,E89、E90):** M2～M3 用 DynamoDB Local。連線由 `app/db.py` 的 `make_dynamodb_client()` 建立:網址來自**必填**的環境變數 `DYNAMODB_ENDPOINT_URL`(boto3 不給網址時預設連真的 AWS,並自動使用電腦上的身分,所以沒設就報錯);連線逾時 2 秒、讀取逾時 5 秒、最多試 2 次(含第一次)、重試模式 `standard`。實測 boto3 的預設值在資料庫連不上時要 48.1 秒才報錯,設定後 6.7 秒。
>
> **v2.10 修訂(D74,E111):** 環境變數改名為 `DYNAMODB_TARGET`(見上方的 v2.10 表),逾時與重試不變。改名時真的遇過:PowerShell 視窗裡留著舊的 `DYNAMODB_ENDPOINT_URL`,43 個測試連到開發用的練習場、清空了資料表,而且全部綠燈;改名剛好把這條路斷掉。

## 3.3 通訊層

### SQS(Standard Queue + DLQ)
> **角色比喻:** 餐廳的出單夾

| 項目 | 內容 |
|---|---|
| **主佇列** | `metering-events` — 存放待處理的計費事件 |
| **死信佇列(DLQ)** | `metering-events-dlq` — 處理失敗 3 次的事件會被丟到這裡 |
| **為什麼要 DLQ** | 沒有 DLQ 的話,壞掉的訊息會消失得無聲無息,帳就對不起來 |
| **送出時機(v2.6)** | Gateway 確認事件送進 SQS 之後才回應使用者(D31) |

## 3.4 AI 模型層(v2.5 改為 OpenAI,v2.6 定案模型)

### OpenAI API

| 項目 | 內容 |
|---|---|
| **呼叫方式** | 官方 Python SDK,外面包一個薄介面函式(`app/providers/openai_client.py` 的 `chat()`),回傳自訂的 `ChatResult`(文字、模型、輸入 / 輸出 / 思考 token)。目的是測試不花錢、OpenAI 的細節集中一處,**不是**為了換供應商(v2.7,D23、E30)。SDK 設 `max_retries=1`、`timeout=30` 秒(D10、E70)。**v2.10 修訂(D70):`OPENAI_MAX_RETRIES = 0`(所有呼叫都不讓 SDK 重試)、`OPENAI_TIMEOUT_SECONDS = 60`;整個程式共用一個連線物件(D72)** |
| **API** | **Chat Completions**(`/v1/chat/completions`);不用 Responses(D29) |
| **連線路徑** | 私有子網 → NAT Gateway → `api.openai.com`,受 DNS 防火牆放行清單管控(4.1) |
| **驗證** | API Key 放 SSM SecureString,容器啟動時注入;不寫成明文環境變數。M4 前評估工作負載身分聯盟(4.5)。本機開發(M1～M3)放 `.env`:不進 Git、不進映像,執行時才以 `--env-file` 提供(E71、E74)。**v2.10 修訂(D71、D72):雲端改用工作負載身分聯盟,SSM 不放 OpenAI 金鑰;`OPENAI_AUTH` 一定要明講 `api_key`(本機)或 `workload_identity`(雲端)** |
| **便宜模型** | **`gpt-6-luna`**:輸入 $0.10 / 輸出 $0.50 每百萬 token;`reasoning_effort: none`(D28) |
| **強模型** | **`gpt-6-sol`**:輸入 $2 / 輸出 $10 每百萬 token;`reasoning_effort: low`(D28) |
| **推理模型注意** | 兩顆都會先「想」再答,思考用的 token 以**輸出單價**計費,預設思考量為 `medium`。成本一律用回應的 `usage` 計算(含 `reasoning_tokens`),不能只數看得到的字(E22 實測 `none` 時為 0)。v2.8:M2 的成本函式用「輸出 token × 輸出單價」,不另外加思考 token(M1 的 E59:輸出 token 已含思考 token);`gpt-6-luna` 設 `none` 時為 0,M2 不受影響,M3 用 `gpt-6-sol` 的一次真實回應再實證(12.5) |
| **供應商端防線** | 本專案專用 Project:儲值上限、硬性花費上限、模型白名單、金鑰最小權限(4.5) |
| **測試用模型** | 便宜模型(避免測試燒錢) |

**v2.9 補充(M3,E100、E101、E103):**

| 項目 | 內容 |
|---|---|
| 設定 | 模型名稱、思考量、輸出上限、單價都在 `app/config.toml`(D54);程式裡沒有寫死的模型名稱 |
| 輸出上限 | `max_completion_tokens`:`gpt-6-luna` 2,000、`gpt-6-sol` 2,000(D58)。一次最多:便宜模型 1,000 micro-USD,強模型約 20,000 加輸入 |
| 思考 token | **已實證算在輸出 token 裡**:強模型上限壓到 16 時,輸出 16、其中思考 16、回答 0 字,照收。成本 = 輸入 × 輸入單價 + 輸出 × 輸出單價,不另加。強模型思考量 `low` 時,20 題的思考 token 只有 0～49 |
| SDK 重試 | 強模型那次 `client.with_options(max_retries=0)`,讓降級本身當作重試;便宜模型保留 1 次。實測(本機假伺服器):SDK 對 429 會重試,連預算用完也重試;照 `retry-after` 等,最多 120 秒;30 秒的逾時不含重試前的等待(D59) |
| 單價再查 | 10/12 再查官方價目表:不變。官方已有同價的 `gpt-6.1-sol`,本案維持 `gpt-6-sol`(換模型要改 OpenAI 端白名單、重做實測);`gpt-6-sol` 沒有棄用公告(E103) |

**v2.10 補充(M4,E109、E110、E113～E115、E123、E124):**

| 項目 | 內容 |
|---|---|
| SDK 重試 | **一律不重試**(`OPENAI_MAX_RETRIES` 1 → 0)。理由:SDK 遇到限流會在背後照 `retry-after` 等最多 120 秒,放到 ALB 後面,ALB 先切斷連線,Gateway 卻還在背後呼叫、扣錢;改成被限流直接回 503 與 `Retry-After`,由使用者決定要不要等。強模型那次的 `with_options(max_retries=0)` 保留(有人把常數改回 1 時仍不重試)。代價:網路瞬間抖動或偶發的 5xx 直接回 502(D70) |
| 逾時 | 30 → **60 秒**。容器實測強模型寫 1,576 個 token 花 25.6 秒(約每秒 62 個),寫滿上限 2,000 個約 32 秒,30 秒一定逾時,而且 OpenAI 可能已經收費;ALB 閒置逾時配合設 **120 秒**(強模型 60 + 降級後便宜模型 60)。60 秒是一個樣本推出來的(D70) |
| 驗證方式 | **工作負載身分聯盟**:任務角色用東京 STS 地區網址(`https://sts.ap-northeast-1.amazonaws.com`)要一張 audience `llm-gateway-capstone`、ES384、300 秒的身分證明(JWT),SDK 拿去 `https://auth.openai.com/oauth/token` 換最多 1 小時的存取權杖,到期前自動重換(D71) |
| 切換 | `app/openai_auth.py`:`read_openai_auth()` 讀 `OPENAI_AUTH`,只收 `api_key`、`workload_identity`(沒設 `KeyError`、其他 `ValueError`);`make_openai_client()` 金鑰模式交給 SDK 讀 `OPENAI_API_KEY`,身分聯盟模式把 `get_aws_identity_token` **本身**(不加括號)交給 SDK;`app/main.py` 啟動時就讀 `OPENAI_AUTH`,`get_client()` 加 `@lru_cache(maxsize=1)` 共用一個連線,權杖才會被重複使用到快到期才換(D72) |
| OpenAI 端 | 身分提供者 `aws-outbound-capstone`(Issuer = 帳號專屬的 AWS 對外身分聯盟網址,Audience `llm-gateway-capstone`);專用服務帳號 **`gateway-wif`**(不用 `m1-gateway`),權限 Restricted、只開 Chat completions;對應 **`gateway-task-role`**:`sub` = 任務角色 `llm-gateway-task` 的 ARN。10/14 探測用的對應(`sub` 是本人的 IAM 使用者)10/19 已刪 |
| SSM 放什麼 | 不放 OpenAI 金鑰;放身分提供者 ID 與服務帳號 ID(`user-` 開頭,10/19 實測是對的)兩個 SecureString(D91) |
| 實測 | 10/14 探測:`chat.completions` 收這種權杖(官方範例只示範 `responses`);audience 改錯 → AWS 照開證明、OpenAI 在換權杖那一步拒絕(`OAuthError`)。10/19 雲端:Fargate 上叫得到 `gpt-6-luna`,**雲端沒有 OpenAI 金鑰** |
| 本機 | 本機開發與 11/2 之後的錄影仍用金鑰(`OPENAI_AUTH=api_key`);`m1-gateway` 11/2 到期,到期前在個人電腦換一把(12.5) |

**為什麼換掉 Bedrock(證據 E3、E5):** 帳號呼叫任何模型都回 `Error 002: Access to Bedrock models is not allowed for this account`,連 Amazon Nova 也一樣,屬帳號層級封鎖。AWS Support 結案回覆:消費紀錄少的帳號通常不開放模型存取,需由業務申請例外。業務表單與指導老師兩條路都在等回覆,但 M3 需要實際呼叫模型,時程等不起。

**為什麼選 OpenAI 而不是 Anthropic API(D24):** 兩者都要對外連線,網路設計相同。OpenAI 的 API 格式是業界最通用的「相容格式」,便宜與強模型的價差也較大(v2.6 定案的兩顆差 20 倍),智慧路由的省錢效果較好展示。Anthropic API 的優點是 Haiku / Sonnet 路由與原設計完全相同、文件改動最少,但沒有推翻原決定的強理由。

**為什麼是 GPT-6 而不是 v2.5 的候選 GPT-5.6(D28,E20):**

| 模型 | 輸入 / 輸出(每百萬) | 判斷 |
|---|---|---|
| **`gpt-6-luna`** | $0.10 / $0.50 | ✅ 便宜模型 |
| **`gpt-6-sol`** | $2 / $10 | ✅ 強模型 |
| `gpt-5.6-luna` | $0.20 / $1.20 | 貴一倍以上,且是上一代 |
| `gpt-5.6-terra` | $2 / $12 | 輸出比 Sol 貴 20% |
| `gpt-6-astra` | $10 / $50 | 旗艦,Demo 預算撐不住;在 OpenAI 端白名單直接擋掉(E22) |

**Bedrock 的位置(v2.7,D33、E29):** **已退場,不再保留為切回選項。** v2.5、v2.6 寫「保留為可切回的供應商」;但一條永遠不會實作、也沒驗證過的切回路線,會讓文件同時存在兩套網路設計(受控出口與 Zero Egress),被追問時拿不出證據。帳號封鎖的兩條路(業務例外、指導老師)也都沒有結果。Zero Egress → 受控出口的轉折仍是專題故事的一部分,留在 7.1 與 E3、E5、E12。

## 3.5 網路層

| 元件 | 說明 |
|---|---|
| **VPC** | 自建虛擬網路,10.0.0.0/16 |
| **公有子網** | 只放 ALB;**必須兩個 AZ 各一個**(ALB 的硬性規定) |
| **私有子網** | 放 Fargate + Lambda;預設路由指向 NAT;單一 AZ(見 7.9) |
| **ALB** | 唯一對外入口,做健康檢查與路徑路由 |
| **NAT Gateway** | **使用(v2.5)**,單 AZ,放在公有子網;私有子網對外的唯一出口(見 7.1) |
| **DNS 防火牆** | Route 53 Resolver DNS Firewall 掛在 VPC 上:放行清單內的網域可解析,其餘一律封鎖並記錄(v2.5) |
| **安全群組** | Fargate、Lambda 對外只開 TCP 443 |

### VPC Endpoint 清單(v2.5:只保留免費的 Gateway Endpoint)

| Endpoint | 類型 | 費用 | 用途 | Endpoint Policy |
|---|---|---|---|---|
| `s3` | **Gateway** | **免費** | ECR 映像層實際存放位置 | 只允許 ECR 映像層 bucket(D16 修訂)。**v2.10 實作:只准 `s3:GetObject` `arn:aws:s3:::prod-ap-northeast-1-starport-layer-bucket/*`** |
| `dynamodb` | **Gateway** | **免費** | 讀寫資料表 | 只允許本專案四張表。**v2.10 實作:只准 `GetItem`、`PutItem`、`UpdateItem`,範圍限三張表(`usage` M5 補)** |

**v2.4 的 7 個 Interface Endpoint 為什麼全部拿掉(D26):** 有了 NAT 之後,Interface Endpoint 已無法保證「沒有對外路徑」。它剩下的價值是 Endpoint Policy 的資料邊界(限制只能存取自己帳號的資源),但本案的 DNS 防火牆已接受「直接用 IP 連線」這個殘餘風險,攻擊者繞得過 DNS,就繞得過 Endpoint Policy 擋的那條路。多付約一倍常駐成本(50 小時 ~$6.9 對 ~$3.4)只買到部分保護,與整體取捨不一致。Demo 流量小,也省不到 NAT 的流量費。

**ECR、CloudWatch Logs、SQS、SSM 改走 NAT:** 流量仍在 AWS 網路內,只是入口從私有 Endpoint 變成服務的公開位址;這些網域必須列入 DNS 防火牆放行清單。

**ECS Exec:** `ssmmessages` 改走 NAT;Terraform 變數 `enable_ecs_exec`(預設 `false`)仍控制 ECS 服務的 `enable_execute_command`,維運通道平常不開。

> **v2.10 修訂(D94,E123):ECS Exec 不做;ECS 服務寫死 `enable_execute_command = false`,沒有 `enable_ecs_exec` 這個變數。** 做的話放行清單要加 `ssmmessages` 等網域、任務角色多權限、本機裝 Session Manager 外掛,唯讀根目錄下還要另外掛可寫的資料夾,與「出口管很緊」反方向。S08 改用一次性任務(同一個任務定義與映像,臨時把啟動指令換成一小段 Python)證明出口管控。

**為什麼 Lambda 仍放 VPC 內(D12 修訂):** 放在 VPC 外的 Lambda 可以直接連網際網路,會繞過 DNS 防火牆與安全群組。放在 VPC 內,它和容器受同一套出口管控。

> ⚠️ **必踩的坑(M4 一定會遇到):**
> 1. **放行清單不能寫 `*.amazonaws.com`:** 攻擊者可以把資料上傳到**他自己帳號的 S3 bucket**,網域一樣是 amazonaws.com。要逐一列出具體網域
> 2. **先告警、後阻擋:** DNS 防火牆先用 ALERT 動作跑一輪,從 Resolver 查詢日誌整理容器實際查詢的網域,再切成 BLOCK。直接上 BLOCK 很容易漏掉 ECR 或 Logs 的網域,Fargate 會卡在 `CannotPullContainerError`
> 3. **S3 Endpoint Policy 寫錯會拉不到映像:** 只放行 ECR 映像層 bucket 時,bucket 名稱要照 AWS 文件的東京區域寫法
> 4. **安全群組管不到 VPC 的 DNS 伺服器:** 安全群組不過濾送往 Amazon 提供的 DNS 的流量,所以「對外只開 443」不會讓 DNS 失效;反過來說,DNS 層的管控只能靠 DNS 防火牆
> 5. **ALB 兩個 AZ:** ALB 必須掛在兩個不同 AZ 的公有子網;Fargate 與 NAT 仍只放一個 AZ

### v2.10:M4 實際建成的網路(E121～E125)

| 元件 | 實作 |
|---|---|
| VPC | `10.0.0.0/16`,開 DNS 支援與主機名稱 |
| 公有子網 | `10.0.0.0/24`(1a)、`10.0.1.0/24`(1c);`map_public_ip_on_launch = false`(不自動發公開 IP);路由 `0.0.0.0/0` → 網際網路閘道 |
| 私有子網 | `10.0.10.0/24`(1a,與 NAT 同 AZ);路由 `0.0.0.0/0` → NAT;S3、DynamoDB 兩條 Gateway Endpoint 只接這張路由表 |
| NAT Gateway | 單一 AZ(1a)+ 彈性 IP(D13) |
| 安全群組 | `alb`:入 80 只准 `admin_cidr`(本人公開 IP,只收 `/32`),出 8000 只到 `gateway`;`gateway`:入 8000 只准從 `alb`,出 443 到 `0.0.0.0/0`(Trivy AWS-0104 刻意接受:OpenAI 的 IP 不固定,只能用網域管)。每條規則一個資源 |
| 預設資源 | 認領預設安全群組、清空規則(忘了指定安全群組的東西不會套到「對外全開」);主路由表、預設網路 ACL 不認領(刪 VPC 時一起消失)(D88) |
| DNS 防火牆 | 規則群組 `llm-gateway-egress`:優先序 100 `ALLOW` 放行清單(`TRUST_REDIRECTION_DOMAIN`:不拿 CNAME 指過去的名字再比一次);優先序 200 其他全部(`*.`)由變數 `dns_firewall_action` 控制,先 `ALERT`、整理完查詢日誌再 `BLOCK`(回 `NODATA`);查詢日誌寫進 `/llm-gateway/dns-queries`(D89) |
| 放行清單(9 個) | `api.openai.com`、`auth.openai.com`、`sts.ap-northeast-1.amazonaws.com`、`api.ecr.ap-northeast-1.amazonaws.com`、`<account-id>.dkr.ecr.ap-northeast-1.amazonaws.com`、`prod-ap-northeast-1-starport-layer-bucket.s3.ap-northeast-1.amazonaws.com`、`logs.ap-northeast-1.amazonaws.com`、`ssm.ap-northeast-1.amazonaws.com`、`dynamodb.ap-northeast-1.amazonaws.com`。v2.10 起程式寫成結尾有點(`api.openai.com.`、`*.`)(D89) |
| ALB | 兩個公有子網;閒置逾時 **120 秒**(D70);HTTP 80(7.8;Trivy AWS-0053、AWS-0054 刻意接受);健康檢查 `/health` |
| ECS | Fargate 0.25 vCPU / 0.5 GB、沒有公開 IP、根目錄唯讀、斷路器自動退回、沒有 ECS Exec;任務定義 `skip_destroy`(D85、D92、D94) |

**五個坑的實測對照(E124):**

1. **沒有寫 `*.amazonaws.com`:** 9 個網域逐一列出
2. **先告警、後阻擋:** ALERT 約一小時(啟動 + 聊天),查詢日誌裡容器查過的網域剛好是放行清單 9 個,一個不多、一個不少(`logs` 160 次,其餘各 2 次);ALERT 期間沒有任何一筆落到清單外(放行的查詢不記 `firewall` 欄位,只有 ALERT/BLOCK 才記)。切 BLOCK 後再聊天照樣成功,證明清單在 BLOCK 下是完整的
3. **S3 Endpoint Policy:** ECS 服務 1 分 8 秒穩定,等於經這條路拉到了映像
4. **安全群組管不到 DNS:** 安全群組沒開 53,DNS 照常
5. **ALB 兩個 AZ:** 公有子網 1a、1c

**M4 新撞到的三件事:**

- **走 Gateway Endpoint 的服務也要放行網域:** 容器仍要先經 VPC 的 DNS 查網域,所以 `dynamodb…` 與 ECR 映像層 bucket 的網域也在清單裡;漏了的話切 BLOCK 後連資料庫都查不到(E123)
- **AWS 會在網域結尾補一個點:** 存成 `api.openai.com.`、`*.`,Terraform 拿程式裡沒有點的版本比,每次 plan 都以為被改過(切 BLOCK 時計畫多出 2 個改動);內容相同、無害,v2.10 把程式改成結尾有點,讓 plan 乾淨、真的改動不會被淹沒。**有沒有消除假改動,待下一次 apply 每日層(M5 開工)時看 plan**(E124、E125)
- **Linux 查不到時會自動接 VPC 內部網域再查一次:** `example.com` 被擋時,查詢日誌是 4 筆 `BLOCK`:`example.com.` 與 `example.com.ap-northeast-1.compute.internal.` 的 A、AAAA,`*` 一起擋(E124)

## 3.6 支援服務

| 服務 | 用途 |
|---|---|
| **ECR** | 存放 Docker 映像檔 |
| **SSM Parameter Store** | 存放設定值、metrics token、HMAC 金鑰與 OpenAI API Key(SecureString,免費) |
| **Route 53 Resolver DNS Firewall** | 出口的網域放行清單與查詢日誌(v2.5) |
| **CloudWatch Logs** | 應用程式日誌 |
| **CloudTrail** | 記錄「誰對 AWS 做了什麼」 |
| **AWS Budgets** | AWS 花費超過 US$20 寄信告警(**不涵蓋 OpenAI 帳單**,OpenAI 另有儲值與 Project 硬上限,見 4.5) |

**v2.10:M4 實際建的支援服務(E118、E123、E124;全部在長期層,平常不拆):**

| 服務 | 實作 |
|---|---|
| **ECR** | 倉庫 `llm-gateway`:`IMMUTABLE`(標籤不能覆蓋)、`scan_on_push`、`AES256`;生命週期:沒標籤 1 天後刪、最多留 10 個。映像標籤 = `main` 的 commit 編號(目前 `90ed268`);推送前建置加 `--provenance=false --sbom=false`,推上去是單一 OCI 映像(D82、D92) |
| **SSM Parameter Store** | 三個 SecureString,本人用 AWS CLI 建(`--value (Read-Host)`,值不進 repo、不進帳本、不進指令紀錄):`/llm-gateway/audit-hmac-key`(雲端專用的新一把,以 `secrets.token_hex(32)` 當場產生,與本機 `.env` 不同)、`/llm-gateway/openai-identity-provider-id`、`/llm-gateway/openai-service-account-id`;用 AWS 預設的 `aws/ssm` 金鑰加密。**沒有 OpenAI 金鑰**(D71);metrics token 在 M6(D91) |
| **CloudWatch Logs** | 兩個日誌群組:`/ecs/llm-gateway`(Gateway 的日誌)、`/llm-gateway/dns-queries`(DNS 查詢日誌);保存 30 天、開 AWS 層級的防刪;每日層拆掉後仍查得到(D95) |
| **CloudWatch 告警** | 指標篩選 `{ $.event = "audit_write_failed" }` → 告警(60 秒一期、1 期、門檻 1)→ SNS。實測:手寫一行假的 `audit_write_failed` 後約 1 分鐘 `OK -> ALARM` 並寄信(`m4-alarm-email.png`),6 分鐘後回 `OK`(缺資料當成沒越線)。Gateway 自己寫失敗的那一段由本機刪表實驗證明(E116),兩者分開記 |
| **SNS** | 告警主題,訂閱本人 Email(本人用 CLI 建,信箱不進 repo);主題沒加密(Trivy AWS-0095 刻意接受:用 AWS 預設金鑰加密時 CloudWatch 告警發不進來,要自管 KMS 金鑰)(D95) |
| **Route 53 Resolver** | DNS 防火牆在每日層;查詢日誌設定在長期層,每日層只把它「接上 VPC」(3.5) |
| **CloudTrail** | M4 沒有用它確認 apply 呼叫了哪些 API(E119 的限制) |
| **S3(State)** | `llm-gateway-tfstate-<亂碼>`,見 5.1 |

---

# PART 4 — 資安設計

> 這是本專案的差異化重點,對應作者的資安維運背景。

## 4.1 核心原則:受控出口(Controlled Egress,v2.5 改寫)

> **v2.4 是 Zero Egress(零對外連線)。** 當時模型用 Bedrock,所有要連的服務都在 AWS 裡,可以完全不開出口。v2.5 改用 OpenAI(見 3.4),必須連到 AWS 外面,所以原則從「沒有出口」改成「**只有一個出口,而且出口有人管**」。

```
v2.4 Zero Egress:                    v2.5 受控出口:

私有子網                              私有子網
   │                                    │
   ▼                                    ├──► Gateway Endpoint ──► DynamoDB(限四張表)
VPC Endpoint ──► 只有 AWS 服務          │                          S3(限 ECR 映像層)
                                        │
沒有出口                                 └──► NAT Gateway ──► 網際網路
                                               ▲
                                  DNS 防火牆:只解析放行清單內的網域
                                  安全群組:對外只開 443
```

**生活比喻:** 一般大樓的出口大門(NAT)只擋外面的人進來,裡面的人想去哪就去哪。本案在大門口加了一位**拿名單的總機**:要出去辦事得先查電話號碼(DNS 查詢),名單上沒有的號碼,總機一律不轉接,還會記下是誰想打。

**擋得住什麼:**
- 被入侵的容器,想用網域名稱把資料送到攻擊者的伺服器 → DNS 查不到,送不出去
- DNS tunneling(把資料夾帶在對惡意網域的 DNS 查詢裡)→ 查詢本身就被封鎖。v2.4 列為殘餘風險的這一項,v2.5 反而處理掉了
- 程式打錯網址、套件偷偷連外(例如 10.3 的惡意版本把憑證 POST 到外部網域)→ 被擋並留下查詢日誌

**擋不住什麼(殘餘風險,見 7.9):** 程式不查 DNS、直接用 IP 連線。總機只管「查號碼」,背得出號碼直接撥的人攔不到。正式環境的升級路線是 AWS Network Firewall 依網域過濾(7.1)。

**v2.10:M4 實測(D89,E124;S08、S10):**

| 步驟 | 結果 |
|---|---|
| ALERT 約一小時 | 容器實際查過的網域剛好是放行清單 9 個;沒有任何一筆落到清單外 |
| 切 BLOCK | 名單內的照通(再聊天一次,`gpt-6-luna` 回答) |
| 出口檢查(一次性任務,`scripts/egress_check.ps1`) | `EGRESS api.openai.com: DNS answered and TCP 443 connected`;`EGRESS example.com: DNS lookup failed (gaierror: [Errno -5] No address associated with hostname)` |
| 查詢日誌 | 4 筆 `BLOCK`、`NOERROR`(`example.com.` 與接上 VPC 內部網域的那一次,各 A、AAAA) |

- 錄影 `m4-s08-egress-control.mp4`(不進 repo)
- **還沒有證明的:** 直接用 IP 連線這次沒有測(擋不到是已知的,7.9);ALERT 只觀察了一種流量(啟動 + 聊天),強模型、降級、限流的路徑沒有走過

## 4.2 六層防護

| 層級 | 措施 |
|---|---|
| **網路層** | 運算節點無 Public IP;對外只經 NAT;DNS 防火牆放行清單;Security Group 對外只開 443;Gateway Endpoint 加 Endpoint Policy |
| **身分層** | IAM 最小權限(只給指定資料表、指定佇列、指定 SSM 參數的權限,不用萬用字元);OpenAI 端用專用 Project 與服務帳號金鑰,只允許兩顆模型、只能呼叫 Chat Completions、30 天到期(4.5) |
| **CI/CD 層** | GitHub OIDC 聯邦身分取得**臨時憑證**,repo 內不存長期 Access Key |
| **應用層** | API Key 驗證(`Authorization: Bearer gw_…`;失敗一律回相同的 401;驗證寫成 FastAPI 的相依,沒通過的請求進不了主流程,不碰模型、不寫稽核;v2.8,D48);`/metrics` 端點另設獨立 token;資料庫讀不到或寫不進去時一律拒絕(fail-closed,回 503,見 10.3、D49、D51);設定檔沒有單價的模型一律拒絕呼叫(D30) |
| **前端層** | Console 的 XSS 防護與憑證處理(見 4.4) |
| **資料層** | 稽核 log 只存**內容的 HMAC 雜湊與摘要**,不存完整 prompt,原文也不進佇列與資料庫(見 PART 12);API Key 只存雜湊;入口先偵測個資並遮罩,**送往外部供應商的也是遮罩後的內容**,摘要取自遮罩後的內容,稽核只記錄「偵測到哪一類個資」。v2.8(D43):偵測四類(信箱、信用卡號、手機、身分證字號),以規則比對;M2 驗收時請模型原樣重複含假身分證字號的句子,回答是 `[TW_ID]`(S04) |

> **v2.9 應用層補充:** 設定檔讀進來就檢查(路由用到的模型要有設定、數字是大於 0 的整數、關鍵字不能空白),有問題 Gateway 起不來(D54);路由選到的模型查不到設定時回 500、不呼叫模型(D56);訊息上限 4,000 字由測試釘住(D64);信箱規則改為線性時間,長字串拖不慢(D63);上游給的 `Retry-After` 也當成不可信的輸入,只收 1～120 的整數秒(D59)。
>
> **v2.10 補充(M4):**
>
> | 層級 | M4 做了什麼 |
> |---|---|
> | 網路層 | 實作並實測:Fargate 沒有公開 IP(S09);NAT 單一出口;DNS 防火牆 9 個網域放行、其他 BLOCK(S08);兩條 Gateway Endpoint 只准特定動作與資源(S10);ALB 安全群組只放行本人公開 IP(D81) |
> | 身分層 | Gateway 的任務角色與執行角色都指定資源;`Resource: *` 只有兩條,都是 AWS 規定不能指定資源的動作:`ecr:GetAuthorizationToken`、`sts:GetWebIdentityToken`(後者限 audience `llm-gateway-capstone` 與 300 秒)(S11,D90)。OpenAI 端改用工作負載身分聯盟,雲端沒有 OpenAI 金鑰(4.5,D71) |
> | CI/CD 層 | GitHub OIDC 已實作,**目前只給 destroy workflow**:只有 environment `destroy`(只准 `main`)借得到角色;角色的刪除權限只限 `Layer=daily`,長期層有明文 Deny(D84、D85);CI 加 `Config scan`(D83)。CD 在 M6 |
> | 應用層 | 說明頁(`/docs`、`/redoc`、`/openapi.json`)一律關閉(D68);資料庫 503 不附 `Retry-After`(D69);`DYNAMODB_TARGET`、`OPENAI_AUTH` 沒講清楚就起不來(D74、D72) |
> | 資料層 | 稽核寫進 `audit` 表、條件寫入不覆蓋、Gateway 只有 `PutItem`;寫不進去時的日誌用白名單挑欄位,不含摘要與 HMAC(D77);雲端的 HMAC 金鑰是新的一把、放 SSM(D91) |
> | 容器 | 根目錄唯讀、非 root、沒有可寫的資料夾(在容器裡建檔被拒:`Permission denied`)(E116) |

## 4.3 `/metrics` 端點保護

監控端點會洩漏用量、成本、使用者行為,**不能公開**。

在 ALB 加一條 Listener Rule:

```
IF   path = /metrics
AND  header X-Metrics-Token = <SSM 存的隨機字串>
THEN → 轉發給 Gateway
ELSE → 直接回 403(不轉發到後端)
```

> **面試講法:**
> 「監控端點本身就是攻擊面。我沒有把它跟業務流量放在同一條授權路徑上,而是在 ALB 這一層就用獨立憑證擋掉未授權請求——惡意流量連碰都碰不到後端容器,這是縱深防禦(Defense in Depth)的實作。」

## 4.4 Demo Console 的前端安全

> 多一個網頁 = 多一個攻擊面。加入 Console 後重新做了一輪威脅建模。

| 風險 | 為什麼危險 | 處理方式 |
|---|---|---|
| **API Key 外洩** | 存在瀏覽器可能被其他腳本讀取,或關機後殘留 | 只放 `sessionStorage`,關掉分頁即消失;**不用** `localStorage` |
| **XSS(跨站腳本)** | **模型輸出是不可信輸入**,可能含惡意 HTML/JS | 一律用 `textContent` 渲染,**絕不用** `innerHTML` |
| **任意人存取 Console** | Demo 期間 ALB 是公開的 | Security Group / ALB 規則加 IP 白名單,只允許本人 IP。**v2.10 已實作(D81,E117、E121):** `alb` 安全群組入 80 只准變數 `admin_cidr`(只收 `/32`),值不進 repo |
| **點擊劫持(Clickjacking)** | 頁面被嵌進惡意 iframe | 回應標頭加 `X-Frame-Options: DENY` |

> **面試講法:**
> 「加上 Console 之後我重新評估了攻擊面。模型輸出對前端來說是**不可信輸入**,所以一律用 textContent 渲染避免 XSS;API Key 只存在 session 層級不落地。多一個介面就要多一輪威脅建模——這是資安工程師的職業習慣。」

## 4.5 外部供應商的風險控管(v2.5 新增,v2.6 補完)

換成 OpenAI 後多了三個 Bedrock 時代沒有的風險:

| 新風險 | 為什麼 | 處理方式 |
|---|---|---|
| **資料離開 AWS** | prompt 會送到第三方 | API 資料預設**不用於訓練**,但為了監測濫用,內容最多保留 **30 天**;要完全不保留(Zero Data Retention)需經 OpenAI 業務審核,本案申請不到(E20)。所以入口個資遮罩從「加分」變「必要」(M2)。另外用 Chat Completions(預設不存),金鑰權限關掉 Responses(預設存 30 天),從權限層保證不會把對話存在 OpenAI(D29) |
| **多了一把長期金鑰** | Bedrock 用 IAM 角色,沒有靜態密碼;OpenAI API Key 是長期金鑰 | 放 SSM SecureString、啟動時注入;服務帳號金鑰、只允許兩顆模型、只能呼叫 Chat Completions、**30 天到期**;實驗用與正式用分開發;用完撤銷。與 M0 刪除 IAM 長期金鑰是同一個邏輯。**M4 前評估工作負載身分聯盟**:若能用 AWS IAM 角色換取 OpenAI 短期憑證,這一列的風險可直接消除。**v2.10(D71):雲端的這一列風險已消除**(Fargate 用任務角色換 OpenAI 存取權杖,SSM 不放金鑰,10/19 實測);**本機開發仍用金鑰**(`m1-gateway`,11/2 到期前換) |
| **帳單分兩處** | AWS Budgets 看不到 OpenAI 的花費 | OpenAI 端設兩道硬上限:預付儲值(不自動加值)+ Project 硬性花費上限 |

### OpenAI 端的五道防線(M0 實作,E21、E22)

| # | 防線 | 設定 | 擋什麼 |
|---|---|---|---|
| 1 | 預付儲值、不自動加值 | 儲值 $5(最低額)、Auto-reload OFF | 錢包見底就停,一毛都不會多扣 |
| 2 | Project 硬性花費上限 | 每月 $2、Enforce a hard limit | 一個月最多花 $2;超過回 429 `project_spend_limit_exceeded`(攔截非即時,可能略超過) |
| 3 | 模型白名單 | 只允許 `gpt-6-luna`、`gpt-6-sol` | 金鑰外洩也叫不動貴的模型(實測 `gpt-6-astra` 被擋,E22) |
| 4 | 金鑰最小權限 | Restricted:只開 Chat completions | 不能傳檔案、訓練模型、用 Responses 存資料 |
| 5 | 服務帳號 + 30 天到期 | 金鑰不綁個人帳號 | 外洩也會自己失效 |

**過程中的兩個「不安全預設值」(E21):** 儲值畫面預設開啟自動加值;金鑰預設「永不過期」。兩者都要主動改掉。跟 LiteLLM 官方範例的預設值問題(E13)同類:**預設值是為了方便,不是為了安全。**

### v2.10:工作負載身分聯盟(M4 實作,E110、E113、E123、E124)

**生活比喻:** 不再發一把萬用鑰匙給員工。員工每次刷員工證(AWS 的身分證明,5 分鐘有效),警衛核對發證單位與用途後,給一張最多一小時的臨時通行證(OpenAI 的存取權杖),通行證只能進一個房間(Chat completions)。

| 項目 | 做法 |
|---|---|
| AWS 端 | 帳號層級開啟「對外身分聯盟」(`aws iam enable-outbound-web-identity-federation`);任務角色 `llm-gateway-task` 有 `sts:GetWebIdentityToken`,條件限 audience `llm-gateway-capstone` 與 `DurationSeconds ≤ 300`;一定用地區的 STS 網址 |
| OpenAI 端 | 身分提供者(Issuer、Audience)→ 服務帳號對應 `gateway-task-role`(`sub` = 任務角色的 ARN;AWS 文件寫明用角色時 `sub` 是角色的 ARN,不是每次不同的 session,所以對應一次就好)→ 專用服務帳號 `gateway-wif`(權限 Restricted,只開 `api.model.chat_completions.request`) |
| 為什麼另建 `gateway-wif` | 用金鑰與不用金鑰的呼叫分屬兩個身分:用量分得開,停其中一個不牽連另一個;不受 `m1-gateway` 金鑰 11/2 到期與換金鑰影響 |
| 退路 | 10/14 先用本人的 IAM 使用者探測(`scripts/probe_wif.py`,偵測到 `OPENAI_API_KEY` 有值就停,避免誤判成功);不通就改回「SSM 放新金鑰」。探測成功,退路沒用到 |
| 破壞實驗 | audience 改成別的值:AWS 照樣開證明,OpenAI 在換權杖那一步拒絕(`OAuthError`),對話端點根本沒被呼叫。替別的服務開出的證明,拿不到這個專案的通行證 |
| DNS 放行 | 多 `auth.openai.com`、`sts.ap-northeast-1.amazonaws.com` 兩個網域 |

**五道防線的變化:** 第 4、5 道(金鑰最小權限、服務帳號 + 30 天到期)在雲端改由 `gateway-wif` 的權限與「沒有金鑰可以外流」取代;第 1～3 道(儲值、Project 硬上限、模型白名單)不變。

**限制(誠實記錄):** 權杖快到期時 SDK 自動重換沒有測到;沒有測「只開 Chat completions」會不會擋下其他端點;探測時錯誤訊息只有 `OAuth authentication error.`,沒有看到 OpenAI 回的原因;帳號層級的對外身分聯盟保持開啟。

> **面試講法(v2.10):** 「Gateway 在雲端沒有放 OpenAI 的金鑰。容器用自己的 IAM 角色向 AWS 要一張 5 分鐘的身分證明,拿去跟 OpenAI 換通行證;角色的權限只准開給 OpenAI 那個對象、最多 300 秒。上雲前我先用自己的 IAM 使用者把整條路打通,因為官方文件只示範 Responses API,沒說 Chat Completions 收不收,也事先定了退路。」

> **面試講法:**
> 「換供應商不只是改一行 API 網址。資料出境、金鑰管理、帳單分散這三件事都要重新設計:送出去的內容先遮罩、金鑰用服務帳號並限定模型與 API、設 30 天到期,儲值與 Project 各設一道硬上限。我在 AWS 做的最小權限、預算上限、短期憑證,在 OpenAI 端再做一次,而且每一道都有實測截圖。」

---

# PART 5 — 自動化與可觀測性

## 5.1 IaC 與 CI/CD

### 角色分工

| 工具 | 比喻 | 負責 |
|---|---|---|
| **Terraform** | 建築藍圖 + 蓋房子的機器人 | AWS 上「要蓋什麼」 |
| **GitHub Actions** | 工地排班系統 | 機器人「什麼時候動工」 |

### Pipeline 流程

```
git push
   │
   ▼
┌─────────────────────────────────────────┐
│  CI 階段(每次 push 都跑)                  │
│                                          │
│  ① pytest         單元測試                │
│  ② tfsec          IaC 組態掃描            │
│  ③ docker build   建置映像                │
│  ④ Trivy          容器漏洞掃描             │
│                                          │
│  任一失敗 → 中止,不部署                    │
└──────────────┬──────────────────────────┘
               │ 全部通過
               ▼
┌─────────────────────────────────────────┐
│  CD 階段                                  │
│                                          │
│  ⑤ OIDC 取得 AWS 臨時憑證                 │
│  ⑥ push 映像到 ECR                       │
│  ⑦ terraform plan                        │
│  ⑧ terraform apply                       │
│  ⑨ ECS 服務更新                           │
└─────────────────────────────────────────┘

CD 階段(⑤～⑨)手動觸發;push 只跑 CI,不會自動開機花錢(見 PART 12)

> **v2.9(D62,E104):CI 已在 M3 上線,和上圖不同的地方:**
> - **tfsec 不用:** 已停止開發、併入 Trivy;M4 有 Terraform 之後用 `trivy config` 掃 IaC
> - 目前的兩個工作:**Tests**(`uv sync --locked`、用 repo 的 `compose.yaml` 起 `dynamodb-test`、`pytest`)、**Image scan**(`docker build` + Trivy,有修補版的 HIGH、CRITICAL 才失敗)
> - 另有 **CodeQL** 預設設定(Python、GitHub Actions),由 GitHub 維護,不在 repo 裡
> - 所有 Action 鎖 commit SHA、過 3 天冷卻期;Trivy 用 2026/3 供應鏈事件後官方公告的安全版本(v0.69.3、`trivy-action` v0.35.0)
> - CD(⑤～⑨)仍在 M6
另有:手動觸發的 terraform destroy workflow(省錢用)
```

> **v2.10(D83～D86,E118、E120～E122、E124、E125):M4 加了什麼。**
> - **CI 第三個工作 `Config scan`:** `trivy config .`,HIGH、CRITICAL 擋,已列入 `protect-main` 必要檢查(必要檢查變成 `Tests`、`Image scan`、`Config scan`)。trivy-action v0.36.0、Trivy v0.74.0(兩個掃描工作都明寫,不寫會用 action 內建的 v0.70.0);升級後 PR #3 起一直出現的 Node.js 20 警告消失。刻意接受的項目用 `#trivy:ignore:<ID>:exp:2026-12-31` 寫在該資源上方,上面幾行寫理由;到期日一過豁免自動失效、CI 變紅。破壞實驗:拿掉豁免開測試 PR,`Config scan` 20 秒內紅、其他照綠(D83)
> - **destroy workflow(`.github/workflows/destroy.yml`):** 手動觸發、只拆每日層;GitHub OIDC 借 `llm-gateway-destroy` 角色,repo 裡沒有長期金鑰。細節見下方「v2.10:兩層與 destroy workflow」
> - **`oidc-check.yml`:** 只驗身分的 workflow:印 `sub`、`aud` 等欄位(不印證明本身),再借一次角色;另有一個「沒掛 environment」的工作,證明它借不到
> - **CD(⑤～⑨)仍在 M6;** M4 的 `plan`/`apply`、`docker push` 都從本人電腦執行(`aws login`)(D80)

### Terraform State 管理

| 項目 | 設定 |
|---|---|
| **State 存放** | S3(開啟加密 + 封鎖公開存取 + 版本控制)。**v2.10 實作(E118、E119):** bucket `llm-gateway-tfstate-<亂碼>`(`bucket_prefix`)、`prevent_destroy`、封鎖公開四開關、版本控制、`AES256`(Trivy AWS-0132 要求自管 KMS 金鑰,刻意接受)、bucket 政策只准 HTTPS;長期層帳本 `persistent/terraform.tfstate`、每日層帳本 `daily/terraform.tfstate` |
| **狀態鎖** | DynamoDB 表,避免多次執行互相覆蓋。**v2.10 修訂(D78):改用 S3 本身的鎖檔(`use_lockfile = true`),不建 DynamoDB 鎖表**(Terraform 官方已把 DynamoDB 鎖標為淘汰) |

**v2.10:State 的實際操作(E119):**

- 長期層先用本機帳本建出 bucket,再 `terraform init -migrate-state` 搬進 S3;`.gitignore` 在第一次 apply **之前**就擋好 `*.tfstate`、`*.tfvars`,帳本在本機那幾分鐘 `git status` 是乾淨的;搬完把本機的空帳本與備份(含帳號 ID 與 ARN)刪掉,`plan` 仍 `No changes`,證明是從 S3 讀的
- **鎖的原理:** Terraform 寫鎖檔時用「只有不存在才寫入」的條件;實際遇過一次中斷的 `plan` 留下 `.tflock`,下一個 `plan` 被 `412 PreconditionFailed` 擋下。先確認鎖的主人、沒有程序在跑,才 `force-unlock`
- **本機登入:** Terraform 1.15 起可直接讀 `aws login` 的快取;先確認沒有殘留的 `AWS_*` 環境變數(環境變數比登入狀態優先,而且會過期)
- **防刪實驗:** `terraform destroy` 先算出拆 10 個,但 State bucket 有 `prevent_destroy`,整份計畫作廢、一個都沒拆;CLI 直接刪表被 DynamoDB 刪除保護擋下。前者只擋 Terraform,後者連主控台都擋;兩者擋的是「手滑」,不是「有權限的惡意」
- 計畫輸出裡的 ARN、ECR 網址有完整帳號 ID,存日誌或截圖時要遮;原則上不用 `plan -out` 存計畫檔(含帳本內容);E124 為了查 BLOCK 的多餘改動存過一次 `block.tfplan`,讀完即刪、沒有進 repo;`.gitignore` 沒有擋 `*.tfplan`,建議補(12.5)

### v2.10:兩層與 destroy workflow(D79～D87,E117、E120～E125)

**兩層(D79):**

| 層 | 放什麼 | 平常 | 誰 apply |
|---|---|---|---|
| **長期層** `infra/persistent/` | State bucket、ECR、三張表、GitHub OIDC 提供者與 destroy 角色、Gateway 的兩個 IAM 角色、兩個日誌群組與 DNS 查詢日誌設定、指標篩選與告警、SNS 主題 | 不拆(閒置每月不到 US$0.01) | 本人電腦 |
| **每日層** `infra/daily/` | VPC、子網、網際網路閘道、路由表、安全群組、兩條 Gateway Endpoint、NAT + 彈性 IP、DNS 防火牆、ALB、ECS 叢集與服務 | 測完當天拆 | 本人電腦 apply;destroy workflow 或本人電腦拆 |

**生活比喻:** 搬家時,戶籍和存摺(State、表、映像)放在固定的保險箱;冷氣和保全(NAT、ALB、Fargate)按小時計費,出門就關。

- 每日層要用長期層的東西時,表名寫死、帳號 ID 用 `aws_caller_identity` 問出來,不讀長期層帳本:每日層讀什麼,destroy 拆之前也要讀什麼,多讀一處就多一項權限(D87)
- 會留在長期層的「不能限標籤」的東西(角色、日誌、查詢日誌設定)都放長期層,destroy 角色就不用拿 `iam:DeleteRole`、`logs:DeleteLogDelivery`(D85、D90、D95)
- 施工順序:A 長期層地基 → B 長期層住戶 → C 每日層免費骨架(**建好就先實測 destroy**)→ D 會跳錶的(NAT、DNS 防火牆、ALB、Fargate)→ E 驗收與 destroy(E117、E120)

**destroy workflow(D84～D86):**

| 項目 | 做法 |
|---|---|
| 觸發與權限 | `workflow_dispatch`;`permissions: {}`,工作上才開 `id-token: write`、`contents: read`;`environment: destroy`;`runs-on: ubuntu-24.04`;`concurrency`(第二次排隊,不取消正在拆的) |
| 誰借得到角色 | 只有 environment `destroy`(只准 `main`、**取消管理員略過**);信任條件 `aud`、`sub` 都完全相等;`sub` 用 GitHub 2026/7/15 後的新格式 `repo:<owner>@<owner-id>/llm-gateway@<repo-id>:environment:destroy`(名字加編號;照舊格式 `repo:<owner>/llm-gateway:…` 寫會永遠借不到) |
| 裝 Terraform | curl 官方 zip,比對寫死在 repo 的 SHA256(`sha256sum --check --strict`),不用第三方 Action |
| 換憑證 | 只把 GitHub 的身分證明存成檔案,設 `AWS_ROLE_ARN`、`AWS_WEB_IDENTITY_TOKEN_FILE`,讓 Terraform 自己換臨時憑證;證明約 5 分鐘過期,所以 `init`、`destroy`、`state list` 每個指令前重新要一張 |
| 遮帳號 ID | 從角色 ARN 取帳號 ID 後 `::add-mask::`,之後每一行都是 `***`;角色 ARN 放 repository secret |
| 拆 | `init` → `destroy -auto-approve -var=admin_cidr=192.0.2.1/32`(RFC 5737 文件專用位址,拆除只照帳本拆)→ `state list` 必須是空的,有剩就失敗 |
| 角色權限 | 帳本只開每日層兩個檔;`Describe` 逐一列出(`Resource "*"` 是 AWS 規定);刪除限 `Layer=daily` 標籤;不給任何 `Create*`、`CreateTags`;長期層有明文 Deny(三張表、帳本 bucket 設定、長期層帳本、ECR、角色自己、OIDC 提供者、Gateway 的角色、SNS、日誌群組、查詢日誌設定);任務定義 `skip_destroy`(不給 `DeregisterTaskDefinition`);`ec2:DisassociateAddress` 單獨一條 `Resource "*"`(D85) |

**實測:**

| 次 | 結果 |
|---|---|
| `oidc-check #1`(`main`) | 掛 environment 的工作借到角色;沒掛的被 AWS 拒(`AccessDenied`);environment 的新 `sub` 格式推定成立 |
| `oidc-check #2`(別的分支) | 掛 environment 的工作一個步驟都沒跑:`Branch … is not allowed to deploy to destroy due to environment protection rules` |
| 權限模擬器 | C 段 5 題、D 段 10 題、修正後 12 題,全部符合預期(`scripts/simulate_destroy_role.ps1`;`m4-destroy-role-simulator.png`) |
| **`destroy #1`(C 段,10/18)** | **成功,51 秒(拆除工作 44 秒),拆光 19 個資源**,`The daily state is empty`;本人 CLI 查 `Layer=daily` 的 VPC 為 `[]`(`m4-destroy-first-run.png`) |
| **`destroy #2`(D 段,10/19)** | **3 分 31 秒失敗**:拆掉 35 個(含 VPC),最後卡在 `ec2:DisassociateAddress`:這個動作的資源是 `*/*`、沒有標籤,放在「限 `Layer=daily`」那一條,條件永遠不成立。本機補拆 `aws_eip.nat`,問 AWS 確認拆光 |
| 修正(PR #16,10/20) | `DisassociateAnyAddress`:`Resource "*"`、不加條件;代價是能把帳號裡任何一個公開 IP 從機器上拔下來,但刪不掉(`ReleaseAddress` 仍限 `daily`)。模擬器補第 11 題(拔 → `allowed`)、第 12 題(刪沒標籤的 → `implicitDeny`)。Config scan 沒有對 `Resource "*"` 提意見 |
| **還沒實測** | **修正後的「一鍵拆光」要等下一次 apply 每日層(M5 開工時)再按 destroy。在那之前,每次 destroy 完都要直接問 AWS 確認拆光** |

**限制(誠實記錄):** 「只准 `main`」在 GitHub 的 environment 設定裡,不在 repo、沒有版本紀錄;有 repo 管理權限的人能拆每日層;權限模擬器不看資源身上真正的標籤(標籤是參數餵的),標籤條件「擋得住不該拆的」沒有在真的資源上做破壞實驗;模擬器只問「這張卡刷這扇門會不會開」,沒出到的題目就抓不到(`destroy #2` 就是這樣)。

## 5.2 監控

### 架構

```
AWS 端(私有子網)                本機(平常關著)
                                
Gateway Service                 ┌──────────────┐
  /metrics 端點 ◄───── ALB ─────│  Prometheus  │
  (prometheus_client)           │      ↓       │
                                │   Grafana    │
                                └──────────────┘
                                  docker-compose
```

**生活比喻:** 不需要在店裡裝一台 24 小時開機的監控主機(那台主機本身就要電費)。只要在店裡裝好「感應器接頭」,要看數據時把筆電接上去讀就好。

### 監控指標

| 指標 | 說明 |
|---|---|
| `llm_requests_total` | 請求總數(依 model / user / status 分類) |
| `llm_tokens_total` | Token 使用量(input / output / reasoning 分開) |
| `llm_cost_usd_total` | 累計成本 |
| `llm_request_duration_seconds` | 延遲直方圖 |
| `llm_rate_limit_rejected_total` | 被限流擋掉的次數 |

---

# PART 6 — 成本試算

## 6.1 核心心法

> **讓時鐘只在你工作時轉。**

| 階段 | 做法 |
|---|---|
| 寫程式 / 測邏輯 | 本機 Docker 模擬,**AWS 完全不開** |
| 測雲端整合 | `terraform apply` → 測完 `terraform destroy` |
| 防呆 | destroy 寫成 GitHub Actions 手動 workflow + 手機提醒 |

> **v2.10(D79,E117、E122、E124):** 時鐘只在「每日層」轉。長期層(State、ECR、表、角色、日誌、告警)閒置幾乎不花錢,平常不拆;每日層測完當天拆。destroy workflow 已建(5.1),C 段 51 秒拆光;第二次執行(D 段第一次拆)失敗後本機補拆。**規則:destroy 之後一定直接問 AWS 確認拆光**(帳本是空的不等於 AWS 上一點不剩,例如任務定義 `skip_destroy` 會留著,不收費)。

## 6.2 單價參考(ap-northeast-1,v2.5 改用 M0 實測,v2.6 補 OpenAI 與 DNS 防火牆)

| 項目 | 單價 | 來源 |
|---|---|---|
| Fargate 0.25 vCPU / 0.5 GB | **$0.0154 / 小時**(vCPU $0.05056、記憶體 $0.00553 / GB) | E7 |
| ALB | **$0.0243 / 小時** + LCU $0.008;Demo 流量下 LCU 可忽略 | E8 |
| NAT Gateway | **$0.062 / 小時** + $0.062 / GB | E10 |
| 公有 IPv4 位址 | $0.005 / 小時 / 個(ALB × 2 + NAT × 1) | 6.2 v2.3 |
| VPC Gateway Endpoint | **免費** | — |
| VPC Interface Endpoint(v2.5 不使用) | $0.014 / 小時 / 個 / AZ | v2.3 |
| Route 53 Resolver DNS 防火牆 | $0.60 / 百萬次查詢 + **每個自訂網域每月 $0.0005**(20 個網域約 $0.01 / 月);查詢日誌寫進 CloudWatch 另計 | E20 |
| OpenAI `gpt-6-luna` | 輸入 **$0.10**、輸出 **$0.50** / 百萬 token(思考 token 以輸出計) | E20 |
| OpenAI `gpt-6-sol` | 輸入 **$2**、輸出 **$10** / 百萬 token | E20 |
| OpenAI 儲值 | 預付制,最低 **$5**、1 年後過期、不可退款 | E20 |
| Lambda | 免費層 100 萬次請求 / 月 | — |
| SQS | 免費層 100 萬則 / 月 | — |
| DynamoDB | 免費層 25 GB + 25 WCU/RCU | — |

> **v2.4 的估計值誤差:** Fargate 原估 ~$0.012,低估約 28%;ALB 原估 ~$0.0225,低估約 8%。
> **M0 估價踩到的坑(E7、E8):** 計算器的「任務數量」單位選成「每天」,月費顯示 $342;ALB 的 LCU 誤把 Lambda 目標與 IP 目標兩欄都填了。雲端估價最容易錯的是**單位與適用對象**,不是單價。
> **M0.5 的同類坑(E24):** OpenAI 單價是「每百萬 token」,設定檔要的是「每 1 個 token」,少一個 0 就差 10 倍。
> **v2.9(E103):** 10/12 再查一次 OpenAI 單價,不變。設定檔的單價單位是「每一百萬個 token 多少 micro-USD」,除以一百萬就是每個 token:`gpt-6-sol` 輸入 2、輸出 10;`gpt-6-luna` 輸入 0.1、輸出 0.5。

**單次呼叫參考(E22 實測):** `gpt-6-luna` 輸入 13、輸出 11 token = **$0.0000068**。以一次約 300 字輸入、500 字輸出估算:Luna 約 $0.00028,Sol 約 $0.0056。

## 6.3 專題全期總帳(6 週,實際上雲約 50 小時,v2.6 重算)

| 項目 | 花費 |
|---|---|
| Fargate | ~$0.77 |
| ALB | ~$1.22 |
| NAT Gateway(時間費;Demo 流量 < 1 GB) | ~$3.15 |
| 公有 IPv4 × 3(ALB × 2 + NAT × 1) | ~$0.75 |
| DNS 防火牆(20 個網域 × 約 2 個月 + 少量查詢) | ~$0.02 |
| VPC Gateway Endpoint × 2 | **$0** |
| Lambda / SQS / DynamoDB | **$0**(免費層) |
| S3(Terraform state) | ~$0.05 |
| CloudWatch Logs | ~$0.20 |
| **AWS 小計** | **~$6.2** |
| OpenAI(預付最低儲值;實際用量估計 < $1,M0～M0.5 實際約 $0.0003) | **$5** |
| **總計** | **約 US$11(約 NT$360)** |

> v2.5 為 US$8～16。OpenAI 從「依用量估計」改成「以最低儲值計」:預付制下,儲值金額就是實際支出,也是上限。

**v2.10:M4 實測花費(Cost Explorer 實際金額 10/20 補上)。**

| 項目 | 花費 | 來源 |
|---|---|---|
| 長期層(State bucket、三張表隨需 + PITR、ECR、IAM、日誌、SNS) | 閒置每月不到 US$0.01(估) | E119 |
| 每日層 C 段(VPC、子網、安全群組、Gateway Endpoint) | 免費 | E122 |
| 每日層 D、E 段(10/19 約 20:49～22:38,約 1 小時 50 分) | **估約 US$0.22**(E123 用 6.2 的單價估全部開著約每小時 US$0.12:NAT 0.062、ALB 0.0243、公開 IPv4 × 3 共 0.015、Fargate 0.0154) | E123、E124 |
| AWS 實際金額 | **約 US$0.29**(Cost Explorer,UTC 10/14～10/20,估計值;10/19 那一格 0.291,其他天合計不到 0.001)。比估算多約 32%,主因是 **NAT 計了 3 小時**(0.186);ALB 計 2 小時(0.0486)、使用中的公開 IPv4 約 0.027、推定 Fargate 約 0.027(未確認)、閒置彈性 IP 約 12 分鐘 0.001 | M5 E129 |
| OpenAI | 小額:探測 24 個 token、本機容器驗證(含一次強模型長回答 16,322 micro-USD,約 US$0.016)、雲端 bob 5 次便宜模型;合計約 17,500 micro-USD(約 US$0.018,Gateway 自己算的),**沒有和後台逐筆對帳** | E113、E114、E116、E124 |

- **估算方法的修正:** 按小時計費的資源要算「建好到拆掉」整段,不滿一小時進位;0.22 只算了驗收那 1 小時 50 分。M5 上雲演練照這個方法重估(M5 E129)
- 原估「實際上雲約 50 小時」:M4 每日層實際跳錶只有 D、E 段的約 1 小時 50 分(C 段免費);M5、M6 還要上雲,全期總帳等結案再重算
- 每日層全部開著約每天 US$2.8(E117),與 6.4「忘記 destroy」那一列同一量級
> v2.4 為 US$12～22。降低的主因是拿掉 Interface Endpoint(~$4.3 → NAT ~$3.2),以及模型費用預估下修。

## 6.4 兩大爆帳風險

| 風險 | 危險程度 | 防範 |
|---|---|---|
| **忘記 destroy** | ALB + NAT + 3 個公有 IP 閒置約 $2.4/天,加上 Fargate 約 $2.8/天(月約 $85) | destroy workflow + 手機固定提醒。**v2.10(E122、E124、E125):** destroy workflow 已建,C 段一次拆光;第二次執行(D 段第一次拆)卡在彈性 IP(會繼續計費的 `aws_eip.nat` 留著),本機補拆。已修,待 M5 開工實測;每次 destroy 完都直接問 AWS 確認(NAT、彈性 IP、VPC、ALB、DNS 防火牆規則群組、ECS 叢集) |
| **模型呼叫失控** | 測試迴圈寫錯、誤用強模型、思考量沒設定 | 全程用便宜模型、`reasoning_effort` 明確設定;OpenAI 端五道防線(4.5),其中儲值 $5 與 Project $2 是兩道硬上限(AWS Budgets 看不到這筆) |

---

# PART 7 — 決策取捨過程

> 以下記錄「為什麼這樣選」。這一段是本專案與一般教學範例最大的差異。

## 7.1 為什麼改用 NAT + 受控出口(v2.5 改寫)

**背景:** v2.4 不用 NAT,理由是「要連的服務全部在 AWS 裡,根本不需要出口」,而且選 Endpoint 的主因是安全、不是省錢(東京單價下 Endpoint 常駐反而比 NAT 貴)。v2.5 模型改用 OpenAI(3.4),這個前提不存在了:**只要接外部供應商,就一定要有出口。**

所以問題從「要不要 NAT」變成兩個:**出口要管到什麼程度**,以及**原本的 Interface Endpoint 還要不要留**。

### 出口管控等級(D25)

| 選項 | 做法 | 擋得住直接用 IP 連線嗎 | 50 小時多花 | 主要代價 |
|---|---|---|---|---|
| A | 只有 NAT | ✗ | 0 | 等於沒有出口管控,被入侵就能送到任何地方 |
| **B(採用)** | NAT + DNS 防火牆放行清單 + 安全群組只開 443 | ✗ | 幾乎 0(E20:20 個網域約每月 $0.01) | 殘餘風險:直接用 IP 連線 |
| C | NAT + AWS Network Firewall(依網域過濾) | ✓ | 約 +$17(東京每端點約 $0.40/小時) | 一個人就吃掉整個 US$20 預算 |
| D | 自架代理伺服器(EC2 跑 Squid,容器只能連代理) | ✓ | 很少 | 多一台要修補、會單點故障的伺服器,本身也是新的攻擊面;與本案「全託管」方向相反 |

**決策理由:** B 幾乎零成本,就能擋下「用網域名稱外連」這一大類攻擊,而且能用查詢日誌拍出實證(S08)。C 的保護最完整但成本不成比例;D 省錢但把託管服務換成要自己顧的伺服器。

### Interface Endpoint 保不保留(D26)

| 選項 | 50 小時成本(E10) | 評估 |
|---|---|---|
| 保留 5 個 + NAT | ~$6.9 | Endpoint Policy 能做資料邊界,但在 B 之下可被「直接用 IP」繞過 |
| **只用 NAT + 免費 Gateway Endpoint(採用)** | ~$3.4 | DNS 放行清單要逐一列出 AWS 服務網域 |

**決策理由:** B 已接受「直接用 IP 連線」的殘餘風險;攻擊者繞得過 DNS,Endpoint Policy 擋的那條路從 NAT 一樣走得通。多付一倍只買到部分保護,與 B 的取捨邏輯不一致。

> **面試講法:** 「我知道 Endpoint Policy 可以做資料邊界。但在只有 DNS 層管控的架構下它能被繞過,所以正式環境我會把它跟 Network Firewall 一起上,而不是單獨買。」

**v2.3 保留下來的更正:** NAT 的封包並不會「經過公開網際網路」才到 AWS 服務,AWS 資源與 AWS 服務之間的流量仍留在 AWS 網路內。差別一直都在「有沒有一個通往任何地方的出口」,v2.5 的答案是:有,但只有一個,而且有人管。

**不再規劃切回 Zero Egress(v2.7,D33、E29):** v2.5、v2.6 在這裡寫「Bedrock 業務例外開通時切回」。9/26 定案 Bedrock 退場後,這條路線刪除;本專題的網路設計只有受控出口一套。若未來的專案能全部使用 AWS 內的服務,Zero Egress 仍是更好的起點,v2.4 的設計與理由保留在變更紀錄中。

**v2.8 補記(E79):** 指導老師 10/5 提醒,Bedrock 之後必然會引入各家模型的調度與監控,是未來重要的學習主題。本案因帳號未開通,維持 D33(已退場),不改架構、不再追 AWS 業務;這個方向列為專題之後的學習主題。

**v2.10 實測(E124):** 選項 B 在 M4 實際成立:ALERT 一小時整理出的網域剛好是 9 個;BLOCK 後名單外的網域連地址都查不到、留下查詢日誌(S08)。殘餘風險(直接用 IP 連線)這次沒有測,仍是已接受的風險(7.9)。安全群組出口 `0.0.0.0/0:443` 被 Trivy 標為 CRITICAL(AWS-0104),以 `trivy:ignore` 刻意接受、理由寫在該行上方:OpenAI 的 IP 不固定,只能用網域管,網域由 DNS 防火牆管(D83)。

## 7.2 為什麼拆成兩個服務,而不是一個或五個

**為什麼要拆(生活比喻):**
餐廳只有一個店員,他要接單 → 煮 → 出餐 → 記帳。問題是客人餐點好了,卻要站著等他記完帳才能走。
正確做法:前台專心出餐,單據丟進出單夾;另一個人自己去拿單子慢慢記帳。

**為什麼只拆兩個(而不是把配額檢查也拆出來):**

> 配額檢查在**同步路徑上**,每次請求都要跑。拆成獨立服務等於每次請求多一次網路往返,延遲增加、故障點也增加,但換來的好處(獨立擴縮)在這個流量規模下根本用不到。
> **微服務的拆分依據是「變更頻率」與「擴縮需求」,不是「功能聽起來不一樣」。**

## 7.3 為什麼 Gateway 用 Fargate、Worker 用 Lambda

| | Gateway | Worker |
|---|---|---|
| 呼叫特性 | 每個請求都要跑,需低延遲 | 一天幾百次,可以慢 |
| 執行時間 | 可能等模型回應數十秒 | 幾百毫秒 |
| 選擇 | **Fargate**(常駐,無冷啟動) | **Lambda**(按次計費,幾乎 $0) |

用 Lambda 跑 Gateway 會有冷啟動延遲;用 Fargate 跑 Worker 則是「養一個全職會計,但一天只上班五分鐘」——浪費。

## 7.4 為什麼用 SQS 而不用 Kafka

| | Kafka (MSK) | SQS(本案) |
|---|---|---|
| 費用 | 常駐 broker,月費三位數美金 | 免費層 100 萬則/月 |
| 適用場景 | 多消費者、需重播歷史事件、百萬級/日 | 單一消費者、事件處理完即丟 |

**決策理由:** 本系統的計費事件是「處理完就結束」,不需要重播、也只有一個消費者。SQS 是 serverless 情境下的等價物。

**為什麼要用佇列,而不是像 LiteLLM 把帳先放記憶體(v2.6,E25、E26):** LiteLLM 也是非同步記帳,但待寫入的帳放在程式記憶體裡,實測回應後 0.8 秒被強制終止,那筆帳永久遺失。佇列的價值不是「非同步」本身,而是**事件離開 Gateway 之後就不怕 Gateway 當機**。前提是事件要在回應之前送進去(D31)。

**升級門檻:** 若日均事件量進入百萬級、或需要多個消費者各自重播歷史事件,才換成 MSK / Kinesis。

## 7.5 為什麼用 DynamoDB 而不用 RDS / MongoDB

| 考量 | 說明 |
|---|---|
| **成本** | DynamoDB Gateway Endpoint **完全免費**;RDS 需常駐執行個體,且本帳號 RDS 免費層已過期 |
| **存取模式** | 主要是 `user_id` 單鍵查詢,不需要複雜 JOIN |
| **維運** | 全託管,不用管版本更新與備份排程 |

**什麼時候該換 RDS:** 需要跨表關聯查詢、複雜報表聚合、或有既有 SQL 生態系要整合時。

## 7.6 為什麼用 GitHub Actions 而不用 Jenkins

| | GitHub Actions | Jenkins |
|---|---|---|
| 比喻 | 平台內建的外送系統 | 自己買機車、請司機、顧保養 |
| 基礎設施 | 不用管,有免費額度 | 需要 24 小時開機的 EC2 |
| 維運 | 零 | 自己顧資安更新、備份、崩潰重啟 |

**決策理由:** Jenkins 需要常駐伺服器,直接違背本專案「低成本 + 低維運 + 全託管」的核心精神。

**若需 Jenkins 經驗:** 本機用 docker-compose 跑 Jenkins,呼叫同一份 `terraform plan/apply`,證明同一套 IaC 可插進不同 CI/CD 引擎。不上雲。

> 補充:GitLab CI 與 GitHub Actions 概念相同(平台原生、免管伺服器),差別只在語法與綁定平台。學會一個,另一個一兩小時就能上手。

## 7.7 為什麼 Console 內嵌在 Gateway,而不獨立部署

**先講為什麼需要 Console:**
沒有 UI 的話,Demo 只能用 `curl`,畫面是黑底白字。但這個系統最有戲劇性的畫面是「**額度用完 → 被擋 → 回 429**」,以及「路由自動選了哪個模型」——這些用網頁演出來非常直觀。

> **生活比喻:** 你做了一台很厲害的引擎,性能數據都很漂亮。但面試時你只能給對方看 Excel 報表,跟你把引擎裝進車裡讓他踩一腳油門,說服力完全不同。

**三個選項比較:**

| 選項 | 做法 | 額外成本 | 評估 |
|---|---|---|---|
| A. 不做 UI | 純 curl + Grafana | $0 | 技術完整,但 Demo 說服力弱 |
| **B. 內嵌 Gateway**(採用) | FastAPI StaticFiles,走現有 ALB | **$0** | ⭐ |
| C. S3 靜態網站 | 前端獨立部署 | ~$0.05 + 多一組模組 | 架構較正統但過度設計 |

**決策理由:**
1. **零額外 AWS 資源** — 不用新開 S3 / CloudFront,Terraform 不用多寫模組
2. **不增加新的入口或出口** — 網頁與 API 走同一條 ALB 路徑
3. **FastAPI 原生支援** — `StaticFiles` 掛載只需三行程式碼

**什麼時候該改用選項 C:** 前端變成獨立產品、需要 CDN 加速、或前後端由不同團隊維護時。

## 7.8 為什麼 Demo 不做 HTTPS

**原因:** ACM 憑證免費,但**必須擁有網域**才能簽發(需 DNS 驗證所有權),不想花 NT$400/年。

**補償措施:** Terraform 中把 listener 的 `port` 與 `protocol` **參數化**,切 HTTPS 只需改變數、不改架構。

**生活比喻:** 房子的結構、水電、消防全部到位,只差門口那塊大理石門牌沒裝。門牌是最容易補的,不影響房子評價。

**正式環境做法:** Route53 託管網域 → ACM 申請憑證 → ALB 掛 443 Listener → 加 80→443 強制轉址規則。

**v2.10(D81、D83,E117、E123):** M4 的 ALB 是 HTTP 80,安全群組只放行本人一個公開 IP(`admin_cidr`,只收 `/32`)。Trivy 的 AWS-0054(不准 HTTP)與 AWS-0053(不准 ALB 對外)都以 `trivy:ignore` 刻意接受、12/31 到期:前者是因為發 HTTPS 憑證要有自己的網域,後者是因為它本來就是對外的入口、只有一個 IP 進得來。

## 7.9 其他「不做」項目

| 項目 | 為什麼不做 | 正式環境會怎麼做 |
|---|---|---|
| **AWS WAF** | 每月固定 ~$5 + 每條規則 $1 | 掛在 ALB 前擋 SQLi / XSS / 惡意 Bot,對 `/v1/chat` 設 rate-based rule |
| **多 AZ 高可用** | NAT Gateway 按 AZ 計費,雙 AZ 直接雙倍 | 至少 2 AZ,每個 AZ 一個 NAT,Fargate desired count ≥ 2 |
| **GuardDuty** | 30 天試用後按資料量計費 | Demo 前一週開啟截圖,結束後關閉 |
| **Grafana 上雲** | 常駐運算成本 | Amazon Managed Grafana 或部署於既有 EKS |
| **Ansible / Linux Server** | Fargate 無伺服器容器,沒有 OS 可管,故事會打架 | 另開獨立作品展示地端能力 |
| **直接用 IP 連線的外洩(v2.5 殘餘風險)** | DNS 防火牆只管 DNS 查詢,擋不到不查 DNS 的連線;Network Firewall 50 小時約 +$17,自架代理要顧伺服器(7.1)。**v2.10:M4 驗證了 DNS 這一層(S08),「直接用 IP 連線」這次沒有測**(E124);VPC Flow Logs 也沒開(E121) | AWS Network Firewall 依網域(TLS SNI)過濾,或集中出口 VPC;搭配 VPC Flow Logs 給 SOC 監控異常目的地 |
| **Endpoint Policy 資料邊界** | 在只有 DNS 層管控的架構下可被繞過,單獨買不划算(7.1) | 與 Network Firewall 一起上,限制只能存取自己組織的資源 |
| **同時接多家供應商** | v2.5 起只接 OpenAI 一家;「同時」接多家做分流、比價、互為備援不做(v2.4 寫的理由是違背 Zero Egress,v2.5 已不成立,改為範圍控制)。v2.7:薄介面已簡化為單一函式,也不再以「換供應商」為設計目標(E30) | 用 LiteLLM 或 AgentCore Gateway,並評估資料出境與供應商合約 |
| **限速(每秒/每分鐘)** | 本案以「月額度」為主;Demo 只有單一容器,用不到分散式限速 | ALB 前掛 WAF rate-based rule,或用 AgentCore Gateway 的限流 |
| **語意快取** | 需要 ElastiCache 或向量資料庫,屬常駐成本 | 評估 LiteLLM 搭配 Valkey / ElastiCache 的語意快取 |
| **管理後台 / SSO** | 超出「調度與治理」核心,Demo Console 只做展示 | 採用現成方案的管理介面,或整合 IAM Identity Center |
| **知識檢索(RAG)** | 本專題定位是 LLM 上線後的治理層(見 1.3)。指導老師 10/5 回覆「看定性」,本案定性為治理層,維持不做。RAG 已在過往專案(面試練習網站)做過,再做一次不會產生新的證明,也會擠壓專題時程(v2.8,E79、E84) | 知識檢索接進來時:① embedding 與生成兩種呼叫都要經過 Gateway,同樣受身分、額度、計費、稽核、個資遮罩管理;② data drift:企業文件更新後檢索結果會變,要定期重跑測試集並比對;③ 測試集:為企業知識建一組固定問答當驗收基準。M3 的 20 題路由測試集是同一種做法,重跑時機為模型換版、單價變更、路由門檻調整。向量資料庫是其中一個元件,依資料量與成本另行選型 |
| **Zero Data Retention(v2.6)** | 需經 OpenAI 業務審核,個人帳號申請不到(E20) | 企業合約申請 ZDR;在那之前靠入口個資遮罩降低風險 |
| **預扣(v2.8)** | M2 的額度會超扣:檢查在呼叫前,金額要呼叫後才知道(實測額度 1000 用到 1120);月額度下超出的金額極小(7.10) | 呼叫前依 `max_completion_tokens` 估算先扣,事後多退少補 |
| **截斷的回答告知使用者、不扣錢(v2.9)** | 錢已經付給供應商,不扣使用者的錢等於 Gateway 自己吸收;M3 只記進稽核(`finish_reason`),本人 10/14 確認維持,等 M6 有真實統計再看(D60) | 回應加一欄告知被截斷;空回答不扣額度或自動重試一次 |
| **降級時便宜模型查不到設定(v2.9)** | 啟動時已檢查兩顆模型都有設定,正常走不到;本人 10/14 確認記為限制、不改程式 | 與 500 那條路合併,留稽核 |
| **語意化的路由(v2.9)** | 規則式(字數 + 關鍵字)好解釋、好測試;字首比對仍有誤判(`designer` 命中 `design`)與漏掉(`analysis` 對不到 `analyze`),誤判只是多花錢,月額度封頂(D55) | 用小模型或分類器判斷難易;以真實稽核紀錄當測試集,定期重跑 |
| **原生工具呼叫(v2.8)** | M7 用文字約定,不改 `POST /v1/chat` 的請求格式(D38、D42);原生做法要讓 Gateway 接受完整對話與工具定義,遮罩與稽核也要處理工具回傳的內容 | Gateway 支援 `messages` 與工具定義,每一輪呼叫照樣經過身分、額度、遮罩、稽核 |
| **API Key 的停用與輪替流程(v2.8)** | `api_keys` 有 `status` 欄位,但 M2 沒有停用 Key 的指令;種子腳本重跑會產生新的 Key、舊的不失效(E91) | 管理介面或指令把 `status` 改成 `disabled`;發新 Key 時設定舊 Key 的到期時間 |
| **個資偵測的涵蓋範圍(v2.8)** | 只以規則比對四類;姓名、地址、變形寫法不在範圍內;模型回答裡的內容不檢查(E81、E85) | 託管的內容防護服務(例如 Bedrock Guardrails),並檢查輸入與輸出兩個方向 |
| **ECS Exec(v2.10)** | 放行清單要加 `ssmmessages` 等網域、任務角色多權限、本機裝 Session Manager 外掛,唯讀根目錄下還要另外掛可寫的資料夾,與「出口管很緊」反方向;S08 改用一次性任務(D94) | 需要時才開,並在出口規則、權限與稽核上一起設計;平常關著 |
| **自管 KMS 金鑰(v2.10)** | State bucket(AWS-0132)與 SNS 主題(AWS-0095)要自管金鑰才過 Trivy:每把每月約 US$1、所有角色都要多一組權限;帳本沒有密碼、主題裡沒有使用者資料。以 `trivy:ignore` 刻意接受,12/31 到期(D83) | 用自管 KMS 金鑰,金鑰政策只給需要的角色 |
| **VPC Flow Logs(v2.10)** | Trivy 標 MEDIUM、不擋;S08 的證據用 DNS 查詢日誌(E121) | 開 Flow Logs 給 SOC 監控異常目的地(搭配上方「直接用 IP 連線」那一列) |
| **一鍵部署(v2.10)** | M4 的 `apply`、`docker push` 從本人電腦執行;GitHub OIDC 角色先只給 destroy(D80) | M6 的 CD:同樣用 OIDC 借角色,從 `main` 建映像、`apply` |

## 7.10 額度扣減:同步、非同步、預扣

| | 同步扣減(M2～M4,已實作) | 非同步扣減(M5 起,採用) | 預扣(不做,升級路線) |
|---|---|---|---|
| 做法 | 拿到模型回應後、回傳前,Gateway 直接扣 | Gateway 只讀額度;Worker 事後依實際 token 扣 | 呼叫前依 `max_completion_tokens` 估算先扣,事後多退少補 |
| 超用空窗 | 小(只有同時進行中的請求) | 稍大(再加上佇列延遲) | 無 |
| 使用者延遲 | 多一次寫入 | 最低(只多一次 SQS 寫入,D31) | 多一次寫入 |
| 記帳故障時 | 使用者也受影響 | 使用者照用(M5 故障演練) | 使用者也受影響 |

**生活比喻:** 預扣像加油前先刷卡預授權;非同步像吃完再結帳,偶爾有人多點一道菜,結帳時才發現超過預算。

**實作細節:** 不論哪一種,用量都用 DynamoDB 的原子累加(`ADD`)寫入,多個容器同時寫也不會互相覆蓋,不需要像 LiteLLM 那樣另開 Redis 共享計數(見 10.3)。

**決策理由:** 本系統的額度以「月」為單位,幾筆請求的超用金額極小,換來的是使用者不用等、記帳故障不影響服務。M5 會實測並記錄實際超出多少。

**對照 LiteLLM(E25):** LiteLLM 同樣是非同步,實測累計花費約 12～14 秒後才寫進資料庫,空窗與本案同一量級。差別在帳放在哪裡:LiteLLM 放記憶體(當機會掉),本案放 SQS(不會掉)。

**升級門檻:** 若額度必須是硬上限(例如依合約向部門計費),改成預扣。

**v2.9(D58,E94、E103):** 預扣 M3 不做,留到 M5 一併決定。M3 先給每顆模型輸出上限,讓「一次最多超扣多少」變成算得出來的數字:便宜模型一次最多 1,000 micro-USD,強模型約 20,000 加輸入(訊息上限 4,000 字,約 8,000)。所以強模型下的超扣會比 M2 實測的 4%～12% 大很多;alice(額度 1,000)若在已用 999 時送出一題被路由到強模型的請求,回來可能是額度的好幾倍。

**v2.10(E116、E124):M4 仍是同步扣減**(事前加 0、事後原子累加,Gateway 自己做),只是搬上雲:任務角色對 `quotas` 有讀與 `UpdateItem`;雲端實測 bob 一次 `cost_micro_usd: 4`、`charged: True`。稽核改寫進 `audit` 表後,「扣額度與寫稽核同時失敗」時,那一筆的金額與 `charged: false` 只留在一行日誌(測試涵蓋;日誌也寫不出去時就沒了);補收是手動的,正式解法與預扣都在 M5。

**v2.8:M2 的同步扣減實際怎麼做(D51,E91、E92)。**

| 時間點 | 做什麼 | 失敗時 |
|---|---|---|
| 呼叫模型之前 | 對當月已用量那一筆做一次「加 0」的寫入(`ADD used_micro_usd 0`;那一筆不存在時會被建立,值為 0) | 回 503,模型還沒被呼叫,一毛都沒花 |
| 模型回答之後 | 算出成本,以 `ADD` 原子累加到同一筆 | 回答照給;稽核記 `charged: false` 與 `cost_micro_usd` |

- **為什麼要事前加 0:** 模型已經回答之後才發現扣不了帳,這時不給回答是白花錢,給了又可能被一直免費用。資料庫整個連不上時,請求在驗證那一步就回 503;會持續免費的只有「讀得到、寫不進去」(例如權限只給了讀),事前加 0 擋的就是這一種
- **不選的做法:** 扣失敗就不給回答、回 503(使用者白等、錢已經花了);不做事前檢查就照給(讀得到寫不進去時可以一直免費用)
- **這是預扣的前半步,不是預扣:** 它只確認「寫得進去」,沒有先保留金額。**所以 M2 會超扣**:檢查在呼叫前,金額要呼叫後才知道。真實驗收時額度 1,000 micro-USD 的使用者,已用量 892 時放行,回來變成 1,120(超出 12%);另一次是 818 → 1,039。同一個人同時送很多請求時幅度更大
- **事前加 0 之後、真的扣款之前,資料庫仍可能出問題;**這時回答照給、錢沒扣到,只留下稽核的一筆紀錄。目前沒有補收的機制與告警(12.5)
- **稽核因此不和額度放在同一個資料庫(D52):** 扣款失敗時靠稽核記下金額;兩者放一起,資料庫寫不進去時這筆紀錄也寫不進去

---

# PART 8 — 實作路線圖

> **v2.1 調整:** 路線圖由「按 AWS 服務分層」改為「按可獨立展示的里程碑」。內容沒有變,只是換成「你能證明什麼」的說法。每一關通過驗證才進下一關,而且每一關完成後,專題本身都是一個完整可展示的作品。

## 8.1 AI agent 分層與本專題定位

**生活比喻:** 一般聊天機器人像櫃檯問路的人:你問一句他答一句,不會離開櫃檯。AI agent 像一位管家:你說「週五幫我訂四人晚餐」,他會自己查餐廳、看行事曆、客滿就換一家,最後回報你。核心是一個迴圈:**想 → 動手(用工具)→ 看結果 → 再想**,直到任務完成。

管家花的是你的錢,所以需要預算、門禁與帳本,這就是本專題的「治理層」。agent 做一件事會在迴圈裡連續呼叫模型十幾次,失控時燒錢比一般聊天快得多,這正是治理層存在的理由。

**定位(v2.8,D41):** 作者是雲端工程師,做的是 LLM 上線之後的治理層,也就是下表的第 2 層;第 5 層知識檢索不實作,理由與「正式環境會怎麼做」見 7.9。

| # | 層級 | 白話 | 怎麼驗證 | 本專題 |
|---|---|---|---|---|
| 1 | 模型串接與紀錄 | 讓 AI 能被呼叫並留下紀錄 | 送一次請求,看到紀錄 | ✅ M1 |
| 2 | 治理(身分、額度、路由、稽核) | 管家的預算、門禁與帳本 | 超額被擋、回 429 | ✅ 主角(M2、M3、M5) |
| 3 | 工具呼叫 | 管家會用電話與行事曆 | AI 要求呼叫工具,結果正確帶回 | ⭕ 有條件開工(M7,文字約定) |
| 4 | 多步驟迴圈 | 想 → 做 → 看 → 再想 | 任務完成,且有最大步數上限 | ⭕ 有條件開工(M7) |
| 5 | 知識檢索(RAG) | 管家翻公司手冊 | — | ❌ 延伸,不做(見 7.9) |
| 6 | 觀測 | 看管家每天花多少 | Grafana 看到曲線 | ✅ M6 |

## 8.2 里程碑總覽

| # | 里程碑 | 證明什麼 | 對應原階段 | 狀態 |
|---|---|---|---|---|
| M0 | 前置作業(不算里程碑) | 有成本防護才開工 | 1 | ✅ 9/26 完成 |
| M0.5 | 拆解 LiteLLM(本機實驗) | 被問「為什麼不用現成的」時有實證 | 新增(v2.2) | ✅ 9/26 完成 |
| M1 | 最小對話閘道(本機) | 會串接 LLM、有可追溯紀錄 | 4(本機部分) | ✅ 10/4 完成 |
| M2 | 身分、額度與個資偵測 | 不只記錄,還能管控;壞掉時安全地壞 | 4(本機部分) | ✅ 10/9 完成 |
| M3 | 智慧路由、成本與備援 | 具備成本意識 | 4(本機部分) | ✅ 10/13 完成 |
| M4 | 上雲與受控出口 | 雲端架構與安全設計 | 2、3、4(ECR → Fargate) | ✅ 10/20 完成 |
| M5 | 非同步記帳與稽核 | 記帳失敗不影響使用者,帳也不會遺失 | 5 | ⬜ |
| M6 | 展示與自動化 | 可觀測、可重複部署、可現場展示 | 6、7、8 | ⬜ |
| M7 | (最後再做)小型 agent | 治理層在 agent 情境下真的有用 | 新增 | ⬜(v2.9:M4～M6 完成後) |
| — | 文件與錄影 | 完整技術說明,貫穿全程、最後定稿;每關驗收當下錄影(v2.8) | 9 | 進行中 |

### M0 前置作業 ✅
- **做什麼:** AWS Budgets(US$20 告警)、確認模型存取權限
- **驗證:** 收到一封測試告警信;用便宜模型成功呼叫一次
- **結果(9/23～9/26):**
  - AWS 帳號基線:MFA、刪長期金鑰、改用 `aws login`、US$20 預算、告警管道驗證(S18 前半)、東京單價查證(E1～E10)
  - Bedrock 被帳號層級封鎖(E3、E5),改用 OpenAI(E12)
  - OpenAI 查證(E20)與五道防線(E21,S21)
  - **9/26 `gpt-6-luna` 第一次呼叫成功**,`reasoning_tokens: 0`,花費 $0.0000068;白名單外的 `gpt-6-astra` 實測被擋(E22)
- **結案說明:** `docs/milestones/m0-m05-report.md`

### M0.5 拆解 LiteLLM(本機實驗,v2.2 新增)✅
- **為什麼:** 指導老師指出懂行的人會問「為什麼不用 LiteLLM」。先拆解別人怎麼設計,再決定自己做什麼,比事後辯解有說服力
- **做什麼:** docker-compose 啟動 LiteLLM 官方映像(依冷卻期規則鎖定版本,用 digest 驗證 cosign 簽章)+ PostgreSQL;設定一個 OpenAI 便宜模型;建立一把預算極小的虛擬金鑰,呼叫到被擋
- **觀察結果:**
  1. 拿掉 PostgreSQL 後預算還有沒有作用 → 斷線 503 拒絕並自動恢復(E18);沒設 → 無虛擬金鑰、無警告(E19)
  2. 記憶體 → 待機 584 MiB、輕度負載 574～578 MiB,都超過 512 MiB 規格(E16、E27)
  3. 啟動時的對外連線 → 下載 GitHub `main` 分支的價格表,以 `LITELLM_LOCAL_MODEL_COST_MAP` 關閉(E15)
  4. 花費同步或批次寫 → **批次**:明細約 7～10 秒、累計約 12～14 秒後寫入(E25)
  5. 官方範例的預設值 → 7 項需強化,已全數處理(E13)
  - **追加 ①:** 內建價格表沒有 `gpt-6-luna`、`gpt-6-sol` → 花費記為 0,預算安靜失效(E23)
  - **追加 ②:** 寫帳前強制終止 → 永久掉帳;照出本案 2.2 流程的缺口(E26 → D31)
  - **追加 ③:** 模型設定以 `LITELLM_SALT_KEY` 加密,這把金鑰不能輪替;當天就遇到它外洩後的兩難(E24、E28)
  - **附帶:** 浮點數誤差 6.8e-6 → 6.799999999999999e-06,佐證 D1(E25)
- **安全措施:** OpenAI 專用 Project 與服務帳號金鑰,設儲值與 Project 上限、只允許兩顆模型;實驗結束撤銷金鑰(E28);LiteLLM 只綁 `127.0.0.1`,PostgreSQL 不對外開埠
- **驗證:** 截圖 S19、S20(見 11.4)
- **實際時間/成本:** 9/25～9/26 約兩個晚上;OpenAI 呼叫約 $0.0003
- **產出:** 10.2 對照表的 LiteLLM 欄、10.3 第 1～13 點;官方範例的安全預設值拆解表(E13)
- **結案說明:** `docs/milestones/m0-m05-report.md`

### M1 最小對話閘道(本機)✅
- **做什麼:** FastAPI + Docker,透過薄介面(官方 OpenAI SDK、Chat Completions)完成對話;記錄 input / output,**內容只存 HMAC 雜湊與遮罩摘要,不存完整 prompt**(符合 4.2 資料層;M1～M4 由 Gateway 直接寫入,M5 移交 Worker;本機的 HMAC 金鑰用環境變數,雲端改從 SSM 注入);pytest 從這一關開始寫
- **開工前:** OpenAI 開一把 M1 專用的新金鑰(規格同 E21:服務帳號、Restricted 只開 Chat completions、30 天到期),不沿用實驗金鑰;開發環境用 VS Code,`.env` 不在 VS Code 中開啟(避免 AI 擴充讀取)
- **驗證:** 本機送一次 `POST /v1/chat` 拿到回應;稽核紀錄看得到 hash 與摘要,找不到完整 prompt;`usage` 的思考 token 有被記錄
- **證明:** 會串接 LLM、有可追溯紀錄(對應指導老師建議的 Step 1)
- **結果(9/28～10/4,v2.7):**
  - **驗證全數通過(E72、E74):** 本機與容器各實際呼叫一次,回應 `hello`、`gpt-6-luna`;稽核紀錄有 64 字元的 HMAC 雜湊與前 50 字摘要;以超過 50 字的句子呼叫後,在稽核檔搜尋後半句**無結果**;`reasoning_tokens: 0` 有被記錄
  - **程式:** `GET /health`、`POST /v1/chat`、薄介面 `chat()`、`hash_prompt`、`make_summary`、`append_audit`;17 個 pytest,全部用假的 OpenAI,不需金鑰、不花錢
  - **測試擋下的三個錯誤(E65、E69):** 檔案已關閉仍寫入;沒有思考 token 明細時程式出錯;**重構時把稽核紀錄整個換掉,少了四個欄位而使用者端看不出來**(由對應驗收條件的測試擋下)
  - **安全基線(E44～E50、E71):** 第一次 commit 前確認 `.env` 進不了 Git、改用 noreply 信箱;第一次 push 前開啟 GitHub 安全功能;`main` 禁止強制推送(實測被擋);M1 專用金鑰(服務帳號、Restricted、30 天)
  - **容器(E74):** 多階段建置、基底映像鎖 digest、非 root、`.dockerignore` 白名單(建置時只送出 307 位元組)、映像內沒有 `.env` 與測試工具;映像 220 MB
  - **與供應商對帳:** OpenAI Usage 顯示 2 次請求、48 個輸入 token,與兩筆稽核紀錄(各 24)一致(E75)
- **M1 的已知限制:** `mask()` 是空殼,只能使用不含個資的測試句(E34);稽核寫入檔案,容器停止即消失(M2 換成 DynamoDB Local);尚未做映像弱點掃描(Trivy 於 CI 建立時加入)
- **實際時間 / 成本:** 約 18 小時;OpenAI 兩次呼叫共 $0.0000088;AWS $0
- **結案說明:** `docs/milestones/m1-report.md`

### M2 身分、額度與個資偵測 ✅
- **做什麼:** API Key 驗證(`api_keys` 表,只存雜湊)、每人每月美元額度(`quotas` 表)、超額回 429;種子腳本建立 alice(**US$0.001**,示範被擋)與 bob(US$1.00),API Key 只在建立時顯示一次。本機階段用 DynamoDB Local,並且**暫時由 Gateway 同步扣減額度**(原子累加,見 7.10),M5 再移交給 Worker
- **加做(v2.2):**
  - **fail-closed:** 配額表讀不到時一律拒絕(回 503),不放行。M0.5 實測 LiteLLM 預設也是這樣(E18),本案採同樣做法;拆解時學到的是 fail-closed 的代價:資料庫掛 = 服務停擺,所以資料庫本身要高可用(見 10.3)
  - **邊界值:** 測試案例加入「額度 0」,確認被當成嚴格上限而不是無上限(E17)
  - **個資偵測:** 送進模型前,用正規表示式偵測身分證字號、手機、Email、信用卡號(加 Luhn 檢查降低誤判),命中就遮罩後再送;稽核表記錄「偵測到哪一類個資」,不記內容。v2.5 起內容會送出 AWS,這一項變成必要(OpenAI 端最多保留 30 天,E20)。正式環境換成託管的內容防護服務(例如 Bedrock Guardrails)
  - **時區(v2.6):** `period` 以台北時間切月,寫成單一函式並加跨月邊界的 pytest(3.2)
  - **錯誤訊息(v2.6):** API Key 錯誤只回「驗證失敗」,不透露是「不存在」還是「已停用」(E22 的 `model_not_found` 啟示)
- **驗證:** 連續呼叫直到超額,看到 429;停掉 DynamoDB Local 容器,看到 503 而不是放行;送出含**假**身分證字號的句子,看到遮罩結果與稽核事件
- **證明:** 不只記錄,還能管控,而且壞掉時是安全地壞
- **結果(10/4～10/9,v2.8):**
  - **驗證全數通過(E92,真的 OpenAI,截圖 S01～S04,各錄一段影片):**
    - **S01:** 錯的 Key 得到 `401`、`www-authenticate: Bearer`、`Authentication failed`;同一個畫面上正確的 Key 得到 200
    - **S02:** alice(額度 1,000 micro-USD)連續呼叫,已用量 444(前兩次之後)→ 665 → 892 → 1,120,共成功 5 次,第 6 次得到 `429`;`retry-after: 1923143`,手算到台北 11/1 00:00 為 22,343 + 1,900,800 = 1,923,143 秒,一秒不差。被擋下的那一次,稽核有 `user_id` 與 `quota_exceeded`,沒有模型與成本欄位
    - **S03:** bob 有額度;停掉 DynamoDB Local 後得到 `503`、`Service temporarily unavailable`,沒有放行
    - **S04:** 請模型原樣重複 `My ID is A123456780`(假的身分證字號),回答是 `My ID is [TW_ID]`;稽核 `pii_types: ["TW_ID"]`;在稽核檔搜尋號碼無結果
  - **程式:** `app/auth.py`(驗證)、`app/db.py`(連線)、`app/quota.py`(切月、超額判斷、讀額度、扣額度)、`app/pricing.py`(成本);`mask()` 補上四類個資;`scripts/create_tables.py`、`scripts/seed.py`;`compose.yaml`(DynamoDB Local 兩個容器)
  - **測試:** 17 → **119 個**;其中 45 個連真的 DynamoDB Local(標 `integration`,用獨立的容器 `127.0.0.1:8002`,每個測試前清空);其餘用假的 OpenAI 與替身,不需金鑰、不花錢。每個功能寫完都做破壞實驗,確認測試為了預期的原因而紅
  - **與原計畫不同的三處:** 額度改放使用者層級(D50);稽核仍存檔案,M4 前搬(D52);成本換算在決策書排在 M3,但扣額度就需要金額,M2 先做只含 `gpt-6-luna` 的最小版(D45)
  - **測試教會的事:** 「被拒絕的請求不碰模型」這個測試,在網址打錯、請求其實是 404 時也是綠的。檢查「某件事沒發生」之前,要先確認請求真的走到了該被擋的地方(E90;結案報告第 4 節)
  - **量測:** M2 映像待機記憶體 62.06 MiB(M1 為 56.08 MiB;LiteLLM 584 MiB)
  - **與供應商對帳:** Gateway 的稽核檔有 15 筆有成本的紀錄,共 2,185 micro-USD;OpenAI 後台近 7 日顯示 17 次請求,扣掉 M1 的 2 次後一致。後台的金額顯示為 `$0.00`,這一關花了多少只有 Gateway 自己的紀錄算得出來
- **M2 的已知限制:** **會超扣**(7.10);扣額度失敗的金額只記在稽核檔,沒有補收與告警;稽核仍是本機檔案;**驗收是直接以 uvicorn 啟動的 Gateway,不是容器**(映像只確認建得起來、`/health` 有回應);S03 示範的是資料庫整個停掉,「讀得到、寫不進去」只有測試涵蓋;個資偵測只有四類規則;沒有停用 Key 的指令;S02 目前是終端機畫面,M6 用 Console 重拍
- **實際時間 / 成本:** 約 29 小時;OpenAI 15 次呼叫共 US$0.002185;AWS $0
- **結案說明:** `docs/milestones/m2-report.md`

### M3 智慧路由、成本與備援
- **做什麼:** 依 PART 12 的路由規則 v1 選擇便宜模型或強模型;用 token × 單價換算每次成本
- **從 M2 接過來的(v2.8):** 成本函式 `cost_micro_usd()` 已在 M2 做了只含 `gpt-6-luna` 的最小版(單價是程式內的字典常數,13 / 11 token → 7 micro-USD 的測試已通過);M3 把單價搬到設定檔、加入 `gpt-6-sol`、決定沒有單價時的錯誤類型與對使用者的回應;用 `gpt-6-sol` 的一次真實回應實證輸出 token 已含思考 token
- **加做(v2.2):**
  - **備援:** 強模型被供應商限流時自動降級到便宜模型,並記錄 fallback 事件;用 pytest mock 模擬,不用真的打到限流。**供應商預算用完的 429 不降級(D32)**
  - **外行版數字:** 用同一組約 20 題,比較「全部用強模型」與「智慧路由」的成本(強模型部分用 token 數 × 單價估算,不實際呼叫),得出 11.2 要用的「省下 X%」
- **加做(v2.6):**
  - **單價缺漏 fail-closed(D30):** 路由選到的模型在設定檔裡沒有單價 → 拒絕呼叫並記錄設定錯誤,不當成 0 元
  - **進位(D30):** token × 單價 → 無條件進位成 micro-USD 整數;pytest 驗算 E22 的 13 / 11 token → 7 micro-USD
  - **記錄原始錯誤碼:** 供應商錯誤(如 `model_not_found`)原樣寫進日誌,方便排查設定錯誤(E22)
- **驗證:** 一個簡單、一個複雜的問題,選到不同模型;成本數字與手算一致;模擬限流時看到降級紀錄;模擬「沒有單價的模型」時看到拒絕
- **證明:** 具備成本意識
- **注意:** M1～M3 在本機執行,只有模型是真的呼叫(小額費用,已含在 6.3 預算內)。為了守住 6.4「全程便宜模型」的省錢原則,強模型只實際呼叫少數幾次,路由邏輯本身用 pytest mock 驗證
- **v2.9 更正:** 為了讓「省下 X%」用實測而不是估算,步驟 7 改為 20 題兩顆模型都真打一次(40 次,US$0.059);調整規則時只重算、不再呼叫(E101、E103)
- **結果(10/10～10/13,v2.9):**
  - **驗證全數通過(E105,真的 OpenAI,截圖 S05～S07,各錄一段影片):**
    - **S05:** 「請把這句話翻成英文:今天天氣很好」→ `gpt-6-luna`、`default`;「請用三句話說明:設計一個多人共用的 AI 服務,架構上要注意什麼?」→ `gpt-6-sol`、`keyword`
    - **S06:** 稽核成本 1,438,畫面上手算 34 × 2 + 137 × 10 = 1,438;簡單題 19 × 0.1 + 10 × 0.5 = 6.9 → 7。20 題比較表:照規則分流 **41,612 對全部用強模型 55,724 micro-USD,省 25.3%**(送對 18 題)
    - **S07(模擬):** `scripts/demo_fallback.py` 只把強模型換成假的 429,其餘全是真的;畫面開頭印 `SIMULATION:`。同一句複雜題 → `200`、回答來自 `gpt-6-luna`,稽核 `routed_model: gpt-6-sol`、`model: gpt-6-luna`、`fallback: True`,成本 65
    - **沒有單價的模型:** 設定檔指到不存在的模型 → Gateway 起不來(`ConfigError`,E96);執行中查不到 → 500、寫稽核、不呼叫模型、不扣錢(4 個測試,E98)
    - **思考 token:** 強模型上限 16 時輸出 16、其中思考 16、回答 0 字,照收 208(E101)
  - **程式:** `app/config.py` 與 `app/config.toml`(設定檔)、`app/router.py`(`choose_model()`、`contains_keyword()`)、`app/fallback.py`(`chat_with_fallback()`、`is_budget_exhausted()`、`retry_after_seconds()`);`app/pricing.py` 改寫為 `find_model_config()` 與收設定物件的 `cost_micro_usd()`;`app/main.py` 接上路由與降級
  - **測試:** 119 → **267 個**(45 個 `integration`);每個功能寫完都做破壞實驗
  - **CI:** pytest + Trivy + CodeQL;第一次執行就抓到基底映像的 HIGH(換指紋)與信箱規則的速度問題(4 萬字 2.5 秒 → 0.007 秒);故意改壞設定開 PR,CI 擋下(E104)
  - **與供應商對帳(E106):** 51 次呼叫、65,352 micro-USD;OpenAI 後台近 7 日 66 次,扣掉 M2 的 15 次是 51,一致;金額只顯示到分,在四捨五入範圍內
  - **測試教會的事:** 數字好看不代表做對了。舊規則省 30.9%,比完美分流的 22.5% 還多,多省的錢是把複雜題送去便宜模型換來的;字數門檻 500 省 54%,其中 24 個百分點來自一題(結案報告第 4 節)
- **M3 的已知限制:** 25.3% 只來自 20 題,規則是用同一組題目調的;從來沒遇過真的 429;強模型下的超扣比 M2 大(預扣在 M5);被截斷的空回答照樣扣錢;容器裡讀不讀得到 `app/config.toml` 還沒有實際跑過(CI 只建映像、不執行);驗收仍是直接以 uvicorn 啟動的 Gateway
- **實際時間 / 成本:** 約 20 小時;OpenAI 51 次呼叫共 US$0.065;AWS $0
- **結案說明:** `docs/milestones/m3-report.md`

### M4 上雲與受控出口(v2.5 改寫)✅
- **做什麼:** Terraform(遠端 State、OIDC 角色、最小權限)建置 VPC、子網、Security Group、NAT Gateway、DNS 防火牆、Gateway Endpoint(含 Endpoint Policy);Gateway 打包上 ECR、跑在 Fargate;ALB 作為唯一對外入口
- **開工前(v2.6):** 評估 OpenAI 工作負載身分聯盟能否以 Fargate 的 IAM 角色換取短期憑證;可以就不在 SSM 放 OpenAI API Key(4.5)
- **開工前(v2.8,從 M2 帶過來):** 稽核搬進 `audit` 表,並決定扣額度失敗的紀錄放哪裡、怎麼補收與告警(D52);`compose.yaml` 加上 Gateway,先在本機驗證容器內連資料庫的完整流程;`app/db.py` 怎麼表示連真的 AWS(不給網址、不帶假帳密,用 Fargate 的 IAM 角色,並保留「沒講清楚要連哪裡就報錯」的性質);決定要不要強一致讀取;上雲後量一次請求延遲(每個請求最多 5 次資料庫往返,而且每次新建連線)
- **開工前(v2.9,從 M3 帶過來):** 容器實際跑一次,確認讀得到 `app/config.toml`、對話流程完整(與 `compose.yaml` 加上 Gateway 一起做);便宜模型那次 SDK 可能等最多 120 秒,與 ALB 預設 60 秒閒置逾時的衝突(關掉便宜模型的重試,或調整 ALB 逾時);Trivy 升級與 Action 的更新方式(評估 Dependabot 搭配冷卻期);M4 有 Terraform 後 CI 加 `trivy config`
- **驗證:** 雲端跑通與本機相同的流程;Fargate 沒有 Public IP;DNS 防火牆先用告警模式收集網域、再切成阻擋;容器連 `api.openai.com` 成功、連清單外的網域被擋,查詢日誌看得到被擋的紀錄;`enable_ecs_exec` 預設關閉,改成 `true` 後能進入容器;`terraform destroy` workflow 實測可以一鍵收掉
- **證明:** 雲端架構與安全設計(受控出口)
- **注意:** 3.5 的五個必踩的坑(不寫 `*.amazonaws.com`、先告警後阻擋、S3 Endpoint Policy、安全群組管不到 DNS、ALB 兩個 AZ)。若實測發現放行清單漏了網域,補上並記進 8.3 的「挫折與解法」
- **開工前各項(v2.6、v2.8、v2.9 列的)v2.10 全部完成(10/14～10/15,E108～E116):** 分支流程實測、容器實際跑一次(讀得到 `config.toml`、真實對話完整)、`compose.yaml` 加上 Gateway、稽核搬進 `audit` 表、`DYNAMODB_TARGET` 與強一致讀取、停用 Key 的腳本、說明頁關閉、資料庫 503 不附 `Retry-After`、SDK 不重試與逾時 60 秒、身分聯盟探測成功、Dependabot;`trivy config` 在本體開工後加入(E118)
- **結果(10/14～10/20,v2.10):**
  - **驗證逐條對照(E122、E124、E125):**

    | 驗證項目 | 結果 |
    |---|---|
    | 雲端跑通與本機相同的流程 | ✅ 每日層 36 個資源 apply,ECS 服務 1 分 8 秒穩定(經 NAT 拉到映像、三個 SSM 參數交給容器、唯讀根目錄下啟動、ALB 健康檢查通過);`/health` 200;bob 聊天 `Bonjour !`(`gpt-6-luna`);雲端稽核 `status: ok`、`charged: True`、`cost_micro_usd: 4`(手算 3.7 → 4)、`pii_types: []` |
    | Fargate 沒有 Public IP | ✅ 服務 `assignPublicIp = DISABLED`、任務網卡 `PublicIp = None`、私有子網 `AutoAssignPublicIp = False`(S09) |
    | DNS 防火牆先告警、再切阻擋 | ✅ ALERT 約一小時,容器查過的網域剛好是放行清單 9 個,不用改清單;切 BLOCK 後再聊天照樣成功 |
    | 連 `api.openai.com` 成功、連清單外被擋,查詢日誌看得到 | ✅ 一次性任務:`api.openai.com` DNS 有回答、TCP 443 連得上;`example.com` DNS 查不到;查詢日誌 4 筆 `BLOCK`(S08,錄影 `m4-s08-egress-control.mp4`) |
    | `enable_ecs_exec` 預設關閉,改成 `true` 後能進入容器 | **不做(D 段定案 6,D94),留白。** ECS 服務寫死不開 ECS Exec;S08 改用一次性任務 |
    | `terraform destroy` workflow 一鍵收掉 | **C 段(10/18):✅ 51 秒拆光 19 個資源**,帳本為空;**D 段(10/19,`destroy #2`):❌ 3 分 31 秒卡在 `ec2:DisassociateAddress`**,本機補拆、問 AWS 確認拆光;**已修(PR #16),修正後待 M5 開工時實測** |
    | Endpoint Policy、IAM 最小權限(S10、S11) | ✅ DynamoDB 走廊只准三種動作三張表、S3 走廊只准 `GetObject` 映像層 bucket(S10);兩個角色的 `Resource: *` 只有兩條,都是 AWS 規定不能指定資源的動作(S11) |

  - **程式(Python):** `app/openai_auth.py`(新,`OPENAI_AUTH`、身分聯盟);`app/db.py`(`DYNAMODB_TARGET`);`app/audit.py`(`write_audit()`、`save_audit()`、`report_audit_failure()`;`append_audit()` 移到 `tests/fakes.py`);`app/auth.py`、`app/quota.py`(強一致讀取);`app/main.py`(說明頁關閉、`OPENAI_MAX_RETRIES = 0`、`OPENAI_TIMEOUT_SECONDS = 60`、`get_audit_writer()`、`get_client()` 共用連線);`scripts/disable_key.py`、`scripts/show_audit.py`、`scripts/probe_wif.py`
  - **IaC 與工具:** `infra/persistent/`(11 個 `.tf`)、`infra/daily/`(11 個 `.tf`);`.github/workflows/destroy.yml`、`oidc-check.yml`;`.github/dependabot.yml`;`scripts/egress_check.ps1`、`egress_check.json`(S08 的一次性任務)、`show_egress_controls.ps1`(S10)、`show_gateway_roles.ps1`(S11)、`simulate_destroy_role.ps1`(權限模擬器 12 題,只印題目與結果);`compose.yaml` 加 `gateway`(profile `gateway`);`Dockerfile` 拿掉可寫的 `data` 資料夾
  - **測試:** 267 → **325 個**;每個功能寫完都做破壞實驗
  - **CI:** 第三個必要檢查 `Config scan`;Trivy v0.74.0;刻意接受 5 項(AWS-0132、0104、0053、0054、0095,12/31 到期)(D83)
  - **身分聯盟:** 雲端沒有 OpenAI 金鑰,Fargate 上叫得到模型(4.5,D71)
  - **告警:** 手寫一行假的 `audit_write_failed`,約 1 分鐘 `OK -> ALARM` 並寄信(`m4-alarm-email.png`)
  - **延遲與記憶體(只量幾次、從台灣量):** `/health` 5 次 113、41、41、42、42 ms;聊天 3 次 3,538、1,956、1,747 ms(多數時間在等 OpenAI);容器記憶體(ECS `MemoryUtilization`)兩小時最高約 14.8%(約 76 MiB),平均值沒有記到
  - **測試教會的事:** 綠燈不代表測對了:改 `DYNAMODB_TARGET` 時,視窗裡殘留的舊環境變數讓 43 個測試連到開發用的資料庫、清空資料表,而且全部綠燈(E111);權限模擬器 10 題全對,真的拆還是卡住,因為沒出到那一題(E124)
  - **挫折與解法(8.3):** PowerShell 5 經管線交 ECR 密碼會被重新編碼(`400 Bad Request`),改用 `--password` 再清掉變數;匯出的臨時憑證約 15 分鐘就過期、而且環境變數比 `aws login` 優先,改成「跑 Python 前後都清 `AWS_*`」;`-chdir=$tf` 裡的變數 PowerShell 不展開,要加引號;Docker 預設多附出廠證明,推 ECR 前加 `--provenance=false --sbom=false`;AWS 在網域結尾補點(D89、D92、D96)
- **M4 的已知限制:** 映像有 3 個 HIGH(上游沒有修補版,帶著上雲,D93);直接用 IP 連線沒有測;ALERT 只觀察約一小時、一種流量;延遲只量幾次、記憶體只有最高值;告警測試用的是手寫的假日誌;**destroy 修正後還沒實測**;DNS 結尾的點有沒有消除假改動待下一次 apply;雲端的 alice、bob Key 只存在當時的 PowerShell 變數裡;記帳仍是同步扣減(7.10);`usage` 表、SQS 在 M5;「只准 `main`」靠 GitHub 的 environment 設定
- **實際時間 / 成本:** 約 27 小時(10/14～10/20);AWS:D、E 段那一天約 1 小時 50 分,估約 US$0.22,**Cost Explorer 實際約 US$0.29**(主因 NAT 計了 3 小時);OpenAI 約 US$0.018(Gateway 自己算的,未與後台對帳;6.3)
- **結案說明:** `docs/milestones/m4-report.md`

### M5 非同步記帳與稽核
- **做什麼:** SQS + DLQ + Lambda Worker(算成本、寫用量表、寫稽核、更新配額);額度扣減由 Gateway 移交給 Worker;**Gateway 確認事件進 SQS 後才回應(D31)**
- **驗證(故障演練):**
  1. 手動停用 Lambda 的 SQS Event Source Mapping → 使用者仍正常拿到回應
  2. 重新啟用後事件補記,帳不漏
  3. 刻意讓處理失敗 3 次 → 訊息進 DLQ
  4. **(v2.6)對照 E26:** Gateway 回應後立刻強制停止工作,確認事件已在 SQS、帳不漏
- **證明:** 記帳失敗不影響使用者,帳也不會遺失
- **取捨紀錄:** 扣減改成非同步後會有超用空窗,實測記錄超出多少(見 7.10)
- **M5 定案項目:** SQS 寫入失敗時的處理(回答照給並記錯誤,或拒絕回答)
- **從 M4 帶過來(v2.10):** 雲端建 `usage` 表,Endpoint Policy 與 IAM 補上;稽核寫不進去的正式解法(目前只有一行日誌與手動補收,D77);預扣(7.10);**開工 apply 每日層時順便實測:修正後的 destroy workflow 一鍵拆光、DNS 網域結尾加點後 plan 是否乾淨**

### M6 展示與自動化
- **做什麼:** Demo Console(含 4.4 前端安全)、`/metrics` + 本機 Prometheus / Grafana、GitHub Actions CI/CD(pytest、tfsec、Trivy、OIDC);所有 Action 釘在 commit SHA、Python 依賴用含 hash 的 lock 檔(見 10.3)
- **v2.9:** CI(pytest、Trivy、CodeQL)已在 M3 完成(D62),M6 只剩 CD(OIDC、ECR、`terraform apply`、ECS 更新)與 destroy workflow;tfsec 改為 `trivy config`。S16 在 M3 已實際發生一次(CI 第一次執行,Trivy 擋下基底映像的 HIGH,換指紋後通過,E104),M6 照原計畫用分支重拍一次截圖。Demo 錄影照 3.1 的三章(D65);Grafana 要有「依使用者、依模型的花費」
- **v2.10:** destroy workflow 已在 M4 完成(D84～D86);M6 只剩 CD。CD 同樣用 GitHub OIDC 借角色(M4 的 OIDC 角色只給 destroy,D80),從 `main` 建映像、標籤用 commit 編號、只改 `image_tag` 再 apply(D92)。`/metrics` 的 token 放 SSM、ALB 加 Listener Rule(4.3)。S17 的 OIDC 已有 M4 的佐證截圖(`m4-oidc-*`)
- **驗證:** 照 3.1 的 Demo 腳本現場操作一次;push 一次程式,pipeline 自動跑完並部署;另開分支故意使用有已知漏洞的舊基底映像,看到 Trivy 擋下部署(截圖 S16)
- **證明:** 可觀測、可重複部署、可現場展示

### M7 (最後再做)小型 agent
- **v2.9(D66):** 本人 10/14 決定先把 M4～M6 做完,M7 最後再做;第一個開工時段(10/17～10/18)取消
- **v2.8 改寫(D42,E79):** 由「選配」改為「有條件開工」,做法由原生工具呼叫改為**文字約定**,限時 6 小時
- **做什麼:** 一個獨立的客戶端腳本(例如 `scripts/agent-demo/`)當 Gateway 的使用者,對本機的 Gateway 執行;`POST /v1/chat` 與請求格式(D38)不改。迴圈用文字約定:模型回 `CALL 工具名(參數)` 就執行工具,結果放進下一輪的 `message`;回 `FINAL 答案` 就結束。一到兩個本機小工具,不連外部服務;設定最大步數上限;每一步都經過 Gateway 的身分、額度、遮罩、稽核
- **為什麼不用 OpenAI 原生的工具呼叫:** 原生做法要讓 Gateway 接受完整對話紀錄與工具定義,等於改掉 D38,遮罩與稽核也要處理工具回傳的內容,估 8～12 小時,而且會動到 M1、M2 已驗收的東西。文字約定不動 Gateway,估 5～6 小時。代價:它不是原生工具呼叫,文件與影片要照實說明;原生做法列為升級路線(7.9)
- **驗證:** ① 正常完成兩三步的任務,稽核看得到每一步;② 拿掉步數上限、改用低額度的 alice,迴圈被額度擋下(429)並停止
- **證明:** 治理層在 agent 情境下真的有用(呼應 8.1)
- **開工條件(v2.9 修訂,兩個時段擇一,都沒達到就不做):**

  | 時段 | 條件 |
  |---|---|
  | ~~10/17～10/18~~ | ~~M3 與 CI 都在 10/16(五)前完成~~(v2.9:條件已達成,但本人選擇先做 M4～M6,取消) |
  | 10/31～11/1 | M6 在 10/30(五)前完成 |
  | 11/2～11/3 | M6 在 11/1 準時完成,且沒有要補的進度、截圖或錄影;金鑰要用新的 |

- **備案:** 把 M2 驗收的「連續呼叫到超額」寫成十幾行的迴圈腳本,旁白講成模擬失控的迴圈
- **開工前要注意:** 工具結果會經過 `mask()`,一串數字可能被當成手機或卡號遮掉;`message` 上限 4,000 字,任務設計成三步以內

## 8.3 每關收尾清單

每一關通過驗證後,立刻補一段紀錄,這些就是面試素材:

1. **驗證證據:** 依 11.4 截圖清單拍攝,並依 11.5 遮蔽敏感資訊。v2.7(E60):截圖只留 11.4 清單與出錯、決策、驗證的關鍵畫面;例行操作(例如 `git push`)改以文字收錄
2. **遇到的挫折與解法:** 卡在哪、怎麼查、怎麼解決
3. **新的取捨決定:** 有的話補進 PART 7,並寫「為什麼不選另一個」
4. **實際花費:** 這一關實際花多少,對照 6.3 的預估
5. **里程碑結案報告(v2.7):** 寫在 `docs/milestones/`,含「發現 → 設計 → 哪一關用到」對照;決策書只在里程碑完成時改版,待改項目先列在報告附錄
6. **錄影(v2.8,E79;v2.9 用 Windows 內建錄影):** 每個驗收條件錄一段(原訂 20～30 秒;M2 實際 32～82 秒、M3 44～59 秒,剪輯時把打字的部分加速)。先不錄跑一次確認結果,再錄。雲端資源驗收完就會 destroy,事後補錄要重新 apply、多花錢,所以驗收當下就錄。規範見 11.5
7. **更新簡報與旁白稿(v2.8,E84):** 替換對應頁面的畫面、更新狀態標籤與附錄的素材狀態,旁白稿同步改;版號 +0.1(11.6)。**v2.10(簡報 v3):** 截圖的重點一律框起來(終端機畫面用細線、只圈那一行,不蓋到上下的字);進度標籤與給自己看的備註不上台;錄影不嵌進 10 分鐘報告版;版號由本人定(10/19 定名 v3,取代原擬的 v2.1)
8. **destroy 之後直接問 AWS 確認拆光(v2.10,E124):** 不只看 workflow 綠燈或帳本是空的;查 `Layer=daily` 的 NAT、彈性 IP、VPC,`llm-gateway` 的 ALB 與 DNS 防火牆規則群組,ECS 叢集是 `INACTIVE`

## 8.4 時間吃緊時的取捨(v2.4 定案)

**不可砍:** 受控出口(M4)、pytest、CI/CD 主 pipeline、技術文件(含 PART 10 對照表與 PART 11 截圖)

**砍的順序:**
1. M7 小型 agent(v2.8:沒達到 8.2 的開工條件就不做,改用備案;v2.9:排在 M4～M6 之後)
2. ~~技術版影片縮為 6～8 分鐘(v2.8 新增)~~(v2.9:呈現改為 10 分鐘報告 + 6 分鐘廠商影片,此項失效;需要時改為「6 分鐘影片只放三章 Demo 的結果」)
3. Jenkins 本機示範
4. 本機 Prometheus / Grafana(保留 `/metrics` 端點)
5. Demo Console 縮成最小版
6. M5 故障演練精簡為只做一種
7. ~~M0.5 本機實驗縮為只讀官方文件~~(v2.6:M0.5 已完成,此項移除)

**排程建議:** CI 階段(pytest、tfsec、Trivy)在 M4 上雲前就先建好,避免「不可砍」的項目全部擠到最後。(v2.9:已在 M3 完成,tfsec 改為 Trivy)

## 8.5 時程與檢查點(v2.4 定案,v2.6、v2.8、v2.9 更新)

| 期間 | 內容 | 在哪裡跑 |
|---|---|---|
| ~~10/1(四)～10/4(日)~~ **9/23～9/26** | M0 前置 + M0.5 拆解 LiteLLM ✅(提前完成) | 本機 |
| **10/1(四)～10/11(日)** | M1 ✅(10/4 完成)+ M2 ✅(10/9 完成,原訂 10/10) | 本機 |
| ~~10/12(一)～10/18(日)~~ **10/10～10/13** | M3 ✅ + CI ✅(10/13 完成,提前五天) | 本機 + GitHub |
| **10/14(三)～10/16(五)** | M3 收尾(決策書 v2.9、`SECURITY.md`、分支流程)+ M4 開工前的本機準備(8.2 M4 的「開工前」各項;12.5 列「M4 前」的項目) | 本機 + GitHub |
| ~~10/19(一)~~ **10/17(六)～10/25(日)** | M4 上雲與受控出口(v2.9 提前兩天開工)✅(10/20 完成,提前五天) | AWS |
| 10/26(一)～11/1(日) | M5 + M6。M7 只在 M6 於 10/30 前完成時,用 10/31～11/1 | AWS |
| 11/2(一)～11/4(三) | 緩衝;M7 的另一個時段 11/2～11/3(條件見 8.2) | AWS |
| 11/5(四)～11/7(六) | 文件定稿、簡報定稿、兩支影片剪接與旁白(各關的畫面已在驗收當下錄好) | 本機 |

> **v2.10(E108～E126):** M4 於 10/20 完成(修正 PR #16 合併),約 27 小時,檢查點 10/25,提前五天。實際走法:10/14～10/15 開工前準備(本機);10/15 晚上本體開工定案(兩層、S3 鎖檔、本人電腦 apply、ALB 只開本人 IP);10/15～10/16 長期層骨架與 CI 的 `Config scan`(沒有登入 AWS);10/17 長期層上雲、GitHub OIDC 與 destroy 角色;10/18 每日層免費骨架與第一次 destroy;10/18 D 段定案與程式;10/19 D、E 段上雲驗收、當天拆;10/20 修正 PR。Claude 在 v2.9 的粗估是 M4 含開工前 25～30 小時,實際約 27 小時,落在範圍內。下一段是 M5 + M6(10/26～11/1),M7 的條件不變。
>
> **v2.9(D66,E106、E107):** M3 於 10/13 完成,約 20 小時,檢查點 10/18,提前五天。本人 10/14 決定:省下的時間**先給 M4～M6,M7 最後再做**,目標是讓後段有餘裕、不要趕。M4 提前到 10/17 開工,10/14～10/16 先做完 M3 收尾與 M4 開工前的本機準備(容器實際跑一次、`compose.yaml` 加上 Gateway、稽核搬進 `audit` 表、`app/db.py` 連真的 AWS 的做法、ALB 逾時與 SDK 等待、工作負載身分聯盟評估)。檢查點不動。
>
> Claude 的粗估(不是量測):M4 含開工前 25～30 小時、M5 12～15、M6 15～20、簡報手作與影片 15～20,合計約 67～85 小時;10/14～11/4 約三週、可投入約 75～85 小時。餘裕仍不大,所以 M7 排在最後、隨時可以改用備案。簡報的手作與計時試講(10/18 前)穿插在 M4 期間做。
>
> **v2.8(E79、E92):** M2 於 10/9 完成,比 10/10 提前一天,實際約 29 小時。10/5 老師回饋後多出的工作量:各關驗收錄影約 3 小時、技術版影片剪接與旁白約 5～6 小時、M7 限時 6 小時,合計約 14～15 小時。v2.7 估的餘裕只有 5～15 小時,影片的 8～9 小時是必做,已吃掉大部分;M7 只能靠前面幾關提早完成來換,所以一定要有開工條件。里程碑的檢查點不動。
>
> **v2.7(E60):** 可投入時間為平日每天至少 3 小時、假日約半天,換算每週約 25 小時;10/1～11/7 約 130 小時,剩餘工作量估計 115～125 小時,可行但餘裕小,最大風險是 M4。每週最後一天對一次進度,落後超過兩天就提早啟用 8.4 的砍除順序。為了守住時程:例行截圖精簡(8.3);Dockerfile 與 M4 的 Terraform 由骨架改寫,本人負責理解、修改、執行、除錯,並能說明每個設定的理由(D40)。M1 於 W1 的最後一天(10/4)完成,未落後。
>
> **v2.6:** M0、M0.5 於 9/26 提前完成,原排在 10/1～10/4 的 4 天變成 M1、M2 的餘裕。M0.5 已不需要 LiteLLM,10/1 不必再依冷卻期重新確認 LiteLLM 版本。

**檢查點(到期沒達成就照 8.4 砍):**

| 日期 | 必須完成 | 沒完成就 |
|---|---|---|
| ~~10/18(日)~~ | ~~M3~~ | ✅ 10/13 完成;M7 第一個時段由本人取消(D66) |
| ~~10/25(日)~~ | ~~M4 跑通~~ | ✅ 10/20 完成(v2.10) |
| 11/1(日) | M6 | M7 取消、改用備案;Console 縮成最小版 |
| 11/4(三) | 所有截圖(11.4)與各關的錄影 | 停止新功能,只補文件、截圖與錄影 |

> 技術文件不是最後一週才寫:每關收尾(8.3)就補進決策書,最後三天只做定稿與錄影。

---

# PART 9 — 決議速查表

| 議題 | 決議 | 理由章節 |
|---|---|---|
| AI 模型存取 | OpenAI API(官方 SDK + 薄介面函式);Bedrock 已退場(v2.7) | 3.4、D23、D24、D33 |
| 模型 | 便宜 `gpt-6-luna`(思考 `none`)、強 `gpt-6-sol`(思考 `low`) | 3.4、D28 |
| 呼叫方式 | Chat Completions;金鑰權限關閉 Responses | 3.4、4.5、D29 |
| OpenAI 驗證方式 | 雲端:工作負載身分聯盟(任務角色 → STS 5 分鐘證明 → OpenAI 存取權杖),SSM 不放金鑰;OpenAI 端 `gateway-wif` 只開 Chat completions、對應 `gateway-task-role`。本機:金鑰。`OPENAI_AUTH` 一定要明講(v2.10) | 3.4、4.5、D71、D72 |
| SDK 重試與逾時 | 一律不重試;逾時 60 秒;ALB 閒置 120 秒(v2.10) | 3.4、D70 |
| OpenAI 端防線 | 儲值 $5 不自動加值、Project 硬上限 $2、模型白名單、金鑰只開 Chat completions、服務帳號 30 天到期 | 4.5 |
| 區域 | ap-northeast-1 | 3.4 |
| 同步運算 | ECS Fargate | 7.3 |
| 非同步運算 | AWS Lambda | 7.3 |
| 佇列 | SQS Standard + DLQ | 7.4 |
| 計費事件順序 | 先確認進 SQS,再回應使用者 | 2.2、D31 |
| 資料庫 | DynamoDB(四張表);本機用 DynamoDB Local。v2.10:雲端先建三張(`usage` 留 M5)、隨需計費、刪除保護、PITR;`DYNAMODB_TARGET` 指定連哪裡;三個讀取強一致 | 3.2、7.5、D47、D74、D75、D82 |
| 額度放哪 | 使用者層級的固定一筆;已用量每月一筆(v2.8) | 3.2、D50 |
| 金額 | micro-USD 整數,無條件進位 | 3.2、D1、D30 |
| 單價 | 放 repo 設定檔;沒有單價的模型拒絕呼叫 | D30 |
| 對外入口 | ALB(保留)。v2.10:HTTP 80 只放行本人公開 IP、閒置 120 秒、健康檢查 `/health` | 4.4、D70、D81 |
| NAT Gateway | 使用,單 AZ(1a);受控出口 | 7.1、D13、D25 |
| 出口管控 | DNS 防火牆放行清單 + 安全群組只開 443。v2.10 實測:9 個網域、ALERT 一小時 → BLOCK(`NODATA`),清單外被擋並留查詢日誌(S08) | 3.5、4.1、D25、D89 |
| VPC Endpoint | 只有 Gateway × 2(S3、DynamoDB,皆加 Endpoint Policy);不用 Interface。v2.10:S3 只准 `GetObject` 映像層 bucket;DynamoDB 只准 `GetItem`/`PutItem`/`UpdateItem` 三張表(S10) | 3.5、D16、D26 |
| IaC | Terraform(S3 遠端 State + **S3 鎖檔**,v2.10 不用 DynamoDB 鎖);**兩層**:長期層平常不拆、每日層測完就拆;Terraform 1.16.5、AWS provider 6.68.0;M4 從本人電腦 apply | 5.1、D78～D80 |
| destroy | 手動觸發的 workflow,只拆每日層;GitHub OIDC(environment `destroy`、只准 `main`);刪除限 `Layer=daily`、長期層明文 Deny;C 段 51 秒拆光,D 段修正後待 M5 實測;拆完一定問 AWS 確認(v2.10) | 5.1、D84～D86 |
| 密鑰 | SSM 三個 SecureString(HMAC 金鑰、OpenAI 身分提供者 ID、服務帳號 ID),本人用 CLI 建;沒有 OpenAI 金鑰(v2.10) | 3.6、D14、D91 |
| 告警 | `audit_write_failed` 指標篩選 → 告警 → SNS Email,實測約 1 分鐘寄信(v2.10) | 3.6、D95 |
| CI/CD | GitHub Actions(Jenkins 僅本機示範) | 7.6 |
| 監控 | 本機 docker-compose 版 Prometheus + Grafana | 5.2 |
| 前端 | Demo Console 內嵌於 Gateway 容器(非獨立部署) | 7.7 |
| HTTPS | Demo 走 HTTP,Terraform 參數化 | 7.8 |
| 測試模型 | 便宜模型全程 | 6.4 |
| 預算上限 | AWS Budgets US$20 告警 + OpenAI 儲值與 Project 兩道硬上限 | 6.4、4.5 |
| 供應商 429 | 限流 → 降級;預算用完 → 不降級、回 503 | D32 |
| 設定檔 | `app/config.toml`(模型、思考量、輸出上限、單價、路由規則);啟動時讀進來就檢查(v2.9) | D54 |
| 路由規則 | 字數 ≥ 300 或含關鍵字 → 強模型;英文關鍵字字首比對;20 題省 25.3%(簡單題 65%) | D8、D55 |
| 降級 | 只認預算代碼、其餘當限流;強模型那次不讓 SDK 重試;`Retry-After` 1～120 秒 | D10、D59 |
| 輸出上限 | 兩顆都是 2,000;思考 token 算在輸出裡 | D58 |
| CI | pytest(含 `integration`)+ Trivy + CodeQL;Action 鎖 SHA;推送結案文件後改走分支加 PR。v2.10:加 `Config scan`(`trivy config`),**三個必要檢查** `Tests`、`Image scan`、`Config scan`;Trivy v0.74.0;`protect-main` 要求經過 PR(核准數 0) | D62、D67、D83、D97 |
| 刻意接受的掃描項目 | `#trivy:ignore:<ID>:exp:2026-12-31` 寫在該行上方附理由:AWS-0132、0104、0053、0054、0095(v2.10) | D83 |
| 版本更新 | Dependabot:GitHub Action 與基底映像每週、冷卻 7 天;Python 套件只收安全性更新(v2.10) | D73 |
| 漏洞回報 | `SECURITY.md`:GitHub Private vulnerability reporting | D67 |
| 資料模型、雜湊、路由規則等 | 22 項開工前定案 + v2.5 追加 5 項 + v2.6 追加 5 項 + v2.7 追加 8 項 + v2.8 追加 13 項 + v2.9 追加 14 項 + v2.10 追加 30 項 | PART 12 |
| 時程 | 10/1 開工、11/7 截止,四個檢查點;M0～M4 已完成(M4 於 10/20,檢查點 10/25,提前五天);每週約 25 小時、每週對帳一次 | 8.5、D66 |
| 實作路線 | 7 個里程碑,按「可獨立展示」切分;M4～M6 先做,M7 最後(v2.9) | 8.2、D66 |
| AI agent | 最後再做:小型 agent 當 Gateway 的客戶,用文字約定、不改 Gateway(M7);M6 完成後才開工 | 8.1、8.2、D42、D66 |
| 定位 | 雲端工程師,做 LLM 上線之後的治理層(v2.8) | 1.3、D41 |
| 知識檢索(RAG) | 不做;文件寫明正式環境會怎麼做 | 7.9 |
| 時間吃緊 | 不可砍:受控出口、pytest、CI/CD、技術文件 | 8.4 |
| 自建 vs 現成 | 專題自建最小 Gateway;正式環境建議先評估 LiteLLM 或 AgentCore Gateway | 10.4、D23 |
| LiteLLM 版本 | 冷卻期:上架滿 3 天、未撤回、無未修補 KEV(M0.5 已完成,僅供紀錄) | D27 |
| 配額故障處理 | fail-closed:讀不到或寫不進去就拒絕,回 503;驗證與額度共用一個訊息 | 10.3、D49、D51 |
| 身分驗證 | `Authorization: Bearer gw_…`;只存 SHA-256;失敗一律回相同的 401 | D3、D48 |
| 超額回應 | 429 + `Retry-After`(到台北時間下個月 1 號);被擋的請求寫稽核 | D46 |
| 個資 | 入口 regex 偵測 + 遮罩(信箱、信用卡號、手機、身分證字號),稽核記類別不記內容 | 4.2、M2、D43 |
| 額度扣減 | M2～M4 同步(事前加 0、事後原子累加,會超扣);M5 起非同步,允許小幅超用 | 7.10、D51 |
| 稽核存放 | M1～M3 本機檔案;**M4 起 `audit` 表**(條件寫入不覆蓋、Gateway 只有 `PutItem`;寫不進去印一行日誌、回應不變、告警);M5 移交 Worker | D36、D52、D77 |
| API 說明頁 | `/docs`、`/redoc`、`/openapi.json` 一律關閉(v2.10) | D68 |
| 資料庫故障的 503 | 不附 `Retry-After`(v2.10) | D69 |
| 停用 Key | `scripts/disable_key.py`:`--key` 停一把、`--user` 停一個人的全部;不存在就報錯、不新建(v2.10) | D76 |
| 呈現方式 | 10 分鐘期末報告(本人報告,含 Demo)+ 6 分鐘廠商影片(緯育推廣),分開做;Demo 播錄影、本人口述;錄影用 Windows 內建功能;外行版開場用情境故事;每關驗收當下錄影;21 項正式截圖(v2.9) | PART 11、D65 |
| 摘要順序 | 先遮罩、再截斷 | D6 |
| 上游失敗 | 稽核記一筆失敗、回 502、只記錯誤類別 | D37 |
| 套件冷卻期 | `uv` 的 `exclude-newer`,日期寫死在 repo | D35 |
| 容器 | 多階段、基底映像鎖 digest、非 root、`.dockerignore` 白名單、金鑰執行時才注入 | D39 |
| 開發機 | 金鑰、`.env` 與真實呼叫只在個人電腦(v2.9 修訂);登入 AWS 與 `plan`/`apply` 也只在個人電腦(v2.10) | D34 |
| 映像 | 從 `main` 建、標籤 = commit 編號、`IMMUTABLE`、`--provenance=false --sbom=false`;ECR 掃到沒有修補版的 HIGH 時評估後帶著上雲(v2.10) | D82、D92、D93 |
| 本機操作 | PowerShell 5 不用管線交密碼;Python 查雲端前後清 `AWS_*`;`"-chdir=$tf"` 加引號(v2.10) | D96 |
| 工作方式 | Python 自行撰寫;Dockerfile、Terraform 由骨架改寫並能逐行說明 | D40 |

---

# PART 10 — 對照拆解:LiteLLM、AWS 原生服務與本專案

> **v2.2 新增。** 起因是指導老師的回饋:外行人看不懂這個作品的意義;懂行的人則會覺得「用 LiteLLM 或雲端廠商自家的服務就好」。這一段要證明兩件事:我拆解過現成方案的設計,也清楚企業 AI 監管的每個環節,而且每個環節都有實作截圖(PART 11)。
>
> 資料查證日期:2026-09-21;LiteLLM 實測 2026-09-25～26(v1.102.0)。雲端服務更新很快,Demo 前一週要再確認一次。

## 10.1 先認識現成方案

**生活比喻:** 想開一間有中央廚房的連鎖店,有三條路:加盟現成品牌(LiteLLM)、租百貨公司美食街的攤位(AWS 全託管服務)、自己從一間小店做起(本專案)。

### LiteLLM

開源的 AI 閘道,用一個統一介面串接上百家模型供應商。以 Proxy 模式部署時由三個零件組成:

| 零件 | 負責 | 比喻 |
|---|---|---|
| Proxy 伺服器 | 驗證虛擬金鑰、路由、呼叫模型 | 櫃檯 |
| PostgreSQL | 虛擬金鑰、團隊、預算、花費紀錄 | 帳本 |
| Redis | 多台 Proxy 共用的限流計數、快取 | 各分店共用的白板 |

拆解重點:
- 預算功能**必須**接 PostgreSQL:M0.5 實測沒設資料庫時無法發虛擬金鑰,只剩管理金鑰(E19)。執行中資料庫斷線時,v1.102.0 預設回 503 拒絕(E18)。官方文件另記載「沒接資料庫時全域預算檢查會被跳過」,本案未實測
- 開多台 Proxy 卻沒有 Redis,每台各算各的,限額實際會變成兩倍
- 花費是**批次**寫回資料庫:M0.5 實測明細約 7～10 秒、金鑰累計約 12～14 秒後才寫入;**寫入前程式被強制終止,那筆帳永久遺失**(E25、E26)。跟本案把記帳丟給 SQS + Lambda 是同一個非同步思路,差別在帳放記憶體還是佇列
- 預算靠價格表算錢:v1.102.0 內建價格表**沒有** `gpt-6-luna`、`gpt-6-sol`,花費記為 0,預算安靜失效;要手動在模型設定補單價(E23、E24)
- 記憶體:M0.5 實測 v1.102.0 待機 **584 MiB**(有資料庫)/ 473.5 MiB(無資料庫)、輕度負載 574～578 MiB,本案 Fargate 規格 0.5 GB = 512 MiB(E16、E19、E27)。第三方部署範本記載約需 0.9 GB,可能含較多 worker,未驗證。**對照(v2.8):** 本案 Gateway 以同一個指令量到 M1 映像 56.08 MiB、M2 映像 62.06 MiB(E76、E92)。兩者功能不對等,這個數字只說明「只需要一家供應商加上額度與稽核時,最小規格就夠用」;而且只量待機,不含處理請求時才建立的資料庫連線

### AWS 官方參考架構

AWS 的「Guidance for Multi-Provider Generative AI Gateway」就是把 LiteLLM 部署在 ECS/EKS 上,前面接 WAF 與 ALB,後面接 RDS 與 ElastiCache。

> **本案的骨架(ALB → 私有子網的 Fargate)與官方參考架構相同。** 差別是本案用 DynamoDB 取代 RDS + ElastiCache,並在 NAT 出口加上 DNS 防火牆放行清單(v2.5)。

### Amazon Bedrock AgentCore Gateway

AWS 全託管的 AI 流量入口。2026 年 8 月起可依使用者限制請求數、token 數與連線時間,限制單位是每秒或每分鐘。

### Bedrock 與帳務原生功能

| 功能 | 能做什麼 | 限制 |
|---|---|---|
| IAM | 誰能呼叫哪個模型 | 管得到「人」,管不到「用量」 |
| Application Inference Profile + 成本分配標籤 | 在帳單上依部門/專案拆帳 | 事後看帳 |
| AWS Budgets | 超過預算寄信,可觸發動作 | 資料一天最多更新三次,間隔約 8～12 小時,擋不住「一個晚上燒掉」 |
| Model Invocation Logging | 記錄每次呼叫的輸入與輸出 | 存完整內容,與本案「稽核不存原文」衝突 |
| Bedrock Guardrails | 偵測/遮罩個資、擋不當內容 | 按處理的文字量另外計費 |
| Intelligent Prompt Routing | 在同一家族的模型間自動選 | 只限同家族 |

## 10.2 企業 AI 監管的十一個環節

| # | 環節 | 白話 | LiteLLM | AWS 原生 | 本專案 | 截圖 |
|---|---|---|---|---|---|---|
| 1 | 入口與身分 | 門禁卡 | 虛擬金鑰(存 PostgreSQL;沒資料庫就無法發,E19) | IAM;AgentCore 支援 OAuth / IAM 身分 | API Key(只存雜湊,失敗一律回相同的 401,✅ M2)+ ALB 唯一入口(只放行本人 IP)+ IAM 最小權限(✅ M4;雲端呼叫 OpenAI 用工作負載身分聯盟) | S01 ✅、S11 ✅ |
| 2 | 月額度 | 手機吃到飽上限 | key / team / user 預算,需 PostgreSQL;資料庫斷線預設 503(E18);**價格表沒有的模型不會扣預算(E23)** | Budgets(事後告警) | `quotas` 表 + fail-closed(✅ M2;額度在使用者層級,事前加 0、事後原子累加);沒有單價的模型拒絕呼叫 | S02 ✅、S03 ✅ |
| 3 | 限速 | 高速公路匝道儀控 | RPM / TPM,多台需 Redis | AgentCore Gateway 每秒/每分鐘限流 | 不做,正式環境用 WAF rate-based rule(7.9) | — |
| 4 | 智慧路由 | 買飲料不叫貨車 | Router;另有依複雜度選模型的 Auto Router(官網標示為加購) | Intelligent Prompt Routing(同家族) | 規則式複雜度判斷(✅ M3;20 題測試集省 25.3%,送對 18 題) | S05 ✅ |
| 5 | 備援 | 主廚請假有副廚 | fallback、重試、冷卻 | 跨區推論設定檔(東京新一代 Claude 用 `jp.`,見 E6) | 強模型被限流時降級到便宜模型一次;預算用完不降級(✅ M3) | S07 ✅(模擬) |
| 6 | 計費與歸屬 | 每戶一個水表 | 花費批次寫回 PostgreSQL(明細 7～10 秒、累計 12～14 秒;寫入前當機會掉帳,E25、E26) | Inference Profile + 成本分配標籤 | 設定檔單價、呼叫前查價(✅ M3)+ `usage` 表 + 先進 SQS 再回應 + Lambda 非同步 | S06 ✅、S12、S13 |
| 7 | 稽核 | 監視器只拍誰進出,不拍帶了什麼 | 花費紀錄(失敗請求也記,E23)、callback 接外部平台 | CloudTrail + Invocation Logging(完整內容) | `audit` 表只存 hash / 摘要 + 個資事件(✅ M4 搬表、雲端寫入已實測;寫不進去印一行日誌並告警) | S14 |
| 8 | 內容防護 | 郵局的違禁品檢查 | 可整合多種 guardrail | Bedrock Guardrails | regex 偵測 + 遮罩,四類(✅ M2;正式環境換 Guardrails) | S04 ✅ |
| 9 | 觀測 | 汽車儀表板 | callback 接外部觀測平台 | CloudWatch | `/metrics` + Prometheus / Grafana | S15 |
| 10 | 網路邊界 | 大門口的總機只轉接名單上的號碼 | 不處理(部署者的責任);官方範例預設對外開埠(E13) | VPC Endpoint / PrivateLink、DNS 防火牆、Network Firewall | 受控出口:NAT + DNS 放行清單 + 443 + Endpoint Policy(✅ M4:9 個網域、ALERT → BLOCK 實測,清單外被擋並留查詢日誌;Fargate 沒有公開 IP) | S08 ✅、S09 ✅、S10 ✅ |
| 11 | 供應鏈與部署 | 食材溯源 | 映像 cosign 簽章、重建後的 CI/CD 流程 | ECR 映像掃描 | Trivy(映像 + IaC 的 `Config scan`,✅ M4)+ CodeQL + OIDC(destroy workflow ✅ M4;CD 在 M6)+ 釘版本 + Dependabot(CI ✅ M3);ECR `scan_on_push` | S16、S17 |

> **看這張表的重點:** 第 1～9 環節現成方案都有,本案做的是最小版本,目的是看懂;第 10～11 環節是「部署者的責任」,現成工具不會幫你做,這正是雲端工程師與資安背景的價值所在。

## 10.3 從 LiteLLM 學到、直接放進設計的事(v2.5.1 依 M0.5 實測改寫,v2.6 補第 10～13 點)

| # | 在 LiteLLM 看到的 | 來源 | 本案怎麼做 |
|---|---|---|---|
| 1 | **資料庫斷線:** v1.102.0 預設回 503 拒絕,2 分鐘後仍拒絕,恢復後不需重啟即自動回復。**沒設資料庫:** 無法發虛擬金鑰,只剩管理金鑰,且啟動時沒有任何警告 | 實測 E18、E19 | 配額表讀不到一律拒絕,回 503(M2),與 LiteLLM 預設相同。fail-closed 的代價是可用性:資料庫掛 = 服務停擺,所以資料庫本身要高可用。DynamoDB 天生跨多個 AZ,RDS 要另付 Multi-AZ。**v2.8(M2 實作,E90、E92):** 資料庫連不上時最先出錯的是驗證,所以驗證與額度共用 `503 Service temporarily unavailable`;boto3 預設要 48.1 秒才報錯,改為 2 秒逾時、最多 2 次後是 6.7 秒;S03 實測停掉資料庫後有額度的人也不放行 |
| 2 | 多台 Proxy 要靠 Redis 共享計數,否則限額加倍 | 官方文件 | 用 DynamoDB 原子累加,多個容器同時寫也不會互相覆蓋,不需另開 Redis(7.10) |
| 3 | 2026/3/24 PyPI 上的 litellm 1.82.7、1.82.8 被植入竊取憑證的惡意程式,官方判斷起因是 CI 裡使用的 Trivy 遭入侵;官方 Docker 映像因鎖定依賴版本而未受影響 | 官方公告 | 本案 CI 也用 Trivy:所有 Action 釘 commit SHA、依賴用含 hash 的 lock 檔、映像鎖定版本(v2.9:M3 已實作,Trivy 用 2026/3 事件後官方公告的安全版本 v0.69.3,E104)。M0.5 自己也照做:冷卻期選版、用 digest 驗簽(E11)。**v2.10(E108、E110、E118、E121):** Trivy 升到 v0.74.0、trivy-action v0.36.0(兩個掃描都明寫版本);Dependabot 管 Action 與基底映像(每週、冷卻 7 天);destroy workflow 不用第三方 Action,Terraform 自己下載、比對寫死的 SHA256;`protect-main` 實測:沒跑過 CI 的 commit 直接推 `main` 被擋(GH013),另加「一定要經過 PR」 |
| 4 | 2026 年也公布過花費紀錄意外記到機密 header、Proxy SQL injection、驗證繞過等問題 | 官方公告 | 稽核只存 hash 與摘要,不記 header 與 API Key。閘道握有所有模型的鑰匙,是高價值目標;不論自建或採用,都要有修補與掃描流程 |
| 5 | **簽章驗證的缺口:** 映像驗過簽,但啟動時會從 GitHub `main` 分支下載一份沒驗證、沒鎖版本的價格表,而預算就是靠它算錢。斷網時重試 3 次、多卡約 10 秒後改用內建備份 | 實測 E15 | 單價放在 repo 的設定檔,價格變更 = 經過審查的版本變更。M4 用 DNS 防火牆查詢日誌確認 Gateway 沒有意料外的對外連線。**v2.10(E124):** ALERT 約一小時的查詢日誌裡,容器查過的網域剛好是放行清單 9 個,沒有任何一筆落到清單外;只觀察了啟動與聊天這一種流量 |
| 6 | 每次啟動自動改資料表結構(171 筆更新 + 差異修補),資料庫帳號必須有改結構的高權限;多容器輪流更新時可能 schema thrashing | 實測 E14 | DynamoDB 沒有資料表結構更新,Gateway 的 IAM 角色只給讀寫權限 |
| 7 | 預算檢查排在模型檢查之前,超額請求碰不到供應商;預算 0 被正確當成嚴格上限 | 實測 E17 | 同樣順序:驗身分 → 查配額 → 路由;M2 測試加入「額度 0」的邊界值(v2.8:已用 ≥ 額度就擋;查不到額度當成 0,E88、E91) |
| 8 | 金鑰以未加鹽 SHA-256 存放(假金鑰錯誤訊息回傳的雜湊經本機驗算相符) | 實測 E18 | `api_keys` 同樣只存 SHA-256,業界實作佐證本案設計(v2.8:種子腳本有一個測試掃整張表,確認找不到 Key 本身,E91) |
| 9 | 超額回 429(type `budget_exceeded`);但 429 的原意是「稍後再試」,許多客戶端 SDK 會自動重試。OpenAI 的 Project 預算用完也回 429(`project_spend_limit_exceeded`) | 實測 E17、E21 | **v2.8 定案(D46,E88、E92):** 超額回 429、固定字串 `Monthly quota exceeded`、附 `Retry-After`(到台北時間下個月 1 號 00:00 的秒數)。429 會讓客戶端自動重試,但額度檢查排在呼叫模型之前,重試碰不到 OpenAI,不會多花錢。客戶端 SDK 遇到長達數週的 `Retry-After` 會怎麼做還沒有觀察(12.5)。M3 呼叫供應商時,兩種 429 分開處理(D32) |
| 10 | **價格表缺新模型 → 預算安靜失效(v2.6):** 為了安全改用內建價格表(第 5 點)後,v1.102.0 收錄了旗艦 `gpt-6-astra` 與上一代 GPT-5.6,卻沒有平價的 `gpt-6-luna`、`gpt-6-sol`。呼叫成功、token 有記,花費卻是 0;預算 $0.01 的金鑰可以無限呼叫,沒有任何錯誤或警告 | 實測 E23 | 驗簽章、鎖版本還不夠,**價格資料也是治理的一部分**。設定檔沒有單價的模型一律拒絕呼叫(D30),「不知道多少錢」不能當成「不用錢」 |
| 11 | **寫帳前當機 → 永久掉帳(v2.6):** 花費先放記憶體,約 7～14 秒後批次寫入;回應後 0.8 秒被強制終止,明細與累計都沒寫入,重啟後也沒補回 | 實測 E25、E26 | 計費事件放 SQS,而且**先確認進佇列再回應**(D31)。這個實驗也照出本案 v2.5 流程(回應與送事件平行)有同樣的缺口 |
| 12 | **模型設定以 `LITELLM_SALT_KEY` 加密存放(v2.6):** 連模型名稱、「金鑰在環境變數裡」這種指路文字都加密,同一明文每次密文不同。但這把金鑰**不能輪替、不能遺失**,一換資料庫裡的設定就全部解不開;實驗當天就遇到它外洩後「換不換」的兩難 | 實測 E24、E28 | 本案 D4 的 HMAC 金鑰同類:換金鑰,舊的稽核雜湊就對不上。兩者都放 SSM SecureString、嚴格限制讀取權限;正式環境要規劃「金鑰版本」欄位,讓新舊金鑰可以並存 |
| 13 | **浮點數記帳(v2.6):** 13 × 1e-7 + 11 × 5e-7 應為 0.0000068,LiteLLM 與 PostgreSQL 都存成 6.799999999999999e-06 | 實測 E25 | D1 用 micro-USD 整數,v2.4 定案時的理由得到實證;D30 補上無條件進位 |

> **第 1 點的更正紀錄:** v2.2～v2.5 寫成「LiteLLM 沒接資料庫時預算會放行,所以本案的配額設計成讀不到就拒絕」,把「沒設資料庫」與「資料庫斷線」兩種情境混在一起。M0.5 實測後改寫:在斷線情境,LiteLLM 與本案做法相同;真正的差異在於它沒設資料庫時會「安靜地」失去預算能力,以及 fail-closed 對資料庫可用性的要求。
>
> 第 4 點不是說 LiteLLM 不安全。自建的程式一樣會有漏洞,差別在於:採用現成方案要追它的公告並即時更新;自建要自己做掃描與測試。兩條路都要有人顧。第 7、8 點則是 LiteLLM 做對、本案也採用的地方。
>
> 第 10、11 點的限制(誠實記錄):各只做一次;第 11 點未測正常關機(`stop`)與 Redis 緩衝的情況。第 10 點是「關掉線上價格表」這個安全選擇的代價,開著線上價格表可能就有這兩顆模型,但那就回到第 5 點的風險。**兩個選項各有代價,所以本案自己管單價。**

## 10.4 為什麼自建,而不直接用?

| 選項 | 做法 | 適合誰 | 本專題為什麼不採用 |
|---|---|---|---|
| A. LiteLLM 自架 | 官方映像 + PostgreSQL + Redis,部署在 ECS(即 AWS 官方參考架構) | 要接多家模型、需要現成管理後台的企業 | 最大價值是同時接多家供應商,本案只接一家;預算功能需常駐 PostgreSQL(本帳號 RDS 免費層已過期);記憶體 574～584 MiB 已超過本案 512 MiB,需升至 1 GB(E16、E27,成本只多約 18%);官方範例預設值需要逐項強化(E13) |
| B. AgentCore Gateway | AWS 全託管,依使用者限流 | 已在 AWS 上跑 agent 的團隊 | 限流單位是每秒/每分鐘,屬於「限速」;8 月公告沒有提到每人月額度與部門成本報表;全託管看不到內部,無法當作拆解學習的對象 |
| C. Bedrock 原生功能拼裝 | IAM + Inference Profile 標籤 + Budgets + Invocation Logging + Guardrails | 小團隊,只需要事後看帳 | Budgets 只能事後告警、擋不住即時超用;Invocation Logging 存完整內容,與稽核設計衝突 |
| **D. 自建最小 Gateway(採用)** | FastAPI + DynamoDB + SQS / Lambda | 學習與展示每個環節 | — |

**結論:**
- **正式環境:** 我會先評估 A 或 B,不建議從零自建。
- **這個專題選 D,理由三個:**
  1. **用不到最大價值:** 本案只接一家供應商,「同時接多家」用不到。(v2.5 更正:v2.4 另寫「要用就得開對外連線」,換成 OpenAI 後本案自己也要對外連線,此理由刪除。LiteLLM 原生支援 OpenAI,所以這題的答案要靠理由 2、3 與 M0.5 的實測撐住)
  2. **成本:** A 必須常駐資料庫,這是主要成本,違背 6.1「時鐘只在工作時轉」;若要配合 fail-closed 做高可用,RDS 還要另付 Multi-AZ。運算規格升到 1 GB 只多約 18%,不是關鍵(v2.5.1 更正:v2.5 以前把「記憶體兩倍」寫得像主要成本,E16 實算後修正)
  3. **學習目的:** 自己做出每個環節的最小版本,才看得懂現成工具的設定、限制與失敗模式;10.3 的實測發現(第 1、5～13 點)就是證據。其中第 11 點還反過來照出本案自己設計的缺口(D31)
- **可替換性:** 本案的 Terraform、網路、CI/CD 與 AWS 官方參考架構同一骨架。企業若改用 LiteLLM,換掉容器映像並補上資料庫,其餘可以沿用。**若採用 LiteLLM,要自己補上:模型單價的設定管理(10.3 第 10 點)、記帳不掉的機制(第 11 點)、SALT_KEY 的保管(第 12 點)。**

**生活比喻:** 我不是要取代市售的輪子,是拆一個輪子,看懂輪軸、軸承、胎壓各自在做什麼。正式上路我會買輪子,但我知道怎麼檢查它、它會在哪裡壞。

## 10.5 面試講法

> 「我評估過 LiteLLM、AgentCore Gateway 和 Bedrock 原生功能。正式環境我會先選現成的;這個專題我刻意做最小版本,因為我要看懂每個環節。動手前我先把 LiteLLM 在本機拆解:驗證映像簽章之後,我發現它啟動時還會從 GitHub 下載一份沒驗證的價格表,而預算就是靠這份表算錢的。我關掉它改用內建價格表,結果發現內建表裡沒有我要用的平價新模型,呼叫照樣成功,花費卻記成 0,預算就這樣安靜地失效,沒有任何錯誤訊息。所以我的 Gateway 遇到沒有單價的模型會直接拒絕。
>
> 我也實測了它的記帳:它是先回答、十幾秒後才批次寫帳,我在這段空窗把它強制關掉,那筆帳就永久不見了。這個實驗同時讓我發現,我自己原本的流程圖把『回答』和『送出計費事件』畫成平行,一樣有這個缺口,所以我改成先確認事件進了 SQS 才回答。
>
> 另外,這些現成工具都不處理網路出口,連官方範例都預設把資料庫埠開在外面,所以我把重點放在受控出口:只有一個出口,而且只放行名單上的網域。換成 OpenAI 之後,我在 OpenAI 端也做了跟 AWS 一樣的最小權限、預算硬上限和短期金鑰。」

---

# PART 11 — 呈現策略與截圖清單

> **v2.2 新增。** 指導老師的評分重點是「完整性」與「對外人的解釋」。同一個作品,要準備兩種講法。

## 11.1 兩層呈現

| | 外行版 | 內行版 |
|---|---|---|
| 對象 | 非技術評審、HR、部門主管 | 技術面試官、指導老師 |
| 時間 | 3 分鐘 | 10～15 分鐘 |
| 重點 | 解決什麼麻煩、看得到的效果、一個數字 | 環節拆解、取捨、截圖證據 |
| 素材 | Demo Console | PART 10 對照表 + 11.4 截圖 |

> **v2.9 定案(D65,E101、E102、E106):10 分鐘期末報告 + 6 分鐘廠商影片,分開做。** 指導老師 10/12:期末由本人報告,抓 10 分鐘(含 Demo,主軸是 Demo);給各家廠商的影片由報告摘要成 6 分鐘(含 Demo),緯育拿去推廣。取代下面 v2.8 的「6 分鐘主影片 + 技術版」與 v2.7 的配置表;兩版的頁序與時間配給見 11.6。
>
> **v2.8 定案(D41,E79):兩支影片。** 指導老師 10/5 同意另附一支。主影片 6 分鐘(下表);技術版 10～15 分鐘,照 11.3 的順序講。兩支影片共用一份簡報當骨架與腳本(11.6)。
>
> **v2.7:結案簡報與錄影的時長(9/30 得知上限約 6 分鐘,待與指導老師確認能否延長)。** 主影片先照 6 分鐘設計;若可延長或可另附影片,內行版照原本的 10～15 分鐘另錄。
>
> | 時間 | 內容 | 來源 |
> |---|---|---|
> | 0:00～3:00 | 外行版(11.2):開場故事、一句話、三個畫面、一個數字、收尾 | Demo Console |
> | 3:00～4:00 | 我先拆了 LiteLLM,並因此修正自己的設計(先進佇列再回應) | 10.3 第 10、11 點 |
> | 4:00～5:30 | 挑兩個環節各講「現成方案怎麼做 → 我怎麼做 → 截圖」:網路邊界(受控出口)、稽核(只存雜湊與摘要) | S08、S14 |
> | 5:30～6:00 | 不做清單與升級路線、實際花費 | 7.9、S18 |

## 11.2 外行版:三分鐘腳本

| 時間 | 內容 |
|---|---|
| 0:00 | **開場故事:** 用 1.1 的情境,並說明這是情境(v2.9 本人定案,不用真實經驗) |
| 0:30 | **一句話:** 「公司共用 AI 就像整棟大樓共用一條水管,沒有分表。我做的是替每戶裝水表和限流閥。」 |
| 1:00 | **三個畫面:** ① 簡單問題自動選便宜模型 ② 額度用完被擋下,配額條變紅 ③ 身分證字號被自動遮罩 |
| 2:00 | **一個數字:** 「同一組 20 個問題,簡單題佔 65% 時,智慧路由比全部用高階模型省 25.3%;整個專題雲端只花了 NT$___。」(v2.9:比例一定要附;簡單題比例越高省越多) |
| 2:30 | **收尾:** 「員工照常用 AI,老闆看得懂帳單,資安查得到紀錄。」 |

## 11.3 內行版:講解順序

1. **我先拆解了 LiteLLM**(M0.5 的 S19、S20,以及 10.3 第 10、11 點的實測)
2. **十一個環節對照表**(10.2),指出第 10、11 環節是部署者的責任
3. **挑 3～4 個環節深入**,每個都講「現成方案怎麼做 → 我怎麼做 → 截圖 → 取捨」。建議挑:月額度(fail-closed、沒有單價就拒絕)、網路邊界(受控出口)、計費(先進佇列再回應、故障演練)、供應鏈(Trivy 攔截)
4. **為什麼自建**(10.4)
5. **不做清單與升級路線**(7.9)

## 11.4 截圖清單

| # | 環節 | 截圖內容 | 哪一關 | 檔名 |
|---|---|---|---|---|
| S01 | 入口與身分 | 錯誤的 API Key 回 401(✅ 10/9) | M2 | `s01-auth-401.png` |
| S02 | 月額度 | Console 配額條變紅、回 429(✅ 10/9 終端機畫面:已用量 609 → 818 → 1,039 → 429 與 `retry-after`;M6 用 Console 重拍) | M2(M6 用 Console 重拍) | `s02-quota-429.png` |
| S03 | 月額度 | 停掉 DynamoDB Local 後回 503,而非放行(✅ 10/9) | M2 | `s03-fail-closed-503.png` |
| S04 | 內容防護 | 假身分證字號被遮罩 + 稽核事件(✅ 10/9) | M2 | `s04-pii-masked.png` |
| S05 | 智慧路由 | 簡單題選便宜模型、複雜題選強模型(✅ 10/13) | M3 | `s05-routing.png` |
| S06 | 計費 | 單次成本與手算對照(1,438)、省下比例表(25.3%)(✅ 10/13;**v2.10:10/19 19:25 右下重截**,左半與手算沿用 10/13,右下換成 PR #14 之後重跑的 `routing_eval`:R2 標「採用」、R3 標「對照」) | M3 | `s06-cost-savings.png` |
| S07 | 備援 | 模擬限流後的降級紀錄(✅ 10/13,模擬:畫面印 `SIMULATION:`) | M3 | `s07-fallback.png` |
| S08 | 網路邊界 | 容器連 `api.openai.com` 成功、連清單外網域被擋 + DNS 查詢日誌的封鎖紀錄(v2.5 改)(**✅ 10/19:** 一次性任務印兩行 `EGRESS`:`api.openai.com` DNS 有回答、TCP 443 連得上;`example.com` DNS 查不到;查詢日誌 4 筆 `BLOCK`/`NOERROR`) | M4 | `s08-egress-control.png` |
| S09 | 網路邊界 | ECS Task 沒有 Public IP(**✅ 10/19:** 服務 `assignPublicIp = DISABLED`、正在跑的任務網卡 `PublicIp = None`、子網 `llm-gateway-private-a` 的 `AutoAssignPublicIp = False`) | M4 | `s09-no-public-ip.png` |
| S10 | 網路邊界 | Gateway Endpoint Policy(DynamoDB 限四張表、S3 限 ECR 映像層)+ DNS 防火牆規則(v2.5 改)(**✅ 10/19,`scripts/show_egress_controls.ps1`:** DynamoDB 走廊只准 `GetItem`/`PutItem`/`UpdateItem` 三張表;S3 走廊只准 `GetObject` 映像層 bucket;DNS 防火牆 100 `ALLOW`、200 `BLOCK`/`NODATA`;9 個網域,帳號 ID 換成 `<account-id>`) | M4 | `s10-endpoints.png` |
| S11 | 入口與身分 | IAM 政策只指定特定資源、沒有萬用字元(**✅ 10/19,`scripts/show_gateway_roles.ps1`:** 任務角色 4 條、執行角色 4 條;`Resource: *` 只有兩條,都是 AWS 規定不能指定資源的動作:`ecr:GetAuthorizationToken`、`sts:GetWebIdentityToken`,後者有 audience 與 300 秒兩個條件)。v2.10:拆成兩張 | M4 | `s11-part1-task-role.png`、`s11-part2-execution-role.png` |
| S12 | 計費 | 停用 Event Source Mapping 後,使用者仍拿到回應 | M5 | `s12-async-survive.png` |
| S13 | 計費 | DLQ 收到處理失敗的訊息 | M5 | `s13-dlq.png` |
| S14 | 稽核 | `audit` 表只有 hash / 摘要,沒有原文(M1 已用檔案版本先行驗證:`m1-first-real-call-audit.png`;v2.8:M2 稽核仍在檔案,S04 的畫面含稽核那一行;搬進資料表後於 M5 拍攝) | M5 | `s14-audit-hash.png` |
| S15 | 觀測 | Grafana 儀表板 | M6 | `s15-grafana.png` |
| S16 | 供應鏈 | Trivy 擋下有漏洞映像的失敗紀錄 + 修正後的通過紀錄(v2.9:M3 的 CI 第一次執行已實際發生,E104;M6 用分支重拍截圖) | M6 | `s16-trivy-block.png` |
| S17 | 供應鏈 | OIDC 設定,repo 內沒有長期金鑰 | M6 | `s17-oidc.png` |
| S18 | 成本控管 | Budgets 測試告警信 + 結案時 Cost Explorer 實際花費 | M0 / 結案 | `s18-cost.png` |
| S19 | 對照 | LiteLLM:cosign 驗證通過 + 虛擬金鑰超出預算被擋(✅ 9/25) | M0.5 | `s19-part1-cosign.png`、`s19-part2-budget-blocked.png` |
| S20 | 對照 | LiteLLM 記憶體用量(`docker stats`)(✅ 9/25) | M0.5 | `s20-litellm-memory.png` |
| S21 | 成本控管 / 身分 | OpenAI Project 模型白名單 + 硬性花費上限(✅ 9/26;實測擋下見 `m0-openai-model-allowlist-block.log`)(v2.6 新增) | M0 | `s21-part1-allowed-models.png`、`s21-part2-spend-hard-limit.png` |

> **v2.7:M1 的佐證截圖(不佔 S 編號,存 `docs/screenshots/`,檔名以 `m1-` 開頭)。** 主要四組:`m1-first-real-call-audit.png`(M1 驗收:回應、稽核紀錄、搜尋原文無結果)、`m1-docker-*.png`(容器驗證三張)、`m1-openai-key-*.png`(M1 金鑰的設定與權限三張)、`m1-force-push-blocked.png`(`main` 禁止強制推送)。其餘為環境建置與除錯過程,清單見證據紀錄 E29～E75。
>
> **v2.8:M0 的補充佐證(不佔 S 編號,E79)。** AWS Support 案件四張:`m0-support-case-1-list.png`、`-2-request.png`、`-3-chat.png`、`-4-reply.png`,對應 Bedrock 被帳號層級封鎖的經過(E3、E5)。
>
> **v2.8:M2 的錄影片段(不進 repo,E92)。** `m2-s01-auth-401.mp4`(32 秒)、`m2-s02-quota-429.mp4`(54 秒)、`m2-s03-fail-closed-503.mp4`(48 秒)、`m2-s04-pii-masked.mp4`(82 秒)。S02、S03、S04 也用在主影片。
>
> **v2.9:M3 的錄影片段(不進 repo,E105、E106)。** `m3-s05-routing.mp4`(44 秒)、`m3-s06-cost-savings.mp4`(44 秒)、`m3-s07-fallback.mp4`(59 秒);10/13 由 Claude 抽格檢查(每秒一格、共 366 格轉文字搜尋,含 M2 四支):沒有洩漏。錄影是 16:10,放進 16:9 要加黑邊或裁上下。
>
> **v2.10:M4 的佐證截圖(不佔 S 編號,檔名以 `m4-` 開頭,E120～E125)。**
>
> | 檔名 | 證明什麼 |
> |---|---|
> | `m4-oidc-check-claims-with-env.png`、`m4-oidc-check-assumed-role.png` | 掛 environment `destroy` 的工作,證明的 `sub` 是新格式,借到 destroy 角色 |
> | `m4-oidc-check-denied-without-env.png` | 沒掛 environment 的工作被 AWS 拒絕 |
> | `m4-oidc-check-branch-blocked.png` | 從別的分支觸發,在 GitHub 那層就被擋 |
> | `m4-oidc-env-branch-rule.png`、`m4-oidc-env-no-admin-bypass.png` | environment 只准 `main`、取消管理員略過 |
> | `m4-daily-resource-map-private.png`、`m4-daily-resource-map-public.png` | 私有子網只連兩條 Endpoint;「0 個私有子網路由至網際網路」 |
> | `m4-destroy-first-run.png` | `destroy #1`:51 秒拆光每日層骨架 |
> | `m4-destroy-role-simulator.png` | destroy 角色的權限模擬器 12 題全對(10/20 覆蓋 10 題版) |
> | `m4-alarm-email.png` | `audit_write_failed` 告警寄出的信(遮掉帳號 ID 與 ARN) |
>
> **v2.10:M4 的錄影(不進 repo,E124)。** `m4-s08-egress-control.mp4`:任務 `2cf4e901…`、兩行 `EGRESS`、4 筆 `BLOCK`;錄之前 `function prompt {"PS> "}`、把查詢包成函式、`cls`。S09～S11 只有截圖。10/19 19:00 本人決定:10 分鐘報告版不嵌錄影(11.6),錄影檔留給 6 分鐘影片版與 M6 的 Console Demo。
>
> **v2.10:S17 的進度。** OIDC 已在 M4 實作(destroy workflow),上面 `m4-oidc-*` 六張是佐證;S17 正式截圖仍照原計畫在 M6(CD 做好後)拍。
>
> **目前到位(v2.10):** 21 項中 15 項:S01～S11、S19～S21 完整,S18 只有前半(結案時補 Cost Explorer)。
>
> **目前到位(v2.9):** 21 項中 11 項:S01～S07、S19～S21 完整,S18 只有前半。

## 11.5 截圖規範

- **存放:** repo 的 `docs/screenshots/`,檔名照 11.4
- **遮蔽:** AWS 帳號 ID、API Key(含末 4 碼)、IP、ARN 中的帳號段;OpenAI 的 Project ID、金鑰 Tracking ID、建立者 user ID(v2.6);個人帳號名稱(含終端機提示字元與路徑中的使用者資料夾)、Email、帳號頭像(v2.7);**信用卡末四碼、案例編號、客服與本人姓名(v2.8,E79)**。文字日誌比照辦理。與本專題無關的內容(其他專案的容器、映像名稱)裁掉或不收錄。用灰色方塊,保留前綴讓人看得出是被截短的值。這是資安習慣,也避免作品公開後外洩
- **說明:** 每張截圖旁寫一句「這張證明什麼」
- **時機:** 每關驗證通過當下立刻拍。事後為了補截圖重建環境,既花時間也花錢(見 8.3)
- **`.env` 不入鏡(v2.6,E28):** 確認 `.env` 時只看行數、長度、前綴,不打開檔案;截終端機前確認沒有其他視窗疊在上面
- **驗證時不把金鑰印出來(v2.7,E71、E74):** `.env` 不在 VS Code 中開啟;寫入密鑰檔前先確認目前所在的資料夾;容器執行中不執行 `docker exec … env`、`docker inspect`(會顯示執行時注入的金鑰)
- **流程(v2.7):** 截圖與日誌收到後先改名、遮蔽,由本人再確認一次;repo 只放遮蔽版
- **確認檔案真的存在(v2.8,E79):** 紀錄裡寫了檔名不等於檔案存在(M0、M1 有三張被引用的截圖當時沒有存檔)。每次收到截圖,改名、遮蔽之後,要確認它出現在 `git status` 裡才算完成。舊圖也要在公開前重新檢查一次(10/5 重遮了 12 張露出使用者資料夾名稱的舊圖)
- **推送前(v2.9,E95):** 簡報開著時 PowerPoint 會產生 `~$` 開頭的鎖定檔(帶有 Office 使用者名稱),已列入 `.gitignore`;一律照檔名逐一 `git add`,不用 `git add .`
- **雲端的畫面(v2.10,E119、E120、E124、E125):** Terraform 的計畫輸出、ARN、ECR 網址都有完整帳號 ID,存日誌或截圖前要遮;S10、S11 與模擬器改用專用腳本(`show_egress_controls.ps1`、`show_gateway_roles.ps1`、`simulate_destroy_role.ps1`),只印要證明的欄位,帳號 ID 換成 `<account-id>`、不印 ARN;GitHub Actions 的 log 用 `::add-mask::` 遮帳號 ID;公開 IP 不印(`admin_cidr` 查到就存進變數);推送前 Claude 掃要推的文字檔,確認沒有 12 位數的帳號 ID
- **截圖傳遞(v2.10,E124):** 本人截圖貼給 Claude,Claude 裁掉空白、放進 `docs/screenshots/`、核對尺寸;同一個暫存檔名第二次傳會送出舊內容,要換檔名重傳
- **錄影(v2.8,E79、E92;v2.9 用 Windows 內建錄影功能):**
  - 錄之前:終端機輸入 `function prompt {"PS> "}`,提示字元就不顯示使用者資料夾;`cls` 清畫面、放大字級;確認沒有開著 `.env`
  - Gateway 的 API Key 用 `Read-Host` 收進變數,不出現在指令與畫面上;種子腳本印出的 Key 不截圖、不錄進畫面
  - 錄瀏覽器(AWS 主控台)時,框選範圍不包含最上面那一列(有帳號名稱與帳號 ID)
  - 一個驗收條件錄一段;先不錄跑一次,再錄;結果出來後停 2 秒再結束;不錄聲音,旁白最後另外錄
  - 檔名對應截圖編號(例如 `m2-s02-quota-429.mp4`);**影片檔不進 repo**(檔案大,repo 是公開的),另存並備份
  - 錄完自己從頭看一遍,確認沒有金鑰、帳號 ID、使用者名稱;M2 另以「每 2 秒抽一格畫面轉成文字再搜尋」做第二道檢查(短於 2 秒的畫面可能漏掉,不能取代人看)

## 11.6 簡報與旁白稿(v2.8 新增,E84;v2.9 改寫,E99、E102;v2.10 更新為 10 分鐘版 v3)

| 項目 | 定案(v2.9) | 為什麼 |
|---|---|---|
| 兩份簡報 | **10 分鐘報告版**(17 頁,`llm-gateway-slides-10min-v2.0.pptx`)與 **6 分鐘廠商影片版**(15 頁,`llm-gateway-slides-6min-v2.0.pptx`),各有一份旁白稿。**v2.10:10 分鐘版改為 v3(37 頁,`llm-gateway-slides-10min-v3.pptx`,10/19,本人定名 v3、取代原擬的 v2.1;頁碼待重排);6 分鐘版仍是 v2.0 的 15 頁,10 分鐘版定稿後再照它重整** | 用途不同:報告是本人現場講,影片給廠商看;取代 v2.8「一份簡報當兩支影片的骨架」。v3:指導老師 10/19 要「至少補新版」;10/12 的回饋(內文至少 16 pt、字不要多、進度標籤與給自己看的備註不要上台、多講個資與節費) |
| 結構 | 秉鴻老師的標題:一頁講完 → 想解決的問題 → 解決前後 → 解法提綱(三道關、放到 AWS 上)→ 技術實踐(節費、個資、額度、看不到的地方)→ 結語;要有 Agenda,每頁標題與 Agenda 一致 | 老師 10/12 的投影片建議 |
| 版面規則 | 一頁不超過 3 個重點(最多 5);字 14～16 pt 以上;標題用本人自己訂的;去 emoji;以圖為主,字幾乎用講的,畫面只放動畫、Demo 或圖。**v2.10(本人 10/19 定,v3):** 內文至少 16 pt;放不下就多張;每個技術實踐先一頁概念、再接驗收畫面;截圖的重點一律框起來(終端機畫面用細線、不留邊,只圈那一行,不蓋到上下的字;之後用動畫控制出現順序);每頁字少、留重點;「答案」一律寫「回答」;不寫「2 倍速」;進度標籤與給自己看的備註不上台;M5～M7 還沒做的只畫設計、留白給驗收畫面 | 老師 10/12 與本人的要求;降低「AI 感」 |
| 做法 | **本人先手作草圖與標題,Claude 再修**;至少一張圖完全自己畫;改完請第二個 AI 扮受眾看一次 | 老師提醒:用 AI 做的簡報會被認為沒掌握內容,面試要能自己講 |
| 技術細節 | 不上台;v1.2 的技術細節 20 頁留著當 Q&A 與面試備用 | 一頁 3 個重點放不下 |
| 動畫 | Claude 用程式逐格算圖做成 MP4,只用在本人實測內容的示意,數量精簡(建議 A1 額度條、A4 三道關、A7 省下比例、A9 掉帳過程;A8 個資遮罩已有樣片) | 生成式影片的字與數字無法保證正確 |
| 組裝 | 10 分鐘版在 PowerPoint 播放,錄影片段嵌入頁面;6 分鐘版用剪輯軟體上繁中字幕;剪輯工具到時再定。**v2.10(本人 10/19 19:00):10 分鐘版的六頁「驗收錄影」拿掉,截圖就夠;錄影檔留給 6 分鐘影片版與 M6 的 Console Demo** | — |
| 時間預算 | 10 分鐘版配給 9 分 07 秒(現場語速每分鐘 200 字),6 分鐘版 5 分 34 秒(每分鐘 220 字) | 留時間給臨場與轉場 |
| 數字 | 省 25.3% 一定附「20 題、簡單題佔 65%」。**v2.10(v3 第 17 頁):** 簡單題 80%、90% 的約 38%、約 57% 是用這 20 題的平均單題成本推算、而且假設每題都分對,標「推算・完全分流」,不能說成實測;第 16 頁「多省的 29%」照本人的話寫,嚴格說是 29 個百分點(54.5 − 25.3) | 比例不同,結果差很多 |
| 存放 | 簡報與旁白稿進 `docs/slides/`;影片檔不進 repo;產生簡報與動畫的程式在 claude.ai Project 的 `claude/slides-tools/` | 影片檔大,repo 是公開的 |

**限制(誠實記錄):** 兩版都還沒計時試講(10/18 前);v2.0 的標題與故事線是 Claude 擬的,本人的手作版還沒做;很多畫面仍是佔位(M4 網路、M5 雲端稽核、M6 Console 與 Grafana)。

**v2.10 的限制(簡報 v3):** 進度標籤已全部拿掉,缺的畫面改為留白(Console、Grafana、S08、S12、S13、M7);第 7 頁一句話後半「虛線是 M5～M7 還沒蓋的」與底下那行說明,M5～M7 蓋好後拿掉;旁白稿仍是 v2.0;第 17 頁的 80%、90% 是「完全分流」的線性推算,不是實測(算法見 `slides-changelog.md`)。

**v2.10:10 分鐘版 v3 的頁面安排(`docs/slides/slides-changelog.md`):**

| 頁 | 內容 |
|---|---|
| 1～6 | 封面、Agenda、一頁講完、想解決的問題、解決前後、三道關(不變) |
| 7 | 解法提綱｜系統架構(對齊 2.1;只留架構圖與一句「外面連不進來,出口只放行 OpenAI」) |
| 8 | 解法提綱｜一次呼叫發生什麼事(新頁,對應 2.2) |
| 9 | 三件事、兩層、一鍵 |
| 10～21 | 節費 ①～③(本人自訂標題「買瓶飲料,不用叫整台貨車幫你送來」「省更多很簡單,答對比較難」;第 15 頁右圖是 10/19 重截的 S06) |
| 22～24 | 個資 |
| 25～29 | 額度 |
| 30～32 | 看不到的地方 ①(LiteLLM 拆解、兩個安靜出錯) |
| 33～36 | 「大樓僅有一個門,門口有警衛」(本人自訂標題;DNS 防火牆機制)、雲端實測 ①②(私有、公有子網的資源地圖)、一鍵拆除(`destroy #1`:workflow 51 秒、拆除工作 44 秒) |
| 37～39 | CI 三關、沒有長期金鑰 ①②(OIDC) |
| 40～41 | M5 帳不會掉、M7 小型 agent(新頁,只有設計與驗收條件,留白) |
| 42～43 | 結語、謝謝 |

- 頁數:錄影六頁 10/19 19:00 移除後為 37 頁,上表是移除前的頁碼,**頁碼待重排**;內容衝突檢查:第 7、8、9、33、34～36、37～39、40～41 各講一件事
- **還留白、下一版補:** 第 10 頁 Demo Console(M6)、第 14 頁右半 Grafana(M6)、第 23 頁雲端稽核畫面(M5)、第 33 頁 S08(M4 已有,下一版加一頁驗收畫面)、第 37 頁 CI 綠勾截圖與 CD 實測(M6)、第 40 頁 S12、S13(M5)、第 41 頁 M7 驗收畫面;動畫的出現順序還沒設定
- **旁白稿:** v3 只交 pptx,`narration-*-v2.0.md` 還沒跟著改;下一次改講稿時版號跟著 v3
- 簡報裡嵌的錄影是加速、1600 px、無聲的壓縮版;影片檔不進 repo

---

# PART 12 — 開工前定案清單

> **v2.4 新增。** 開工前把「寫程式時一定會遇到、但文件還沒說清楚」的問題一次定案,避免做到一半才回頭改資料結構。每一項都寫「為什麼」,這些也是面試素材。

## 12.1 資料與稽核

| # | 項目 | 定案 | 為什麼 | 影響 |
|---|---|---|---|---|
| D1 | 額度單位 | **美元**,以 micro-USD 整數儲存(v2.6:無條件進位,見 D30) | 若用 token 計,路由到貴模型不會多扣額度,智慧路由就跟額度脫鉤;整數避免小數誤差(E25 實證) | M2 |
| D2 | `quotas` 主鍵 | `user_id` + `period`(`YYYY-MM`,台北時間)。**v2.8 修訂(D50):** 主鍵不變;`period` 另有一個固定值 `limit`,那一筆存額度。`period` 由 `period_of()` 算出(D44) | 換月自然產生新紀錄,不用寫重置排程。v2.8:這句話只對已用量成立;額度若也放在每月那一筆,換月時就要有人建新的一筆 | M2 |
| D3 | API Key 存放 | 新增 `api_keys` 表,只存 SHA-256 雜湊;原文只在建立時顯示一次。v2.8(D48、D53):Key 的格式是 `gw_` 加 `secrets.token_hex(32)`,共 67 個字元;表內有 `status` 欄位,值是 `active` 才放行 | 資料庫外洩也拿不到可用的 Key;API Key 是長亂數,一般雜湊就猜不出來。稽核的指紋用 HMAC(D4)、API Key 用一般雜湊,依據是被雜湊的東西好不好猜 | M2 |
| D4 | 稽核雜湊 | **HMAC-SHA256**,金鑰放 SSM SecureString | 短句的一般雜湊可以被字典攻擊猜回原文(例如把常見問句逐一算雜湊比對);HMAC 沒有金鑰就算不出來。v2.6 補:這把金鑰跟 LiteLLM 的 SALT_KEY 一樣「換了舊資料就對不上」,要嚴格限制讀取(10.3 第 12 點)。v2.7 補(E63、E67、E71、E74):本機用環境變數 `AUDIT_HMAC_KEY`,以 Python `secrets.token_hex(32)` 產生並直接寫入 `.env`,不顯示在畫面上;雜湊以**原文**計算(事後比對時拿的是原句),原文本身不落地;實測同一句話、同一把金鑰在本機與容器算出相同的雜湊。**v2.10(D91,E123):** 雲端用新的一把(`secrets.token_hex(32)` 當場產生、不顯示),本人用 CLI 存 SSM `/llm-gateway/audit-hmac-key`;與本機 `.env` 的不同把,所以本機與雲端的指紋不能互相比對 | M1 |
| D5 | 原文的活動範圍 | Gateway 算好 HMAC 與遮罩摘要,SQS 事件只帶中繼資料 | 佇列、Lambda、DynamoDB 都碰不到原文;原文只存在 Gateway 記憶體;送往模型供應商的是遮罩後的內容(v2.5) | M1、M5 |
| D6 | 摘要 | 遮罩後內容的前 50 字,不另外呼叫模型。**順序固定為先遮罩、再截斷**(v2.7,E34):程式寫成 `mask(text)[:50]` | 產生摘要若再呼叫模型,每次請求都多一筆費用。順序若反過來,一支手機號碼剛好被切在第 50 字,剩下的半截認不出來,就會漏進稽核紀錄。M1 的 `mask()` 是空殼,靠「測試資料不含個資」這個人為約束;M2 補上實作與邊界測試 | M1、M2 |
| D7 | 應用日誌 | 不記錄 prompt 與回應內容,只記 `request_id`、狀態、耗時。**v2.10(D77,E116):** 稽核寫不進去時印的那一行 JSON 以白名單挑欄位(`request_id`、`user_id`、`timestamp`、`status`、`cost_micro_usd`、`charged`,加 `event`、`error_type`),不含摘要與 HMAC;`user_id` 是內部帳號名,補收時要知道扣誰,所以日誌群組設保存 30 天與防刪 | CloudWatch Logs 也是資料外洩點 | M1 |

## 12.2 路由與備援

| # | 項目 | 定案 | 為什麼 | 影響 |
|---|---|---|---|---|
| D8 | 路由規則 v1 | 輸入 ≥ 300 字,或含關鍵字(分析、比較、評估、設計、架構、程式碼、除錯、code、debug)→ 強模型;其他 → 便宜模型。規則、模型 ID、單價、思考量都放設定檔(v2.5 由 Sonnet / Haiku 改為通用名稱;v2.6 定案 `gpt-6-sol` / `gpt-6-luna`)。**v2.9 修訂(D55):** 關鍵字改為「分析、請比較、優缺點、評估、設計、架構、程式碼、除錯、code、debug、design、architecture、trade-off、compare、analyze」;英文關鍵字字首比對;字數門檻維持 300 | 規則式好解釋、好測試,Demo 時說得出「為什麼選這個模型」 | M3 |
| D9 | 使用者能不能指定模型 | **不能** | 能指定的話,大家都會選最貴的,治理就失效 | M3 |
| D10 | 備援 | 強模型被供應商**限流** → 降級便宜模型一次並記錄;便宜模型也限流 → 回 503 並附 `Retry-After`。**供應商預算用完不降級(v2.6,D32)**。SDK 重試次數設小(OpenAI SDK 預設會自動重試),避免和降級邏輯疊加。v2.7(E70):SDK 預設重試 2 次、逾時 10 分鐘,M1 改為重試 1 次、逾時 30 秒。v2.8(E90):資料庫的連線同樣要自己設,見 D49(boto3 預設在連不上時要 48.1 秒才報錯)。**v2.9(D59):** 強模型那次不讓 SDK 重試、便宜模型保留 1 次;兩種 429 用預算代碼分辨;`Retry-After` 照抄 1～120 秒。**v2.10 修訂(D70):** 所有 OpenAI 呼叫都不讓 SDK 重試(`OPENAI_MAX_RETRIES = 0`,「重試 1 次」作廢),逾時 30 → 60 秒,ALB 閒置逾時 120 秒 | 不無限重試,避免重試本身變成燒錢迴圈。預設值是為了盡量成功,不是為了快點回報失敗;閘道要自己決定等多久 | M3 |
| D11 | Demo 帳號 | alice 每月 **US$0.001**(示範被擋;v2.6 由 US$0.01 下修)、bob 每月 US$1.00;用種子腳本建立 | 讓 429 在 Demo 時幾次呼叫內就出現。以 `gpt-6-luna` 一次約 $0.00028 計,US$0.01 要打約 36 次,US$0.001 約 4 次。v2.8 實測(E92):請模型寫一篇約 300 字的故事,一次約 210～230 micro-USD,alice 成功 5 次後、第 6 次被擋;種子腳本見 D53 | M2 |

## 12.3 雲端架構

| # | 項目 | 定案 | 為什麼 | 影響 |
|---|---|---|---|---|
| D12 | Lambda 放哪裡 | 放在私有子網(VPC 內) | 放在 VPC 外的 Lambda 可以直接連網際網路,會繞過 DNS 防火牆;放在 VPC 內才受同一套出口管控(v2.5 改寫理由) | M5 |
| D13 | AZ 配置 | 私有子網與 NAT 1 個 AZ;公有子網 2 個 AZ(v2.5)。**v2.10 實作(E121、E123):** 私有子網與 NAT 都在 1a;公有子網 1a、1c | NAT 按 AZ 計費;ALB 規定至少兩個 AZ | M4 |
| D14 | 密鑰注入 | SSM SecureString,啟動時注入;v2.5 改走 NAT,不再用 `ssm` Endpoint。**v2.10 修訂(D71、D91):SSM 只放 HMAC 金鑰與兩個 OpenAI ID(身分提供者、服務帳號),不放 OpenAI API Key;三個參數由本人用 CLI 建,Terraform 只寫名字;metrics token 在 M6** | metrics token、HMAC 金鑰(D4)、OpenAI API Key 都不該寫成明文環境變數;M4 前評估 OpenAI 工作負載身分聯盟,可行就不需要 OpenAI API Key(4.5)。v2.10:評估可行、已實作 | M4 |
| D15 | Fargate 規格 | 0.25 vCPU / 0.5 GB,desired count 1 | 最小規格即可應付 Demo 流量。v2.8:Gateway 待機記憶體實測 M1 映像 56.08 MiB、M2 映像 62.06 MiB,約為 512 MiB 的 12%(E76、E92);只量待機,有負載時的數字待 M4。**v2.10(E124):** 雲端兩小時(含聊天)ECS `MemoryUtilization` 最高約 14.8%(約 76 MiB);只有最高值,平均值沒有記到 | M4 |
| D16 | Endpoint Policy | DynamoDB 限本專案四張表;**S3 限 ECR 映像層 bucket**(v2.5 修訂)。**v2.10 實作(E121、E124):** DynamoDB 只准 `GetItem`、`PutItem`、`UpdateItem`,範圍限三張表(`app/` 只用這三種呼叫;`usage` M5 補);S3 只准 `s3:GetObject` `prod-ap-northeast-1-starport-layer-bucket/*`;兩條都只接私有路由表 | 免費、可截圖(S10)。v2.4 怕拉不到映像而不限制 S3;v2.5 改用 AWS 文件提供的寫法,封住「上傳到攻擊者自己的 S3」這條路。v2.10:ECS 1 分 8 秒穩定,證明這樣寫拉得到映像 | M4 |
| D17 | Region / 模型 | ap-northeast-1;模型供應商改 OpenAI(D24),模型見 D28。M0 曾查證 `apac.` 只涵蓋舊世代,新一代 Claude 需用 `jp.`(E6) | 延續 3.4 | M0 |

## 12.4 工具與流程

| # | 項目 | 定案 | 為什麼 | 影響 |
|---|---|---|---|---|
| D18 | Python | 3.12,Gateway 容器與 Lambda 同版本;套件管理用 `uv`(lock 檔含 hash)。v2.7:`uv` 以 winget 安裝(安裝前比對雜湊,E33);容器內以 `uv sync --frozen --no-dev` 照 lock 檔安裝,不裝測試工具(E74);套件冷卻期見 D35 | 本機、容器、Lambda 行為一致;含 hash 的 lock 檔是 10.3 的供應鏈防護 | M1 |
| D19 | 版本鎖定 | Terraform、AWS provider、GitHub Actions(commit SHA)、基底映像(digest)在開工時鎖定當下最新穩定版。v2.7(E74):Gateway 映像的基底為 `python:3.12-slim`(`sha256:dddfd7e0…`)與 `ghcr.io/astral-sh/uv:0.12.19`(`sha256:04d046b1…`),完整 digest 寫在 `Dockerfile`。**v2.9(E104):** 基底改為 `python:3.12-slim@sha256:a6e34c59…`(Trivy 掃出 `libpcre2-8-0` 的 HIGH,新映像已含修補、過冷卻期);做法:換指紋,不在 Dockerfile 用 `apt-get upgrade`。CI 的 Action 鎖 commit SHA(`checkout` v7.0.1、`setup-uv` v10.2.0、`trivy-action` v0.35.0)。**v2.10(E118、E121、E124):** Terraform **1.16.5**(`~> 1.16.5`;1.16.6 當時未過冷卻期)、AWS provider **6.68.0**(`= 6.68.0`;查發佈頁時看到 6.57.0 曾因嚴重 bug 被下架,佐證冷卻期)、兩層的 `.terraform.lock.hcl` 進 Git;trivy-action **v0.36.0**、Trivy **v0.74.0**(明寫);destroy workflow 的 Terraform 以寫死的 SHA256 驗證官方 zip;Dependabot 管 Action 與基底映像(D73)。映像推 ECR 前建置加 `--provenance=false --sbom=false`(D92) | 同一份程式碼一個月後重建,結果要一樣 | M1、M4、M6 |
| D20 | 部署觸發 | push 只跑 CI;CD(apply + 部署)與 destroy 都手動觸發。**v2.10(D79、D80、D84～D86):** destroy workflow 已在 M4 建好(手動觸發、只拆每日層、GitHub OIDC、environment `destroy` 只准 `main`);M4 的 `apply` 從本人電腦執行;CD 仍在 M6 | 若 push 就自動 apply,在沒工作的日子也會把環境開起來花錢,違背 6.1 | M4、M6 |
| D21 | GitHub repo | 公開;開啟 secret scanning、push protection、Dependabot;`main` 分支要求 CI 通過才能合併。v2.7(E44、E48、E50):以上安全功能已在第一次 push 之前開啟;commit 使用 GitHub noreply 信箱;規則集 `protect-main` 已禁止強制推送與刪除分支(實測被擋,GH013);「CI 通過才能合併」待 CI 建立後補上(12.5)。**v2.9(D67):** CI 已上線;M3 結案文件推送之後開「CI 通過才能合併」,改走分支加 PR;新增 `SECURITY.md`(回報方式:GitHub Private vulnerability reporting)。**v2.10(D97,E108、E118、E120):** 實測沒跑過 CI 的 commit 直接推 `main` 被擋(GH013,「2 of 2 required status checks」);`protect-main` 另加「Require a pull request before merging」(核准數 0)、Bypass list 為空;必要檢查加 `Config scan` 變成三個。已滿足條件的 PR,從終端機推它的 commit 等於合併它。Dependabot 改由 `.github/dependabot.yml` 管版本更新(D73);GitHub environment `destroy` 取消管理員略過(D84) | 當作品集要公開;這些功能免費,也擋住「不小心把金鑰推上去」 | M1 |
| D22 | Repo 結構 | 見下方。**v2.10 修訂:** 加 `infra/`(兩層)、`app/openai_auth.py`、`scripts/` 的 M4 工具、`tests/` 新檔、`.github/workflows/` 的 `destroy.yml` 與 `oidc-check.yml`、`.github/dependabot.yml`;圖已更新到 M4 結束(`main` = `bd849c1`) | 一個 repo 放全部,面試時一個連結就看得到全貌 | M1 |

```
llm-gateway/
├── app/                 Gateway(FastAPI)                         ✅ M1～M4
│   ├── main.py          入口:/health、/v1/chat;領用窗口(相依);
│   │                    說明頁關閉、SDK 不重試、逾時 60 秒、共用連線 ✅ M4
│   ├── audit.py         HMAC 雜湊、摘要、個資遮罩與類別;
│   │                    寫 audit 表、寫不進去印一行日誌             ✅ M2、M4
│   ├── auth.py          API Key:雜湊、取出 Bearer、查出使用者     ✅ M2
│   ├── db.py            DynamoDB 連線(DYNAMODB_TARGET)、表名、逾時與重試 ✅ M2、M4
│   ├── quota.py         切月、超額判斷、讀額度、扣額度             ✅ M2
│   ├── pricing.py       查模型設定、成本換算                       ✅ M2、M3
│   ├── config.py        讀設定檔並檢查;config.toml 是設定檔本身    ✅ M3
│   ├── router.py        選模型:字數、關鍵字(字首比對)             ✅ M3
│   ├── fallback.py      降級、兩種 429 的分辨、Retry-After         ✅ M3
│   ├── openai_auth.py   OPENAI_AUTH:金鑰或工作負載身分聯盟         ✅ M4
│   ├── providers/       openai_client.py(薄介面)
│   └── static/          Demo Console                             M6
├── worker/              Metering & Audit Worker(Lambda)          M5
├── infra/               Terraform(兩層,各有 .terraform.lock.hcl)  ✅ M4
│   ├── persistent/      長期層,平常不拆:state_bucket、ecr、dynamodb(三張表)、
│   │                    github_oidc(OIDC 提供者與 destroy 角色)、ecs_roles、
│   │                    logs(日誌群組、DNS 查詢日誌設定、指標篩選與告警)、
│   │                    alerts(SNS)、backend、providers、versions、outputs
│   └── daily/           每日層,測完就拆:network、security_groups、endpoints、
│                        dns_firewall、alb、ecs、backend、providers、versions、
│                        variables、outputs
├── tests/               pytest;fakes.py 為共用的假 OpenAI、假資料庫與
│                        寫暫存檔的稽核替身;conftest.py 提供考場的資料庫連線、
│                        開頭強制 OPENAI_AUTH=api_key               ✅ M1～M4
├── monitoring/          Prometheus / Grafana(docker-compose)      M6
├── scripts/             create_tables.py(建表)、seed.py(示範帳號)✅ M2;
│                        LiteLLM 對照實驗;
│                        probe_usage.py(真實用量探測)、routing_questions.toml
│                        (20 題)、run_routing_eval.py、routing_eval.py(比較規則)、
│                        ask_cheap.py、demo_fallback.py(S07 模擬)  ✅ M3;
│                        disable_key.py(停用 Key)、show_audit.py(查稽核)、
│                        probe_wif.py(身分聯盟探測)、egress_check.ps1 與
│                        egress_check.json(S08 一次性任務)、
│                        show_egress_controls.ps1(S10)、show_gateway_roles.ps1(S11)、
│                        simulate_destroy_role.ps1(權限模擬器)     ✅ M4
├── docs/
│   ├── decision-book/   各版決策書(本文件)
│   ├── evidence/        文字證據紀錄(每關一份,E 編號跨檔接續)
│   ├── logs/            實驗日誌
│   ├── milestones/      里程碑結案報告
│   ├── screenshots/     截圖
│   └── slides/          簡報與旁白稿、slides-changelog.md(影片檔不進 repo)✅ v2.8、v2.10
├── compose.yaml         本機的 DynamoDB Local(練習場、考場)+ gateway
│                        (profile gateway)                         ✅ M2、M4
├── Dockerfile           多階段建置(D39);不建可寫的資料夾          ✅ M1、M4
├── .dockerignore        白名單                                    ✅ M1
├── .env.example         設定檔範本(只有欄位名稱;DYNAMODB_TARGET、OPENAI_AUTH);
│                        .env 不進 Git                             ✅ M1、M4
├── pyproject.toml、uv.lock
├── SECURITY.md          漏洞回報方式                               ✅ M3
└── .github/
    ├── dependabot.yml   Action 與基底映像的版本更新                 ✅ M4
    └── workflows/       ci.yml(Tests、Image scan、Config scan)✅ M3、M4;
                         destroy.yml、oidc-check.yml ✅ M4;CD      M6
```

> **v2.7 與 v2.6 的差異(E42、M0 結案報告附錄):** 維持根目錄 `app/`,不採用 `uv init` 預設的 `src/` 打包結構(本專題部署成容器,不發佈套件);`docs/` 改為五個資料夾,證據紀錄與結案報告按類型分資料夾。
>
> **v2.8 的差異(E84～E91):** `app/` 依職責多四個檔(驗證、連線、額度、成本);建表與種子資料放 `scripts/`,不放 `app/`(不會進容器;Gateway 在雲端不該有建表的權限,10.3 第 6 點);新增 `compose.yaml` 與 `docs/slides/`。
>
> **v2.9 的差異(E95～E105):** `app/` 多設定檔、路由、降級三塊;`scripts/` 多測試集與驗收工具(需要金鑰的只在個人電腦執行,不進 CI);`tests/` 新增 15 個檔(`test_config`、`test_router`、`test_router_word_boundary`、`test_chat_routing`、`test_fallback`、`test_chat_fallback`、`test_chat_truncation`、`test_routing_eval`、`test_routing_rules`、`test_mask_speed`、`test_message_limit`、`test_ask_cheap`、`test_demo_fallback` 等);`docs/logs/` 多 `m3-step6-usage-probe.log`、`m3-step7-routing-run.json`;`.github/workflows/ci.yml`;`SECURITY.md`。
>
> **v2.10 的差異(E109～E125):** 新增 `infra/`,分 `persistent/`(長期層)與 `daily/`(每日層)兩個各自有帳本的 Terraform 根目錄(D79);`app/` 多 `openai_auth.py`,`audit.py` 改寫進 `audit` 表(`append_audit()` 搬到 `tests/fakes.py`,只剩測試在用);`scripts/` 多 M4 的工具(需要登入 AWS 的只在個人電腦執行;`.ps1` 只印要證明的欄位、不印帳號 ID);`tests/` 新增 `test_production_settings`、`test_consistent_reads`、`test_disable_key`、`test_audit_store`、`test_chat_audit_store`、`test_show_audit`、`test_openai_auth`,改寫 `test_db`(3 → 11 個);`.github/` 多 `dependabot.yml`、`workflows/destroy.yml`、`workflows/oidc-check.yml`;`docs/logs/` 多 `m4-wif-probe.log`;`docs/slides/` 多 `llm-gateway-slides-10min-v3.pptx`、`slides-changelog.md`;`docs/screenshots/` 多 S08～S11 與 11 張 `m4-` 佐證;`compose.yaml` 加 `gateway` 服務;`Dockerfile` 拿掉可寫的 `data` 資料夾;`.gitignore` 在第一次 apply 前加 `.terraform/`、`*.tfstate`、`*.tfstate.*`、`*.tfvars`、`crash.log`。

## 12.5 刻意留到里程碑才定的項目

這些不是沒想清楚,而是需要實際環境或資料才能定。

| 項目 | 何時定 | 怎麼定 |
|---|---|---|
| ~~Haiku、Sonnet 的實際模型 ID~~ | M0 ✅ | 已查證(E6);v2.5 改供應商後由下一列取代 |
| ~~OpenAI 便宜 / 強模型 ID 與單價~~ | ✅ 9/26 | `gpt-6-luna`、`gpt-6-sol`(E20,D28) |
| ~~OpenAI API 資料保留政策、最低儲值金額~~ | ✅ 9/26 | 已補進 4.5(E20) |
| ~~DNS 防火牆每個網域的月費~~ | ✅ 9/26 | 每月 $0.0005,已更新 6.2(E20) |
| ~~LiteLLM 觀察 4 與負載下記憶體~~ | ✅ 9/26 | 批次寫入(E25);574～578 MiB(E27) |
| ~~Fargate、ALB 的東京單價~~ | M0 ✅ | 已更新 6.2、6.3(E7、E8) |
| ~~DNS 放行清單的完整網域~~ | ✅ 10/19 | ALERT 約一小時,容器查過的剛好是 9 個網域,不用改清單;切 BLOCK 後照通(D89,E124) |
| ~~超額回應的狀態碼與重試語意~~ | ✅ 10/7 | 429、固定字串、附 `Retry-After`(D46,E88);10/9 實測並驗算(E92) |
| SQS 寫入失敗時的處理(v2.6) | M5 | 回答照給並記錯誤,或拒絕回答;取捨同 fail-closed(D31) |
| ~~OpenAI 工作負載身分聯盟(v2.6)~~ | ✅ 10/14、10/19 | 10/14 以本人的 IAM 使用者探測成功(`chat.completions` 收這種權杖);10/19 Fargate 上可用,雲端不放金鑰(D71,E113、E124) |
| 與供應商帳單對帳(v2.6) | M6 | 用 OpenAI Usage 核對 `usage` 表的呼叫數與金額;M0.5 已看到 LiteLLM 帳與實際呼叫對不上(E23、E26)。評估做成排程或只在 Demo 手動比對 |
| ~~路由門檻的數字(300 字、關鍵字清單)~~ | ✅ 10/13 | 20 題測試集:字數 300 不變,關鍵字改版、英文字首比對(D55) |
| M7 做不做 | 10/30、11/1 | v2.9:M4～M6 先做;第一個時段本人取消,剩兩個時段,條件見 8.2(D66) |
| ~~FastAPI 自動文件頁 `/docs`、`/openapi.json`(v2.7)~~ | ✅ 10/14 | 一律關閉(三個參數都是 `None`),`tests/test_production_settings.py` 釘住;容器裡 `/docs` 回 404(D68,E109、E114) |
| ~~`protect-main` 加上「CI 通過才能合併」(v2.7)~~ | ✅ M3 結案 | 推送結案文件後開,改走分支加 PR(D67) |
| ~~CodeQL 程式碼掃描(v2.7)~~ | ✅ 10/13 | 預設設定(Python、GitHub Actions);4 個 High:1 個修正、3 個附理由關閉(D62、D63) |
| ~~結案簡報與錄影的時長(v2.7)~~ | ✅ 10/5 | 兩支影片:6 分鐘主影片 + 技術版 10～15 分鐘(D41,E79) |
| ~~M1 金鑰到期後的接續(v2.7)~~ | ✅ 雲端 10/19 | 雲端改用工作負載身分聯盟,不需要金鑰;**本機仍要**,見下方新增的一列(E124) |
| ~~Gateway 記憶體量測(v2.7)~~ | ✅ 10/4、10/9 | M1 映像 56.08 MiB、M2 映像 62.06 MiB(E76、E92);有負載時的記憶體與延遲見下方新增的一列 |
| ~~外行版開場用真實經驗或情境~~ | ✅ 10/13 | 情境故事(本人,D65) |
| ~~沒有單價時的錯誤類型與對使用者的回應(v2.8)~~ | ✅ 10/10 | `ModelNotConfiguredError`;回 500、寫稽核、不呼叫模型(D56) |
| ~~輸出 token 是否已含思考 token 的實證(v2.8)~~ | ✅ 10/12 | 已含;成本函式不另加(D58) |
| 預扣:解決超扣與同時送出多個請求(v2.8) | M5 | v2.9:M3 不做,先加輸出上限讓一次最多超扣多少算得出來(D58)。v2.10:M4 也沒做,仍是同步扣減(7.10) |
| ~~CI 怎麼跑 `integration` 測試(v2.8)~~ | ✅ 10/13 | 用 repo 的 `compose.yaml` 起 `dynamodb-test`(D62) |
| ~~稽核搬進 `audit` 表;扣額度失敗的紀錄放哪裡、怎麼補收與告警;`pii_types` 的型別(v2.8)~~ | ✅ 10/15 | 寫進 `audit` 表(條件寫入);寫不進去印一行 JSON 日誌、回應不變;`pii_types` 存清單;M4 加告警(實測約 1 分鐘寄信)。補收仍是手動,見下方新增的一列(D77、D95,E116、E124) |
| ~~`compose.yaml` 加上 Gateway,驗證容器內的完整流程(v2.8)~~ | ✅ 10/14 | `gateway` 服務(profile `gateway`);容器裡驗 Key、扣額度、真實對話、寫稽核都通(E114、E116) |
| ~~`app/db.py` 怎麼表示連真的 AWS;DynamoDB 的計費模式;要不要強一致讀取(v2.8)~~ | ✅ 10/14 | `DYNAMODB_TARGET`;隨需;三個讀取強一致(D74、D75,E111);雲端連線 10/19 實測可用(E124) |
| ~~停用 Key 的指令(v2.8)~~ | ✅ 10/14 | `scripts/disable_key.py`:`--key` 停一把、`--user` 停一個人的全部(D76,E112) |
| 種子腳本重跑時舊 Key 的處理(v2.8) | M5～M6 | M4 沒有處理:重跑仍產生新 Key、舊的不失效;雲端 alice、bob 的 Key 雜湊還在 `api_keys` 表(E124)。可用 `disable_key.py --user` 先停舊的再重灌 |
| ~~每個請求新建資料庫連線、最多 5 次往返的延遲;有負載時的記憶體(v2.8)~~ | ✅ 10/19 | 從台灣量:`/health` 約 41 ms(第一次 113)、聊天 1.7～3.5 秒(多數時間在等 OpenAI)、記憶體最高約 14.8%;只量幾次,連線方式沒有改(E124) |
| ~~資料庫故障的 503 要不要附 `Retry-After`(v2.8)~~ | ✅ 10/14 | 不附,4 個測試釘住(D69,E109) |
| 客戶端 SDK 對很大的 `Retry-After` 的行為(v2.8) | M6 | M2 驗收用的是 `curl.exe`,沒有觀察到;做 Demo Console 時觀察(E88) |
| 簡報計時試講(v2.8) | 10/18 前 | 10 分鐘報告版至少計時試講一次(v2.9:PowerPoint 桌面版確認版面已於 10/12 完成) |
| ~~容器內讀得到 `app/config.toml`、對話流程完整(v2.9)~~ | ✅ 10/14 | `config.toml` 打包在映像裡;設定寫錯時容器載入就停(`ConfigError`),所以 ECS 要靠健康檢查與斷路器判斷(E114) |
| ~~SDK 的等待與 ALB 閒置逾時(v2.9)~~ | ✅ 10/15 | SDK 一律不重試、逾時 60 秒、ALB 閒置 120 秒(D70,E109、E115);上雲後只量了一般長度的聊天,長回答在 ALB 後面的最長等待沒有量 |
| 供應商預算用完的告警(v2.9) | M5～M6 | D32 寫「回 503 並告警」,M3 只有稽核的 `error_code`(E100);**v2.10:M4 沒有做**,M4 的告警只有 `audit_write_failed` |
| ~~Trivy 升級與 Action 的更新方式(v2.9)~~ | ✅ 10/14、10/16 | Dependabot 管 Action 與基底映像(D73);Trivy 本身在加 `trivy config` 時手動升到 v0.74.0(D83) |
| 路由規則重驗(v2.9) | M4 之後 | 用新題目或真實稽核紀錄;一併評估中英文字數的算法、字首比對的殘餘誤判、字數門檻 500(E103、E105) |
| 被截斷的回答要不要告知使用者(v2.9) | M6 之後 | 本人 10/14 確認維持只記稽核;有真實統計再看(D60) |
| ~~`routing_eval` 的 R2、R3 標籤分不出哪個是採用的(v2.10,簡報 v3)~~ | ✅ 10/19 | PR #14:標籤改成「R2 採用:現在的規則(300 字 + 關鍵字,10/13 定案)」「R3 對照:字數門檻放寬到 500」;重跑只讀 `docs/logs/m3-step7-routing-run.json`,不呼叫模型;S06 右下重截 |
| ~~CodeQL 預設設定的機器 10/19 起改指 Ubuntu 26(v2.10)~~ | ✅ 10/19 | `ci.yml`、`destroy.yml` 都鎖 `ubuntu-24.04`;10/19 之後第一個 PR(#15)CodeQL 正常(E117、E124) |
| 本機的 OpenAI 金鑰 `m1-gateway` 11/2 到期(v2.10) | 11/2 前 | 雲端不需要;本機開發與 11/2 之後的錄影仍要用,到期前在個人電腦換一把新的(規格同 E21) |
| 稽核寫不進去的補收(v2.10) | M5 | 目前看日誌、手動補扣;日誌只有中繼資料,還原不出完整紀錄;正式解法是 SQS(D77) |
| 映像的三個 HIGH(v2.10) | 每次建映像 | zlib CVE-2026-85091、glibc CVE-2026-5435、CVE-2026-19499:Debian 13 沒有修補版、卡在 Gateway 用不到的函式;看 ECR 掃描,出修補就換基底映像指紋(D93,E124) |
| 修正後的 destroy workflow 一鍵拆光(v2.10) | M5 開工時 | 下一次 apply 每日層後按 destroy;在那之前每次 destroy 完都直接問 AWS 確認(D85,E124、E125) |
| DNS 網域結尾加點後,假改動有沒有消失(v2.10) | M5 開工時 | 下一次 apply 每日層、切 BLOCK 時,plan 應只剩「其他全部」那條規則的動作一個改動(D89,E125) |
| Trivy 刻意接受的 5 項 12/31 到期(v2.10) | 12/31 前 | AWS-0132(State bucket 沒用自管 KMS)、AWS-0104(安全群組出口 `0.0.0.0/0`)、AWS-0053(ALB 對外)、AWS-0054(HTTP)、AWS-0095(SNS 沒加密);到期前逐項決定改掉或延長(D83) |
| Terraform 1.16.6(v2.10) | M5(下次動 Terraform 時) | 過冷卻期後一起升:兩層 `versions.tf`、`destroy.yml` 的版本與指紋;證據紀錄原訂 M4 內,M4 結束時尚未升(E122) |
| `.gitignore` 沒有擋 `*.tfplan`(v2.10) | M4 結案的 docs PR 或 M5 第一個 PR | 計畫檔含帳本內容;加一行 `*.tfplan`。E124 的證據紀錄原寫「被擋」是錯的,10/20 更正(E126 之後的待決) |
| 主路由表、預設網路 ACL(v2.10) | 不處理(記錄) | 預設安全群組已認領並清空;主路由表與預設網路 ACL 不認領,沒有名字與標籤,刪 VPC 時一起消失,不影響 destroy(D88,E122、E123) |
| `usage` 表(v2.10) | M5 | 雲端建表;Endpoint Policy 與 IAM 要補(D82,E118) |

## 12.6 v2.5 追加定案(2026-09-25)

| # | 項目 | 定案 | 為什麼 | 不選的選項 |
|---|---|---|---|---|
| D23 | 平台層 | 自建 Gateway;LiteLLM 只在 M0.5 當拆解對照;呼叫模型用官方 SDK,外面包一層薄介面。**v2.7 修訂(E30):** 薄介面簡化為一個檔案、一個函式;理由由「換供應商只改設定」改為「測試不花錢」與「OpenAI 的細節集中一處」。抽象層要有真的需求才做 | 展示 Python 與資安設計(個資遮罩、fail-closed、HMAC 稽核都要自己寫才看得到);成本最低;不用重寫 v2.4 | 部署 LiteLLM(作品辨識度低、需常駐資料庫與約兩倍記憶體);混合使用 LiteLLM SDK(把 2026/3 被植入惡意程式的套件拉進主程式) |
| D24 | 模型供應商 | OpenAI API | 業界通用格式;便宜與強模型價差大,省錢效果好展示。(v2.7:刪除「薄介面保留切回 Bedrock 的彈性」,見 D33) | Anthropic API(路由與原設計相同、改動最少,但無推翻原決定的強理由);繼續等 Bedrock(時程風險) |
| D25 | 出口管控 | NAT + DNS 防火牆放行清單 + 安全群組只開 443 | 幾乎零成本,可實證擋下清單外網域 | Network Firewall(50 小時約 +$17)、自架代理(多一台要顧的伺服器) |
| D26 | Interface Endpoint | 不保留;S3、DynamoDB 走免費 Gateway Endpoint 並加 Policy | D25 已接受直接用 IP 的殘餘風險,多付一倍只買到部分保護 | 保留 5 個(50 小時 ~$6.9) |
| D27 | LiteLLM 版本 | 冷卻期:上架滿 3 天、未撤回、無未修補 KEV;用 digest 鎖定並驗簽 | 不當第一批試用者;2026/3 的供應鏈事件就發生在新版本上架的幾小時內 | 追最新版(v1.102.1 於 9/23 發布,當時 0 天) |

## 12.7 v2.6 追加定案(2026-09-26)

| # | 項目 | 定案 | 為什麼 | 不選的選項 |
|---|---|---|---|---|
| D28 | 模型 | 便宜 `gpt-6-luna`(`reasoning_effort: none`)、強 `gpt-6-sol`(`reasoning_effort: low`);成本一律用回應的 `usage` 計算(含思考 token) | 比 v2.5 候選更新也更便宜;兩顆價差 20 倍,智慧路由效果好展示;推理模型的思考 token 以輸出計費,不設定會預設 `medium` 暗中燒錢(E20、E22) | GPT-5.6 Luna / Terra(較貴、上一代);`gpt-6-astra`(輸出 $50 / 百萬,預算撐不住) |
| D29 | 呼叫方式 | Chat Completions;金鑰權限只開 Chat completions,關閉 Responses | Responses 預設把回應存在 OpenAI 30 天,與「稽核不存原文」的精神衝突;在權限層關掉,程式寫錯也存不了。Chat Completions 也是 D24「業界通用格式」的那個格式(E20、E21) | Responses 並設 `store: false`(要靠每次呼叫都記得設,一次忘記就存下去) |
| D30 | 單價與進位 | 單價放 repo 設定檔;**設定檔沒有單價的模型一律拒絕呼叫**;token × 單價 → 無條件進位成 micro-USD 整數 | M0.5 實測 LiteLLM 內建價格表缺新模型時花費記 0,預算安靜失效(E23);「不知道多少錢」不能當成「不用錢」。進位:治理系統寧可多算,不能讓額度被每次的零頭慢慢偷走(E22)。**v2.8 的 M2 實作(D45,E87):** `app/pricing.py` 的 `cost_micro_usd(model, input_tokens, output_tokens)`;單價以整數存(每一百萬個 token 多少 micro-USD);輸入與輸出加總後進位一次(1.3 + 5.5 = 6.8 → 7);沒有單價的模型丟 `ValueError`。M2 的單價是程式內的字典常數(仍在 repo 裡、改價要經過版本紀錄),M3 搬到設定檔 | 價格表缺項時當 0 元(E23 的失敗模式);四捨五入(每次可能少算最多 0.5 micro-USD);從網路下載價格表(10.3 第 5 點) |
| D31 | 計費事件順序 | Gateway **確認事件送進 SQS 之後才回應使用者** | M0.5 實測 LiteLLM 在「回答已送出、帳還沒寫」時被強制終止會永久掉帳(E26);本案 v2.5 流程(平行)有同樣缺口。多一次 SQS 寫入約十幾毫秒,換到「回答了 = 帳一定在佇列裡」 | 回應與送事件平行(最快,但有掉帳空窗);回應後才送(同上) |
| D32 | 供應商 429 的分流 | 限流(rate limit)→ 降級便宜模型一次;供應商預算用完(`project_spend_limit_exceeded` 等)→ 不降級,回 503 並告警 | 兩者狀態碼都是 429,但意義不同:預算用完時降級到便宜模型一樣會被擋,只是多浪費一次呼叫;而且這代表 Gateway 自己的額度控管與供應商帳單對不上,需要人處理(E20、E21) | 所有 429 一律降級(預算用完時白費力氣,並掩蓋對帳問題) |

## 12.8 v2.7 追加定案(M1 期間,2026-09-26～10-04)

| # | 項目 | 定案 | 為什麼 | 不選的選項 |
|---|---|---|---|---|
| D33 | Bedrock 的定位 | **退場,不再當備案**;架構固定為 NAT + 受控出口 + OpenAI API | 保留一條不會實作、也沒驗證過的切回路線,文件裡就同時存在兩套網路設計,被追問時拿不出證據;帳號封鎖的兩條路都沒有結果(E29) | 繼續保留為「可切回的供應商」(v2.5、v2.6 的寫法) |
| D34 | 開發機 | 只用個人電腦;公司電腦不再用於本專題。**v2.9 修訂(E94):** 金鑰、`.env` 與真實呼叫只在個人電腦。**v2.10 補(E123):** 登入 AWS 與 `plan`/`apply`、`docker push` 也只在個人電腦;另一個理由是 ALB 只開給 `admin_cidr`,在公司網路查到的是全公司共用的對外 IP。公司電腦只做文件與讀程式 | 個人專案的金鑰與程式碼不該放在公司管理的設備上,對公司的資安政策與自己的資產都不好(E31) | 兩台電腦並用(M0～M0.5 的做法) |
| D35 | Python 套件冷卻期 | `pyproject.toml` 設 `[tool.uv] exclude-newer`,日期寫死;放寬時手動改日期並 commit | 把 D27 的冷卻期從 LiteLLM 映像擴大到所有 Python 套件;2026/3 的惡意版本在上架數小時內就被下載(10.3 第 3 點)。日期寫死,每次放寬都留下可追查的版本紀錄(E51)。實測排除了當時剛上架的 openai 3.21.0(E58) | 自動滾動的相對日期(放寬時沒有紀錄);不設冷卻期 |
| D36 | M1 的稽核存放 | JSON Lines 檔(一行一筆),包成 `append_audit()`;M2 換成 DynamoDB Local 時只換這個函式的實作。以附加模式開檔、明確指定 UTF-8;執行時資料放 `data/`,不進 Git。**v2.8 修訂(D52):** M2 沒有換,稽核仍存這個檔案,M4 上雲前才搬。**v2.10 修訂(D77,E116):** 已搬進 `audit` 表;換的方式照這裡的設計,呼叫端改用領用窗口 `get_audit_writer()`,`append_audit()` 搬到 `tests/fakes.py` 只剩測試在用 | 稽核只新增不修改,與「接在最後寫一行」吻合;存放細節藏在函式後面,呼叫端不用改(E65) | SQLite(關聯式,M2 全部作廢);M1 就上 DynamoDB Local(第一次成功對話前要先搞定 docker-compose、boto3、建表) |
| D37 | 上游(OpenAI)失敗的處理 | 稽核照記一筆 `status: error`,回 **502**,訊息固定為 `Upstream model error`;稽核只記錯誤的**類別名稱**,不記錯誤訊息 | 使用者確實送了請求,稽核不能查不到(同 E23:失敗請求也要記);502 的語意就是「閘道向上游取資料,上游出錯」;錯誤訊息可能夾帶帳號資訊或請求內容,本身就是洩漏管道(E69)。依錯誤類型分流(限流降級、預算用完不降級)在 M3 依 D10、D32 實作 | 讓例外直接變成 500(稽核無紀錄);把供應商的錯誤訊息原樣回給使用者 |
| D38 | `POST /v1/chat` 的請求格式 | 只有 `message` 一欄,長度 1～4000 字;不合格由框架回 422。回應為 `request_id`、`reply`、`model` | 沒有 `model` 欄位,從格式上就做到 D9(使用者不能指定模型);長度上限避免超長輸入造成超額花費;回應帶 `request_id`,使用者可以拿它對回稽核紀錄(E67、E72) | 相容 OpenAI 的 `messages` 陣列格式(M1 用不到多輪對話;M7 若做 agent 再評估)。**v2.8 評估結果(D42):** M7 用文字約定,D38 不改;原生工具呼叫列為升級路線(7.9)。**v2.9(D64):** 4,000 字是字數不是位元組;超過回 422、不寫稽核;由測試釘住 |
| D39 | 容器建置原則 | 多階段建置;基底映像以 digest 鎖定;照 `uv.lock` 安裝且不裝開發工具;以一般使用者執行;`.dockerignore` 用白名單(先全部排除,再放行 `app`、`pyproject.toml`、`uv.lock`);金鑰不進映像,執行時才提供;本機執行只綁 `127.0.0.1` | 每一項都有指令可以證明(E74):`whoami` 不是 root、映像內沒有 `.env`、`import pytest` 失敗、找不到 `uv`、建置時只送出 307 位元組。安裝工具以 `COPY --from` 自官方映像取得,不下載腳本後直接執行 | 單階段建置(安裝工具留在映像裡);`.dockerignore` 用黑名單(新增的檔案預設會被送進去) |
| D40 | 工作方式 | Python 程式由本人撰寫(提示分三層,AI 自動補全關閉);Dockerfile 與 M4 的 Terraform 由含註解的骨架改寫,本人負責理解、修改、執行、除錯,並能逐行說明。函式上方加一行中文註解,英文 docstring 保留 | 面試被追問時要答得出來;同時守住 11/7 的時程(E60)。Dockerfile、Terraform 屬宣告式設定,重點在看懂每個設定的理由與除錯,不在從空白打字 | 全部從零自己寫(時程不允許);全部由 AI 產生(答不出細節) |

> **冷卻期的一次例外(誠實記錄,E74):** D39 的 `python:3.12-slim` 於建置當下距製作時間 2 天 10 小時,未滿 D27 的 3 天。評估後當天照做:映像只在本機測試、不推送,digest 已鎖定;Docker 官方映像定期重建是為了納入安全更新,風險型態不同於任何人都能上傳的 PyPI 套件。M4 推上 ECR 前再確認此 digest 仍然有效。
>
> **v2.8 複查(E89):** 10/7 以 `docker buildx imagetools inspect` 確認這個 digest 仍然存在、指紋沒有變。只確認了存在,沒有掃弱點(Trivy 於 CI 建立時加入)。M2 用到的 `amazon/dynamodb-local:3.3.1` 於 7/31 上架,已過冷卻期,同樣鎖 digest。

## 12.9 v2.8 追加定案(M2 期間,2026-10-04～10-09)

| # | 項目 | 定案 | 為什麼 | 不選的選項 |
|---|---|---|---|---|
| D41 | 定位與呈現 | 定位:**雲端工程師,做 LLM 上線之後的治理層**。兩支影片:6 分鐘主影片 + 技術版 10～15 分鐘;一份簡報是兩支影片的共同骨架;每關驗收當下錄影;旁白稿另存,素材到齊才放進簡報 | 指導老師 10/5 回覆知識層做不做「看你對你的定性」,並同意另附一支影片;外人看完的感受要等於想要的定位(E79、E84) | 定位成「替企業做 AI 化」(知識層就躲不掉,離 11/7 不到五週);只做一支影片(技術細節講不完);兩支影片各做一份簡報(會互相對不上) |
| D42 | M7 小型 agent | **有條件開工**,限時 6 小時;用文字約定(`CALL 工具(參數)` / `FINAL 答案`),不改 Gateway 與 D38;三個開工時段都沒達到就改用備案 | 作者決定保留 M7 當挑戰;影片與錄影已吃掉大部分餘裕,只能靠前面幾關提早完成來換,所以要有開工條件(E79) | 取消 M7;用 OpenAI 原生工具呼叫(要改請求格式、遮罩與稽核,估 8～12 小時,會動到已驗收的東西) |
| D43 | 個資遮罩規則 | 四類:信箱、信用卡號、手機、身分證字號。遮成類別標籤(`[EMAIL]`、`[CARD]`、`[PHONE]`、`[TW_ID]`);處理順序固定為信箱 → 信用卡號 → 手機 → 身分證字號;信用卡號通過 Luhn 才遮,身分證字號不驗檢查碼、大小寫都遮;手機涵蓋日常寫法(連續、加連字號或空格、`+886`)。稽核欄位 `pii_types` 記類別、不記內容。一個內部函式同時算出遮好的句子與類別。**v2.10(D77,E116):** 寫進 DynamoDB 時 `pii_types` 存清單(`L`),不用 String Set:空清單存得進去、順序不變 | 標籤讓模型知道這裡原本是什麼,句子仍讀得通,稽核也能沿用。順序:有的信箱開頭長得像手機,先換手機會把它切成兩半。13～19 位純數字太常見(訂單編號),驗 Luhn 可減少約九成誤遮;身分證字號寧可多遮也不要漏。遮罩與類別只有一份比對邏輯,兩邊不會對不上(E77～E85) | 遮成 `***`(模型與稽核都分不出類別);市話與各國號碼都抓(誤遮大量正常數字);另寫一個函式重新比對類別(會多記沒有被遮的類別);從遮好的句子裡找標籤字樣反推(使用者自己打出標籤就誤判) |
| D44 | 切月與「現在」 | `period_of(moment)`:固定偏移 UTC+8,回傳 `YYYY-MM`;只收帶時區的時間,否則丟 `ValueError`。「現在」由 FastAPI 的相依提供,同一個請求的 `period`、`Retry-After`、稽核時間用同一個值 | 台灣沒有日光節約時間,固定偏移全用 Python 內建,Windows、容器、Lambda 一定一致;函式不自己取時間,跨月邊界才測得到;不知道是哪個時區就不該猜(E86、E91) | 時區資料庫(Windows 要另裝 `tzdata`,多一個相依套件);函式自己取「現在」(邊界無法重現);沒帶時區當成 UTC |
| D45 | M2 的最小成本函式 | 成本換算提前到 M2,只含 `gpt-6-luna`;細節見 D30 的 v2.8 補充。扣額度時用程式指定的模型名稱查單價,不用供應商回報的名稱 | v2.7 把成本換算排在 M3,但 M2 由 Gateway 扣額度就需要金額。供應商回報的名稱可能帶日期尾碼,查不到單價時會在已經花錢之後出錯(E87、E91) | 等 M3 再做(M2 無法扣額度);M2 就做完整設定檔(與路由規則一起做較合理) |
| D46 | 超額回應 | **429**,`{"detail": "Monthly quota exceeded"}`,附 `Retry-After`(到台北時間下個月 1 號 00:00 的秒數,不足一秒進位);已用 ≥ 額度就擋;被擋的請求寫稽核,`status` 為 `quota_exceeded`,沒有模型與成本欄位 | 與流程圖、LiteLLM、OpenAI 的做法一致;額度檢查排在呼叫模型之前,客戶端自動重試碰不到供應商、不會多花錢;被擋的請求要查得到是誰(同 D37)。10/9 兩次實測的 `Retry-After` 經手算都一秒不差(E88、E92) | 402(使用者無法用付費解決)、403(與權限混淆);結構化的錯誤內容(與 502 的格式不一致);不附 `Retry-After`;用 `>` 判斷(額度 0 的人還能呼叫一次) |
| D47 | 本機的資料層 | DynamoDB Local(`amazon/dynamodb-local:3.3.1`,鎖 digest,`-sharedDb -inMemory`);兩個容器:開發與驗收用 `127.0.0.1:8001`,測試專用 `127.0.0.1:8002`(每個測試前清空)。網址是必填的環境變數;假帳密寫成程式內的具名常數並明確帶入;建表在 `scripts/create_tables.py`,已存在就跳過。碰資料庫的測試打真的 DynamoDB Local,標 `integration`,連不到就明確地紅。**v2.10 修訂(D74,E111):** 網址的環境變數改為 `DYNAMODB_TARGET`(寫 `aws` 連雲端、寫網址連練習場);練習場仍一定帶假帳密(實驗拿掉後,43 個測試跑去找本人電腦上 `aws login` 的身分) | 不寫 `127.0.0.1` 會開給區域網路(E13);不加 `-sharedDb` 會依存取金鑰分成不同的資料庫且沒有任何錯誤;boto3 不給網址或帳密時會去連真的 AWS、用電腦上真的身分;手寫的假資料庫不會解讀運算式,扣額度最容易錯的部分測不到(E89) | 資料掛磁碟(測試被舊資料干擾);建表放進 Gateway(雲端不該有建表權限);用模擬套件(多一個相依套件);連不到資料庫時自動跳過測試(綠燈不代表有測) |
| D48 | API Key 驗證 | `Authorization: Bearer gw_…`;沒帶、不存在、被停用一律回相同的 `401` `Authentication failed`,附 `WWW-Authenticate: Bearer`;驗證寫成 FastAPI 的相依,失敗的請求不碰模型、不寫稽核;`api_keys` 的 `status` 是 `active` 才放行。**v2.10(D69、D75、D76):** 驗票口的資料庫 503 不附 `Retry-After`;查 Key 用強一致讀取(剛停用的 Key 不會再用一次);停用用 `scripts/disable_key.py` | `Authorization` 是 HTTP 放憑證的標準位置;訊息不同的話,外面的人可以分辨一把 Key 存不存在;寫成相依,「沒通過就進不了主流程」由結構保證,不是靠每個地方記得檢查;停用用 `status` 而不是刪除,才查得到這把 Key 原本屬於誰(E90) | `X-API-Key`(自訂標頭,工具不認得它是機密);驗證寫在主流程裡(失敗的請求可能已經做了別的事);驗證失敗也寫稽核(沒有身分可記,會被假 Key 灌爆) |
| D49 | 資料庫讀不到或寫不進去 | 一律不放行,回 **503** `{"detail": "Service temporarily unavailable"}`,驗證與額度共用;連線逾時 2 秒、讀取逾時 5 秒、最多試 2 次、`standard` 模式。**v2.10(D69、D74,E109、E111):** 不附 `Retry-After`(測試釘住);雲端與練習場用同一組逾時與重試(`DYNAMODB_TARGET` 兩種目標都測) | fail-closed。帶著正確 Key 的人不該被告知 Key 有問題,所以是 503 不是 401;驗證與額度其實是同一個資料庫,各用一個訊息只是對外透露內部結構。實測預設值要等 48.1 秒,設定後 6.7 秒(E90、E92 的 S03) | 放行(資料庫一出事額度就失效);回 401;維持 boto3 預設;只試 1 次(一次瞬間的連線問題就變成 503) |
| D50 | 額度放哪裡 | **使用者層級**:`quotas` 表 `user_id` + `period = "limit"` 那一筆存 `limit_micro_usd`;每月一筆只存 `used_micro_usd`。查不到已用量當成 0;查不到額度當成 0、回 429 | 換月不用任何人動手。額度與已用量放同一筆的話,換月時新的一筆沒有人建,所有人查不到額度(E91) | 兩者都放在每月那一筆(v2.4～v2.7 的原設計,要每月開帳);放在 `api_keys`(額度變成跟著 Key 而不是跟著人);查不到額度就放行(等於沒有上限) |
| D51 | 扣額度(M2～M4) | 呼叫模型前對當月那一筆 `ADD` 0,寫不進去回 503;模型回答後以 `ADD` 原子累加實際成本;事後扣失敗時回答照給,稽核記 `charged: false` 與金額。已知會超扣。**v2.10(D77,E116):** M4 照這個做法上雲;稽核也寫不進去時,`charged: false` 與金額只留在一行日誌(測試涵蓋) | 模型已回答才發現扣不了帳時,不給是白花錢,給了又可能被一直免費用;事前加 0 擋掉「讀得到、寫不進去」。`ADD` 不用先讀再寫,兩個請求同時扣也不會互相蓋掉(E91;實測超扣見 7.10) | 扣失敗就不給回答;不做事前檢查;讀出來、算好、再寫回去(同時扣會有一筆被蓋掉);M2 就做預扣(要估計金額並處理多退少補) |
| D52 | M2 的稽核存放(修訂 D36) | **仍存本機檔案**,欄位加 `user_id`、`cost_micro_usd`、`charged`;M4 上雲前搬進 `audit` 表。**v2.10:10/15 已搬(D77,E116)**;「這筆紀錄放哪裡」的答案:寫不進表時印一行日誌、M4 告警、M5 用 SQS | 扣額度失敗時靠稽核記下沒扣到的金額(D51);稽核和額度放同一個資料庫,資料庫寫不進去時這筆紀錄也寫不進去。代價:工作是往後挪,不是省掉;檔案不能按人查詢,容器重開就消失,所以 M4 前一定要搬,屆時一併決定這筆紀錄放哪裡(E91) | M2 就搬進 DynamoDB Local(D36 的原計畫);同時寫檔案與資料庫(兩份要對帳) |
| D53 | 種子腳本 | `scripts/seed.py`:alice 1,000 micro-USD、bob 1,000,000 micro-USD;Key 以 `secrets` 產生、只印一次,資料庫只存雜湊;執行時先建表;每次執行產生新的 Key | 示範帳號要能重建(本機資料庫重開就清空);用 `secrets` 而不是一般的亂數;有一個測試掃整張表確認找不到 Key 本身。限制:重跑後舊的 Key 不會失效(E91) | 把 Key 寫進檔案(多一個要保護的檔案);固定的示範 Key 寫在 repo 裡 |

## 12.10 v2.9 追加定案(M3 期間,2026-10-10～10-14)

| # | 項目 | 定案 | 為什麼 | 不選的選項 |
|---|---|---|---|---|
| D54 | 設定檔 | `app/config.toml`(TOML,一個檔):`[routing]` 指名兩顆模型、字數門檻、關鍵字;`[models.名稱]` 放思考量、輸出上限、單價(每一百萬 token 多少 micro-USD,整數)。`app/config.py` 的 `load_config()` 讀進來就檢查:路由用到的模型要有設定、數字是大於 0 的整數、關鍵字不能空白、不能少欄位,有問題丟 `ConfigError`,Gateway 起不來。設定做成領用窗口 `get_config()`,測試換得掉 | JSON 不能寫註解,單價旁邊無法註明單位與來源;空字串「出現在」每一句話裡,混進關鍵字清單會把所有請求送去強模型而且不報錯;單價少打一個 0 不會當掉,所以測試裡另寫一次決策書的數字對帳(E94、E95) | JSON;YAML(多一個套件);放根目錄 `config/`(`.dockerignore` 與 `Dockerfile` 都要改) |
| D55 | 路由規則(修訂 D8) | `choose_model()`(`app/router.py`)吃**遮罩後**的文字,回傳模型與理由(`length`、`keyword`、`default`),先看字數再看關鍵字。關鍵字見 D8;英文關鍵字**字首比對**:前面不能緊貼英文字母或數字(`code` 不命中 `decode`,`debug` 命中 `debugging`);中文維持有出現就算。字數門檻 300。20 題測試集(簡單 13、複雜 7)兩顆模型都真打:送對 18 題、**省 25.3%** | 模型實際收到的是遮罩後的內容;「比較」常當副詞(「改得比較有禮貌」);整字比對會漏掉 `debugging`,漏掉(難題拿到較弱的回答)比多花錢更糟;Python 的 `\b` 把中文當成字的一部分。字數門檻 500 省 54%,但 24 個百分點來自一題,而且送錯的代價不對稱(E97、E103、E105) | 字數門檻 500;整字比對;子字串比對;用原文路由 |
| D56 | 查單價的時機 | 路由一決定就用 `find_model_config()` 查這顆模型的設定,查不到丟 `ModelNotConfiguredError`:回 500 `Internal server error`、寫稽核、不呼叫模型、不扣錢。`cost_micro_usd()` 改收設定物件,算成本用的就是查到的那一份 | M2 的成本函式排在模型回答之後,M3 模型由路由決定,沒有單價的模型會在花了錢之後才出錯。拆成兩步,「花了錢才發現沒單價」由函式的形狀保證不會發生(E94、E96、E97) | 維持回答之後才查;回 503(客戶端會白白重試,也和資料庫故障混在一起);讓框架自己回 500(沒有稽核) |
| D57 | 稽核欄位 | 新增 `route_reason`、`routed_model`、`provider_model`、`fallback`、`fallback_reason`、`error_code`、`finish_reason`;`model` 改記實際回答並計費的名稱;回給使用者的 `model` 也是這個。一個請求仍只有一筆(見 3.2) | 降級時要看得出原本選誰、實際誰回答、為什麼;供應商回報的名稱可能帶日期尾碼;錯誤只記短代碼不記訊息(同 D37)(E98、E100、E101) | 降級寫成兩筆(主鍵是 `request_id`,會相撞);只記最後的模型(看不出降級過) |
| D58 | 輸出上限與預扣 | 每顆模型設 `max_completion_tokens`:`gpt-6-luna` 2,000、`gpt-6-sol` 2,000。思考 token 已實證算在輸出裡。預扣 M3 不做,留到 M5 | 便宜模型答複雜題寫得比強模型長,1,000 時 20 題有 2 題被截斷;強模型最多用到 1,372。預扣要改已驗收的扣款流程,M5 移交 Worker 時又要重做;先讓一次最多超扣多少變成算得出來的數字(E94、E101、E103) | 便宜模型維持 1,000;M3 就做預扣;不設上限 |
| D59 | 降級(補 D10、D32) | `app/fallback.py` 的 `chat_with_fallback()`:強模型被限流 → 便宜模型一次;兩顆都限流 → 503 附 `Retry-After`(照抄供應商 1～120 的整數秒,超過回 120,沒有或看不懂回 30);預算用完 → 不降級、503 不附 `Retry-After`;其他錯誤 → 502。兩種 429 用**排除法**:代碼是 `insufficient_quota`、`credit_balance_exhausted`、`project_spend_limit_exceeded`、`organization_spend_limit_exceeded`、`organization_usage_limit_exceeded`,或類型是 `insufficient_quota` → 預算用完,其餘當限流。強模型那次 `with_options(max_retries=0)`,便宜模型保留 1 次。不論成敗都以 `CallOutcome` 交回,不往外丟錯誤。**v2.10 修訂(D70,E109):** 便宜模型也不重試(照連線本身的設定 `OPENAI_MAX_RETRIES = 0`);強模型那次的 `with_options(max_retries=0)` 保留 | 官方沒有給限流固定代碼,只認限流代碼的話備援會安靜失效;認錯的代價只是多打一次會被拒、不花錢的呼叫。SDK 連預算用完也會重試、照 `retry-after` 等最多 120 秒,30 秒的逾時管不到;讓降級本身當作重試,最壞從 4 次 HTTP 請求降為 3 次。錯誤往外丟的話,降級過、最後失敗的請求在稽核裡看不出降級過(E100) | 只認限流代碼;比對錯誤訊息文字;維持 SDK 重試;固定 30 秒的 `Retry-After` |
| D60 | 被截斷的回答 | 稽核記 `finish_reason`;照樣回 200、照樣計費;使用者的回應沒有這一欄。本人 10/14 確認維持,M6 有真實統計再看 | 錢已經付給供應商,不扣使用者的錢等於 Gateway 自己吸收,而且會改到行為(E101) | 空回答回 502、不扣錢;不記 |
| D61 | 省下比例的量法與報法 | `scripts/routing_eval.py` 的 `summarize()`:用 Gateway 同一個 `choose_model()` 重新分流 20 題,成本取自實測的結果檔,換規則不必再呼叫模型;比例的分母是「全部用強模型」。報告時一定附題數與題目比例(簡單 65%);完全照判斷分流是 22.5%。定案的數字由 `tests/test_routing_rules.py` 鎖住,改規則測試會紅。重跑時機:模型換版、單價變更、改路由規則 | 量到的就是線上真正的路由;省最多的規則不是最好的規則,所以要同時看送對幾題、送錯分「多花錢」與「可能答不好」兩種(E103、E105) | 用估算的 token 數;只報比例不附題目比例 |
| D62 | CI | `.github/workflows/ci.yml`:Tests(`uv sync --locked`、`compose.yaml` 起 `dynamodb-test`、`pytest`)與 Image scan(`docker build` + Trivy,有修補版的 HIGH、CRITICAL 才失敗);CodeQL 預設設定。Action 鎖 commit SHA、過 3 天冷卻期;權限只有 `contents: read`、不留權杖。tfsec 不用。**v2.10 修訂(D83,E118):** 加第三個工作 `Config scan`(`trivy config .`,HIGH/CRITICAL 擋),列入必要檢查;trivy-action v0.36.0、Trivy v0.74.0 | 只擋有修補版的,擋下來就有事可做;全部擋的話沒有修補版的弱點只能等上游,紅字看久了沒人看。`trivy-action` 在 2026/3 有 76 個標籤被改指向惡意程式,鎖 SHA 的不受影響(E101、E104) | 全部列出不擋;所有 HIGH、CRITICAL 都擋;用標籤指定 Action;tfsec(已停止開發) |
| D63 | 信箱規則 | `EMAIL_PATTERN` 加起點限制 `(?<![A-Za-z0-9._%+-])`,比對時間與長度成正比(4 萬字 2.5 秒 → 0.007 秒),比對結果不變;`tests/test_mask_speed.py` 守住速度。CodeQL 修正後仍標記,附實測數字關閉 | 一長串字母會從每個位置各重掃一次;能讓 CodeQL 不再標記的寫法(名字最多 64 字)會讓長信箱不被遮。不為了讓工具不再標記而改行為(E104) | 「名字最多 64 字」;前面一定要是空白(中文句子裡的信箱會漏遮) |
| D64 | 訊息上限(確認 D38) | 4,000 字(字數,不是位元組);超過回 422、不呼叫模型、不寫稽核;壞 Key 加超長先回 401;由 `tests/test_message_limit.py` 釘住 | 上限從 M2 就存在,只補測試;單次成本的主要槓桿是輸出上限,不是輸入長度(強模型一次最多約 28,000 micro-USD,其中 20,000 來自輸出)(E105) | 調低上限(沒有資料支持);改回 413 |
| D65 | 呈現方式(修訂 D41) | 10 分鐘期末報告(本人報告,含 Demo)與 6 分鐘廠商影片(緯育推廣),兩份簡報、兩份旁白稿;Demo 三章(節費、個資、額度),播錄影、本人現場口述;錄影用 Windows 內建功能,剪接工具到時再定;外行版開場用情境故事;本人先手作、Claude 再修;動畫只用在實測內容的示意 | 老師 10/12 的回覆與簡報建議;現場操作有 IP 白名單、雲端資源平常關著、回應時間不固定等風險;用 AI 做的簡報會被認為沒掌握內容(E101、E102、E106) | 6 分鐘主影片 + 技術版(v2.8);現場操作 Demo;自動放大的錄影工具(本人選擇維持現在的錄法) |
| D66 | 時程(修訂 8.2 的 M7、8.5) | 用 M3 省下的時間先把 M4～M6 做完,**M7 最後再做**;M7 的第一個開工時段(10/17～10/18)取消;M4 提前到 10/17 開工,10/14～10/16 做 M3 收尾與 M4 開工前的本機準備。檢查點不動 | 本人 10/14:不想讓專題太趕、太緊張,要有餘裕;M4 是最大風險,M7 是可砍的第一項(E107) | 10/17～10/18 開工 M7(條件已達成) |
| D67 | 分支流程與漏洞回報 | M3 結案文件推送之後,`protect-main` 加「CI 通過才能合併」,之後改走分支加 PR;新增 `SECURITY.md`,回報方式為 GitHub Private vulnerability reporting(已開啟)。**v2.10(D97,E108):** 實測直接推 `main` 被擋;規則另加「要走 PR」(核准數 0) | CI 紅了也擋不住直接推送;公開 repo 要讓人知道怎麼私下回報漏洞(E104、E105) | 維持直接推送 `main`;沒有回報說明 |

## 12.11 v2.10 追加定案(M4 期間,2026-10-14～10-20)

> 來源是證據紀錄 E108～E126 各筆的「定案」表;相近的合併成一條,每條都寫 E 編號。「本人照建議」「本人選 A」等作答方式見證據紀錄。

| # | 項目 | 定案 | 為什麼 | 不選的選項 |
|---|---|---|---|---|
| D68 | API 說明頁 | `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`:`/docs`、`/redoc`、`/openapi.json`、`/docs/oauth2-redirect` 一律關閉;`tests/test_production_settings.py` 釘住(E109) | 使用者用不到,只會把 API 的地圖交給想攻擊的人。破壞實驗:只拿掉 `openapi_url=None`,測試照樣紅,因為說明頁只是把那份 JSON 畫成網頁,真正交出地圖的是 JSON 本身 | 環境變數控制本機開、正式關(多一個設定,忘了設就是開著);只在 ALB 擋(容器本身仍開著、只剩一層防線) |
| D69 | 資料庫故障的 503 | **不附 `Retry-After`**(維持現狀),4 個資料庫 503 的測試各加一行釘住(E109) | 多久恢復無從得知;給固定秒數等於叫所有客戶端在同一秒一起重試,資料庫剛恢復又被打垮。原本只是剛好沒寫,沒有測試守著 | 附固定秒數 |
| D70 | SDK 重試、逾時與 ALB 閒置(修訂 D10、D59) | 所有 OpenAI 呼叫都不讓 SDK 重試(`OPENAI_MAX_RETRIES` 1 → 0),被限流直接回 503 與 `Retry-After`;強模型那次的 `with_options(max_retries=0)` 保留。逾時 30 → **60 秒**;ALB 閒置逾時 **120 秒**,在 Terraform 明寫(E109、E114、E115) | SDK 遇到限流會在背後等最多 120 秒,ALB 先斷線,Gateway 卻還在呼叫、扣錢。容器實測強模型 1,576 個 token 花 25.6 秒,寫滿 2,000 個約 32 秒,30 秒一定逾時、OpenAI 可能已經收費。120 = 強模型 60 + 降級後便宜模型 60。代價:網路抖一下就 502;60 秒是一個樣本推的 | 保留重試、ALB 調到 180 秒(最多等 3 分鐘);Gateway 自己分配整個請求的剩餘時間(要寫新邏輯);強模型輸出上限降到 1,500(實測那題就會被截斷,供應商一慢照樣撞線);串流回應(`chat()`、稽核、成本都要重寫);只給強模型 60 秒(要改 `fallback.py`,現在不值得) |
| D71 | OpenAI 驗證方式(修訂 D14、4.5) | **M4 直接用工作負載身分聯盟,SSM 不放 OpenAI 金鑰**;先在個人電腦探測(`scripts/probe_wif.py`),不通就退回「SSM 放新金鑰」。OpenAI 端新建專用服務帳號 **`gateway-wif`**,權限只開 Chat completions;Fargate 的對應 `gateway-task-role`(`sub` = 任務角色的 ARN)(E110、E113、E123、E124) | 沒有金鑰可以外流、也不用輪替。探測證明 `chat.completions` 收這種權杖(官方只示範 `responses`);audience 改錯會在換權杖那一步被拒。另建服務帳號:用金鑰與不用金鑰的呼叫分屬兩個身分,停其中一個不牽連另一個,也不受 `m1-gateway` 11/2 到期影響 | M4 先用 SSM 放新金鑰、驗收後再升級(Claude 原本的建議;本人選擇直接做);只寫進決策書;沿用 `m1-gateway` |
| D72 | `OPENAI_AUTH` 與共用連線 | 新環境變數 `OPENAI_AUTH`,一定要明講:`api_key`(本機)/`workload_identity`(雲端);沒設 `KeyError`、寫錯 `ValueError`,啟動就檢查。`app/openai_auth.py`:東京 STS 地區網址、audience `llm-gateway-capstone`、ES384、300 秒;把取得證明的函式**本身**交給 SDK。`get_client()` 加 `@lru_cache(maxsize=1)`,整個程式共用一個連線。`tests/conftest.py` 開頭強制 `OPENAI_AUTH=api_key`(E110、E123) | 程式自己猜的話,視窗殘留的環境變數會讓本機悄悄換路(E111 的 43 個測試連錯資料庫就是這類);每個請求新建連線的話,每次都重換一次權杖、多兩趟網路。破壞實驗:函式加了括號,建連線那一刻就去要證明,本人電腦真的往下去找 `aws login` 的身分;STS 改全球網址,測試擋下 | 自動判斷用哪一種;本機也用身分聯盟(每次開發要匯出會過期的憑證,而且讓管理員帳號當 OpenAI 的身分);每個請求建一個 `OpenAI()` |
| D73 | 版本更新 | `.github/dependabot.yml`:**只開 GitHub Action 與 Dockerfile 基底映像**的版本更新,每週、冷卻 7 天、一次最多 3 個 PR;Python 套件只收安全性更新(E110) | 合併後幾分鐘就開出第一個 PR(Trivy Action v0.36.0),證明有運作。11/7 前每週換 `openai`、`fastapi` 的版本,專題期間風險高 | 加上 Python 套件;維持手動(版本停在原地)。限制:鎖了指紋的基底映像能不能被更新官方沒寫清楚;`compose.yaml` 的 DynamoDB Local 與 Trivy 本身的版本不在範圍內 |
| D74 | 資料庫連線目標(修訂 D47、D49) | 環境變數改名 **`DYNAMODB_TARGET`**:`aws` → 東京真的 DynamoDB(不給網址、不給帳密,身分交給 IAM 角色);`http://`、`https://` 開頭 → 那個網址的練習場(假帳密 `local`);沒設 `KeyError`、其他值 `ValueError`(E111) | boto3 什麼都不給時會自己連真的 AWS、用這台電腦登入的身分。破壞實驗:最後的 `raise` 改成「當作 `aws`」,`AWS`、空字串、忘了 `http://` 都會默默連雲端 | 名稱不變寫 `DYNAMODB_ENDPOINT_URL=aws`(「網址」變數裝的不是網址);加第二個變數(兩個設定可能互相矛盾);沒設就當成雲端(忘了設定就用本機的 AWS 身分改雲端資料) |
| D75 | 強一致讀取與計費模式 | 查 Key、查額度、查已用量都加 `ConsistentRead=True`;雲端表用隨需(`PAY_PER_REQUEST`)(E111) | 預設的最終一致可能讓剛停用的 Key 再用一次、剛扣完的錢讀到舊的;讀取費用 2 倍,Demo 的量一個月不到一分錢。隨需不用估容量 | 只有查 Key 用強一致(額度仍可能多放行一次);都不用;預置容量吃免費額度(要自己估,Demo 時可能被 `ProvisionedThroughputExceeded` 擋下) |
| D76 | 停用 Key | `scripts/disable_key.py`:`--key`(`getpass` 輸入,不顯示、不留在指令紀錄)停一把;`--user` 用 `scan` 翻頁找出那個人的全部 Key 並停用;更新加 `ConditionExpression="attribute_exists(key_hash)"`,不存在丟 `KeyNotFoundError`(E112) | DynamoDB 的 `update_item` 在那一筆不存在時會**自己新建一筆**:輸入打錯一個字會多出一筆「已停用的、不存在的 Key」,真正外流的那把照樣能用。破壞實驗:拿掉條件,只有「打錯字」那個測試紅;只看第一頁,`1 == 3` | 只做停一把,或只做停一個人;不加條件。限制:掃表在表大了會慢;停用不可復原、沒有記錄時間與操作者 |
| D77 | 稽核寫進 `audit` 表(修訂 D36、D52) | `write_audit()` 條件寫入(`attribute_not_exists(request_id)`,不覆蓋);`save_audit()` **只接** `BotoCoreError`、`ClientError`,交給 `report_audit_failure()` 以白名單印一行 JSON 到 stderr(不含摘要與 HMAC);**回應不變**(成功照給、429 照 429、502 照 502);`pii_types` 存清單(`L`);領用窗口 `get_audit_writer()`,既有測試換成「寫暫存檔、寫之前先轉 DynamoDB 格式」的替身,約 110 處斷言不用改;`Dockerfile` 不建可寫的資料夾,ECS 設唯讀根目錄(E116) | 容器重建稽核就消失;錢已經付給供應商,不能因為稽核寫不進去就不給回答(D51)。`put_item` 預設覆蓋、不報錯;只接資料庫的錯,寫錯的程式才不會被偽裝成資料庫問題。容器實測:刪掉 `audit` 表 → 200、日誌一行、表建回來查不到那一筆 | 容器內檔案(重建就消失);另開 SQS/S3(等於提前做 M5);寫不進去回 503;String Set(不收空的、不保留順序);所有測試改讀資料庫(改動上百處);`except Exception` |
| D78 | Terraform State 鎖(修訂 5.1) | **只用 S3 本身的鎖檔**(`use_lockfile = true`),不建 DynamoDB 鎖表(E117、E119) | Terraform 官方已把 DynamoDB 鎖標為淘汰。實際遇過一次中斷的 `plan` 留下鎖,下一個被 `412 PreconditionFailed` 擋下,證明鎖有效 | 照原設計另建 DynamoDB 鎖表 |
| D79 | Terraform 分兩層 | **長期層**(State bucket、GitHub OIDC、ECR、三張表,D 段加 IAM 角色、日誌、告警)平常不拆;**每日層**(網路、安全群組、Gateway Endpoint、NAT、DNS 防火牆、ALB、ECS)測完就拆;destroy workflow 只拆每日層(E117) | 全部一層的話,每次都要重建表、重跑種子腳本、所有 Key 換新 | 全部一層、一鍵全拆。弱點:兩層分開 apply;長期層結案時要另外記得清 |
| D80 | M4 從哪裡執行 | 本人電腦(`aws login`)跑 `plan`/`apply`、`docker push`;GitHub OIDC 角色先只給 destroy workflow,CD 留到 M6(E117) | M4 每次除錯都要推、等 CI 的話會慢很多 | M4 就全部走 GitHub Actions。弱點:M4 期間部署是手動的 |
| D81 | ALB 開給誰 | 安全群組只放行本人的公開 IP(變數 `admin_cidr`,只收 `/32`,`0.0.0.0/0` 被擋);HTTP 80。本機用 `TF_VAR_admin_cidr`,每開一個終端機查一次當下的公開 IP,不存 `.tfvars`;destroy workflow 填 RFC 5737 文件專用位址 `192.0.2.1/32`(E117、E121) | 開給全世界的話,誰掃到都能打 Gateway、灌日誌、吃 ALB 費用。本人常換網路;硬碟上不留 IP,忘了設 Terraform 會停下來問。拆除只照帳本拆,不會用到這個值 | 開給全世界;IP 存 `.tfvars`(換網路容易拿舊 IP);存成 GitHub secret(個人 IP 多存一處) |
| D82 | 長期層的資料保護 | 雲端先建三張表(`usage` M5);表開 AWS 層級的刪除保護與 PITR;State bucket `prevent_destroy`、封鎖公開、版本控制、`AES256`、只准 HTTPS;ECR `IMMUTABLE`、`scan_on_push`、沒標籤 1 天刪、最多 10 個,映像標籤用 git commit 編號(E118、E119) | `usage` 的欄位 M5 才定。`prevent_destroy` 只擋 Terraform,擋不住主控台;實測 CLI 刪表被擋、`terraform destroy` 一個都沒拆。可覆蓋的 `latest` 出事時查不到當時跑的是哪一份 | 現在建四張;只用 `prevent_destroy`;`MUTABLE` 加 `latest`。限制:兩者擋的是「手滑」,不是「有權限的惡意」 |
| D83 | IaC 掃描與刻意接受(修訂 D62) | CI 加 `Config scan`(`trivy config .`,HIGH/CRITICAL 擋),列入必要檢查;Trivy v0.74.0。刻意接受的項目在該資源上方寫 `#trivy:ignore:<ID>:exp:2026-12-31`,上面幾行寫理由:AWS-0132(State bucket 沒用自管 KMS)、AWS-0104(安全群組出口 `0.0.0.0/0:443`)、AWS-0053(ALB 對外)、AWS-0054(HTTP)、AWS-0095(SNS 沒加密)(E118、E121、E123) | 理由跟程式碼放一起,改到那段的人一定看得到;到期日一過豁免自動失效、CI 變紅,逼人重新檢討。破壞實驗:拿掉 AWS-0132 那一行,`Config scan` 20 秒內紅、其他照綠。各項的理由:帳本沒有密碼、存取由 IAM 與 HTTPS-only 管住;OpenAI 的 IP 不固定、只能用網域管;ALB 只有一個 IP 進得來;沒有網域發不了 HTTPS 憑證(7.8);預設金鑰加密的主題 CloudWatch 告警發不進來 | 自管 KMS 金鑰(每把每月約 US$1、所有角色多一組權限);CI 只擋 CRITICAL(為了過關降低門檻);另開 `.trivyignore`(理由與程式碼分開) |
| D84 | 誰能借 destroy 角色 | GitHub environment **`destroy`**,只准 `main`;信任條件 `sub`、`aud`(`sts.amazonaws.com`)都完全相等;`sub` 用 GitHub 2026/7/15 後新 repo 的「名字@編號」格式;不設審核人;**取消管理員略過**;角色 ARN 放 repository secret(E120) | 只限 `main` 分支的話,`main` 上任何 workflow 的任何工作(包括 CI)都借得到。舊格式照抄會永遠借不到,錯誤只有「沒有權限」;先用 `oidc-check` 印出證明欄位才確定。管理員略過預設是勾的,而這個 repo 唯一會觸發的人就是管理員;實測從別的分支觸發在 GitHub 那層就被擋。environment secret 只有掛了 environment 的工作讀得到,沒掛的那個工作被拒的原因會變成「參數不對」 | 只限 `main` 分支(`sub` 結尾 `ref:refs/heads/main`);保留管理員略過;ARN 放 environment secret。弱點:「只准 `main`」在 GitHub 的設定裡,不在 repo、沒有版本紀錄 |
| D85 | destroy 角色的權限 | **分批長出來、護欄先到:** 第一批只有每日層帳本兩個檔,但長期層的明文 Deny 先寫好;`Describe` 逐一列出(`Resource "*"` 是 AWS 規定);刪除限本帳號、東京、指定資源種類,再加 `aws:ResourceTag/Layer = daily`;不給任何 `Create*`、`CreateTags`;**能不給就不給**:任務定義 `skip_destroy`(不給 `DeregisterTaskDefinition`)、角色與日誌放長期層;真的沒辦法才寫 `Resource "*"` 並附理由:`ec2:DisassociateAddress` 單獨一條 `DisassociateAnyAddress`(E120、E121、E123、E125) | 照文件猜一整份,猜多了就是多給。打錯的動作名稱不會報錯、只會變成「沒給」,所以 Deny 寫完一定用權限模擬器逐一問。不給 `CreateTags`,就不能把長期層的東西改貼成 `daily` 再刪。`DisassociateAddress` 的資源是 `*/*`、沒有標籤可比,限標籤的條件永遠不成立(`destroy #2` 卡在這裡);代價是能拔帳號裡任何公開 IP,但刪不掉(`ReleaseAddress` 仍限 `daily`),模擬器第 11、12 題證明 | 一次照文件猜整份;`ec2:Describe*`(動作欄有萬用字元);直接給 `ecs:DeregisterTaskDefinition` 的 `Resource "*"`(換來的只是撕掉不花錢的東西);讓本人電腦拆(workflow 拆不乾淨);`DisassociateAddress` 繼續限標籤 |
| D86 | destroy workflow 的做法 | curl 下載 Terraform 官方 zip、比對寫死的 SHA256;只把 GitHub 的身分證明存成檔案,設 `AWS_ROLE_ARN`、`AWS_WEB_IDENTITY_TOKEN_FILE` 讓 Terraform 自己換憑證,每個指令前重要一張;`::add-mask::` 遮帳號 ID;拆完 `state list` 必須是空的;`concurrency` 不取消正在拆的;**C 段(免費)建好就先實測**;先做一支只驗身分的 `oidc-check.yml`(E120、E121、E122) | 不用第三方 Action,少信任一方、不用每次更新都再審;憑證本身從來不出現在環境變數或 log 裡;拆到一半被取消會留下鎖。C 段實測 51 秒拆光 19 個,第一次就拆乾淨,把會跳錶的 D 段的錯先撞在不花錢的地方 | `hashicorp/setup-terraform`、`aws-actions/configure-aws-credentials`(多信任外部 Action);沿用 `oidc-check` 的 CLI 寫法再寫進環境變數(三個值都要自己遮,漏一行就進公開 log);照原順序到 E 段才第一次拆;不先驗身分(`sub` 寫錯與權限不夠兩種原因會混在一起) |
| D87 | 每日層怎麼拿長期層的資料 | 表名寫死;帳號 ID 用 `aws_caller_identity` 問出來(E121) | 每日層讀什麼,destroy 拆之前也要讀什麼,多讀一處就多一項權限;讀整份長期層帳本是 E120 模擬器驗過關著的門 | `terraform_remote_state`(destroy 角色要能讀長期層帳本);data source(要多開三張表的 `DescribeTable`)。弱點:表改名要改三處,Terraform 不會提醒 |
| D88 | 網路骨架的細節 | 網際網路閘道放 C 段(免費);公有子網不自動發公開 IP;私有子網在 1a(與 NAT 同 AZ);安全群組每條規則一個資源;**只認領預設安全群組**,規則清空、貼名字與 `Layer=daily`;主路由表、預設網路 ACL 不動(E121、E122、E123) | 「卸大門」在免費時就驗過;忘了指定安全群組的東西不會套到「對外全開」的預設;網路 ACL 規則寫錯會擋死整個子網 | 閘道放 D 段;三個預設資源都認領;都不動 |
| D89 | 上雲節奏與 DNS 放行清單 | **一次全上**:「其他全部」先 ALERT,用真實對話與一次性任務製造查詢,從查詢日誌整理清單 → 改 BLOCK(回 `NODATA`)再 apply(只改一條規則)→ 重跑 → 當天 destroy。放行清單 9 個網域(3.5),放行規則設 `TRUST_REDIRECTION_DOMAIN`;10/20 起網域寫成結尾有點(`api.openai.com.`、`*.`)(E123、E124、E125) | 直接 BLOCK,漏一個網域就卡在 `CannotPullContainerError`(3.5 坑 2);拆兩次的話,臨時任務本身就要 ECR、日誌、任務定義,多一輪 apply/destroy。實測 ALERT 一小時剛好 9 個、不用改。預設會連 CNAME 指過去的名字也拿去比,切 BLOCK 時會被擋。AWS 存網域時補一個點,沒有點的寫法讓每次 plan 都有假改動 | 拆兩次上雲;直接 BLOCK;保留沒有點的寫法(無害,但真的改動會被淹沒)。弱點:ALERT 那段時間出口只有紀錄、沒有擋(ALB 只收本人 IP) |
| D90 | Gateway 的兩個 IAM 角色 | 執行角色與任務角色都放**長期層**;任務角色:`audit` 只 `PutItem`、`api_keys` 只讀、`quotas` 讀 + `UpdateItem`、`sts:GetWebIdentityToken` 限 audience 與 300 秒;執行角色只准讀三個 SSM 參數;信任條件限 `ecs-tasks.amazonaws.com` 與本帳號(任務角色加 `aws:SourceAccount`、`aws:SourceArn`,執行角色加 `aws:SourceAccount`)(E116、E123) | 放每日層的話,destroy 角色要多拿 `iam:DeleteRole` 等「註銷身分」的權限,與連 `CreateTags` 都不給的原則相反;稽核不能被改。`Resource: *` 只有兩條、都是 AWS 規定不能指定資源的動作(S11) | 放每日層;拆開放(兩邊的缺點都拿到)。弱點:每日層拆掉後角色還在(沒有任務在跑就沒人借得到) |
| D91 | 密鑰怎麼交給 Fargate(修訂 D14) | 本人用 AWS CLI 建三個 SSM SecureString(`--value (Read-Host)`):HMAC 金鑰(雲端用新的一把)、OpenAI 身分提供者 ID、服務帳號 ID(`user-` 開頭);Terraform 只寫名字(任務定義的 `secrets` 指過去);用 AWS 預設的 `aws/ssm` 金鑰加密(E123、E124) | 值不進 repo、不進帳本、不進指令紀錄(10/14 探測時用 `$env:` 設的兩個 ID 以明文留在 PowerShell 歷史檔,這次改掉)。兩個 OpenAI ID 證據紀錄一直遮蔽,不放 repo | Terraform 用 write-only 參數建(要多引入 `random` provider、功能較新);明文環境變數(違反 D14)。弱點:唯一不歸 Terraform 管的東西,誤刪要手動重建 |
| D92 | 映像版本與部署 | 程式與 Terraform 同一個 PR → CI 全綠 → 合併 → **從 `main` 建映像,標籤 = commit 編號** → 推 ECR → apply;之後改程式只改 `image_tag`。任務定義寫明 `X86_64`;建置加 `--provenance=false --sbom=false`;ALB 健康檢查 `/health` + 部署斷路器自動退回;根目錄唯讀(E114、E116、E123、E124) | 從分支建的話,雲上跑過的那一份可能不在 `main`;`IMMUTABLE` 不准覆蓋固定標籤。Docker 預設多附出廠證明,推上去變成「目錄」格式,沒標籤的子層可能被「沒標籤 1 天」的規則清掉。容器 `Started`、`Up` 都不代表服務可用(設定寫錯時程式載入就停),所以要靠健康檢查判斷 | 從分支建;固定標籤;預設建置(附出廠證明);只看「任務有沒有啟動」 |
| D93 | 帶著沒有修補版的 HIGH 上雲 | ECR 掃描 HIGH 3(zlib、glibc ×2)、MEDIUM 9、LOW 3、沒有 CRITICAL:三個 HIGH 都是 Debian 13 沒有修補版、卡在 Gateway 用不到的函式 → **上雲**;每次建映像看 ECR 掃描,出修補就換基底映像指紋(E124) | 換指紋也修不掉;與 CI 只擋「有修補版的 HIGH、CRITICAL」一致(D62) | 當時沒有另外列出不選的選項(E124 只記決定與理由);反面就是等修補出來才上雲,而上游沒有修補時程 |
| D94 | S08 怎麼證明;ECS Exec | **一次性任務**:同一個任務定義與映像,臨時把啟動指令換成一小段 Python,查 `api.openai.com` 與 `example.com` 並試連 443,結果進 CloudWatch 日誌;設定放 `scripts/egress_check.json`,外包 `egress_check.ps1`。**ECS Exec 不做**,8.2 M4 驗證列的「`enable_ecs_exec` 改成 `true` 後能進入容器」留白(E123) | ECS Exec 要放行 `ssmmessages` 等網域、任務角色多權限、本機裝 Session Manager 外掛,唯讀根目錄下還要另外掛可寫的資料夾,與「出口管很緊」反方向 | ECS Exec;兩個都做(還是要付 ECS Exec 的複雜度) |
| D95 | 日誌與告警 | 兩個日誌群組(`/ecs/llm-gateway`、`/llm-gateway/dns-queries`)、DNS 查詢日誌設定、`audit_write_failed` 指標篩選與告警放**長期層**,保存 30 天、AWS 層級防刪;SNS 主題放長期層,本人用 CLI 訂閱 Email(確認一次);AWS-0095 刻意接受(E123、E124) | 刪查詢日誌設定要 `logs:DeleteLogDelivery`(只能寫 `*`);日誌在每日層拆掉後仍查得到。沒人聽得到的警報器等於沒有;主題放每日層的話每天要重新確認信、destroy 角色多 SNS 刪除權限。實測約 1 分鐘寄信 | 不接通知;主題放每日層;日誌群組放每日層 |
| D96 | 本機操作規則 | PowerShell 5 不用管線把密碼交給外部程式(ECR 登入改 `--password $pw`,用完 `Remove-Variable`);Python 查雲端前後都 `Get-ChildItem Env:AWS_* \| Remove-Item`,中間才 `aws configure export-credentials`;`terraform "-chdir=$tf"` 加引號;往 `.env` 尾巴加行前先確認最後一行有換行;**destroy 之後一定直接問 AWS 確認拆光**(E113、E123、E124) | PowerShell 5 經管線會重新編碼,ECR 登入兩次 `400 Bad Request`;匯出的臨時憑證約 15 分鐘就過期、不會自動續期,而且環境變數比 `aws login` 優先,重新登入也救不回來;`-` 開頭的字串裡的變數不會展開;`destroy #2` 失敗時帳本與 workflow 都不能代表 AWS 上的真實狀態 | 管線交密碼;匯出後不清;`-chdir=$tf` 不加引號;只看 workflow 綠燈 |
| D97 | 分支流程與 PR 規則(補 D67) | `protect-main` 加「Require a pull request before merging」(核准數 0)、Bypass list 為空;必要檢查 `Tests`、`Image scan`、`Config scan`;之後用按鈕合併。**commit 訊息用英文、PR 說明用中文,兩者都不附 Claude 署名或對話連結**(本人 10/18、10/20 定)(E108、E115、E118、E123、E125) | 「要經過 PR」由規則明文保證,不靠 `ci.yml` 剛好只對 PR 跑;一個人開發,核准數 0 不會卡住自己。實測沒跑過 CI 的 commit 直接推 `main` 被擋(GH013) | 維持只要求「檢查要通過」。限制:「沒進 PR、但有綠勾的 commit」能不能被擋沒有測到(目前的 `ci.yml` 做不出這種 commit) |
