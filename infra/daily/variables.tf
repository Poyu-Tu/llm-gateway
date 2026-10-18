# ALB 只放行這一個位址（E117 定案 4）。本機用環境變數 TF_VAR_admin_cidr 給值（E121 定案 6 補充），不存檔
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

# 要跑哪一版映像：合併進 main 之後那個 commit 的編號（E123 定案 5）；ECR 是 IMMUTABLE，同一個標籤永遠是同一份
# destroy workflow 拆除用不到這個值，填一個假的編號
variable "image_tag" {
  description = "Tag of the Gateway image in ECR: the main commit it was built from (7 to 40 hex characters)"
  type        = string

  validation {
    condition     = can(regex("^[0-9a-f]{7,40}$", var.image_tag))
    error_message = "image_tag must be a git commit hash (7 to 40 lowercase hex characters)."
  }
}
