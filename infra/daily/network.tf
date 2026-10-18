# 每日層的骨架：圍牆（VPC）、隔間（子網）、大門（網際網路閘道）、指路牌（路由表）
# 全部免費；NAT 與通往 NAT 的路由在 D 段加（E121）

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  # D 段的 DNS 防火牆要靠 VPC 內建的 DNS；兩個都要開
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "llm-gateway" }
}

# ---- 公有子網：只放 ALB（之後還有 NAT）。ALB 規定要兩個不同的 AZ（決策書 3.5 坑 5）----
# 不自動發公開 IP：ALB 與 NAT 都不需要，關掉也避開 Trivy AWS-0164

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.0.0/24"
  availability_zone       = "ap-northeast-1a"
  map_public_ip_on_launch = false

  tags = { Name = "llm-gateway-public-a" }
}

resource "aws_subnet" "public_c" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "ap-northeast-1c"
  map_public_ip_on_launch = false

  tags = { Name = "llm-gateway-public-c" }
}

# ---- 私有子網：放 Fargate。跟之後的 NAT 同一個 AZ（D13）：跨 AZ 的流量要另外收費 ----

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "ap-northeast-1a"

  tags = { Name = "llm-gateway-private-a" }
}

# ---- 大門：公有子網通往網際網路（E121 定案 5：放 C 段，destroy 第一次就驗到「卸大門」）----

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "llm-gateway" }
}

# 公有子網的指路牌：要去外面的，走大門
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "llm-gateway-public" }
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_c" {
  subnet_id      = aws_subnet.public_c.id
  route_table_id = aws_route_table.public.id
}

# 私有子網的指路牌：現在只有 VPC 內部與兩條 Gateway Endpoint 路由（endpoints.tf 自動加）
# 通往 NAT 的 0.0.0.0/0 在 D 段加；在那之前，私有子網完全沒有對外的路
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "llm-gateway-private" }
}

resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private.id
}

# ==== D 段（E123）====

# ---- NAT：私有子網對外唯一的出口（單 AZ，跟私有子網同在 1a，D13）----
# 按小時計費（約 US$0.062／小時，加上彈性 IP 約 US$0.005／小時），測完當天 destroy

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = { Name = "llm-gateway-nat" }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id

  tags = { Name = "llm-gateway" }

  # NAT 要等大門裝好才能真的通到外面
  depends_on = [aws_internet_gateway.main]
}

# 私有子網的指路牌加一條：要去外面的（OpenAI、STS、ECR、Logs、SSM），走 NAT
# S3 與 DynamoDB 不會走這條：Gateway Endpoint 的路由比 0.0.0.0/0 更精準，會先被選中
resource "aws_route" "private_internet" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main.id
}

# ---- 認領 AWS 附送的預設安全群組（E123 定案 8-2）----
# 任何東西建在這個 VPC 卻忘了指定安全群組，就會套用它；AWS 預設是「對外全開、同群組互通」
# 這裡不寫任何 ingress、egress，Terraform 就把它的規則全部清空：忘了指定的東西進不來也出不去
# destroy 時 Terraform 只把它從帳本移除（AWS 不准刪預設安全群組），刪 VPC 時 AWS 一起刪
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "llm-gateway-default-unused" }
}
