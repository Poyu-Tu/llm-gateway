# apply 完印出 AWS 補完的 bucket 全名，下一步「把帳本搬進去」要用
output "tfstate_bucket" {
  description = "Name of the bucket that holds Terraform state"
  value       = aws_s3_bucket.tfstate.bucket
}
