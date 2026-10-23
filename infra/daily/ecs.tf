# 店員（ECS Fargate）：在私有子網跑 Gateway 容器，沒有公開 IP，只收 ALB 送來的請求
# 按小時計費（0.25 vCPU／0.5 GB 約 US$0.0154／小時，D15），測完當天 destroy
# 兩個 IAM 角色、日誌群組在長期層（E123 定案 2、7），這裡用寫死的名字組出 ARN

locals {
  account_id = data.aws_caller_identity.current.account_id

  # 長期層建的東西（名字要跟 infra/persistent/ 一模一樣）
  gateway_image          = "${local.account_id}.dkr.ecr.ap-northeast-1.amazonaws.com/llm-gateway:${var.image_tag}"
  task_execution_role    = "arn:aws:iam::${local.account_id}:role/llm-gateway-task-execution"
  task_role              = "arn:aws:iam::${local.account_id}:role/llm-gateway-task"
  gateway_log_group_name = "/ecs/llm-gateway"
  ssm_parameter_prefix   = "arn:aws:ssm:ap-northeast-1:${local.account_id}:parameter/llm-gateway"
  # 長期層 sqs.tf 的主佇列網址；Gateway 啟動時檢查，沒寫或寫錯就起不來（E131 定案 5）
  charge_queue_url = "https://sqs.ap-northeast-1.amazonaws.com/${local.account_id}/llm-gateway-charge"
}

resource "aws_ecs_cluster" "main" {
  name = "llm-gateway"

  # Container Insights 會另外收指標的錢；Demo 看 CloudWatch Logs 與 ALB 的健康檢查就夠
  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

# 任務定義：跑哪個映像、多大、什麼身分、哪些設定與機密
resource "aws_ecs_task_definition" "gateway" {
  family                   = "llm-gateway"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = local.task_execution_role
  task_role_arn            = local.task_role

  # 映像在本人電腦建（x86_64），寫明避免被排到 ARM 的機器上起不來
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  # destroy 時只從帳本移除、不去 AWS 註銷（E123 定案 7）：註銷這個動作只能寫 Resource "*"，
  # 拆除組就不用拿這個權限。任務定義不收費，留著當版本紀錄（哪天跑過哪個映像標籤）；裡面沒有機密的值
  skip_destroy = true

  container_definitions = jsonencode([
    {
      name      = "gateway"
      image     = local.gateway_image
      essential = true

      portMappings = [{ containerPort = local.gateway_port, protocol = "tcp" }]

      # 根目錄唯讀（E116）：程式不寫任何檔案，Dockerfile 也不再建可寫的資料夾
      readonlyRootFilesystem = true

      # 不是機密的設定
      environment = [
        # 連東京真的 DynamoDB，身分用任務角色（E111）
        { name = "DYNAMODB_TARGET", value = "aws" },
        # 用 AWS 的身分換 OpenAI 的通行證，不用金鑰（E113、E123 定案 4）
        { name = "OPENAI_AUTH", value = "workload_identity" },
        { name = "OPENAI_WIF_AUDIENCE", value = "llm-gateway-capstone" },
        # 成功那一筆送進出單夾（E134）
        { name = "CHARGE_QUEUE_URL", value = local.charge_queue_url }
      ]

      # 機密：ECS 啟動時用執行角色從 SSM 拿值，直接交給容器；任務定義與帳本裡只有參數的名字（E123 定案 3、4）
      secrets = [
        { name = "AUDIT_HMAC_KEY", valueFrom = "${local.ssm_parameter_prefix}/audit-hmac-key" },
        { name = "OPENAI_IDENTITY_PROVIDER_ID", valueFrom = "${local.ssm_parameter_prefix}/openai-identity-provider-id" },
        { name = "OPENAI_SERVICE_ACCOUNT_ID", valueFrom = "${local.ssm_parameter_prefix}/openai-service-account-id" },
      ]

      # 容器印出來的每一行（含 audit_write_failed）都送進長期層的日誌群組
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = local.gateway_log_group_name
          "awslogs-region"        = "ap-northeast-1"
          "awslogs-stream-prefix" = "gateway"
        }
      }
    }
  ])

  tags = { Name = "llm-gateway" }
}

resource "aws_ecs_service" "gateway" {
  name            = "llm-gateway"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.gateway.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = [aws_subnet.private_a.id]
    security_groups = [aws_security_group.gateway.id]
    # 沒有公開 IP（S09）：對外只能走 NAT
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.gateway.arn
    container_name   = "gateway"
    container_port   = local.gateway_port
  }

  # 容器剛起來要幾秒載入程式；這段時間的健康檢查失敗不算
  health_check_grace_period_seconds = 30

  # 部署斷路器（E114）：新版本一直起不來（例如設定檔寫錯），ECS 自己停下來並退回上一版
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  # 不開 ECS Exec（E123 定案 6）：要開就得放寬出口、加權限、在唯讀根目錄開例外
  enable_execute_command = false

  # 每個任務也貼上服務的標籤（Layer = daily），主控台查得到是哪一層的
  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"

  # apply 等到服務真的穩定（任務起來、健康檢查通過）才算成功；起不來的話 apply 會失敗，不會「看起來成功」
  wait_for_steady_state = true

  tags = { Name = "llm-gateway" }

  # 先有 ALB 的入口，服務才把任務登記上去
  # 先 Worker、後 Gateway（E131、E139 第 2 題）：建立與更新都等觸發好了，Gateway 才開始送單
  depends_on = [aws_lb_listener.http, aws_lambda_event_source_mapping.charge]
}
