import pytest

from app.pricing import cost_micro_usd


# 輸入和輸出的單價不同；token 數故意不一樣，兩個單價拿反時答案才會不同
def test_cost_uses_input_and_output_prices():
    result = cost_micro_usd("gpt-6-luna", 2_000_000, 1_000_000)
    assert result == 700_000


# 決策書 D30 的例子：13 / 11 個 token 是 6.8 micro-USD，零頭一律進位成 7，不能少收
def test_cost_rounds_up_to_whole_micro_usd():
    result = cost_micro_usd("gpt-6-luna", 13, 11)
    assert result == 7


# 字典裡沒有單價的模型不能當成 0 元：不知道多少錢就拒絕（D30）
def test_cost_rejects_model_without_price():
    with pytest.raises(ValueError):
        cost_micro_usd("gpt-6-astra", 13, 11)


# 再小的用量也要收 1：算成 0 的話，很短的請求就能無限次免費呼叫，額度永遠扣不到
def test_cost_charges_at_least_one_for_tiny_usage():
    result = cost_micro_usd("gpt-6-luna", 1, 0)
    assert result == 1