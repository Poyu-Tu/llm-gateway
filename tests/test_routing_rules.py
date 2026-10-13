"""Tests that pin the routing rules and output caps decided from the step 7 test set (10/13)."""

from app.config import CONFIG_PATH, load_config
from app.router import choose_model
from scripts.routing_eval import RUN_PATH, load_rows, summarize

# 正式的設定檔：這個檔的測試都在守「步驟 7 定案的規則」
CONFIG = load_config(CONFIG_PATH)
ROUTING = CONFIG.routing


# 20 題用現在的規則重新分流：送對 17 題，送錯的就是定案時接受的那三題
def test_shipped_rules_route_the_test_set_as_decided():
    result = summarize(load_rows(RUN_PATH), ROUTING)

    assert result.matched == 17
    assert result.wasted == ["s11", "s12"]
    assert result.risky == ["c06"]


# 簡報與結語用的數字：全部用強模型 55,724、現在的規則 41,888，省 24.8%
def test_shipped_rules_save_the_recorded_amount():
    result = summarize(load_rows(RUN_PATH), ROUTING)

    assert result.all_strong == 55724
    assert result.routed == 41888
    assert result.saving_percent == 24.8


# 「比較」當副詞用（比較有禮貌、比較常用）時是簡單的問題，不能送去強模型
def test_everyday_use_of_bijiao_stays_on_the_cheap_model():
    for text in ["幫我把這句話改得比較有禮貌", "「帳號」和「賬號」哪個比較常用？"]:
        assert choose_model(text, ROUTING).model == ROUTING.cheap_model


# 真的要做比較時（請比較、優缺點）仍然送去強模型
def test_asking_for_a_comparison_goes_to_the_strong_model():
    for text in ["請比較 A 和 B 兩個方案", "這兩個方案各有什麼優缺點？"]:
        assert choose_model(text, ROUTING).model == ROUTING.strong_model


# 同一種問題，用中文問和用英文問，要送去同一顆模型
def test_english_and_chinese_design_questions_go_to_the_same_model():
    pairs = [
        ("幫我設計一個登入頁", "Design a login page"),
        ("請說明這個系統的架構", "Explain the architecture of this system"),
    ]
    for chinese, english in pairs:
        assert choose_model(chinese, ROUTING).model == ROUTING.strong_model
        assert choose_model(english, ROUTING).model == ROUTING.strong_model


# 輸出上限：便宜模型 1,000 時有兩題被截斷（c03、c07），改為 2,000；強模型最多用到 1,372，維持 2,000
def test_shipped_output_caps_follow_the_test_set():
    assert CONFIG.models[ROUTING.cheap_model].max_completion_tokens == 2000
    assert CONFIG.models[ROUTING.strong_model].max_completion_tokens == 2000
