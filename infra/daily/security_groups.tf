# 兩道門禁：ALB 只收你的 IP；Gateway 只收 ALB 送來的請求
# 每條規則一個資源（不寫在安全群組裡面）：兩個群組互相指來指去也不會繞圈，每條規則也能貼標籤

locals {
  # Gateway 容器聽的埠（Dockerfile 的 EXPOSE 8000）
  gateway_port = 8000
}

# ---- ALB ----

resource "aws_security_group" "alb" {
  name        = "llm-gateway-alb"
  description = "ALB: HTTP from the admin address only"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "llm-gateway-alb" }
}

# 只放行你一個人的公開 IP（E117 定案 4）；HTTP 80（決策書 7.8）
resource "aws_vpc_security_group_ingress_rule" "alb_http_from_admin" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP from the admin address"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = var.admin_cidr
}

# ALB 只能往 Gateway 送，不寫 0.0.0.0/0
resource "aws_vpc_security_group_egress_rule" "alb_to_gateway" {
  security_group_id            = aws_security_group.alb.id
  description                  = "Forward requests to the Gateway tasks"
  ip_protocol                  = "tcp"
  from_port                    = local.gateway_port
  to_port                      = local.gateway_port
  referenced_security_group_id = aws_security_group.gateway.id
}

# ---- Gateway（Fargate）----

resource "aws_security_group" "gateway" {
  name        = "llm-gateway-gateway"
  description = "Gateway tasks: requests from the ALB only, HTTPS out"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "llm-gateway-gateway" }
}

resource "aws_vpc_security_group_ingress_rule" "gateway_from_alb" {
  security_group_id            = aws_security_group.gateway.id
  description                  = "Requests from the ALB"
  ip_protocol                  = "tcp"
  from_port                    = local.gateway_port
  to_port                      = local.gateway_port
  referenced_security_group_id = aws_security_group.alb.id
}

# 對外只開 443：經 NAT 連 OpenAI、ECR、CloudWatch Logs；S3 與 DynamoDB 走 Gateway Endpoint
# 安全群組管不到 Amazon 提供的 DNS（3.5 坑 4），所以不用開 53
# Trivy AWS-0104（CRITICAL）不准出口寫 0.0.0.0/0：刻意接受。OpenAI 的 IP 不固定，只能用網域管；
# 去哪些網域由 DNS 防火牆的放行清單管（決策書 4.1、7.1 選項 B），直接用 IP 連線是已接受的殘餘風險（7.9）
#trivy:ignore:AWS-0104:exp:2026-12-31
resource "aws_vpc_security_group_egress_rule" "gateway_https_out" {
  security_group_id = aws_security_group.gateway.id
  description       = "HTTPS out through NAT and the gateway endpoints"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}
