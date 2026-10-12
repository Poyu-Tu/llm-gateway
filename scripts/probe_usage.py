"""One-off probe for M3 step 6: what OpenAI reports in usage for our two models.

Run from the repo root on the personal PC only (it calls the real API):
    uv run --env-file .env python -m scripts.probe_usage
"""

from openai import OpenAI

from app.config import CONFIG_PATH, load_config
from app.pricing import cost_micro_usd

# 要問的四次：（模型, 輸出上限, 問題）；上限寫 None 代表用設定檔裡那顆模型自己的上限
# 第 2、4 次故意把上限壓到很小，看回答被截斷時長什麼樣子
PROBES = [
    ("gpt-6-sol", None, "請比較 TCP 與 UDP，各舉兩個適合的使用情境。"),
    ("gpt-6-sol", 16, "請比較 TCP 與 UDP，各舉兩個適合的使用情境。"),
    ("gpt-6-luna", None, "請用大約 100 個字介紹台灣的夜市文化。"),
    ("gpt-6-luna", 16, "請用大約 100 個字介紹台灣的夜市文化。"),
]


# 把回答濃縮成一行，只留開頭幾個字，方便在終端機上看
def preview(text: str) -> str:
    """Return the first characters of the text on one line."""
    one_line = text.replace("\n", " ")
    return one_line[:40]


# 依序問四次，把供應商回報的用量逐項印出來；不印金鑰、不印請求編號
def main() -> None:
    """Call each model and print what the provider reports."""
    config = load_config(CONFIG_PATH)
    # 不讓 SDK 自己重試：一次就是一次，帳才對得起來
    client = OpenAI(max_retries=0, timeout=60)
    total = 0

    for number, (model, cap, prompt) in enumerate(PROBES, start=1):
        settings = config.models[model]
        if cap is None:
            cap = settings.max_completion_tokens

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            reasoning_effort=settings.reasoning_effort,
            max_completion_tokens=cap,
        )

        usage = response.usage
        details = usage.completion_tokens_details
        if details:
            reasoning_tokens = details.reasoning_tokens
        else:
            reasoning_tokens = None
        content = response.choices[0].message.content or ""
        cost = cost_micro_usd(settings, usage.prompt_tokens, usage.completion_tokens)
        total = total + cost

        print(f"[{number}] {model} | 思考 {settings.reasoning_effort} | 上限 {cap}")
        print(f"    回報的模型: {response.model}")
        print(f"    finish_reason: {response.choices[0].finish_reason}")
        print(f"    prompt_tokens: {usage.prompt_tokens} | completion_tokens: {usage.completion_tokens} | reasoning_tokens: {reasoning_tokens}")
        print(f"    看得到的回答: {len(content)} 字 | 開頭: {preview(content)}")
        print(f"    依我們的單價: {cost} micro-USD")

    print(f"合計: {total} micro-USD")


if __name__ == "__main__":
    main()
