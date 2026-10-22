# GitHub Actions 向 AWS 借臨時身分的鑰匙（OIDC）。放在長期層：destroy 不能把自己的鑰匙也拆掉
# 第一批只開「讀寫每日層的帳本」（E120 定案 2）；
# 第二批加拆每日層骨架的權限（E121）；
# 第三批加拆 D 段（NAT、DNS 防火牆、ALB、ECS）的權限（E123）；
# 第四批加拆 Worker（Lambda 與 SQS 觸發）的權限（E135）

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

  # 第三批（E123）：D 段會跳錶的東西。一樣只限本帳號、東京區、這幾種，再加 Layer = daily 標籤條件
  account_region = "ap-northeast-1:${data.aws_caller_identity.current.account_id}"
  daily_runtime_resources = [
    "${local.daily_ec2_arn_prefix}:natgateway/*",
    "${local.daily_ec2_arn_prefix}:elastic-ip/*",
    "arn:aws:elasticloadbalancing:${local.account_region}:loadbalancer/app/*",
    "arn:aws:elasticloadbalancing:${local.account_region}:listener/app/*",
    "arn:aws:elasticloadbalancing:${local.account_region}:targetgroup/*",
    "arn:aws:ecs:${local.account_region}:cluster/*",
    "arn:aws:ecs:${local.account_region}:service/*",
    "arn:aws:route53resolver:${local.account_region}:firewall-domain-list/*",
    "arn:aws:route53resolver:${local.account_region}:firewall-rule-group/*",
    "arn:aws:route53resolver:${local.account_region}:firewall-rule-group-association/*",
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

  # ---- 第三批（E123）：拆 D 段（NAT、彈性 IP、DNS 防火牆、ALB、ECS）----

  # 一樣先看現況。這幾個服務的 Describe、List 有的不能指定資源；只看不改，全部寫 "*"
  # （跟 DescribeDailyNetwork 同一個做法，動作逐一列出）
  statement {
    sid    = "DescribeDailyRuntime"
    effect = "Allow"
    actions = [
      "ec2:DescribeNatGateways",
      "ec2:DescribeAddresses",
      "ec2:DescribeAddressesAttribute",
      "elasticloadbalancing:DescribeLoadBalancers",
      "elasticloadbalancing:DescribeLoadBalancerAttributes",
      "elasticloadbalancing:DescribeListeners",
      "elasticloadbalancing:DescribeListenerAttributes",
      "elasticloadbalancing:DescribeTargetGroups",
      "elasticloadbalancing:DescribeTargetGroupAttributes",
      "elasticloadbalancing:DescribeTags",
      "elasticloadbalancing:DescribeCapacityReservation",
      "ecs:DescribeClusters",
      "ecs:DescribeServices",
      "ecs:DescribeTaskDefinition",
      "ecs:ListTagsForResource",
      "route53resolver:GetFirewallDomainList",
      "route53resolver:ListFirewallDomains",
      "route53resolver:GetFirewallRuleGroup",
      "route53resolver:ListFirewallRules",
      "route53resolver:GetFirewallRuleGroupAssociation",
      "route53resolver:ListResolverQueryLogConfigs",
      "route53resolver:GetResolverQueryLogConfig",
      "route53resolver:GetResolverQueryLogConfigAssociation",
      "route53resolver:ListTagsForResource",
    ]
    resources = ["*"]
  }

  # 一樣只准刪貼著 Layer = daily 的東西；不給任何 Create*、Tag*
  # 任務定義不在這裡：它設了 skip_destroy，拆的時候不去 AWS 註銷（E123 定案 7）
  statement {
    sid    = "DeleteDailyRuntime"
    effect = "Allow"
    actions = [
      "ec2:DeleteNatGateway",
      "ec2:ReleaseAddress",
      "elasticloadbalancing:DeleteListener",
      "elasticloadbalancing:DeleteLoadBalancer",
      "elasticloadbalancing:DeleteTargetGroup",
      # 刪服務前 Terraform 先把任務數改成 0（UpdateService），等任務都停了才刪
      "ecs:UpdateService",
      "ecs:DeleteService",
      "ecs:DeleteCluster",
      "route53resolver:DisassociateFirewallRuleGroup",
      "route53resolver:DeleteFirewallRule",
      "route53resolver:DeleteFirewallRuleGroup",
      "route53resolver:DeleteFirewallDomainList",
    ]
    resources = local.daily_runtime_resources

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Layer"
      values   = ["daily"]
    }
  }

  # 把公開 IP 從 NAT 上拔下來（E124）：Terraform 拆 EIP 前一定先呼叫 DisassociateAddress
  # AWS 檢查這個動作時看不到是哪一個 IP（資源是 */*），也就沒有標籤可比；
  # 放在上面那條（限 Layer = daily）條件永遠不成立，destroy #2 就卡在這裡
  # 只能寫 "*"、不加條件。代價：拆除組能把帳號裡任何一個公開 IP 從機器上拔下來，
  # 但刪不掉（ReleaseAddress 仍限 daily）；這個帳號只有本專題的 IP
  statement {
    sid       = "DisassociateAnyAddress"
    effect    = "Allow"
    actions   = ["ec2:DisassociateAddress"]
    resources = ["*"]
  }

  # DNS 查詢日誌的設定在長期層（貼的是 persistent），每日層只有「接上 VPC」那條線
  # 只准拆那條線、只限這一個設定；刪設定本身在下面明文 Deny
  statement {
    sid       = "DetachDnsQueryLogging"
    effect    = "Allow"
    actions   = ["route53resolver:DisassociateResolverQueryLogConfig"]
    resources = [aws_route53_resolver_query_log_config.dns.arn]
  }

  # ---- 第四批（E135）：拆 Worker（Lambda 函式與 SQS 觸發）----

  # 拆之前先看現況：只看不改，寫 "*"（跟前兩批的 Describe 同一個做法）
  statement {
    sid    = "DescribeDailyWorker"
    effect = "Allow"
    actions = [
      "lambda:GetFunction",
      "lambda:GetFunctionCodeSigningConfig",
      "lambda:GetPolicy",
      "lambda:ListVersionsByFunction",
      "lambda:GetEventSourceMapping",
      "lambda:ListTags",
    ]
    resources = ["*"]
  }

  # 刪函式：只准刪貼著 Layer = daily 的
  statement {
    sid       = "DeleteDailyWorker"
    effect    = "Allow"
    actions   = ["lambda:DeleteFunction"]
    resources = ["arn:aws:lambda:${local.account_region}:function:*"]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Layer"
      values   = ["daily"]
    }
  }

  # 刪觸發：不靠標籤，改看「這條觸發接的是哪個函式」，只限 Worker 那一個
  statement {
    sid       = "DeleteWorkerTrigger"
    effect    = "Allow"
    actions   = ["lambda:DeleteEventSourceMapping"]
    resources = ["arn:aws:lambda:${local.account_region}:event-source-mapping:*"]

    condition {
      test     = "ArnEquals"
      variable = "lambda:FunctionArn"
      values   = [local.worker_function_arn]
    }
  }

  # ---- 以下是明文 Deny：之後不管加了什麼允許，長期層都碰不到（Deny 一定贏過 Allow）----

  # 四張表：不准刪表、不准關刪除保護（UpdateTable）、不准關時光機、不准改資料
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
      aws_dynamodb_table.usage.arn,
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

  # 第三批（E123）：Gateway 的兩個角色、告警、日誌、DNS 查詢日誌的設定，一樣碰不到
  # 第四批（E135）：Worker 的角色、記帳失敗告警、Worker 日誌、兩個佇列，一樣碰不到
  statement {
    sid    = "DenyGatewayRolesChange"
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
    resources = [
      aws_iam_role.task_execution.arn,
      aws_iam_role.task.arn,
      aws_iam_role.worker.arn,
    ]
  }

  statement {
    sid    = "DenyAlertsChange"
    effect = "Deny"
    actions = [
      "sns:DeleteTopic",
      "sns:SetTopicAttributes",
      "sns:AddPermission",
      "sns:RemovePermission",
      "cloudwatch:DeleteAlarms",
      "cloudwatch:PutMetricAlarm",
      "cloudwatch:DisableAlarmActions",
    ]
    resources = [
      aws_sns_topic.alerts.arn,
      aws_cloudwatch_metric_alarm.audit_write_failed.arn,
      aws_cloudwatch_metric_alarm.charge_queue_failed.arn,
    ]
  }

  statement {
    sid    = "DenyPersistentLogsChange"
    effect = "Deny"
    actions = [
      "logs:DeleteLogGroup",
      "logs:PutRetentionPolicy",
      "logs:DeleteRetentionPolicy",
      "logs:PutMetricFilter",
      "logs:DeleteMetricFilter",
    ]
    # 日誌群組的 ARN 在 IAM 裡有兩種寫法（結尾有沒有 :*），兩種都列，Deny 才不會漏
    resources = [
      aws_cloudwatch_log_group.gateway.arn,
      "${aws_cloudwatch_log_group.gateway.arn}:*",
      aws_cloudwatch_log_group.dns_queries.arn,
      "${aws_cloudwatch_log_group.dns_queries.arn}:*",
      aws_cloudwatch_log_group.worker.arn,
      "${aws_cloudwatch_log_group.worker.arn}:*",
    ]
  }

  statement {
    sid       = "DenyQueryLogConfigDelete"
    effect    = "Deny"
    actions   = ["route53resolver:DeleteResolverQueryLogConfig"]
    resources = [aws_route53_resolver_query_log_config.dns.arn]
  }

  # 出單夾與問題單抽屜：不准刪佇列、改設定（含 DLQ 次數、加密、抽屜收誰的單）、改存取政策、清空、一張張拿單銷單
  statement {
    sid    = "DenyChargeQueues"
    effect = "Deny"
    actions = [
      "sqs:DeleteQueue",
      "sqs:SetQueueAttributes",
      "sqs:AddPermission",
      "sqs:RemovePermission",
      "sqs:PurgeQueue",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
    ]
    resources = [aws_sqs_queue.charge_dlq.arn, aws_sqs_queue.charge.arn]
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
