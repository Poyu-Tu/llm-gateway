"""Tests for reading and checking the gateway settings from a TOML file."""

import pytest

from app.config import CONFIG_PATH, ConfigError, ModelConfig, RoutingConfig, load_config

# 測試用的設定：每個數字都故意不一樣，欄位拿反時答案才會不同
SAMPLE = """
[routing]
cheap_model = "small"
strong_model = "big"
min_chars = 44
keywords = ["分析", "debug"]

[models.small]
reasoning_effort = "none"
max_completion_tokens = 333
input_price = 111
output_price = 222

[models.big]
reasoning_effort = "low"
max_completion_tokens = 666
input_price = 444
output_price = 555
"""


# 把一段設定文字存成暫時的檔案，交回檔案位置
def write_config(tmp_path, text):
    """Write the text to a temporary TOML file and return its path."""
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


# 路由規則的四個欄位要各自放對位置；關鍵字含中文，順便確認檔案是照 UTF-8 讀的
def test_load_config_reads_routing_rules(tmp_path):
    path = write_config(tmp_path, SAMPLE)

    config = load_config(path)

    assert config.routing == RoutingConfig(
        cheap_model="small",
        strong_model="big",
        min_chars=44,
        keywords=["分析", "debug"],
    )


# 一顆模型的四個欄位要各自放對位置
def test_load_config_reads_model_fields(tmp_path):
    path = write_config(tmp_path, SAMPLE)

    config = load_config(path)

    assert config.models["small"] == ModelConfig(
        reasoning_effort="none",
        max_completion_tokens=333,
        input_price=111,
        output_price=222,
    )


# 每一顆模型都要讀到，而且各拿各的設定，不能全部變成同一顆
def test_load_config_reads_every_model(tmp_path):
    path = write_config(tmp_path, SAMPLE)

    config = load_config(path)

    assert sorted(config.models) == ["big", "small"]
    assert config.models["big"].input_price == 444
    assert config.models["big"].reasoning_effort == "low"


# 正式的設定檔：單價要等於決策書的數字（Luna $0.10 / $0.50，Sol $2 / $10，每一百萬個 token）
# 單價在這裡再寫一次是故意的：設定檔少打一個 0，要有另一個地方對得出來
def test_shipped_config_has_decision_book_prices():
    config = load_config(CONFIG_PATH)

    assert config.models["gpt-6-luna"].input_price == 100_000
    assert config.models["gpt-6-luna"].output_price == 500_000
    assert config.models["gpt-6-sol"].input_price == 2_000_000
    assert config.models["gpt-6-sol"].output_price == 10_000_000


# 正式的設定檔：便宜模型不思考、強模型少量思考；沒設定的話 OpenAI 會用預設的思考量，暗中多花錢
def test_shipped_config_sets_models_and_reasoning_effort():
    config = load_config(CONFIG_PATH)

    assert config.routing.cheap_model == "gpt-6-luna"
    assert config.routing.strong_model == "gpt-6-sol"
    assert config.models["gpt-6-luna"].reasoning_effort == "none"
    assert config.models["gpt-6-sol"].reasoning_effort == "low"


# ---- 以下是「讀進來就檢查」：設定有問題要拒絕，而且訊息要說出是哪一項 ----
# 每個測試都用 match 對訊息：確認它是為了這一項被擋下，不是碰巧被別的檢查擋掉


# 路由指到一顆沒有設定的強模型：等於會選到不知道多少錢的模型，要拒絕
def test_load_config_rejects_strong_model_without_settings(tmp_path):
    text = SAMPLE.replace('strong_model = "big"', 'strong_model = "huge"')
    path = write_config(tmp_path, text)

    with pytest.raises(ConfigError, match="huge"):
        load_config(path)


# 便宜模型也一樣要有設定；只檢查強模型的話，這個測試會抓到
def test_load_config_rejects_cheap_model_without_settings(tmp_path):
    text = SAMPLE.replace('cheap_model = "small"', 'cheap_model = "tiny"')
    path = write_config(tmp_path, text)

    with pytest.raises(ConfigError, match="tiny"):
        load_config(path)


# 單價寫成小數（把 micro-USD 寫成美元）：全程整數的計算會壞掉，要拒絕
def test_load_config_rejects_price_written_as_decimal(tmp_path):
    text = SAMPLE.replace("input_price = 444", "input_price = 0.1")
    path = write_config(tmp_path, text)

    with pytest.raises(ConfigError, match="big.input_price"):
        load_config(path)


# 單價是 0 等於這顆模型免費，額度永遠扣不到，要拒絕
def test_load_config_rejects_zero_price(tmp_path):
    text = SAMPLE.replace("output_price = 222", "output_price = 0")
    path = write_config(tmp_path, text)

    with pytest.raises(ConfigError, match="small.output_price"):
        load_config(path)


# 輸出上限是 0：模型一個字都不能回
def test_load_config_rejects_zero_output_cap(tmp_path):
    text = SAMPLE.replace("max_completion_tokens = 666", "max_completion_tokens = 0")
    path = write_config(tmp_path, text)

    with pytest.raises(ConfigError, match="big.max_completion_tokens"):
        load_config(path)


# 字數門檻是 0：每一句話都「達到門檻」，全部送去強模型
def test_load_config_rejects_zero_min_chars(tmp_path):
    text = SAMPLE.replace("min_chars = 44", "min_chars = 0")
    path = write_config(tmp_path, text)

    with pytest.raises(ConfigError, match="routing.min_chars"):
        load_config(path)


# 空字串出現在任何句子裡：混進關鍵字清單，所有請求都會被送去強模型
def test_load_config_rejects_empty_keyword(tmp_path):
    text = SAMPLE.replace('keywords = ["分析", "debug"]', 'keywords = ["分析", ""]')
    path = write_config(tmp_path, text)

    with pytest.raises(ConfigError, match="keywords"):
        load_config(path)


# 只有空格的關鍵字也一樣：幾乎每一句英文都有空格
def test_load_config_rejects_blank_keyword(tmp_path):
    text = SAMPLE.replace('keywords = ["分析", "debug"]', 'keywords = ["分析", " "]')
    path = write_config(tmp_path, text)

    with pytest.raises(ConfigError, match="keywords"):
        load_config(path)


# 少了一個欄位：要當成設定錯誤，並說出少的是哪一個
def test_load_config_rejects_missing_setting(tmp_path):
    text = SAMPLE.replace("output_price = 555\n", "")
    path = write_config(tmp_path, text)

    with pytest.raises(ConfigError, match="output_price"):
        load_config(path)