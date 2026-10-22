# 四張表的名字要和 app/db.py 一模一樣（API_KEYS_TABLE、QUOTAS_TABLE、AUDIT_TABLE、USAGE_TABLE），Gateway 與 Worker 才找得到
# 主鍵照 scripts/create_tables.py；四張表都在這裡（usage 是 M5 加的）

# 查 Key：主鍵是 Key 的雜湊
resource "aws_dynamodb_table" "api_keys" {
  name         = "api_keys"
  billing_mode = "PAY_PER_REQUEST" # 隨需計費：沒請求就不花錢（E111 定案）
  hash_key     = "key_hash"

  attribute {
    name = "key_hash"
    type = "S"
  }

  # AWS 層級的防刪：連主控台都刪不掉，要先關掉這個開關（跟 prevent_destroy 只擋 Terraform 不同）
  deletion_protection_enabled = true

  # 時光機：35 天內任何一秒都能還原；表幾乎是空的，費用趨近 0
  point_in_time_recovery {
    enabled = true
  }
}

# 額度：user_id + period（額度那筆的 period 是 "limit"，每月已用量是 "YYYY-MM"）
resource "aws_dynamodb_table" "quotas" {
  name         = "quotas"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "period"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "period"
    type = "S"
  }

  deletion_protection_enabled = true

  point_in_time_recovery {
    enabled = true
  }
}

# 稽核：一筆請求一筆，用 request_id 找
resource "aws_dynamodb_table" "audit" {
  name         = "audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"

  attribute {
    name = "request_id"
    type = "S"
  }

  deletion_protection_enabled = true

  point_in_time_recovery {
    enabled = true
  }
}

# 用量明細（M5）：一筆記帳一列，按人查、照時間排（E130 定案 2）
# 由 Worker 與 Gateway 備援透過 record_charge() 的交易寫入
resource "aws_dynamodb_table" "usage" {
  name         = "usage"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "ts_request"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "ts_request"
    type = "S"
  }

  deletion_protection_enabled = true

  point_in_time_recovery {
    enabled = true
  }
}