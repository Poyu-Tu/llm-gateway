# 測試時用 ALB 的網址打 Gateway（http://<這個值>/health）
output "alb_dns_name" {
  description = "Address of the load balancer"
  value       = aws_lb.gateway.dns_name
}

# 一次性任務（S08 的出口測試）要用：跑在同一個私有子網、同一個安全群組
output "private_subnet_id" {
  description = "Private subnet the Gateway tasks run in"
  value       = aws_subnet.private_a.id
}

output "gateway_security_group_id" {
  description = "Security group of the Gateway tasks"
  value       = aws_security_group.gateway.id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

# 一次性任務要指定任務定義的版本（family:revision）
output "task_definition" {
  description = "Task definition family and revision currently used by the service"
  value       = "${aws_ecs_task_definition.gateway.family}:${aws_ecs_task_definition.gateway.revision}"
}
