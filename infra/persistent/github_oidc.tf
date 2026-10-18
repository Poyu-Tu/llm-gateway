# GitHub Actions 向 AWS 借臨時身分的鑰匙（OIDC）。放在長期層：destroy 不能把自己的鑰匙也拆掉
# 第一批只開「讀寫每日層的帳本」（E120 定案 2）；第二批加拆每日層骨架的權限（E121）

locals {
  # GitHub 2026/7/15 之後建立的 repo，身分證明的 sub 是「名字@編號」的新格式（本 repo 9/29 建立）
  # 兩個編號是公開資訊：https://api.github.com/repos/Poyu-Tu/llm-gateway 的 owner.id 與 id
  github_repo_subject = "repo:Poyu-Tu@62129723/llm-gateway@1394630828"

  # 只有掛 environment destroy 的工作拿得到這個 sub；environment 本身只准 main（GitHub 端設定）
  destroy_subject = "${local.github_repo_subject}:environment:destroy"

  # 每日層的帳本與鎖檔，路徑寫死、不用萬用字元
  daily_state_object = "${aws_s3_bucket.tfstate.arn}/daily/terraform.tfstate"

  # 長期層的帳本與鎖檔：明文 Deny 用
  persistent_state_object = "${aws_s3_bucket.tfstate.arn}/persistent/terraform.tfstate"

  # 每日層骨架的資源種類（E121）：只限本帳號、東京區、這幾種；再加 Layer = daily 標籤條件
  daily_ec2_arn_prefix = "arn:aws:ec2:ap-northeast-1:${data.aws_caller_identity.current.account_id}"
  daily_network_resources = [
    "${local.daily_ec2_arn_prefix}:vpc/*",
    "${local.daily_ec2_arn_prefix}:subnet/*",
    "${local.daily_ec2_arn_prefix}:route-table/*",
    "${local.daily_ec2_arn_prefix}:internet-gateway/*",
    "${local.daily_ec2_arn_prefix}:security-group/*",
    "${local.daily_ec2_arn_prefix}:security-group-rule/*",
    "${local.daily_ec2_arn_prefix}:vpc-endpoint/*",
  ]
}

# 帳號 ID 向 AWS 問「我是誰」就知道，不用寫進 repo
data "aws_caller_identity" "current" {}

# 讓 AWS 認得「GitHub Actions 開的身分證明」
# 不寫 thumbprint_list：AWS 驗證 GitHub 的證明改用自己信任的憑證機構，指紋已不使用
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

# 誰能借這個角色：只有本 repo、掛 environment destroy 的工作；兩個條件都是完全相等，沒有萬用字元
data "aws_iam_policy_document" "destroy_trust" {
  statement {
    sid     = "GitHubDestroyEnvironmentOnly"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    # 證明是開給 AWS STS 用的，不是開給別的服務
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # 證明上寫的是哪個 repo、哪個 environment
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.destroy_subject]
    }
  }
}

# destroy workflow 用的角色；借一次最多 1 小時
resource "aws_iam_role" "destroy" {
  name                 = "llm-gateway-destroy"
  description          = "Assumed by the GitHub destroy workflow to tear down the daily layer"
  assume_role_policy   = data.aws_iam_policy_document.destroy_trust.json
  max_session_duration = 3600
}

# 角色能做什麼：上半段是允許（只碰每日層的帳本），下半段是明文 Deny（長期層一律不准碰）
data "aws_iam_policy_document" "destroy_permissions" {
  # Terraform init 要列出 bucket 裡的檔名；檔名不是秘密，不加前綴條件（加錯會讓 init 失敗）
  statement {
    sid       = "ListStateBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.tfstate.arn]
  }

  # 讀寫每日層的帳本（帳本本身不需要刪除權限）
  statement {
    sid       = "ReadWriteDailyState"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = [local.daily_state_object]
  }

  # 每日層的鎖檔：上鎖是寫、解鎖是刪
  statement {
    sid       = "LockDailyState"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${local.daily_state_object}.tflock"]
  }

  # ---- 第二批（E121）：拆每日層的骨架（VPC、子網、大門、路由表、安全群組、Gateway Endpoint）----

  # 拆之前要先看現況。EC2 的 Describe 不能指定資源，AWS 規定 Resource 只能寫 "*"
  # 動作逐一列出、不寫 ec2:Describe*（E121 定案 2）；缺哪個，destroy 的錯誤訊息會寫出來，再補
  statement {
    sid    = "DescribeDailyNetwork"
    effect = "Allow"
    actions = [
      "ec2:DescribeVpcs",
      "ec2:DescribeVpcAttribute",
      "ec2:DescribeSubnets",
      "ec2:DescribeRouteTables",
      "ec2:DescribeInternetGateways",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSecurityGroupRules",
      "ec2:DescribeNetworkAcls",
      "ec2:DescribeVpcEndpoints",
      "ec2:DescribePrefixLists",
      "ec2:DescribeNetworkInterfaces",
    ]
    resources = ["*"]
  }

  # 只准刪貼著 Layer = daily 的東西（每日層的 default_tags 會自動貼）
  # 卸大門（DetachInternetGateway）會同時檢查大門與 VPC 兩邊的標籤
  # 刻意不給任何 Create*、CreateTags：拆除組不能蓋東西，也不能把別的東西改貼成 daily 再刪
  statement {
    sid    = "DeleteDailyNetwork"
    effect = "Allow"
    actions = [
      "ec2:DeleteVpc",
      "ec2:DeleteSubnet",
      "ec2:DeleteRouteTable",
      "ec2:DisassociateRouteTable",
      "ec2:DeleteRoute",
      "ec2:DetachInternetGateway",
      "ec2:DeleteInternetGateway",
      "ec2:DeleteSecurityGroup",
      "ec2:RevokeSecurityGroupIngress",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:DeleteVpcEndpoints",
    ]
    # 每個 ID 事先不知道（每次 apply 都不同），所以種類後面是 *；真正的範圍由下面的標籤條件決定
    resources = local.daily_network_resources

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Layer"
      values   = ["daily"]
    }
  }

  # ---- 以下是明文 Deny：之後不管加了什麼允許，長期層都碰不到（Deny 一定贏過 Allow）----

  # 三張表：不准刪表、不准關刪除保護（UpdateTable）、不准關時光機、不准改資料
  statement {
    sid    = "DenyPersistentTables"
    effect = "Deny"
    actions = [
      "dynamodb:DeleteTable",
      "dynamodb:UpdateTable",
      "dynamodb:UpdateContinuousBackups",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:BatchWriteItem",
    ]
    resources = [
      aws_dynamodb_table.api_keys.arn,
      aws_dynamodb_table.quotas.arn,
      aws_dynamodb_table.audit.arn,
    ]
  }

  # 帳本 bucket 本身：不准刪、不准改政策、版本控制、加密、封鎖公開、生命週期
  statement {
    sid    = "DenyStateBucketSettings"
    effect = "Deny"
    actions = [
      "s3:DeleteBucket",
      "s3:PutBucketPolicy",
      "s3:DeleteBucketPolicy",
      "s3:PutBucketVersioning",
      "s3:PutEncryptionConfiguration",
      "s3:PutBucketPublicAccessBlock",
      "s3:PutLifecycleConfiguration",
    ]
    resources = [aws_s3_bucket.tfstate.arn]
  }

  # 長期層的帳本與鎖檔：不准寫、不准刪（含舊版本）
  statement {
    sid    = "DenyPersistentState"
    effect = "Deny"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
    ]
    resources = [
      local.persistent_state_object,
      "${local.persistent_state_object}.tflock",
    ]
  }

  # 映像倉庫：不准刪倉庫、刪映像、改政策與生命週期、改成可覆蓋標籤
  statement {
    sid    = "DenyEcrRepository"
    effect = "Deny"
    actions = [
      "ecr:DeleteRepository",
      "ecr:BatchDeleteImage",
      "ecr:SetRepositoryPolicy",
      "ecr:DeleteRepositoryPolicy",
      "ecr:PutLifecyclePolicy",
      "ecr:DeleteLifecyclePolicy",
      "ecr:PutImageTagMutability",
    ]
    resources = [aws_ecr_repository.gateway.arn]
  }

  # 角色自己與 OIDC 提供者：不准給自己加權限、改信任條件、把自己刪掉
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
    resources = [aws_iam_role.destroy.arn]
  }

  statement {
    sid    = "DenyOidcProviderChange"
    effect = "Deny"
    actions = [
      "iam:DeleteOpenIDConnectProvider",
      "iam:UpdateOpenIDConnectProviderThumbprint",
      "iam:AddClientIDToOpenIDConnectProvider",
      "iam:RemoveClientIDFromOpenIDConnectProvider",
    ]
    resources = [aws_iam_openid_connect_provider.github.arn]
  }
}

# 權限直接掛在角色上（inline）：角色刪掉，權限跟著消失，不會留下沒人用的政策
resource "aws_iam_role_policy" "destroy" {
  name   = "llm-gateway-destroy"
  role   = aws_iam_role.destroy.id
  policy = data.aws_iam_policy_document.destroy_permissions.json
}
