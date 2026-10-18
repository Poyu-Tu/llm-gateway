# 店門口（ALB）：唯一對外的入口，只收本人的 IP（安全群組在 security_groups.tf，E117 定案 4）
# 按小時計費（約 US$0.0243／小時，加上兩個公開 IP 約 US$0.01／小時），測完當天 destroy

# Trivy AWS-0053（HIGH）不准 ALB 對外：刻意接受。它本來就是對外的入口，
# 能進來的只有 admin_cidr 那一個 IP（變數只收 /32），12/31 到期重新檢討
#trivy:ignore:AWS-0053:exp:2026-12-31
resource "aws_lb" "gateway" {
  name               = "llm-gateway"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  # ALB 規定兩個不同 AZ 的子網（決策書 3.5 坑 5）
  subnets = [aws_subnet.public_a.id, aws_subnet.public_c.id]

  # 120 秒：強模型最多 60 秒，被限流降級後便宜模型再 60 秒（E115）；預設 60 秒會在 Gateway 還在等時先斷線
  idle_timeout = 120

  # 格式不對的 HTTP 標頭直接丟掉，不轉給 Gateway（Trivy AWS-0052）
  drop_invalid_header_fields = true

  tags = { Name = "llm-gateway" }
}

# 後面接的是誰：Fargate 任務的私有 IP、8000 埠
resource "aws_lb_target_group" "gateway" {
  name        = "llm-gateway"
  target_type = "ip"
  protocol    = "HTTP"
  port        = local.gateway_port
  vpc_id      = aws_vpc.main.id

  # 健康檢查打 /health（E114）：程式載入失敗時容器照樣是 Up，要靠這個判斷服務真的活著
  health_check {
    path                = "/health"
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  # 換版時舊任務最多再等 30 秒把手上的請求做完（預設 300 秒，測試時等太久）
  deregistration_delay = 30

  tags = { Name = "llm-gateway" }
}

# Trivy AWS-0054（CRITICAL）不准 HTTP：刻意接受。發 HTTPS 憑證要有自己的網域（決策書 7.8，不買網域）；
# 只有本人一個 IP 連得進來。正式環境改 443 加 ACM 憑證、80 轉 443。12/31 到期重新檢討
#trivy:ignore:AWS-0054:exp:2026-12-31
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.gateway.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.gateway.arn
  }

  tags = { Name = "llm-gateway-http" }
}
