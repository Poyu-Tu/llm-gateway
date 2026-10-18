# 拿名單的總機（Route 53 Resolver DNS 防火牆，決策書 4.1、7.1 選項 B、D25）
# VPC 裡每一次「查號碼」（DNS 查詢）都先過它：名單上的網域照常回答，其他的先記下（ALERT）、之後擋掉（BLOCK）
# 先告警、後阻擋（決策書 3.5 坑 2；E123 定案 1）：var.dns_firewall_action 從 ALERT 開始，
# 整理完查詢日誌再用 -var=dns_firewall_action=BLOCK apply 一次，只改「其他全部」那條規則
# 費用：每個網域每月約 US$0.0005、每百萬次查詢 US$0.60，Demo 幾乎是 0

locals {
  # 放行清單：一個一個寫完整網域，不寫 *.amazonaws.com（決策書 3.5 坑 1：攻擊者自己帳號的 S3 也在那底下）
  allowed_domains = [
    # OpenAI：模型、身分聯盟換通行證（E113）
    "api.openai.com",
    "auth.openai.com",
    # 任務角色向東京的 STS 要身分證明（只有地區網址開得出這種證明）
    "sts.ap-northeast-1.amazonaws.com",
    # 拉映像：先跟 ECR 換登入權杖，再到本帳號的倉庫拿映像清單，映像層本身在 AWS 的 S3 bucket
    "api.ecr.ap-northeast-1.amazonaws.com",
    "${data.aws_caller_identity.current.account_id}.dkr.ecr.ap-northeast-1.amazonaws.com",
    "prod-ap-northeast-1-starport-layer-bucket.s3.ap-northeast-1.amazonaws.com",
    # 寫日誌、啟動時拿 SSM 的機密
    "logs.ap-northeast-1.amazonaws.com",
    "ssm.ap-northeast-1.amazonaws.com",
    # 資料庫：雖然走 Gateway Endpoint 不經 NAT，但程式還是要先查這個網域，查不到就連不上
    "dynamodb.ap-northeast-1.amazonaws.com",
  ]
}

variable "dns_firewall_action" {
  description = "What to do with every domain not on the allow list: ALERT (log only) first, then BLOCK"
  type        = string
  default     = "ALERT"

  validation {
    condition     = contains(["ALERT", "BLOCK"], var.dns_firewall_action)
    error_message = "dns_firewall_action must be ALERT or BLOCK."
  }
}

resource "aws_route53_resolver_firewall_domain_list" "allowed" {
  name    = "llm-gateway-allowed"
  domains = local.allowed_domains
}

# 「其他全部」：* 代表任何網域；排在放行清單後面，所以只會抓到名單外的
resource "aws_route53_resolver_firewall_domain_list" "everything" {
  name    = "llm-gateway-everything-else"
  domains = ["*"]
}

resource "aws_route53_resolver_firewall_rule_group" "egress" {
  name = "llm-gateway-egress"
}

# 規則 1（數字小的先比）：名單上的放行
resource "aws_route53_resolver_firewall_rule" "allow_listed" {
  name                    = "allow-listed-domains"
  firewall_rule_group_id  = aws_route53_resolver_firewall_rule_group.egress.id
  firewall_domain_list_id = aws_route53_resolver_firewall_domain_list.allowed.id
  priority                = 100
  action                  = "ALLOW"

  # 很多網域的答案是「請改問另一個名字」（CNAME，例如轉到 CDN）。預設會連那個名字也拿去比，
  # 而那個名字不在名單上，切成 BLOCK 時就會被擋。名單上的網域信任它指過去的名字
  firewall_domain_redirection_action = "TRUST_REDIRECTION_DOMAIN"
}

# 規則 2：其他全部。ALERT 只記不擋；BLOCK 回「查無資料」（NODATA），容器就連不出去
resource "aws_route53_resolver_firewall_rule" "everything_else" {
  name                    = "everything-else"
  firewall_rule_group_id  = aws_route53_resolver_firewall_rule_group.egress.id
  firewall_domain_list_id = aws_route53_resolver_firewall_domain_list.everything.id
  priority                = 200
  action                  = var.dns_firewall_action
  block_response          = var.dns_firewall_action == "BLOCK" ? "NODATA" : null
}

# 把規則群組掛上 VPC：從這一刻起，VPC 裡的查詢都要過總機
resource "aws_route53_resolver_firewall_rule_group_association" "egress" {
  name                   = "llm-gateway-egress"
  firewall_rule_group_id = aws_route53_resolver_firewall_rule_group.egress.id
  vpc_id                 = aws_vpc.main.id
  priority               = 101
  # 不開變更保護：開了之後要先解除才拆得掉，拆除組就得多一個權限
  mutation_protection = "DISABLED"
}

# ---- DNS 查詢日誌：把 VPC 接到長期層的查詢日誌設定（設定本身與日誌群組在 infra/persistent/logs.tf）----
# 用名字查出長期層建好的設定（只讀）；拆除時只拆這條連線，設定與日誌都留著
data "aws_route53_resolver_query_log_config" "dns" {
  filter {
    name   = "Name"
    values = ["llm-gateway-dns-queries"]
  }
}

resource "aws_route53_resolver_query_log_config_association" "dns" {
  resolver_query_log_config_id = data.aws_route53_resolver_query_log_config.dns.id
  resource_id                  = aws_vpc.main.id
}
