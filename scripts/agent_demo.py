"""M7: a small agent that uses the Gateway as an ordinary client.

The Gateway is not changed. Every step is one POST /v1/chat, so every step goes through the key check,
the monthly quota, masking and the audit record. The model and this script agree on plain text:
    CALL tool(argument)  -> run the tool here, send the result back in the next step
    FINAL answer         -> stop

Run from the repo root while the Gateway is running on this machine (the key is asked for, not typed on the command line):
    uv run python -m scripts.agent_demo
    uv run python -m scripts.agent_demo --max-steps 0 --budget 0
"""

import argparse
import getpass
import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from app.config import CONFIG_PATH, GatewayConfig, load_config
from scripts.agent_tools import run_tool

# 只連本機的 Gateway：網址寫死，不讓命令列換成別的地方
GATEWAY_URL = "http://127.0.0.1:8000/v1/chat"

# 預設任務：要先查路由、再查兩顆模型的單價、再算兩次，才答得出來
DEFAULT_TASK = (
    "「幫我設計一個備份架構」這題會走哪個模型？假設用了 50 個輸入、800 個輸出 token，"
    "要花多少美元？如果改走便宜模型，貴了幾倍？"
)

# 兩道自己的煞車（E155 定案）：最多 8 步、最多花 30,000 micro-USD（US$0.03）；0 代表不限
DEFAULT_MAX_STEPS = 8
DEFAULT_BUDGET = 30_000

# 等模型回答最多幾秒：強模型 60 秒，被限流降級後便宜模型再 60 秒
TIMEOUT_SECONDS = 130

# 跟模型的文字約定：每一輪都整段重送（Gateway 不記得上一輪）
RULES = """你是一個會用工具的助理。每次只回一行，二選一：
CALL 工具名(參數)
FINAL 答案
工具：
route(問題)：這個問題在 Gateway 會走哪個模型
price(模型名)：這個模型的單價（美元／百萬 token）
calc(算式)：四則運算，只能用數字、+ - * / 和括號
一次只叫一個工具，看到結果再決定下一步。"""

# 一行只能是這兩種之一；工具名稱只收小寫英文
CALL_PATTERN = re.compile(r"^CALL\s+([a-z_]+)\((.*)\)$")
FINAL_PATTERN = re.compile(r"^FINAL\s+(.+)$")

# 畫面上的停止理由
STOP_MESSAGES = {
    "final": "完成",
    "max_steps": "達到步數上限",
    "budget": "達到 agent 自己的預算",
    "quota": "被 Gateway 擋下：額度用完（429）",
}


# 模型這一輪說了什麼：叫工具（tool、argument）、給答案（answer），或兩者都不是
@dataclass(frozen=True)
class Reply:
    """What the model asked for in one step."""
    kind: str
    tool: str = ""
    argument: str = ""
    answer: str = ""


# Gateway 回了什麼：狀態碼，成功時加上回應內容
@dataclass(frozen=True)
class GatewayReply:
    """The status code from the Gateway and, on success, the response body."""
    status: int
    body: dict


# 這一次跑完的結果：為什麼停、總共花多少、最後的答案
@dataclass
class AgentRun:
    """How the run ended."""
    stop_reason: str = ""
    spent_micro_usd: int = 0
    answer: str = ""


# 從模型的回答找第一行 CALL 或 FINAL；模型愛加的引號和反引號先去掉
def parse_reply(text: str) -> Reply:
    """Return the first CALL or FINAL line in the text, or an invalid reply when there is none."""
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("`").strip()
        call = CALL_PATTERN.match(line)
        if call:
            argument = call.group(2).strip().strip("\"'「」")
            return Reply(kind="call", tool=call.group(1), argument=argument)
        final = FINAL_PATTERN.match(line)
        if final:
            return Reply(kind="final", answer=final.group(1).strip())
    return Reply(kind="invalid")


# 這一輪要送的 message：規則、任務、做過的每一步（Gateway 不記得上一輪，所以每次都整包送）
def build_message(task: str, history: list[str]) -> str:
    """Return the message for the next step."""
    lines = [RULES, "", "任務：" + task]
    if history:
        lines.append("")
        lines.append("已經做過的步驟：")
        lines.extend(history)
    lines.append("")
    lines.append("下一步：")
    return "\n".join(lines)


# 送一次 POST /v1/chat；用 Python 內建的 urllib，不多裝套件。4xx、5xx 交回狀態碼，不往外丟
def post_chat(api_key: str, message: str) -> GatewayReply:
    """Send one message to the local Gateway and return its status code and body."""
    request = urllib.request.Request(
        GATEWAY_URL,
        data=json.dumps({"message": message}).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return GatewayReply(status=response.status, body=json.loads(response.read()))
    except urllib.error.HTTPError as exc:
        return GatewayReply(status=exc.code, body={})


# 主迴圈：送出 → 讀回答 → 叫工具 → 記下結果，直到 FINAL 或四道煞車之一
# send 由外面傳進來：正式跑用 post_chat，測試換成照劇本回答的假 Gateway
def run_agent(
    task: str,
    send: Callable[[str], GatewayReply],
    config: GatewayConfig,
    max_steps: int,
    budget_micro_usd: int,
    log: Callable[[str], None],
) -> AgentRun:
    """Run the agent until it answers or one of the limits stops it."""
    run = AgentRun()
    history: list[str] = []
    step = 0
    while True:
        # 自己的兩道煞車都在送出之前檢查；一步要花多少要做完才知道，所以最後一步可能超出預算
        if max_steps > 0 and step >= max_steps:
            run.stop_reason = "max_steps"
            return run
        if budget_micro_usd > 0 and run.spent_micro_usd >= budget_micro_usd:
            run.stop_reason = "budget"
            return run

        step = step + 1
        reply = send(build_message(task, history))
        # Gateway 的煞車：額度用完回 429；其他錯誤也停，不重試
        if reply.status == 429:
            run.stop_reason = "quota"
            return run
        if reply.status != 200:
            run.stop_reason = f"http_{reply.status}"
            return run

        cost = reply.body["cost_micro_usd"]
        run.spent_micro_usd = run.spent_micro_usd + cost
        # 畫面上每一步都印單號：拿去 audit 表對得到同一筆
        prefix = f"{step}. [{reply.body['request_id']}｜{reply.body['model']}｜{cost} micro-USD]"
        parsed = parse_reply(reply.body["reply"])
        if parsed.kind == "final":
            log(f"{prefix} FINAL {parsed.answer}")
            run.answer = parsed.answer
            run.stop_reason = "final"
            return run
        if parsed.kind == "call":
            result = run_tool(parsed.tool, parsed.argument, config)
            action = f"CALL {parsed.tool}({parsed.argument}) → {result}"
        else:
            action = "格式不對：只能回一行 CALL 或 FINAL"
        log(f"{prefix} {action}")
        history.append(f"{step}. {action}")


# 命令列：Key 用 getpass 問（不顯示、不進命令歷史、錄影也拍不到）
def main() -> None:
    """Ask for the API key and run the agent against the local Gateway."""
    parser = argparse.ArgumentParser(description="Run the M7 agent against the local Gateway.")
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS, help="0 means no limit")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET, help="micro-USD; 0 means no limit")
    args = parser.parse_args()

    api_key = getpass.getpass("API Key: ")
    config = load_config(CONFIG_PATH)
    run = run_agent(
        args.task,
        lambda message: post_chat(api_key, message),
        config,
        args.max_steps,
        args.budget,
        print,
    )
    reason = STOP_MESSAGES.get(run.stop_reason, "Gateway 回錯誤：" + run.stop_reason)
    print(f"停止：{reason}；共花 {run.spent_micro_usd} micro-USD")
    if run.answer:
        print("回答：" + run.answer)


if __name__ == "__main__":
    main()
