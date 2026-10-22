# Gateway 在 Fargate 上用的兩個身分（E123 定案 2：放長期層）
#   執行角色：給 ECS 平台用。拉映像、寫日誌、把 SSM 的機密交給容器，容器裡的程式拿不到它
#   任務角色：給 Gateway 程式用。讀寫四張表、送記帳事件進 SQS、向 STS 要身分證明去換 OpenAI 的通行證
# 放長期層的理由：IAM 免費；任務角色的 ARN 不變，OpenAI 那邊的對應設一次就好；
# destroy 角色完全不需要任何 IAM 刪除權限
# 指到每日層的東西（日誌群組、SSM 參數）用寫死的名字，每日層那邊要用一模一樣的名字

locals {
  ecs_arn_prefix  = "arn:aws:ecs:ap-northeast-1:${data.aws_caller_identity.current.account_id}"
  logs_arn_prefix = "arn:aws:logs:ap-northeast-1:${data.aws_caller_identity.current.account_id}"
  ssm_arn_prefix  = "arn:aws:ssm:ap-northeast-1:${data.aws_caller_identity.current.account_id}"

  # 每日層的日誌群組（infra/daily/ecs.tf 用同一個名字）
  gateway_log_group = "/ecs/llm-gateway"

  # 三個 SSM 參數由本人用 CLI 建（E123 定案 3、4）：值不進 Terraform 的帳本，也不進 repo
  gateway_ssm_parameters = [
    "${local.ssm_arn_prefix}:parameter/llm-gateway/audit-hmac-key",
    "${local.ssm_arn_prefix}:parameter/llm-gateway/openai-identity-provider-id",
    "${local.ssm_arn_prefix}:parameter/llm-gateway/openai-service-account-id",
  ]

  # OpenAI 身分提供者登記的 audience（E113）；任務角色只准開這個 audience 的證明
  openai_wif_audience = "llm-gateway-capstone"
}

# ---- 執行角色 ----

# 只有 ECS 能借，而且只限本帳號替自己借
data "aws_iam_policy_document" "task_execution_trust" {
  statement {
    sid     = "EcsTasksInThisAccount"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "llm-gateway-task-execution"
  description        = "Used by ECS to pull the Gateway image, write its logs and hand it its secrets"
  assume_role_policy = data.aws_iam_policy_document.task_execution_trust.json
}

data "aws_iam_policy_document" "task_execution_permissions" {
  # 跟 ECR 換登入權杖：AWS 規定這個動作只能寫 "*"（它不屬於任何一個倉庫）
  statement {
    sid       = "EcrLogin"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # 只准從本專案的倉庫拉映像
  statement {
    sid       = "PullGatewayImage"
    effect    = "Allow"
    actions   = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"]
    resources = [aws_ecr_repository.gateway.arn]
  }

  # 只准寫進 Gateway 的日誌群組（建日誌串流、寫日誌）；不給建群組，群組由每日層的 Terraform 建
  statement {
    sid       = "WriteGatewayLogs"
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${local.logs_arn_prefix}:log-group:${local.gateway_log_group}:*"]
  }

  # 只准讀這三個參數；用 AWS 預設的 aws/ssm 金鑰加密，所以不用 kms:Decrypt（ECS 文件寫明只有自管金鑰才要）
  statement {
    sid       = "ReadGatewaySecrets"
    effect    = "Allow"
    actions   = ["ssm:GetParameters"]
    resources = local.gateway_ssm_parameters
  }
}

resource "aws_iam_role_policy" "task_execution" {
  name   = "llm-gateway-task-execution"
  role   = aws_iam_role.task_execution.id
  policy = data.aws_iam_policy_document.task_execution_permissions.json
}

# ---- 任務角色 ----

# 只有本帳號、東京區的 ECS 任務能借（ECS 文件建議的兩個條件，防止別人的服務借用）
data "aws_iam_policy_document" "task_trust" {
  statement {
    sid     = "EcsTasksInThisAccount"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["${local.ecs_arn_prefix}:*"]
    }
  }
}

resource "aws_iam_role" "task" {
  name               = "llm-gateway-task"
  description        = "Used by the Gateway code: the three tables and the OpenAI workload identity"
  assume_role_policy = data.aws_iam_policy_document.task_trust.json
}

data "aws_iam_policy_document" "task_permissions" {
  # 驗票口：只查 Key（app/auth.py 的 find_user_id）
  statement {
    sid       = "ReadApiKeys"
    effect    = "Allow"
    actions   = ["dynamodb:GetItem"]
    resources = [aws_dynamodb_table.api_keys.arn]
  }

  # 額度：讀額度與已用量、原子累加（app/quota.py）
  statement {
    sid       = "ReadAndChargeQuotas"
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
    resources = [aws_dynamodb_table.quotas.arn]
  }

  # 稽核：只能新增（app/audit.py 的 write_audit）。不給 UpdateItem、DeleteItem、GetItem：
  # Gateway 就算被入侵，也改不了、刪不了、讀不到別人的稽核紀錄（E116）
  statement {
    sid       = "AppendAuditRecords"
    effect    = "Allow"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.audit.arn]
  }

  # 用量明細：只有 record_charge() 的交易會寫（SQS 送不進去時的備援，E134），所以只准在交易裡新增（E135 定案 4）
  # quotas、audit 不加這個條件：花錢前的「加 0」與沒花錢的三條路都在交易外面寫
  statement {
    sid       = "InsertUsageInTransaction"
    effect    = "Allow"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.usage.arn]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "dynamodb:EnclosingOperation"
      values   = ["TransactWriteItems"]
    }
  }

  # 成功那一筆送進出單夾（app/events.py 的 send_event）；只准送，不准收、不准刪，也碰不到 DLQ
  statement {
    sid       = "SendChargeEvents"
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.charge.arn]
  }

  # 向 STS 要身分證明去換 OpenAI 的通行證（E113）。這個動作 AWS 規定 Resource 寫 "*"；
  # 用條件鎖住：只准開給 OpenAI 那個 audience、最多 5 分鐘（OpenAI 文件建議的兩個條件）
  statement {
    sid       = "OpenAiWorkloadIdentity"
    effect    = "Allow"
    actions   = ["sts:GetWebIdentityToken"]
    resources = ["*"]

    condition {
      test     = "ForAllValues:StringEquals"
      variable = "sts:IdentityTokenAudience"
      values   = [local.openai_wif_audience]
    }

    condition {
      test     = "NumericLessThanEquals"
      variable = "sts:DurationSeconds"
      values   = ["300"]
    }
  }
}

resource "aws_iam_role_policy" "task" {
  name   = "llm-gateway-task"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task_permissions.json
}
