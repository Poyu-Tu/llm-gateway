# destroy 角色的權限模擬器（E123 定案 5：第三批，NAT／ALB／ECS／DNS 防火牆的拆除，與保護長期層的 Deny；
# E124 補第 11、12 題：拔公開 IP 不能限標籤、刪公開 IP 仍限 daily；
# M6 補第 13～16 題：拆 /metrics 的規則、讀通行證只限那一個參數、deploy 角色碰不到）
# 用 IAM 的 simulate-principal-policy 問 AWS：「這個角色能不能對這個東西做這件事？」，不會真的動到任何資源
# 標籤用 --context-entries 餵 aws:ResourceTag/Layer（模擬器不會自己去看資源身上真正的標籤）
# 用法（repo 根目錄、aws login 之後）：.\scripts\simulate_destroy_role.ps1
# 畫面只印題目與結果，不印帳號 ID 與 ARN

$acct = aws sts get-caller-identity --query Account --output text
$role = terraform "-chdir=infra/persistent" output -raw destroy_role_arn
$queryLog = terraform "-chdir=infra/persistent" output -raw dns_query_log_config_id
$p = "ap-northeast-1:${acct}"

function Test-Destroy($action, $resource, $layer) {
  $context = @()
  if ($layer) {
    $context = @('--context-entries', "ContextKeyName=aws:ResourceTag/Layer,ContextKeyValues=$layer,ContextKeyType=string")
  }
  aws iam simulate-principal-policy --policy-source-arn $role --action-names $action --resource-arns $resource @context `
    --query "EvaluationResults[0].EvalDecision" --output text
}

# 題號、題目、動作、資源、標籤（空字串 = 沒標籤）、預期
$cases = @(
  @(1,  '拆 NAT（daily）',               'ec2:DeleteNatGateway',                          "arn:aws:ec2:${p}:natgateway/nat-test",                                   'daily',      'allowed'),
  @(2,  '拆 ALB（daily）',               'elasticloadbalancing:DeleteLoadBalancer',       "arn:aws:elasticloadbalancing:${p}:loadbalancer/app/test/0123456789abcdef", 'daily',      'allowed'),
  @(3,  '拆 ALB（沒標籤）',              'elasticloadbalancing:DeleteLoadBalancer',       "arn:aws:elasticloadbalancing:${p}:loadbalancer/app/test/0123456789abcdef", '',           'implicitDeny'),
  @(4,  '拆 ECS 叢集（daily）',          'ecs:DeleteCluster',                             "arn:aws:ecs:${p}:cluster/test",                                          'daily',      'allowed'),
  @(5,  '拆 DNS 防火牆規則群組（persistent）', 'route53resolver:DeleteFirewallRuleGroup', "arn:aws:route53resolver:${p}:firewall-rule-group/rslvr-frg-test",       'persistent', 'implicitDeny'),
  @(6,  '刪 Gateway 的任務角色',         'iam:DeleteRole',                                "arn:aws:iam::${acct}:role/llm-gateway-task",                             '',           'explicitDeny'),
  @(7,  '刪告警的 SNS 主題',             'sns:DeleteTopic',                               "arn:aws:sns:${p}:llm-gateway-alerts",                                    '',           'explicitDeny'),
  @(8,  '刪 Gateway 的日誌群組',         'logs:DeleteLogGroup',                           "arn:aws:logs:${p}:log-group:/ecs/llm-gateway:*",                          '',           'explicitDeny'),
  @(9,  '刪 DNS 查詢日誌設定',           'route53resolver:DeleteResolverQueryLogConfig',  "arn:aws:route53resolver:${p}:resolver-query-log-config/$queryLog",       '',           'explicitDeny'),
  @(10, '把查詢日誌從 VPC 拆開',         'route53resolver:DisassociateResolverQueryLogConfig', "arn:aws:route53resolver:${p}:resolver-query-log-config/$queryLog",  '',           'allowed'),
  @(11, '把公開 IP 從機器上拔下來',      'ec2:DisassociateAddress',                       '*',                                                                      '',           'allowed'),
  @(12, '刪公開 IP（沒標籤）',           'ec2:ReleaseAddress',                            "arn:aws:ec2:${p}:elastic-ip/eipalloc-test",                              '',           'implicitDeny'),
  @(13, '拆 /metrics 的規則（daily）',   'elasticloadbalancing:DeleteRule',               "arn:aws:elasticloadbalancing:${p}:listener-rule/app/test/0123456789abcdef/0123456789abcdef/0123456789abcdef", 'daily', 'allowed'),
  @(14, '讀 /metrics 的通行證',          'ssm:GetParameter',                              "arn:aws:ssm:${p}:parameter/llm-gateway/metrics-token",                   '',           'allowed'),
  @(15, '讀稽核的 HMAC 金鑰',            'ssm:GetParameter',                              "arn:aws:ssm:${p}:parameter/llm-gateway/audit-hmac-key",                  '',           'implicitDeny'),
  @(16, '刪 deploy 角色',                'iam:DeleteRole',                                "arn:aws:iam::${acct}:role/llm-gateway-deploy",                           '',           'explicitDeny')
)

$cases | ForEach-Object {
  $result = Test-Destroy $_[2] $_[3] $_[4]
  [pscustomobject]@{
    '#'      = $_[0]
    Question = $_[1]
    Expected = $_[5]
    Result   = $result
    Match    = $(if ($result -eq $_[5]) { 'O' } else { 'X' })
  }
} | Format-Table -AutoSize
