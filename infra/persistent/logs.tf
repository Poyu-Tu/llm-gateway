# 三個日誌群組、DNS 查詢日誌的設定、兩個告警：都放長期層（E123 定案 7 推出來的安排；M5 加 Worker 的群組與 SQS 告警）
#   不需要拆除組多拿 logs:DeleteLogDelivery 那種只能寫 "*" 的刪除權限（DNS 查詢日誌刪設定時要用）
#   日誌在每日層拆掉之後還在：S08 的封鎖紀錄、稽核寫失敗的那一行，事後查得到
#   日誌群組、查詢日誌設定、指標篩選都不跳錶；告警每個每月約 US$0.10（前 10 個免費）
# 每日層只做「接上 VPC」那一步（infra/daily/dns_firewall.tf），拆的時候只拆那條線

# ---- Gateway 容器的日誌 ----
# 日誌裡有 user_id（稽核寫失敗的那一行，E116），所以要有保存期限：30 天後自動刪
# Trivy AWS-0017（LOW）：沒用自管 KMS 金鑰加密，CloudWatch Logs 預設已用 AWS 的金鑰加密，接受
resource "aws_cloudwatch_log_group" "gateway" {
  name              = local.gateway_log_group
  retention_in_days = 30

  # AWS 層級的防刪：主控台、CLI 也刪不掉（跟三張表的刪除保護同一個想法）
  deletion_protection_enabled = true
}

# ---- DNS 查詢日誌 ----
# 每一筆 DNS 查詢都會記：查了哪個網域、DNS 防火牆放行、告警還是封鎖（S08 的證據）
resource "aws_cloudwatch_log_group" "dns_queries" {
  name                        = "/llm-gateway/dns-queries"
  retention_in_days           = 30
  deletion_protection_enabled = true
}

# ---- Worker（Lambda）的日誌 ----
# 每則訊息一行 charge_recorded／charge_already_recorded，只有單號與金額（E131 預設值）
# 名字照 Lambda 的規定：/aws/lambda/<函式名>；函式在每日層，群組在這裡先建好，拆每日層時日誌還在
resource "aws_cloudwatch_log_group" "worker" {
  name                        = local.worker_log_group
  retention_in_days           = 30
  deletion_protection_enabled = true
}

# 查詢日誌的設定：寫到上面那個群組。建立時 AWS 會替它開一條日誌輸送管道；
# 刪設定時要拆那條管道（logs:DeleteLogDelivery，只能寫 "*"），所以設定留在長期層，拆除組不碰
resource "aws_route53_resolver_query_log_config" "dns" {
  name            = "llm-gateway-dns-queries"
  destination_arn = aws_cloudwatch_log_group.dns_queries.arn
}

# ---- 稽核寫失敗的告警（E116、E123 定案 8）----
# Gateway 寫不進 audit 表時，照樣回答使用者，只在日誌印一行 {"event": "audit_write_failed", ...}
# 這個篩選把那一行變成一個數字，告警看到數字 ≥ 1 就發到 SNS
resource "aws_cloudwatch_log_metric_filter" "audit_write_failed" {
  name           = "llm-gateway-audit-write-failed"
  log_group_name = aws_cloudwatch_log_group.gateway.name
  pattern        = "{ $.event = \"audit_write_failed\" }"

  metric_transformation {
    name      = "AuditWriteFailed"
    namespace = "LLMGateway"
    value     = "1"
    # 沒有這種日誌時不產生數字，告警把「沒有資料」當成正常（下面的 treat_missing_data）
  }
}

resource "aws_cloudwatch_metric_alarm" "audit_write_failed" {
  alarm_name        = "llm-gateway-audit-write-failed"
  alarm_description = "An audit record did not reach the audit table; it is only in the Gateway log"

  namespace   = "LLMGateway"
  metric_name = "AuditWriteFailed"
  statistic   = "Sum"
  # 1 分鐘內有 1 筆就響：稽核漏掉一筆就是一筆，不等累積
  period              = 60
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

# ---- SQS 送不進去的告警（E135 定案 6）----
# Gateway 送不進 SQS 時改走備援、帳是對的，只在日誌印一行 {"event": "charge_queue_failed", ...}
# 偶爾一次不響；5 分鐘內 3 次以上代表持續故障（DNS 漏網域、IAM 少權限），才通知
resource "aws_cloudwatch_log_metric_filter" "charge_queue_failed" {
  name           = "llm-gateway-charge-queue-failed"
  log_group_name = aws_cloudwatch_log_group.gateway.name
  pattern        = "{ $.event = \"charge_queue_failed\" }"

  metric_transformation {
    name      = "ChargeQueueFailed"
    namespace = "LLMGateway"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "charge_queue_failed" {
  alarm_name        = "llm-gateway-charge-queue-failed"
  alarm_description = "The Gateway keeps failing to send charge events to SQS; charges fall back to the synchronous ledger"

  namespace   = "LLMGateway"
  metric_name = "ChargeQueueFailed"
  statistic   = "Sum"
  # 5 分鐘一格、看 1 格、≥ 3 筆就響
  period              = 300
  evaluation_periods  = 1
  threshold           = 3
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}