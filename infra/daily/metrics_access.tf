# /metrics 的門禁（決策書 4.3，M6）：監控數字會洩漏用量、成本、誰在用，不能公開
# 在 ALB 這一層就擋：帶對的 X-Metrics-Token 才轉給 Gateway，其他打 /metrics 的一律 403，碰不到容器
# 業務流量（/、/v1/*、/health）不受影響，照 listener 原本的 default_action 轉給 Gateway
#
# 通行證放 SSM（SecureString，本人用 CLI 建，值不進 repo）；這裡用 data 讀出來填進規則
# 弱點（誠實記錄）：規則的條件要寫明文，所以每日層帳本和 ALB 設定裡看得到原值；
# Demo 走 HTTP（7.8），通行證在網路上是明文——靠 ALB 只放本人一個 IP 撐住
# ALB 比對標頭不分大小寫、* 和 ? 是萬用字元、最長 128 字：通行證用 64 個十六進位字元，不會撞到

data "aws_ssm_parameter" "metrics_token" {
  name = "/llm-gateway/metrics-token"
}

# 第一條（數字小的先比）：路徑是 /metrics「而且」通行證對 → 轉給 Gateway
resource "aws_lb_listener_rule" "metrics_with_token" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.gateway.arn
  }

  condition {
    path_pattern {
      values = ["/metrics"]
    }
  }

  condition {
    http_header {
      http_header_name = "X-Metrics-Token"
      values           = [data.aws_ssm_parameter.metrics_token.value]
    }
  }

  tags = { Name = "llm-gateway-metrics-with-token" }
}

# 第二條：其他打 /metrics 的（沒帶、帶錯）→ ALB 自己回 403，不轉給 Gateway
# /metrics/* 一起擋：Gateway 對結尾多一個斜線的路徑會轉址回 /metrics，從源頭就不給
resource "aws_lb_listener_rule" "metrics_forbidden" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20

  action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Forbidden"
      status_code  = "403"
    }
  }

  condition {
    path_pattern {
      values = ["/metrics", "/metrics/*"]
    }
  }

  tags = { Name = "llm-gateway-metrics-forbidden" }
}
