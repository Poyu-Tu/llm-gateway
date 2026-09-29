# LiteLLM 拆解實驗（M0.5）

在動手自建 Gateway 之前，先把現成方案 LiteLLM 在本機跑起來拆解，讓「為什麼不直接用現成的」有實測數據。
完整證據見 `docs/evidence/m0-evidence-log.md` 的 E11～E19，結論見決策書 10.3。

## 檔案

| 檔案 | 用途 |
|---|---|
| `docker-compose.yml` | 主設定：LiteLLM + PostgreSQL，已依官方範例拆解結果強化 7 項（E13） |
| `egress-test.yml` | 覆蓋檔：把網路設為 `internal: true` 模擬零對外連線，並關閉價格表下載（E15） |
| `nodb-compose.yml` | 獨立專案：不設資料庫，埠 4001（E19） |
| `cosign.pub` | LiteLLM 簽章公鑰，取自固定 commit（E11） |
| `.env.example` | 密鑰範本；實際的 `.env` 不進版控 |

## 版本與驗證

- 映像：`ghcr.io/berriai/litellm-database:v1.102.0`，以 digest 鎖定
- 選版規則：上架滿 3 天、未撤回、無未修補 KEV（決策書 D27）
- 驗簽：`cosign-windows-amd64 verify --key cosign.pub ghcr.io/berriai/litellm-database@sha256:<digest>`

## 相對官方範例的強化

1. 密碼不寫在 compose 檔，改從 `.env` 讀
2. 管理金鑰用亂數，不用範例的 `sk-1234`
3. PostgreSQL 不對外開埠
4. LiteLLM 只綁 `127.0.0.1`
5. 映像用 digest 鎖定，不用浮動標籤
6. 拿掉不需要的 Prometheus
7. `LITELLM_LOCAL_MODEL_COST_MAP: "True"`：不在啟動時從 GitHub 下載未驗證的價格表

## 使用方式

```
copy .env.example .env      # 填入三組亂數（用記事本存成 UTF-8）
docker compose config --quiet
docker compose up -d
curl.exe -sS http://127.0.0.1:4000/health/liveliness
```

斷網實驗：`docker compose -f docker-compose.yml -f egress-test.yml up -d`
無資料庫實驗：`docker compose -f nodb-compose.yml up -d`

## 實驗結論摘要

| 觀察 | 結論 |
|---|---|
| 資料庫斷線 | 預設回 503 拒絕，恢復後自動回復（與本案 fail-closed 設計相同） |
| 沒設資料庫 | 無法發虛擬金鑰、沒有每人預算，而且啟動時沒有任何警告 |
| 記憶體 | 待機 584 MiB，超過本案 512 MiB 規格；成本只多約 18%，主要差異在必須常駐資料庫 |
| 對外連線 | 啟動時從 GitHub `main` 分支下載價格表，映像驗過簽但這份資料沒有 |
| 預算檢查 | 排在模型檢查之前；預算 0 被正確當成嚴格上限 |

## 收尾

```
docker compose down            # 保留資料
docker compose down -v         # 連資料一起刪
Remove-Variable mk,vk,h,vh,fh,r   # 清掉 PowerShell 工作階段裡的金鑰變數
```
