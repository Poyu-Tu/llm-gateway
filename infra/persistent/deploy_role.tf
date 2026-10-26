# CD 用的角色（M6）：GitHub Actions 的 deploy workflow 借它，換 Gateway 的映像
# 能做的只有三件事：讀每日層（plan 要先看現況）、推映像到 ECR、登記新的任務定義並讓 ECS 服務換過去
# 不能新建、不能刪除任何東西：每日層沒建時 apply 一定被拒絕（安全地失敗）；跟 destroy 角色同一套思路
# 放長期層：角色是「不能限標籤」的東西，destroy 不用拿 iam:DeleteRole

locals {
  # 只有掛 environment deploy 的工作拿得到這個 sub；environment 本身只准 main（GitHub 端設定，本人按）
  deploy_subject = "${local.github_repo_subject}:environment:deploy"

  # 每日層的 ECS 服務：叢集名／服務名都是 llm-gateway（infra/daily/ecs.tf）
  gateway_service_arn = "arn:aws:ecs:${local.account_region}:service/llm-gateway/llm-gateway"

  # 任務定義的每一個版本（llm-gateway:1、:2…）
  gateway_task_definition_arn = "arn:aws:ecs:${local.account_region}:task-definition/llm-gateway:*"
}

# 誰能借這個角色：只有本 repo、掛 environment deploy 的工作；兩個條件都是完全相等，沒有萬用字元
data "aws_iam_policy_document" "deploy_trust" {
  statement {
    sid     = "GitHubDeployEnvironmentOnly"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.deploy_subject]
    }
  }
}

resource "aws_iam_role" "deploy" {
  name                 = "llm-gateway-deploy"
  description          = "Assumed by the GitHub deploy workflow to roll out a new Gateway image"
  assume_role_policy   = data.aws_iam_policy_document.deploy_trust.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "deploy_permissions" {
  # ---- 帳本：跟 destroy 角色一樣，只碰每日層那一份 ----

  statement {
    sid       = "ListStateBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.tfstate.arn]
  }

  statement {
    sid       = "ReadWriteDailyState"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = [local.daily_state_object]
  }

  statement {
    sid       = "LockDailyState"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${local.daily_state_object}.tflock"]
  }

  # ---- 讀每日層：plan 要先把每一樣東西讀一遍，清單跟 destroy 角色共用（daily_read.tf）----

  statement {
    sid       = "ReadDailyLayer"
    effect    = "Allow"
    actions   = local.daily_read_actions
    resources = ["*"]
  }

  statement {
    sid       = "ReadMetricsToken"
    effect    = "Allow"
    actions   = ["ssm:GetParameter"]
    resources = [local.metrics_token_parameter]
  }

  # ---- 推映像 ----

  # 登入 ECR 拿一張推送用的通行證：AWS 規定 Resource 只能寫 "*"（跟 Gateway 執行角色同一條）
  statement {
    sid       = "LoginToEcr"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # 只准推到 llm-gateway 這個倉庫；DescribeImages 用來先查「這個標籤推過沒有」（IMMUTABLE 不准再推一次）
  statement {
    sid    = "PushGatewayImage"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
      "ecr:BatchGetImage",
      "ecr:DescribeImages",
    ]
    resources = [aws_ecr_repository.gateway.arn]
  }

  # ---- 換版：登記新的任務定義、讓服務換過去 ----

  # 登記任務定義：AWS 規定 Resource 只能寫 "*"（登記之前還沒有 ARN）
  statement {
    sid       = "RegisterTaskDefinition"
    effect    = "Allow"
    actions   = ["ecs:RegisterTaskDefinition"]
    resources = ["*"]
  }

  # 登記時順手貼上 default_tags（Layer = daily）：只准在「登記這個動作」裡貼，不能拿去改別的東西的標籤
  statement {
    sid       = "TagNewTaskDefinition"
    effect    = "Allow"
    actions   = ["ecs:TagResource"]
    resources = [local.gateway_task_definition_arn]

    condition {
      test     = "StringEquals"
      variable = "ecs:CreateAction"
      values   = ["RegisterTaskDefinition"]
    }
  }

  # 新的任務定義要寫明用哪兩個角色，登記的人要有「把角色交給 ECS」的權限
  # 只准這兩個角色、只准交給 ECS 的任務，不能拿去給 EC2、Lambda
  statement {
    sid       = "PassGatewayRoles"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.task_execution.arn, aws_iam_role.task.arn]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }

  # 讓服務換到新的任務定義：只限這一個服務，而且要貼著 Layer = daily
  statement {
    sid       = "UpdateGatewayService"
    effect    = "Allow"
    actions   = ["ecs:UpdateService"]
    resources = [local.gateway_service_arn]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Layer"
      values   = ["daily"]
    }
  }

  # ---- 明文 Deny：不准給自己加權限、改信任條件、把自己刪掉 ----
  statement {
    sid    = "DenySelfChange"
    effect = "Deny"
    actions = [
      "iam:DeleteRole",
      "iam:UpdateRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:PutRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:AttachRolePolicy",
      "iam:DetachRolePolicy",
      "iam:PutRolePermissionsBoundary",
      "iam:DeleteRolePermissionsBoundary",
    ]
    resources = [aws_iam_role.deploy.arn]
  }
}

resource "aws_iam_role_policy" "deploy" {
  name   = "llm-gateway-deploy"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.deploy_permissions.json
}
