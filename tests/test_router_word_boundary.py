"""Tests for keyword matching: an English keyword must not start in the middle of another word."""

from app.config import CONFIG_PATH, RoutingConfig, load_config
from app.router import RouteDecision, choose_model

# 測試用的規則：門檻設得很大，這個檔的句子只會因為關鍵字被送去強模型
ROUTING = RoutingConfig(
    cheap_model="small",
    strong_model="big",
    min_chars=1000,
    keywords=["分析", "code", "debug", "trade-off", "a.b"],
)


# 關鍵字藏在別的字中間：不算（decode、barcode、encode 都不是在寫程式）
def test_keyword_inside_another_word_does_not_count():
    for text in ["decode this", "scan the barcode", "encode it", "xdebug", "2code"]:
        assert choose_model(text, ROUTING) == RouteDecision(model="small", reason="default")


# 關鍵字開頭的字（debugging、codebase）：照算，不然「幫我 debugging」會被送去便宜模型
def test_word_that_starts_with_the_keyword_still_counts():
    for text in ["fix my debugging", "read the codebase", "list the codes"]:
        assert choose_model(text, ROUTING) == RouteDecision(model="big", reason="keyword")


# 關鍵字在整句的最前面（前面沒有任何字）：算
def test_keyword_at_the_start_of_the_text_counts():
    assert choose_model("debug this", ROUTING) == RouteDecision(model="big", reason="keyword")


# 前面是中文字或標點：算（只擋英文字母與數字；中文沒有空格，前面常常緊貼著中文）
def test_keyword_after_chinese_or_punctuation_counts():
    for text in ["請幫我debug這個", "(debug)", "re-code it", "OK,code"]:
        assert choose_model(text, ROUTING) == RouteDecision(model="big", reason="keyword")


# 大小寫照舊不分
def test_keyword_ignores_case():
    assert choose_model("DeBuG it", ROUTING).reason == "keyword"
    assert choose_model("xDEBUG", ROUTING).reason == "default"


# 中文關鍵字不受影響：前面緊貼英文字母或數字也照算
def test_chinese_keyword_is_still_found_anywhere():
    for text in ["請分析一下", "abc分析", "3分析"]:
        assert choose_model(text, ROUTING) == RouteDecision(model="big", reason="keyword")


# 關鍵字裡的符號是字面意思：a.b 的點不是「任何字」，axb 不能中
def test_symbols_in_a_keyword_are_literal():
    assert choose_model("axb", ROUTING).reason == "default"
    assert choose_model("see a.b here", ROUTING).reason == "keyword"
    assert choose_model("a trade-off", ROUTING).reason == "keyword"


# 正式的規則：decode、barcode 留在便宜模型；debugging、designing 仍送強模型
def test_shipped_rules_follow_the_word_boundary():
    routing = load_config(CONFIG_PATH).routing

    for text in ["decode this base64", "scan the barcode"]:
        assert choose_model(text, routing).model == routing.cheap_model
    for text in ["I keep debugging this", "I am designing a login page"]:
        assert choose_model(text, routing).model == routing.strong_model
