# 兩條免費的專用走廊（Gateway Endpoint），只接在私有子網的路由表上
# 每條走廊都掛政策：只准走到指定的地方（決策書 3.5、D16）

# 帳號 ID 向 AWS 問「我是誰」就知道，不用任何權限（E121 定案 1：不讀長期層的帳本）
data "aws_caller_identity" "current" {}

locals {
  # 表名寫死，要和 infra/persistent/dynamodb.tf、app/db.py 一模一樣；改名要三邊一起改
  gateway_tables = ["api_keys", "quotas", "audit", "usage"]

  gateway_table_arns = [
    for name in local.gateway_tables :
    "arn:aws:dynamodb:ap-northeast-1:${data.aws_caller_identity.current.account_id}:table/${name}"
  ]
}

# ---- S3：只准拉 ECR 的映像層 ----
# ECR 的映像層實際放在 AWS 自己的 bucket；寫法照 AWS 的 ECR 文件（決策書 3.5 坑 3）
# 擋的是：被入侵的容器把資料上傳到攻擊者自己帳號的 S3（網域一樣是 amazonaws.com）

data "aws_iam_policy_document" "s3_endpoint" {
  statement {
    sid       = "EcrImageLayersOnly"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::prod-ap-northeast-1-starport-layer-bucket/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.ap-northeast-1.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
  policy            = data.aws_iam_policy_document.s3_endpoint.json

  tags = { Name = "llm-gateway-s3" }
}

# ---- DynamoDB：只准碰本專案的四張表、只准程式用到的三種呼叫 ----
# app/ 只用 get_item、put_item、update_item；交易裡每一件也是這三種動作；走廊只管表，每張表的動作由 IAM 管（E139 第 3 題）

data "aws_iam_policy_document" "dynamodb_endpoint" {
  statement {
    sid       = "GatewayTablesOnly"
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = local.gateway_table_arns

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.ap-northeast-1.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
  policy            = data.aws_iam_policy_document.dynamodb_endpoint.json

  tags = { Name = "llm-gateway-dynamodb" }
}
