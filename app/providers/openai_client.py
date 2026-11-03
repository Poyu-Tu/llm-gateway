"""Thin wrapper around the OpenAI SDK."""

from dataclasses import dataclass


# 一次對話的結果：只留我們需要的 6 個欄位
@dataclass(frozen=True)
class ChatResult:
    """The fields we need from one chat call."""
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    # 結束原因："stop" 是正常說完，"length" 是被輸出上限截斷
    finish_reason: str | None


# 呼叫 OpenAI，把回應轉成我們自己的格式；client 由外面傳入，這樣測試時可以塞一個假的 client，不用真的花錢打 OpenAI
def chat(client, model: str, messages: list[dict], reasoning_effort: str, max_completion_tokens: int) -> ChatResult:
    """Call the Chat Completions API and return the fields we need."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        reasoning_effort=reasoning_effort,  # 要模型「想多深」。值來自 app/config.toml：luna 是 "none"（不思考），sol 是 "low"。
        # 輸出上限：一次呼叫最多花多少，靠它才算得出來（思考 token 也算在裡面）
        max_completion_tokens=max_completion_tokens
    )
    # 沒有明細就算 0，避免程式出錯
    details = response.usage.completion_tokens_details
    if details:
        reasoning_tokens = details.reasoning_tokens
    else:
        reasoning_tokens = 0
        
    return ChatResult(
        # 回答是空的（None）就改用空字串
        text=response.choices[0].message.content or "", # 被截斷時回答可能是 None，改成空字串，後面的程式就不用每次都判斷「是不是 None」。
        model=response.model,   # OpenAI 回報的型號，最後變成稽核裡的 provider_model。
        input_tokens=response.usage.prompt_tokens,  # 把 OpenAI 的叫法翻譯成我們的叫法。
        output_tokens=response.usage.completion_tokens, # 把 OpenAI 的叫法翻譯成我們的叫法。
        reasoning_tokens=reasoning_tokens,
        finish_reason=response.choices[0].finish_reason,
    )
