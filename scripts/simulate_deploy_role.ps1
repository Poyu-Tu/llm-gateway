# deploy 角色的權限模擬器（M6）：CD 只能讀寫每日層帳本、推映像、登記任務定義、讓服務換版；其他一律不行
# 用 IAM 的 simulate-principal-policy 問 AWS：「這個角色能不能對這個東西做這件事？」，不會真的動到任何資源
# 條件用 --context-entries 餵（模擬器不會自己去看資源身上真正的標籤，也不知道是哪個動作順手貼標籤）
# 用法（repo 根目錄、aws login 之後）：.\scripts\simulate_deploy_role.ps1
# 畫面只印題目與結果，不印帳號 ID 與 ARN

$acct = aws sts get-caller-identity --query Account --output text
$role = terraform "-chdir=infra/persistent" output -raw deploy_role_arn
$bucket = terraform "-chdir=infra/persistent" output -raw tfstate_bucket
$p = "ap-northeast-1:${acct}"

# 三種條件的寫法（空字串 = 不餵）
$daily  = 'ContextKeyName=aws:ResourceTag/Layer,ContextKeyValues=daily,ContextKeyType=string'
$create = 'ContextKeyName=ecs:CreateAction,ContextKeyValues=RegisterTaskDefinition,ContextKeyType=string'
$toEcs  = 'ContextKeyName=iam:PassedToService,ContextKeyValues=ecs-tasks.amazonaws.com,ContextKeyType=string'
$toLam  = 'ContextKeyName=iam:PassedToService,ContextKeyValues=lambda.amazonaws.com,ContextKeyType=string'

function Test-Deploy($action, $resource, $entry) {
  $context = @()
  if ($entry) { $context = @('--context-entries', $entry) }
  aws iam simulate-principal-policy --policy-source-arn $role --action-names $action --resource-arns $resource @context `
    --query "EvaluationResults[0].EvalDecision" --output text
}

$repo    = "arn:aws:ecr:${p}:repository/llm-gateway"
$taskDef = "arn:aws:ecs:${p}:task-definition/llm-gateway:99"
$service = "arn:aws:ecs:${p}:service/llm-gateway/llm-gateway"
$taskRole = "arn:aws:iam::${acct}:role/llm-gateway-task"

# 題號、題目、動作、資源、條件、預期
$cases = @(
  @(1,  '推映像到 llm-gateway',            'ecr:PutImage',                    $repo,                                              '',      'allowed'),
  @(2,  '推映像到別的倉庫',                'ecr:PutImage',                    "arn:aws:ecr:${p}:repository/other",                '',      'implicitDeny'),
  @(3,  '登記任務定義',                    'ecs:RegisterTaskDefinition',      '*',                                                '',      'allowed'),
  @(4,  '登記時貼標籤',                    'ecs:TagResource',                 $taskDef,                                           $create, 'allowed'),
  @(5,  '事後改任務定義的標籤',            'ecs:TagResource',                 $taskDef,                                           '',      'implicitDeny'),
  @(6,  '把任務角色交給 ECS',              'iam:PassRole',                    $taskRole,                                          $toEcs,  'allowed'),
  @(7,  '把任務角色交給 Lambda',           'iam:PassRole',                    $taskRole,                                          $toLam,  'implicitDeny'),
  @(8,  '把 Worker 角色交給 ECS',          'iam:PassRole',                    "arn:aws:iam::${acct}:role/llm-gateway-charge-worker",     $toEcs,  'implicitDeny'),
  @(9,  '服務換版（daily）',               'ecs:UpdateService',               $service,                                           $daily,  'allowed'),
  @(10, '服務換版（沒標籤）',              'ecs:UpdateService',               $service,                                           '',      'implicitDeny'),
  @(11, '刪 ECS 服務（daily）',            'ecs:DeleteService',               $service,                                           $daily,  'implicitDeny'),
  @(12, '建新的 ECS 服務',                 'ecs:CreateService',               $service,                                           '',      'implicitDeny'),
  @(13, '建 VPC（每日層沒建時）',          'ec2:CreateVpc',                   "arn:aws:ec2:${p}:vpc/*",                           '',      'implicitDeny'),
  @(14, '改安全群組放行（daily）',         'ec2:AuthorizeSecurityGroupIngress', "arn:aws:ec2:${p}:security-group/sg-test",        $daily,  'implicitDeny'),
  @(15, '改 Worker 的程式',                'lambda:UpdateFunctionCode',       "arn:aws:lambda:${p}:function:llm-gateway-charge-worker",  $daily,  'implicitDeny'),
  @(16, '改 /metrics 的規則',              'elasticloadbalancing:ModifyRule', "arn:aws:elasticloadbalancing:${p}:listener-rule/app/test/0123456789abcdef/0123456789abcdef/0123456789abcdef", $daily, 'implicitDeny'),
  @(17, '讀 /metrics 的通行證',            'ssm:GetParameter',                "arn:aws:ssm:${p}:parameter/llm-gateway/metrics-token",  '',  'allowed'),
  @(18, '讀稽核的 HMAC 金鑰',              'ssm:GetParameter',                "arn:aws:ssm:${p}:parameter/llm-gateway/audit-hmac-key", '',  'implicitDeny'),
  @(19, '給自己加權限',                    'iam:PutRolePolicy',               $role,                                              '',      'explicitDeny'),
  @(20, '讀每日層的帳本',                  's3:GetObject',                    "arn:aws:s3:::${bucket}/daily/terraform.tfstate",   '',      'allowed'),
  @(21, '寫每日層的帳本',                  's3:PutObject',                    "arn:aws:s3:::${bucket}/daily/terraform.tfstate",   '',      'allowed'),
  @(22, '寫長期層的帳本',                  's3:PutObject',                    "arn:aws:s3:::${bucket}/persistent/terraform.tfstate", '',   'implicitDeny')
)

$cases | ForEach-Object {
  $result = Test-Deploy $_[2] $_[3] $_[4]
  [pscustomobject]@{
    '#'      = $_[0]
    Question = $_[1]
    Expected = $_[5]
    Result   = $result
    Match    = $(if ($result -eq $_[5]) { 'O' } else { 'X' })
  }
} | Format-Table -AutoSize
