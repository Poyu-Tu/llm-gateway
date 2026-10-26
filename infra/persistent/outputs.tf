# apply 完印出 AWS 補完的 bucket 全名，下一步「把帳本搬進去」要用
output "tfstate_bucket" {
  description = "Name of the bucket that holds Terraform state"
  value       = aws_s3_bucket.tfstate.bucket
}

# docker push 要推到這個網址；之後 ECS 的任務定義也要用
output "ecr_repository_url" {
  description = "URL to push the Gateway image to"
  value       = aws_ecr_repository.gateway.repository_url
}

# 之後寫 IAM 政策時，用這些 ARN 指定「只准碰這幾張表」
output "dynamodb_table_arns" {
  description = "ARNs of the Gateway tables"
  value = {
    api_keys = aws_dynamodb_table.api_keys.arn
    quotas   = aws_dynamodb_table.quotas.arn
    audit    = aws_dynamodb_table.audit.arn
    usage    = aws_dynamodb_table.usage.arn
  }
}

# destroy workflow 要借的角色；值含帳號 ID，存進 GitHub 的 repository secret（公開的 log 會遮掉）
output "destroy_role_arn" {
  description = "ARN of the role the GitHub destroy workflow assumes"
  value       = aws_iam_role.destroy.arn
}

# 每日層的 ECS 任務定義要用這兩個角色；ARN 含帳號 ID，每日層用名字自己組，這裡印出來給人核對
output "task_execution_role_arn" {
  description = "ARN of the role ECS uses to start the Gateway task"
  value       = aws_iam_role.task_execution.arn
}

# OpenAI 那邊的服務帳號對應，sub 要填這個（E123）
output "task_role_arn" {
  description = "ARN of the role the Gateway code runs as (the sub OpenAI maps to gateway-wif)"
  value       = aws_iam_role.task.arn
}

# 本人用 CLI 訂閱 Email 時要用
output "alerts_topic_arn" {
  description = "ARN of the SNS topic the alarms publish to"
  value       = aws_sns_topic.alerts.arn
}

# 每日層把 DNS 查詢日誌接到 VPC 時要用（每日層用名字查不到它，所以在這裡印出 ID 給人核對）
output "dns_query_log_config_id" {
  description = "ID of the Resolver query log configuration the daily VPC is attached to"
  value       = aws_route53_resolver_query_log_config.dns.id
}

# 每日層 ECS 的環境變數 CHARGE_QUEUE_URL 要填這個；網址含帳號 ID，只印出給人核對，不寫進任何紀錄
output "charge_queue_url" {
  description = "URL of the queue the Gateway sends charge events to"
  value       = aws_sqs_queue.charge.url
}

# 每日層的 Worker Lambda 用這個角色；ARN 含帳號 ID，每日層用名字自己組，這裡印出來給人核對
output "worker_role_arn" {
  description = "ARN of the role the charge Worker Lambda runs as"
  value       = aws_iam_role.worker.arn
}

# deploy workflow 要借的角色；值含帳號 ID，存進 GitHub environment deploy 的 secret（公開的 log 會遮掉）
output "deploy_role_arn" {
  description = "ARN of the role the GitHub deploy workflow assumes"
  value       = aws_iam_role.deploy.arn
}
