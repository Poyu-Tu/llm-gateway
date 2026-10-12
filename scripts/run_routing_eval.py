"""M3 step 7: ask both models every question in the routing test set and save what they report.

Run from the repo root on the personal PC only (it calls the real API):
    uv run --env-file .env python -m scripts.run_routing_eval
"""

import json
import tomllib
from pathlib import Path

from openai import OpenAI, OpenAIError

from app.audit import mask
from app.config import CONFIG_PATH, load_config
from app.pricing import cost_micro_usd
from app.providers.openai_client import chat
from app.router import choose_model

# 測試集（20 題）與結果檔的位置
QUESTIONS_PATH = Path(__file__).parent / "routing_questions.toml"
RESULT_PATH = Path(__file__).parent.parent / "docs" / "logs" / "m3-step7-routing-run.json"


# 讀測試集：每一題有編號、應該由哪一種模型回答、題目本身
def load_questions(path: Path) -> list[dict]:
    """Return the questions in the order they are written in the file."""
    with open(path, "rb") as file:
        return tomllib.load(file)["questions"]


# 讀之前跑到一半的結果：中途出錯重跑時，已經問過的就不再問（不重複花錢）
def load_results(path: Path) -> dict:
    """Return the saved results by question id, or an empty dict when there are none."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    results = {}
    for row in data["questions"]:
        results[row["id"]] = row
    return results


# 存結果：照測試集的順序寫出來，連同當時的模型設定（之後才知道這些數字是用什麼設定量的）
def save_results(path: Path, results: dict, questions: list[dict], config) -> None:
    """Write every finished question, plus the model settings used, to the result file."""
    settings = {}
    for name, model in config.models.items():
        settings[name] = {
            "reasoning_effort": model.reasoning_effort,
            "max_completion_tokens": model.max_completion_tokens,
            "input_price": model.input_price,
            "output_price": model.output_price,
        }
    rows = []
    for question in questions:
        if question["id"] in results:
            rows.append(results[question["id"]])
    data = {"settings": settings, "questions": rows}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


# 每一題都問兩顆模型：路由選哪一顆照記，但兩顆都問，才算得出「全部用強模型」要花多少
def main() -> None:
    """Ask both models every question and save the token counts, costs and answers."""
    config = load_config(CONFIG_PATH)
    # 不讓 SDK 重試：一次就是一次，帳才對得起來；強模型寫長答案可能要比較久，逾時放寬到 120 秒
    client = OpenAI(max_retries=0, timeout=120)
    questions = load_questions(QUESTIONS_PATH)
    results = load_results(RESULT_PATH)
    models = [config.routing.cheap_model, config.routing.strong_model]

    for number, question in enumerate(questions, start=1):
        # 和 Gateway 一樣：先遮罩，再用遮罩後的內容路由、送給模型
        masked = mask(question["text"].strip())
        decision = choose_model(masked, config.routing)

        row = results.get(question["id"], {"answers": {}})
        row["id"] = question["id"]
        row["expected"] = question["expected"]
        row["masked"] = masked
        row["chars"] = len(masked)
        row["routed_model"] = decision.model
        row["route_reason"] = decision.reason
        results[question["id"]] = row

        for model in models:
            if model in row["answers"]:
                print(f"[{number:02}/{len(questions)}] {question['id']} {model}: 已經問過，略過")
                continue
            settings = config.models[model]
            try:
                result = chat(
                    client,
                    model,
                    [{"role": "user", "content": masked}],
                    settings.reasoning_effort,
                    settings.max_completion_tokens,
                )
            except OpenAIError as exc:
                # 出錯就停下來：只印錯誤的種類，不印訊息（可能夾帶帳號資訊）；已經存下的結果不會不見
                print(f"[{number:02}/{len(questions)}] {question['id']} {model}: 出錯 {type(exc).__name__}")
                print("已經問過的都存在結果檔裡；處理好之後重跑同一個指令，會從這一題繼續")
                raise SystemExit(1)
            cost = cost_micro_usd(settings, result.input_tokens, result.output_tokens)
            row["answers"][model] = {
                "provider_model": result.model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "reasoning_tokens": result.reasoning_tokens,
                "finish_reason": result.finish_reason,
                "cost_micro_usd": cost,
                "text": result.text,
            }
            # 每問完一次就存檔：中途出錯時，已經花錢拿到的結果不會不見
            save_results(RESULT_PATH, results, questions, config)
            print(
                f"[{number:02}/{len(questions)}] {question['id']} {model}: "
                f"輸出 {result.output_tokens}（思考 {result.reasoning_tokens}）"
                f" {result.finish_reason} {cost} micro-USD"
            )

    total = 0
    for row in results.values():
        for answer in row["answers"].values():
            total = total + answer["cost_micro_usd"]
    print(f"完成：{len(results)} 題，這個結果檔裡的呼叫合計 {total} micro-USD")
    print(f"結果檔：{RESULT_PATH}")


if __name__ == "__main__":
    main()
