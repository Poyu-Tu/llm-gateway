"""Thin wrapper around the OpenAI SDK."""

from dataclasses import dataclass


# 一次對話的結果：只留我們需要的 5 個欄位
@dataclass(frozen=True)
class ChatResult:
    """The fields we need from one chat call."""
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int


# 呼叫 OpenAI，把回應轉成我們自己的格式；client 由外面傳入，方便測試
def chat(client, model: str, messages: list[dict], reasoning_effort: str) -> ChatResult:
    """Call the Chat Completions API and return the fields we need."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        reasoning_effort=reasoning_effort,
    )
    # 沒有明細就算 0，避免程式出錯
    details = response.usage.completion_tokens_details
    if details:
        reasoning_tokens = details.reasoning_tokens
    else:
        reasoning_tokens = 0
        
    return ChatResult(
        # 回答是空的（None）就改用空字串
        text=response.choices[0].message.content or "",
        model=response.model,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        reasoning_tokens=reasoning_tokens,
    )