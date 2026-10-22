# 出單夾（SQS）與問題單抽屜（DLQ）：放長期層（E127 定案 5），沒有訊息時不收費
# 主佇列的訊息是 app/events.py 的信封；Gateway 送（任務角色）、Worker 收（每日層的 Lambda 觸發）
# 兩個佇列都用 SQS 自管的鑰匙加密（E135 定案 7）：免費、不用改任何權限

# ---- 問題單抽屜 ----
# Worker 連續失敗 maxReceiveCount 次的訊息會被搬到這裡；修好之後可以用主控台搬回主佇列
resource "aws_sqs_queue" "charge_dlq" {
  name = "llm-gateway-charge-dlq"

  # 保留 14 天（E127 預設值）：單位是秒
  message_retention_seconds = 1209600 # 14 × 24 × 60 × 60

  sqs_managed_sse_enabled = true
}

# ---- 出單夾 ----
resource "aws_sqs_queue" "charge" {
  name = "llm-gateway-charge"

  # 隱藏時間：Worker 拿走後這段時間內別人看不到；要 ≥ Lambda 逾時，AWS 建議 6 倍（E135 定案 3）
  # Lambda 逾時 20 秒寫在每日層（infra/daily/worker.tf），兩邊要一起改
  visibility_timeout_seconds = 120

  sqs_managed_sse_enabled = true

  # 失敗幾次進 DLQ：AWS 建議至少 5，因為 Lambda 被限流時也算收過一次（E135 定案 2）
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.charge_dlq.arn
    maxReceiveCount     = 5
  })
}

# 抽屜只收這一個出單夾丟過來的；別的佇列不能把它當 DLQ
resource "aws_sqs_queue_redrive_allow_policy" "charge_dlq" {
  queue_url = aws_sqs_queue.charge_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.charge.arn]
  })
}