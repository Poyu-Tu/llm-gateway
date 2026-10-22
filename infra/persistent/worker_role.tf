# 會計（Worker Lambda）的執行角色：放長期層（E127 定案 5），IAM 免費、ARN 不變
# 函式本身在每日層（infra/daily/worker.tf），用寫死的名字指過來；每日層那邊要用一模一樣的名字
# 它只做四件事：從出單夾拿單與銷單、用一個交易寫三本帳、在私有子網建網卡、寫自己的日誌

locals {
  # 每日層的函式名與日誌群組（logs.tf、github_oidc.tf、infra/daily/worker.tf 都用這兩個名字）
  worker_function_name = "llm-gateway-charge-worker"
  worker_log_group     = "/aws/lambda/${local.worker_function_name}"
  worker_function_arn  = "arn:aws:lambda:ap-northeast-1:${data.aws_caller_identity.current.account_id}:function:${local.worker_function_name}"
}

# ---- 誰能借：只有 Lambda 服務、只限本帳號、只限這一個函式 ----
data "aws_iam_policy_document" "worker_trust" {
  statement {
    sid     = "LambdaInThisAccount"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [local.worker_function_arn]
    }
  }
}

resource "aws_iam_role" "worker" {
  name               = "llm-gateway-charge-worker"
  description        = "Used by charge Worker Lambda: read the charge queue and write the three ledgers in one transcation"
  assume_role_policy = data.aws_iam_policy_document.worker_trust.json
}

data "aws_iam_policy_document" "worker_permissions" {
  # 從出單夾拿單、銷單、看佇列狀態（Lambda 服務代拉訊息時用這張證）；只限主佇列，碰不到 DLQ
  statement {
    sid       = "ReadChargeQueue"
    effect    = "Allow"
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.charge.arn]
  }

  # 三本帳：每張表只給 record_charge() 用到的那一個動作，而且只准在交易裡做（E135 定案 4）
  # IAM 沒有「交易」這個權限，交易裡每一件照本來的動作檢查；EnclosingOperation 把它鎖在交易裡
  statement {
    sid       = "InsertUsageInTranscation"
    effect    = "Allow"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.usage.arn]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "dynamodb:EnclosingOperation"
      values   = ["TransactWriteItems"]
    }
  }

  statement {
    sid       = "AddQuotaUsageInTransaction"
    effect    = "Allow"
    actions   = ["dynamodb:UpdateItem"]
    resources = [aws_dynamodb_table.quotas.arn]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "dynamodb:EnclosingOperation"
      values   = ["TransactWriteItems"]
    }
  }

  statement {
    sid       = "AppendAuditInTransaction"
    effect    = "Allow"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.audit.arn]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "dynamodb:EnclosingOperation"
      values   = ["TransactWriteItems"]
    }
  }

  # 坐進私有子網：Lambda 服務替函式建、查、刪網卡。這幾個動作 AWS 規定只能寫 "*"（E127 定案 5 的弱點）
  # 動作照 AWS 的 AWSLambdaVPCAccessExecutionRole 逐一列，不掛那個現成的政策（它還多給了寫任何日誌群組的權限）
  statement {
    sid    = "ManageNetworkInterfaces"
    effect = "Allow"
    actions =[
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
      "ec2:DescribeSubnets",
      "ec2:DescribeSecurityGroups",
      "ec2:AssignPrivateIpAddresses",
      "ec2:UnassignPrivateIpAddresses",
    ]
    resources = ["*"]
  }

  # 只准寫進自己的日誌群組；群組由 logs.tf 建，不給建群組
  statement {
    sid       = "WriteWorkerLogs"
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${local.logs_arn_prefix}:log-group:${local.worker_log_group}:*"]
  }
}

resource "aws_iam_role_policy" "worker" {
  name   = "llm-gateway-charge-worker"
  role   = aws_iam_role.worker.id
  policy = data.aws_iam_policy_document.worker_permissions.json
}