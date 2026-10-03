"""Tests for the OpenAI thin wrapper, using a fake client."""

from app.providers.openai_client import ChatResult, chat
from tests.fakes import make_fake_client


# 回應的 5 個欄位要正確裝進 ChatResult
def test_chat_maps_response_fields():
    client, _ = make_fake_client()

    result = chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none")

    assert result == ChatResult(
        text="Hi there",
        model="gpt-6-luna",
        input_tokens=13,
        output_tokens=11,
        reasoning_tokens=0,
    )


# 送出的請求要帶對 model 和 reasoning_effort
def test_chat_sends_model_and_reasoning_effort():
    """The first test cannot catch a missing parameter, so check the request too."""
    client, completions = make_fake_client()

    chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none")

    assert completions.last_request["model"] == "gpt-6-luna"
    assert completions.last_request["reasoning_effort"] == "none"


# 模型沒有回答內容（None）時，text 要是空字串，程式不能出錯
def test_chat_returns_empty_text_when_content_is_none():
    client, _ = make_fake_client(content=None)

    result = chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none")

    assert result.text == ""


# 回應裡沒有思考用量的明細時，思考 token 算 0
def test_chat_counts_zero_reasoning_tokens_without_details():
    client, _ = make_fake_client(has_details=False)

    result = chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none")

    assert result.reasoning_tokens == 0