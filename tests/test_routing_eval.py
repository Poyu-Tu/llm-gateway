"""Tests for scripts/routing_eval.py: the saving percentage and the misrouted questions."""

import pytest

from app.config import RoutingConfig
from scripts.routing_eval import saving_percent, summarize

# 測試用的規則：模型叫 small 與 big，18 個字或含 debug 才用 big
# 名稱故意和正式的不同：函式若偷用寫死的模型名稱，馬上查不到成本
TEST_ROUTING = RoutingConfig(cheap_model="small", strong_model="big", min_chars=18, keywords=["debug"])


# 做一題假的紀錄：和結果檔同樣的形狀，只放這裡用得到的欄位
def make_row(question_id, expected, masked, small_cost, big_cost):
    """Return one recorded question with the cost of each model."""
    return {
        "id": question_id,
        "expected": expected,
        "masked": masked,
        "answers": {
            "small": {"cost_micro_usd": small_cost},
            "big": {"cost_micro_usd": big_cost},
        },
    }


# 兩題都送對：短句 → small（2 對 40），含 debug → big（5 對 100）
def two_correct_rows():
    """Return a simple question and a hard one, both labelled correctly."""
    return [
        make_row("s01", "cheap", "Say hi", 2, 40),
        make_row("c01", "strong", "Please debug it", 5, 100),
    ]


# 全部用強模型：每一題都拿 big 的成本，40 + 100
def test_summarize_adds_up_the_all_strong_cost():
    result = summarize(two_correct_rows(), TEST_ROUTING)

    assert result.all_strong == 140


# 照規則分流：短句拿 small 的 2，含 debug 拿 big 的 100
def test_summarize_adds_up_the_routed_cost():
    result = summarize(two_correct_rows(), TEST_ROUTING)

    assert result.routed == 102


# 省下的比例：(140 - 102) / 140 = 27.14…%，取到小數第一位
def test_saving_percent_compares_with_the_all_strong_cost():
    assert saving_percent(140, 102) == 27.1


# 比例要用「全部用強模型」當分母：分流比較便宜時，答案不能超過 100
def test_saving_percent_is_100_when_routing_costs_nothing():
    assert saving_percent(80, 0) == 100.0


# 分流和全部用強模型一樣貴：一毛都沒省
def test_saving_percent_is_zero_when_nothing_is_saved():
    assert saving_percent(80, 80) == 0.0


# 沒有成本可以比：不能除以 0
def test_saving_percent_rejects_zero_cost():
    with pytest.raises(ValueError):
        saving_percent(0, 0)


# 成績單裡的比例要和兩個總數對得起來
def test_summarize_reports_the_saving_percent():
    result = summarize(two_correct_rows(), TEST_ROUTING)

    assert result.saving_percent == 27.1


# 兩題都送對：送對 2 題，沒有送錯的
def test_summarize_counts_the_matches():
    result = summarize(two_correct_rows(), TEST_ROUTING)

    assert result.matched == 2
    assert result.wasted == []
    assert result.risky == []


# 簡單的題目含 debug，被送去 big：記成「多花錢」
def test_summarize_lists_simple_questions_sent_to_the_strong_model():
    rows = [make_row("s02", "cheap", "What does debug mean", 3, 60)]

    result = summarize(rows, TEST_ROUTING)

    assert result.wasted == ["s02"]
    assert result.risky == []
    assert result.matched == 0


# 複雜的題目很短又沒有關鍵字，被送去 small：記成「可能答不好」
def test_summarize_lists_hard_questions_sent_to_the_cheap_model():
    rows = [make_row("c02", "strong", "Why so slow", 7, 90)]

    result = summarize(rows, TEST_ROUTING)

    assert result.risky == ["c02"]
    assert result.wasted == []
    assert result.matched == 0


# 送錯的題目照順序列出來，兩種不能混在一起
def test_summarize_keeps_both_kinds_of_misroutes_apart():
    rows = two_correct_rows() + [
        make_row("s02", "cheap", "What does debug mean", 3, 60),
        make_row("c02", "strong", "Why so slow", 7, 90),
        make_row("s03", "cheap", "A sentence of more than 18 chars", 4, 70),
    ]

    result = summarize(rows, TEST_ROUTING)

    assert result.matched == 2
    assert result.wasted == ["s02", "s03"]
    assert result.risky == ["c02"]


# 換一組規則（沒有關鍵字），同樣的資料要算出不同的結果：函式用的是交進來的規則
def test_summarize_uses_the_given_rules():
    no_keywords = RoutingConfig(cheap_model="small", strong_model="big", min_chars=18, keywords=[])

    result = summarize(two_correct_rows(), no_keywords)

    assert result.routed == 2 + 5
    assert result.risky == ["c01"]
