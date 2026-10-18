# 兩個日誌群組、DNS 查詢日誌的設定、稽核寫失敗的告警：都放長期層（E123 定案 7 推出來的安排）
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
