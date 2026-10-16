# 放 Gateway 映像的倉庫，Fargate 從這裡拉映像
resource "aws_ecr_repository" "gateway" {
  name = "llm-gateway"

  # 同一個標籤不能被覆蓋：v1 推上去之後永遠是那一份，出事時查得到當時跑的是哪一版
  image_tag_mutability = "IMMUTABLE"

  # 每次推上來就做一次基本弱點掃描（免費）；CI 的 Trivy 是第一道，這裡是第二道
  image_scanning_configuration {
    scan_on_push = true
  }

  # 存放時加密，用 AWS 管的金鑰（免費）
  encryption_configuration {
    encryption_type = "AES256"
  }
}

# 自動清舊映像：沒標籤的 1 天後刪；全部最多留 10 個，避免越存越貴
resource "aws_ecr_lifecycle_policy" "gateway" {
  repository = aws_ecr_repository.gateway.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expire untagged images after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep only the 10 most recent images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = { type = "expire" }
      }
    ]
  })
}