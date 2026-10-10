"""Tests for choosing the model from the text and the routing rules."""

from app.audit import mask
from app.config import CONFIG_PATH, RoutingConfig, load_config
from app.router import RouteDecision, choose_model

# 測試用的規則：門檻故意設成 10 個字，測試的句子才不用寫到 300 字
ROUTING = RoutingConfig(
    cheap_model="small",
    strong_model="big",
    min_chars=10,
    keywords=["分析", "debug"],
)


# 短、又沒有關鍵字：用便宜模型，理由是 default
def test_choose_model_uses_cheap_model_by_default():
    result = choose_model("Say hi", ROUTING)

    assert result == RouteDecision(model="small", reason="default")


# 剛好達到門檻（10 個字）就用強模型，理由是 length
def test_choose_model_uses_strong_model_at_the_length_threshold():
    result = choose_model("a" * 10, ROUTING)

    assert result == RouteDecision(model="big", reason="length")


# 差一個字（9 個字）還是便宜模型；和上一個測試從兩邊夾住門檻
def test_choose_model_keeps_cheap_model_just_below_the_threshold():
    result = choose_model("a" * 9, ROUTING)

    assert result == RouteDecision(model="small", reason="default")


# 一個中文字算一個字：10 個中文字達到門檻，9 個沒有
def test_choose_model_counts_each_chinese_character_as_one():
    assert choose_model("好" * 10, ROUTING).reason == "length"
    assert choose_model("好" * 9, ROUTING).reason == "default"


# 句子不長，但含中文關鍵字：用強模型，理由是 keyword
def test_choose_model_uses_strong_model_for_chinese_keyword():
    result = choose_model("請分析一下", ROUTING)

    assert result == RouteDecision(model="big", reason="keyword")


# 英文關鍵字出現在句子中間也算
def test_choose_model_uses_strong_model_for_english_keyword():
    result = choose_model("go debug", ROUTING)

    assert result == RouteDecision(model="big", reason="keyword")


# 使用者把關鍵字打成大寫也要算：DEBUG 和 debug 是同一個字
def test_choose_model_ignores_case_of_the_text():
    result = choose_model("go DEBUG", ROUTING)

    assert result == RouteDecision(model="big", reason="keyword")


# 設定檔裡的關鍵字寫成大寫開頭也要算：比的時候兩邊都要轉成小寫
def test_choose_model_ignores_case_of_the_keyword():
    routing = RoutingConfig(cheap_model="small", strong_model="big", min_chars=10, keywords=["Debug"])

    result = choose_model("go debug", routing)

    assert result == RouteDecision(model="big", reason="keyword")


# 又長又含關鍵字：理由固定記 length（先看長度），同一句話每次的理由才會一樣
def test_choose_model_reports_length_first_when_both_apply():
    result = choose_model("please debug this", ROUTING)

    assert result == RouteDecision(model="big", reason="length")


# 沒有任何關鍵字的規則也要能用：只看長度
def test_choose_model_works_without_keywords():
    routing = RoutingConfig(cheap_model="small", strong_model="big", min_chars=10, keywords=[])

    assert choose_model("Say hi", routing).model == "small"
    assert choose_model("a" * 10, routing).model == "big"


# 正式的設定檔：M2 驗收用過的三句話都要留在便宜模型，否則 S02 的示範（連續呼叫到超額）會變樣
def test_shipped_rules_keep_m2_acceptance_prompts_on_the_cheap_model():
    routing = load_config(CONFIG_PATH).routing

    for message in [
        "Say hi",
        "Write a 300-word story about a lighthouse",
        "Repeat this sentence exactly: My ID is A123456780",
    ]:
        assert choose_model(mask(message), routing).model == "gpt-6-luna"


# 正式的設定檔：遮罩的四種標籤本身不能命中關鍵字，否則含個資的訊息全部會被送去強模型
def test_shipped_keywords_do_not_match_mask_labels():
    routing = load_config(CONFIG_PATH).routing

    result = choose_model("[EMAIL] [CARD] [PHONE] [TW_ID]", routing)

    assert result.reason == "default"


# 正式的設定檔：達到門檻的長度、清單裡的每一個關鍵字，都要選到強模型
def test_shipped_rules_send_long_or_keyword_text_to_the_strong_model():
    routing = load_config(CONFIG_PATH).routing

    assert choose_model("a" * routing.min_chars, routing).model == "gpt-6-sol"
    for keyword in routing.keywords:
        assert choose_model(keyword, routing) == RouteDecision(model="gpt-6-sol", reason="keyword")
