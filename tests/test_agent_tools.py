"""Tests for scripts/agent_tools.py: the agent's three local tools."""

import pytest

from app.config import CONFIG_PATH, load_config
from scripts.agent_tools import ToolError, run_tool, safe_calc, tool_price, tool_route

CONFIG = load_config(CONFIG_PATH)


# route 跟 Gateway 用同一套規則：含「設計」走強模型、理由是 keyword
def test_route_uses_the_gateway_rules_for_a_keyword_question():
    assert tool_route("幫我設計一個備份架構", CONFIG) == "gpt-6-sol（理由：keyword）"


# 短、沒有關鍵字的問題走便宜模型
def test_route_picks_the_cheap_model_for_a_short_plain_question():
    assert tool_route("今天星期幾", CONFIG) == "gpt-6-luna（理由：default）"


# 跟 Gateway 一樣先遮罩再判斷：信箱裡的 code 被遮掉，不會讓問題變成強模型
def test_route_masks_the_question_first_like_the_gateway():
    assert tool_route("寄給 code@example.com", CONFIG) == "gpt-6-luna（理由：default）"


# 空白的問題不收
def test_route_rejects_a_blank_question():
    with pytest.raises(ToolError):
        tool_route("   ", CONFIG)


# 單價從 config.toml 換算成美元／百萬 token：sol 輸出 10、luna 輸出 0.5
def test_price_reads_the_prices_from_the_config():
    assert tool_price("gpt-6-sol", CONFIG) == "輸入 2、輸出 10（美元／百萬 token）"
    assert tool_price("gpt-6-luna", CONFIG) == "輸入 0.1、輸出 0.5（美元／百萬 token）"


# 查不到的模型：說查不到，並列出有哪些
def test_price_lists_the_known_models_for_an_unknown_one():
    with pytest.raises(ToolError, match="gpt-6-luna、gpt-6-sol"):
        tool_price("gpt-4o", CONFIG)


# 四則運算與括號照數學的先後順序
def test_calc_follows_brackets_and_operator_order():
    assert safe_calc("(50*2 + 800*10) / 1000000") == "0.0081"
    assert safe_calc("10 / 0.5") == "20"
    assert safe_calc("-3 + 5") == "2"


# 不是四則運算的東西一律拒絕：呼叫函式、取屬性、次方、文字
@pytest.mark.parametrize(
    "expression",
    ["__import__('os').system('dir')", "(1).__class__", "2 ** 10", "'a' * 3", "True + 1"],
)
def test_calc_rejects_anything_but_arithmetic(expression):
    with pytest.raises(ToolError):
        safe_calc(expression)


# 看不懂的算式、除以 0、太長的算式：都變成 ToolError，不讓程式掛掉
@pytest.mark.parametrize("expression", ["1 +", "1 / 0", "1+" * 60 + "1"])
def test_calc_turns_bad_input_into_a_tool_error(expression):
    with pytest.raises(ToolError):
        safe_calc(expression)


# run_tool 照名稱分派
def test_run_tool_dispatches_by_name():
    assert run_tool("calc", "1+1", CONFIG) == "2"
    assert run_tool("price", "gpt-6-sol", CONFIG).startswith("輸入 2")


# 工具名稱錯、參數錯：回「錯誤：……」給模型看，不往外丟
def test_run_tool_returns_an_error_message_instead_of_raising():
    assert run_tool("search", "x", CONFIG) == "錯誤：沒有這個工具：search（有：route、price、calc）"
    assert run_tool("calc", "1 / 0", CONFIG) == "錯誤：不能除以 0"
