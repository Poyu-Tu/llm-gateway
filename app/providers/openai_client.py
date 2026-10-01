"""Thin wrapper around the OpenAI SDK."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatResult:
    """The fields we need from one chat call."""
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int


def chat(client, model: str, messages: list[dict], reasoning_effort: str) -> ChatResult:
    """Call the Chat Completions API and return the fields we need."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        reasoning_effort=reasoning_effort,
    )
    return ChatResult(
        text=response.choices[0].message.content,
        model=response.model,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        reasoning_tokens=response.usage.completion_tokens_details.reasoning_tokens,
    )