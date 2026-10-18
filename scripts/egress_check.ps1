# S08 出口測試（E123 定案 6）：用 Gateway 同一個任務定義、同一個私有子網與安全群組，
# 臨時把啟動指令換成一小段 Python（scripts/egress_check.json），試著查詢並連線兩個網域：
#   api.openai.com（在放行清單）、example.com（不在清單）
# 結果印進 CloudWatch 日誌群組 /ecs/llm-gateway；DNS 防火牆的判斷記在 /llm-gateway/dns-queries
# 用法（repo 根目錄、aws login 之後）：.\scripts\egress_check.ps1
# 印出的是這次任務的 ARN；任務跑完幾秒就自己結束，不會一直計費

$tf = "infra/daily"
$cluster = terraform -chdir=$tf output -raw ecs_cluster_name
$taskdef = terraform -chdir=$tf output -raw task_definition
$subnet = terraform -chdir=$tf output -raw private_subnet_id
$sg = terraform -chdir=$tf output -raw gateway_security_group_id

# 跟 Gateway 一樣：沒有公開 IP，對外只能走 NAT，查網域要過 DNS 防火牆
aws ecs run-task --cluster $cluster --task-definition $taskdef --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[$subnet],securityGroups=[$sg],assignPublicIp=DISABLED}" `
  --overrides file://scripts/egress_check.json `
  --query "tasks[0].taskArn" --output text
