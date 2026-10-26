"""Check a Terraform plan before the deploy workflow applies it.

The deploy workflow only swaps the Gateway image. The plan may register a new task
definition and point the ECS service at it; any other change stops the deploy.
    python3 scripts/check_deploy_plan.py plan.json      (plan.json = terraform show -json)
"""

import json
import sys

# 換映像時唯一該有的兩個改變（D92、E150 定案 A）：
#   任務定義換新版：映像變了，Terraform 寫成「先刪後建」（skip_destroy：舊版只從帳本移除，AWS 上留著）
#   ECS 服務改指新版本：update
ALLOWED_CHANGES = {
    "aws_ecs_task_definition.gateway": {("delete", "create"), ("create", "delete")},
    "aws_ecs_service.gateway": {("update",)},
}

# 什麼都沒變（no-op）、只是讀資料（read）：不算改變
NO_CHANGE = {("no-op",), ("read",)}


# 守門：把計畫裡每一個「換映像以外」的改變列出來；空的才准 apply
def disallowed_changes(plan: dict) -> list[str]:
    """Return one line for every change in the plan that a deploy must not make."""
    problems = []
    for change in plan.get("resource_changes", []):
        address = change["address"]
        actions = tuple(change["change"]["actions"])
        if actions in NO_CHANGE:
            continue
        if actions in ALLOWED_CHANGES.get(address, set()):
            continue
        problems.append(f"{address}: {'/'.join(actions)}")
    return problems


# 讀 terraform show -json 的檔案；有不該有的改變就列出來並回 1，讓 workflow 停在 apply 之前
def main(path: str) -> int:
    """Print what the plan must not change and return 1, or return 0 if only the image changes."""
    with open(path, encoding="utf-8") as file:
        plan = json.load(file)
    problems = disallowed_changes(plan)
    if problems:
        print("The plan changes more than the Gateway image, so nothing was applied:")
        for line in problems:
            print(f"  {line}")
        return 1
    print("The plan only swaps the Gateway image")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
