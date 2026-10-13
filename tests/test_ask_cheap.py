"""Tests for scripts/ask_cheap.py: always the cheap model, always the cap from the config."""

from app.config import CONFIG_PATH, load_config
from scripts.ask_cheap import ask_cheap, find_question
from tests.fakes import make_fake_client

CONFIG = load_config(CONFIG_PATH)
CHEAP = CONFIG.routing.cheap_model


# 問的是便宜模型，輸出上限是設定檔裡那顆模型的上限
def test_asks_the_cheap_model_with_its_cap_from_the_config():
    client, completions = make_fake_client()

    ask_cheap(client, "Say hi", CONFIG)

    request = completions.last_request
    assert request["model"] == CHEAP
    assert request["max_completion_tokens"] == CONFIG.models[CHEAP].max_completion_tokens


# 先遮罩再送出：個資不會直接送給模型
def test_masks_the_question_before_sending_it():
    client, completions = make_fake_client()

    ask_cheap(client, "Mail test@example.com now", CONFIG)

    content = completions.last_request["messages"][0]["content"]
    assert "test@example.com" not in content
    assert "[EMAIL]" in content


# 回傳回答的結束原因與成本：被截斷時看得出來
def test_returns_finish_reason_and_the_cost():
    client, _ = make_fake_client(finish_reason="length")

    result, cost = ask_cheap(client, "Say hi", CONFIG)

    assert result.finish_reason == "length"
    # 假的回應固定是輸入 13、輸出 11 token：13 × 0.1 + 11 × 0.5 = 6.8，進位成 7
    assert cost == 7


# 找得到的編號回題目，找不到回 None
def test_find_question_by_id():
    questions = [{"id": "s01"}, {"id": "c07"}]

    assert find_question(questions, "c07") == {"id": "c07"}
    assert find_question(questions, "x99") is None
