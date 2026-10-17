# 連東京區；這一層建的每樣東西都自動貼三張標籤，帳單和主控台一眼看得出是誰的
provider "aws" {
  region = "ap-northeast-1"

  default_tags {
    tags = {
      Project   = "llm-gateway"
      Layer     = "persistent"
      ManagedBy = "terraform"
    }
  }
}
