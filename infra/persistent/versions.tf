# Terraform 本體與外掛的版本都寫死（D19）：同一份設定一個月後跑，結果要一樣
terraform {
  # 1.16.x 都可以（之後升 1.16.6 不用改），但不會自己跳到 1.17
  required_version = "~> 1.16.5"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # 6.68.0：10/7 發佈，已過 3 天冷卻期（6.69.0 是 10/14，還沒過）
      version = "= 6.68.0"
    }
  }
}
