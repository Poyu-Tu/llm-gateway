"""Tests for reading the gateway settings from a TOML file."""

from app.config import CONFIG_PATH, ModelConfig, RoutingConfig, load_config

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
