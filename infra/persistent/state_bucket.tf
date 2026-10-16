# 放 Terraform 帳本（State）的保險箱
resource "aws_s3_bucket" "tfstate" {
  # 只給開頭，後面由 AWS 補一串亂碼：名字全世界唯一，也不用把帳號 ID 寫進公開的 repo
  bucket_prefix = "llm-gateway-tfstate-"

  # 防手滑：terraform destroy 碰到它會直接報錯，帳本不會跟著被拆掉
  lifecycle {
    prevent_destroy = true
  }
}

# 四個開關全開：不管誰設了什麼，這個 bucket 都不可能變成公開
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 版本控制：帳本被改壞或誤刪，還能拿回上一版
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 存進去就加密；用 S3 自己管的金鑰（免費），帳本裡沒有密碼，不需要另付 KMS
# Trivy AWS-0132（HIGH）要求改用自管的 KMS 金鑰：刻意接受。存取已由 IAM 與 bucket 政策管住，
# 自管金鑰每月約 US$1、所有讀寫帳本的角色都要多給 KMS 權限；專題結束前（12/31 到期）再檢討

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 只准走加密連線（HTTPS）：沒加密的請求一律拒絕
resource "aws_s3_bucket_policy" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  policy = data.aws_iam_policy_document.tfstate_tls_only.json

  # 先把「禁止公開」設好才掛政策，避免兩個設定同時改時互相卡住
  depends_on = [aws_s3_bucket_public_access_block.tfstate]
}

data "aws_iam_policy_document" "tfstate_tls_only" {
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.tfstate.arn, "${aws_s3_bucket.tfstate.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}
