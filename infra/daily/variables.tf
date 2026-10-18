# ALB 只放行這一個位址（E117 定案 4）。值放在本機的 .tfvars，.gitignore 已擋，不進 repo
# destroy workflow 填 RFC 5737 的文件專用位址：拆除用不到這個值（E121 定案 6）
variable "admin_cidr" {
  description = "The only address allowed to reach the ALB, as a /32 (for example 198.51.100.7/32)"
  type        = string

  # 只收單一位址；0.0.0.0/0 或一整段網段都會被擋，ALB 不會意外對全世界開放
  validation {
    condition     = can(cidrhost(var.admin_cidr, 0)) && endswith(var.admin_cidr, "/32")
    error_message = "admin_cidr must be a single address written as x.x.x.x/32."
  }
}
