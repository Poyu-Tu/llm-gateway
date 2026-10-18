# 每日層的帳本放在長期層同一個 bucket 的 daily/ 底下
# destroy 角色只開了這個檔和它的鎖檔（E120）；路徑改了，角色就讀不到
terraform {
  backend "s3" {
    bucket       = "llm-gateway-tfstate-629ceebfae70aa842b70303422"
    key          = "daily/terraform.tfstate"
    region       = "ap-northeast-1"
    encrypt      = true
    use_lockfile = true
  }
}
