# 連東京區；這一層建的每樣東西都自動貼三張標籤
# Layer = "daily" 不只是給人看的：destroy 角色的刪除權限只准刪貼著這張標籤的東西（E121）
provider "aws" {
  region = "ap-northeast-1"

  default_tags {
    tags = {
      Project   = "llm-gateway"
      Layer     = "daily"
      ManagedBy = "terraform"
    }
  }
}
