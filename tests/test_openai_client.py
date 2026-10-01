"""Tests for the OpenAI thin wrapper, using a fake client."""

from types import SimpleNamespace

from app.providers.openai_client import ChatResult, chat


class FakeCompletions:
    """Stands in for client.chat.completions and records the request."""

    def __init__(self):
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(
            model="gpt-6-luna",
            choices=[SimpleNamespace(message=SimpleNamespace(content="Hi there"))],
            usage=SimpleNamespace(
                prompt_tokens=13,
                completion_tokens=11,
                completion_tokens_details=SimpleNamespace(reasoning_tokens=0),
            ),
        )


def make_fake_client():
    """Return the fake client and its completions, so tests can check the request."""
    completions = FakeCompletions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


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


def test_chat_sends_model_and_reasoning_effort():
    """The first test cannot catch a missing parameter, so check the request too."""
    client, completions = make_fake_client()

    chat(client, "gpt-6-luna", [{"role": "user", "content": "Say hi"}], "none")

    assert completions.last_request["model"] == "gpt-6-luna"
    assert completions.last_request["reasoning_effort"] == "none"