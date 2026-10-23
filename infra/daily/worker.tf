# 會計的座位（Worker Lambda）：坐在私有子網，跟 Gateway 受同一套出口管控（E127 定案 5）
# 角色、日誌群組、出單夾在長期層；這裡用寫死的名字組出 ARN（名字要跟 infra/persistent/ 一模一樣）
# Lambda 按次計費，沒有訊息就不收錢；但觸發待命時會一直問出單夾「有單嗎」（算 SQS 請求數），所以觸發也放每日層，測完就拆

locals {
  # 長期層 worker_role.tf、logs.tf、github_oidc.tf 都用這個名字；改名要四邊一起改
  worker_function_name = "llm-gateway-charge-worker"
  worker_role          = "arn:aws:iam::${local.account_id}:role/llm-gateway-charge-worker"
  # 長期層 sqs.tf 的主佇列
  charge_queue_arn = "arn:aws:sqs:ap-northeast-1:${local.account_id}:llm-gateway-charge"
}

# ---- 打包：照清單一件一件放（E139 第 1 題 A）----
# 只放 Worker 用得到的 6 個檔；boto3 用 Lambda 內建的版本，不裝第三方套件
# 不用 source_dir：排除清單漏一個，.env、.venv 就會被打包上雲，而且不會報錯
# Worker 以後多 import 一個檔，這裡要多一段；漏了的話 Lambda 一跑就是 ModuleNotFoundError
# zip 放 build/（.gitignore 已擋）；.gitattributes 規定換行一律 LF，兩台電腦打出來的 zip 一樣
data "archive_file" "worker" {
  type        = "zip"
  output_path = "${path.module}/build/worker.zip"

  # 兩個 __init__.py 是空檔：讓 app、worker 成為套件
  source {
    content  = file("${path.module}/../../app/__init__.py")
    filename = "app/__init__.py"
  }

  source {
    content  = file("${path.module}/../../app/db.py")
    filename = "app/db.py"
  }

  source {
    content  = file("${path.module}/../../app/ledger.py")
    filename = "app/ledger.py"
  }

  source {
    content  = file("${path.module}/../../app/events.py")
    filename = "app/events.py"
  }

  source {
    content  = file("${path.module}/../../worker/__init__.py")
    filename = "worker/__init__.py"
  }

  source {
    content  = file("${path.module}/../../worker/handler.py")
    filename = "worker/handler.py"
  }
}

# ---- 門禁：入口不開，出口只開 443 到 DynamoDB（E135 定案 5）----
# 不寫 0.0.0.0/0，不用 Trivy AWS-0104 豁免；表的範圍再由 endpoints.tf 的 Endpoint Policy 鎖（兩層缺一不可）
# SQS 拉訊息、寫日誌都由 Lambda 服務代做，不經過這張門禁；DNS 查詢也不受安全群組管（3.5 坑 4）

resource "aws_security_group" "worker" {
  name        = "llm-gateway-worker"
  description = "Charge Worker Lambda: nothing in, HTTPS to DynamoDB only"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "llm-gateway-worker" }
}

# prefix list = AWS 維護的「東京 DynamoDB 所有 IP」清單，Gateway Endpoint 建好就有
resource "aws_vpc_security_group_egress_rule" "worker_to_dynamodb" {
  security_group_id = aws_security_group.worker.id
  description       = "HTTPS to DynamoDB through the gateway endpoint"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  prefix_list_id    = aws_vpc_endpoint.dynamodb.prefix_list_id
}

# ---- 會計本人 ----

resource "aws_lambda_function" "worker" {
  function_name = local.worker_function_name
  role          = local.worker_role

  # 跟 Dockerfile、本機測試同一版 Python；x86_64 跟 ECS 一樣
  runtime       = "python3.12"
  architectures = ["x86_64"]
  # 「檔案路徑.函式名」：worker/handler.py 裡的 handler()
  handler = "worker.handler.handler"

  filename = data.archive_file.worker.output_path
  # 程式一改，zip 的指紋就變，Terraform 才知道要重新上傳
  source_code_hash = data.archive_file.worker.output_base64sha256

  # 逾時 20 秒：Worker 最壞卡約 15 秒（連線 2 + 讀取 5，最多 2 次），要比它長（E135 定案 3）
  # 長期層 sqs.tf 的隱藏時間 120 秒 = 6 倍，兩邊要一起改
  memory_size = 128
  timeout     = 20

  # 坐私有子網、掛自己的門禁；Lambda 服務會替它建網卡（拆的時候收回要一段時間，演練第 7 步計時）
  vpc_config {
    subnet_ids         = [aws_subnet.private_a.id]
    security_group_ids = [aws_security_group.worker.id]
  }

  # 要連哪裡一定要明講（app/db.py）：寫 aws 就連東京真的 DynamoDB，身分用執行角色
  environment {
    variables = {
      DYNAMODB_TARGET = "aws"
    }
  }

  tags = { Name = "llm-gateway-charge-worker" }
}

# ---- 出單夾到座位的那條線（SQS 觸發）----
# Lambda 服務用 Worker 的執行角色去拉訊息；Worker 丟錯 → 訊息隱藏 120 秒後重來，第 5 次失敗進 DLQ
# 批次 1 則：一則壞掉不會連累同一批的其他帳（E127 預設值）

resource "aws_lambda_event_source_mapping" "charge" {
  event_source_arn = local.charge_queue_arn
  function_name    = aws_lambda_function.worker.arn
  batch_size       = 1
  enabled          = true

  tags = { Name = "llm-gateway-charge-trigger" }
}
