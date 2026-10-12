"""Tests for the OpenAI thin wrapper, using a fake client."""

from app.providers.openai_client import ChatResult, chat
from tests.fakes import make_fake_client


# 回應的 6 個欄位要正確裝進 ChatResult
def test_chat_maps_response_fields():
    client, _ = make_fake_client()

    result = chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none", 500)

    assert result == ChatResult(
        text="Hi there",
        model="gpt-6-luna",
        input_tokens=13,
        output_tokens=11,
        reasoning_tokens=0,
        finish_reason="stop",
    )


# 送出的請求要帶對 model 和 reasoning_effort
def test_chat_sends_model_and_reasoning_effort():
    """The first test cannot catch a missing parameter, so check the request too."""
    client, completions = make_fake_client()

    chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none", 500)

    assert completions.last_request["model"] == "gpt-6-luna"
    assert completions.last_request["reasoning_effort"] == "none"


# 送出的請求要帶上輸出上限：沒有帶的話，一次呼叫能花多少就沒有上限
def test_chat_sends_the_output_cap():
    client, completions = make_fake_client()

    chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none", 500)

    assert completions.last_request["max_completion_tokens"] == 500


# 模型沒有回答內容（None）時，text 要是空字串，程式不能出錯
def test_chat_returns_empty_text_when_content_is_none():
    client, _ = make_fake_client(content=None)

    result = chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none", 500)

    assert result.text == ""


# 回應裡沒有思考用量的明細時，思考 token 算 0
def test_chat_counts_zero_reasoning_tokens_without_details():
    client, _ = make_fake_client(has_details=False)

    result = chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none", 500)

    assert result.reasoning_tokens == 0


# 結束原因要照實帶回來：被輸出上限截斷時是 "length"（10/12 實測：強模型被截斷時回答可能整個是空的）
def test_chat_returns_the_finish_reason():
    client, _ = make_fake_client(content="", finish_reason="length")

    result = chat(client, "gpt-6-sol", [{"role": "user", "content": "Say hi"}], "low", 16)

    assert result.finish_reason == "length"
    assert result.text == ""
