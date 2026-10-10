"""Tests for looking up a model's settings and working out the cost of a call."""

import pytest

import app.pricing
from app.config import CONFIG_PATH, ModelConfig, load_config
from app.pricing import ModelNotConfiguredError, cost_micro_usd, find_model_config

# 測試用的兩顆模型，單價照決策書：Luna $0.10 / $0.50，Sol $2 / $10（每一百萬個 token）
LUNA = ModelConfig(
    reasoning_effort="none",
    max_completion_tokens=1000,
    input_price=100_000,
    output_price=500_000,
)
SOL = ModelConfig(
    reasoning_effort="low",
    max_completion_tokens=2000,
    input_price=2_000_000,
    output_price=10_000_000,
)
MODELS = {"gpt-6-luna": LUNA, "gpt-6-sol": SOL}


# 輸入和輸出的單價不同；token 數故意不一樣，兩個單價拿反時答案才會不同
def test_cost_uses_input_and_output_prices():
    result = cost_micro_usd(LUNA, 2_000_000, 1_000_000)
    assert result == 700_000


# 決策書 D30 的例子：13 / 11 個 token 是 6.8 micro-USD，零頭一律進位成 7，不能少收
def test_cost_rounds_up_to_whole_micro_usd():
    result = cost_micro_usd(LUNA, 13, 11)
    assert result == 7


# 再小的用量也要收 1：算成 0 的話，很短的請求就能無限次免費呼叫，額度永遠扣不到
def test_cost_charges_at_least_one_for_tiny_usage():
    result = cost_micro_usd(LUNA, 1, 0)
    assert result == 1


# 同樣的 13 / 11 個 token，強模型是 13 x 2 + 11 x 10 = 136；用錯單價（算成 Luna 的 7）會被抓到
def test_cost_uses_the_prices_of_the_given_model():
    result = cost_micro_usd(SOL, 13, 11)
    assert result == 136


# 查設定：要拿到指定的那一顆，不是隨便一顆
def test_find_model_config_returns_the_named_model():
    assert find_model_config(MODELS, "gpt-6-sol") == SOL
    assert find_model_config(MODELS, "gpt-6-luna") == LUNA


# 沒有設定的模型不能當成 0 元：查不到就報錯，而且訊息要說出是哪一顆（D30）
def test_find_model_config_rejects_model_without_settings():
    with pytest.raises(ModelNotConfiguredError, match="gpt-6-astra"):
        find_model_config(MODELS, "gpt-6-astra")


# 正式的設定檔從頭走一遍：查設定、算成本，要等於決策書的數字
def test_shipped_config_gives_decision_book_costs():
    models = load_config(CONFIG_PATH).models

    assert cost_micro_usd(find_model_config(models, "gpt-6-luna"), 13, 11) == 7
    assert cost_micro_usd(find_model_config(models, "gpt-6-sol"), 13, 11) == 136


# 單價只能有一個來源：pricing.py 自己不能再留一份價目表，否則改價時會有兩個地方要改
def test_pricing_module_keeps_no_price_table_of_its_own():
    assert not hasattr(app.pricing, "PRICES")
