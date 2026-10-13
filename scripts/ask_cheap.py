"""M3 step 9: ask the cheap model one question from the routing test set, with the output cap in the config.

Run from the repo root on the personal PC only (it calls the real API):
    uv run --env-file .env python -m scripts.ask_cheap c07
"""

import sys

from openai import OpenAI, OpenAIError

from app.audit import mask
from app.config import CONFIG_PATH, GatewayConfig, load_config
from app.pricing import cost_micro_usd
from app.providers.openai_client import ChatResult, chat
from scripts.run_routing_eval import QUESTIONS_PATH, load_questions


# 用便宜模型問一次：和 Gateway 一樣先遮罩，輸出上限用設定檔裡的；交回結果與成本
def ask_cheap(client, text: str, config: GatewayConfig) -> tuple[ChatResult, int]:
    """Ask the cheap model once and return the result together with its cost in micro-USD."""
    model = config.routing.cheap_model
    settings = config.models[model]
    result = chat(
        client,
        model,
        [{"role": "user", "content": mask(text.strip())}],
        settings.reasoning_effort,
        settings.max_completion_tokens,
    )
    cost = cost_micro_usd(settings, result.input_tokens, result.output_tokens)
    return result, cost


# 在測試集裡找這個編號的題目；找不到就回 None
def find_question(questions: list[dict], question_id: str) -> dict | None:
    """Return the question with this id, or None."""
    for question in questions:
        if question["id"] == question_id:
            return question
    return None


# 命令列：後面接題目編號，例如 c07
def main() -> None:
    """Ask the cheap model the question named on the command line and print the whole answer."""
    if len(sys.argv) != 2:
        print("用法：uv run --env-file .env python -m scripts.ask_cheap c07")
        raise SystemExit(2)

    question = find_question(load_questions(QUESTIONS_PATH), sys.argv[1])
    if question is None:
        print(f"測試集裡沒有 {sys.argv[1]} 這一題")
        raise SystemExit(2)

    config = load_config(CONFIG_PATH)
    # 不讓 SDK 重試：一次就是一次
    client = OpenAI(max_retries=0, timeout=120)
    try:
        result, cost = ask_cheap(client, question["text"], config)
    except OpenAIError as exc:
        # 只印錯誤的種類，不印訊息（可能夾帶帳號資訊）
        print(f"出錯 {type(exc).__name__}")
        raise SystemExit(1)

    print(f"{question['id']} {result.model}：輸出 {result.output_tokens} token、結束原因 {result.finish_reason}、{cost} micro-USD")
    print()
    print(result.text)


if __name__ == "__main__":
    main()
