# 每日層「只看不改」的動作清單：destroy 角色與 deploy 角色共用一份（M6）
# Terraform 不管是要拆還是要改，都會先把每日層每一樣東西讀一遍，兩個角色要讀的東西一模一樣；
# 寫在一個地方，以後每日層多一種資源，只要改這裡，兩個角色不會一個有、一個沒有
# 這些 Describe、Get、List 大多不能指定資源，AWS 規定 Resource 只能寫 "*"；動作逐一列出、不寫 Describe*

locals {
  daily_read_actions = [
    # 網路骨架（destroy 第二批）
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
    # NAT、ALB、ECS、DNS 防火牆（destroy 第三批）
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
    # M6：/metrics 的兩條 Listener Rule
    "elasticloadbalancing:DescribeRules",
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
    # Worker（destroy 第四批）
    "lambda:GetFunction",
    "lambda:GetFunctionCodeSigningConfig",
    "lambda:GetPolicy",
    "lambda:ListVersionsByFunction",
    "lambda:GetEventSourceMapping",
    "lambda:ListTags",
  ]

  # /metrics 的通行證（4.3）：本人用 CLI 建的 SecureString，值不進長期層帳本；每日層用 data 讀它
  # 用 AWS 預設的 aws/ssm 金鑰加密，讀的時候不用另外給 kms:Decrypt（跟 Gateway 的三個參數一樣）
  metrics_token_parameter = "${local.ssm_arn_prefix}:parameter/llm-gateway/metrics-token"
}
