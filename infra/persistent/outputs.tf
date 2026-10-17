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
  }
}

# destroy workflow 要借的角色；值含帳號 ID，存進 GitHub 的 repository secret（公開的 log 會遮掉）
output "destroy_role_arn" {
  description = "ARN of the role the GitHub destroy workflow assumes"
  value       = aws_iam_role.destroy.arn
}
