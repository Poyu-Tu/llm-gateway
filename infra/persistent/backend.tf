# 帳本（State）不放這台電腦，放進第 5 步建好的 bucket
# 鎖用 S3 自己的鎖檔（use_lockfile），不另外建 DynamoDB 鎖表（E117 定案；DynamoDB 鎖已被 Terraform 標為淘汰）
terraform {
  backend "s3" {
    bucket       = "llm-gateway-tfstate-629ceebfae70aa842b70303422"
    key          = "persistent/terraform.tfstate"
    region       = "ap-northeast-1"
    encrypt      = true
    use_lockfile = true
  }
}
