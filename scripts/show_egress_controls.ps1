# S10：Gateway 對外的兩道管制（E123 定案 6 的驗收畫面）
#   1. 兩條 Gateway Endpoint 的政策：S3 只准拉 ECR 映像層、DynamoDB 只准三張表的讀寫
#   2. DNS 防火牆：名單內放行（優先序 100），其他全部擋（優先序 200）
#   3. 放行名單的網域
# 帳號 ID 一律換成 <account-id>，畫面可以直接截圖
# 用法（repo 根目錄、aws login 之後、每日層 apply 之後）：.\scripts\show_egress_controls.ps1

function Hide-AccountId($text) { $text -replace '\d{12}', '<account-id>' }

Write-Output "== VPC Gateway Endpoints（每日層）=="
$endpoints = aws ec2 describe-vpc-endpoints --filters Name=tag:Layer,Values=daily `
  --query "VpcEndpoints[].[ServiceName,PolicyDocument]" --output json | Out-String | ConvertFrom-Json
$rows = foreach ($endpoint in $endpoints) {
  $policy = $endpoint[1] | ConvertFrom-Json
  [pscustomobject]@{
    Endpoint = $endpoint[0].Split('.')[-1]
    Effect   = ($policy.Statement.Effect | Select-Object -Unique) -join ', '
    Action   = ($policy.Statement.Action) -join ', '
    Resource = Hide-AccountId (($policy.Statement.Resource) -join "`n")
  }
}
$rows | Format-List

Write-Output ""
Write-Output "== Route 53 Resolver DNS Firewall：規則 =="
$group = aws route53resolver list-firewall-rule-groups `
  --query "FirewallRuleGroups[?Name=='llm-gateway-egress'].Id" --output text
aws route53resolver list-firewall-rules --firewall-rule-group-id $group `
  --query "sort_by(FirewallRules,&Priority)[].{Priority:Priority,Name:Name,Action:Action,BlockResponse:BlockResponse}" --output table

Write-Output ""
Write-Output "== 放行名單（llm-gateway-allowed）=="
$list = aws route53resolver list-firewall-domain-lists `
  --query "FirewallDomainLists[?Name=='llm-gateway-allowed'].Id" --output text
$domains = (aws route53resolver list-firewall-domains --firewall-domain-list-id $list --output json | Out-String | ConvertFrom-Json).Domains
$domains | Sort-Object | ForEach-Object { "  " + (Hide-AccountId $_) }
