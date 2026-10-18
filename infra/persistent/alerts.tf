# 告警的廣播站（E123 定案 8）：每日層的 CloudWatch 告警響了，往這裡發；本人的 Email 訂閱它
# 放長期層：每天 apply 不用重點確認信，destroy 角色也不用 SNS 刪除權限
# Email 訂閱由本人用 CLI 建（信箱是個人資料，不進 repo、不進帳本），點一次確認信就生效

# Trivy AWS-0095（CRITICAL／HIGH）要求主題加密：刻意接受，12/31 到期重新檢討。
# 用 AWS 預設的 alias/aws/sns 加密時，CloudWatch 告警發不進來；要自管 KMS 金鑰（每月約 US$1）
# 並另寫金鑰政策。主題裡只有「哪個告警、什麼狀態」，沒有使用者資料
#trivy:ignore:AWS-0095:exp:2026-12-31
resource "aws_sns_topic" "alerts" {
  name = "llm-gateway-alerts"
}
