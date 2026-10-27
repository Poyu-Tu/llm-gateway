"""Tests for scripts/check_deploy_plan.py: the guard the deploy workflow runs before apply."""

import json

from scripts.check_deploy_plan import disallowed_changes, main


# 計畫裡的一筆改變（只放守門會看的兩個欄位，跟 terraform show -json 的格式一樣）
def change(address, *actions):
    """Return one entry of resource_changes."""
    return {"address": address, "change": {"actions": list(actions)}}


# 正常換映像的計畫：任務定義先刪後建、服務 update，其他資源 no-op，data 是 read
def image_swap_plan():
    """Return a plan that only swaps the Gateway image."""
    return {
        "resource_changes": [
            change("data.aws_ssm_parameter.metrics_token", "read"),
            change("aws_ecs_task_definition.gateway", "delete", "create"),
            change("aws_ecs_service.gateway", "update"),
            change("aws_lb.gateway", "no-op"),
            change("aws_vpc_security_group_ingress_rule.alb_http_from_admin", "no-op"),
        ]
    }


# 只換映像：放行
def test_an_image_swap_is_allowed():
    assert disallowed_changes(image_swap_plan()) == []


# 沒有任何改變（同一個映像再按一次）：放行，apply 什麼都不做
def test_a_plan_with_no_changes_is_allowed():
    plan = {"resource_changes": [change("aws_lb.gateway", "no-op")]}

    assert disallowed_changes(plan) == []


# 家裡的 IP 變了、secret 沒更新：安全群組規則要被換掉 → 擋下
def test_a_security_group_change_is_refused():
    plan = image_swap_plan()
    plan["resource_changes"][4] = change("aws_vpc_security_group_ingress_rule.alb_http_from_admin", "delete", "create")

    assert disallowed_changes(plan) == ["aws_vpc_security_group_ingress_rule.alb_http_from_admin: delete/create"]


# 每日層沒建：每樣東西都要新建 → 全部列出、擋下
def test_a_plan_that_builds_the_daily_layer_is_refused():
    plan = {
        "resource_changes": [
            change("aws_vpc.main", "create"),
            change("aws_ecs_task_definition.gateway", "create"),
            change("aws_ecs_service.gateway", "create"),
        ]
    }

    assert disallowed_changes(plan) == [
        "aws_vpc.main: create",
        "aws_ecs_task_definition.gateway: create",
        "aws_ecs_service.gateway: create",
    ]


# Worker 的程式改過：Lambda 要更新 → 擋下（Worker 不在 CD 範圍，要從本人電腦 apply）
def test_a_worker_update_is_refused():
    plan = image_swap_plan()
    plan["resource_changes"].append(change("aws_lambda_function.worker", "update"))

    assert disallowed_changes(plan) == ["aws_lambda_function.worker: update"]


# 允許的是「哪個資源＋哪種動作」的組合：服務被刪掉重建也要擋
def test_replacing_the_service_is_refused():
    plan = image_swap_plan()
    plan["resource_changes"][2] = change("aws_ecs_service.gateway", "delete", "create")

    assert disallowed_changes(plan) == ["aws_ecs_service.gateway: delete/create"]


# 指令列入口：讀檔、有問題回 1 並把問題印出來
def test_main_returns_1_and_lists_the_problems(tmp_path, capsys):
    plan = image_swap_plan()
    plan["resource_changes"].append(change("aws_lb_listener_rule.metrics_with_token", "update"))
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")

    assert main(str(path)) == 1
    assert "aws_lb_listener_rule.metrics_with_token: update" in capsys.readouterr().out


# 指令列入口：只換映像回 0
def test_main_returns_0_for_an_image_swap(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(image_swap_plan()), encoding="utf-8")

    assert main(str(path)) == 0
