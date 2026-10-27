"""Tests for scripts/agent_demo.py: parsing the model's reply and the agent loop with its four stops."""

from app.config import CONFIG_PATH, load_config
from scripts.agent_demo import GatewayReply, build_message, parse_reply, run_agent

CONFIG = load_config(CONFIG_PATH)
TASK = "sol 的輸出單價是 luna 的幾倍？"


# 假的 Gateway：照劇本一步一步回答，並記下每一步收到的 message
class ScriptedGateway:
    """Answers each step from a list of replies and keeps the messages it received."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.messages = []

    def __call__(self, message):
        self.messages.append(message)
        return self.replies.pop(0)


# 一個成功的回應：模型說了 text、這一步花了 cost
def ok(text, cost=3000, request_id="req"):
    body = {"request_id": request_id, "reply": text, "model": "gpt-6-sol", "cost_micro_usd": cost}
    return GatewayReply(status=200, body=body)


# 跑一次 agent，交回結果、假 Gateway 和印出來的每一行
def run(replies, max_steps=8, budget=30_000):
    gateway = ScriptedGateway(replies)
    lines = []
    result = run_agent(TASK, gateway, CONFIG, max_steps, budget, lines.append)
    return result, gateway, lines


# 認得 CALL：工具名稱與參數分開，括號裡還有括號也不會切錯
def test_parse_reply_reads_a_call_with_brackets_inside():
    reply = parse_reply("CALL calc((50*2 + 800*10) / 1000000)")

    assert reply.kind == "call"
    assert reply.tool == "calc"
    assert reply.argument == "(50*2 + 800*10) / 1000000"


# 模型常在前面多講一句、加反引號或引號：取第一行合格的，引號去掉
def test_parse_reply_skips_chatter_and_strips_quotes():
    reply = parse_reply("好的，我先查價格。\n`CALL price(\"gpt-6-sol\")`")

    assert reply.kind == "call"
    assert reply.argument == "gpt-6-sol"


# 認得 FINAL
def test_parse_reply_reads_a_final_answer():
    reply = parse_reply("FINAL 貴 20 倍")

    assert reply.kind == "final"
    assert reply.answer == "貴 20 倍"


# 兩種都不是：invalid
def test_parse_reply_marks_anything_else_invalid():
    assert parse_reply("我覺得大概 20 倍吧").kind == "invalid"


# 每一輪都帶規則與任務；第一輪沒有「已經做過的步驟」
def test_build_message_without_history_has_rules_and_task():
    message = build_message(TASK, [])

    assert "CALL 工具名(參數)" in message
    assert "任務：" + TASK in message
    assert "已經做過的步驟" not in message


# 正常完成：CALL → CALL → CALL → FINAL；工具真的被叫、結果帶進下一輪、花費累加
def test_run_agent_calls_tools_and_finishes():
    replies = [
        ok("CALL price(gpt-6-luna)"),
        ok("CALL price(gpt-6-sol)"),
        ok("CALL calc(10 / 0.5)"),
        ok("FINAL 貴 20 倍", cost=1000),
    ]

    result, gateway, lines = run(replies)

    assert result.stop_reason == "final"
    assert result.answer == "貴 20 倍"
    assert result.spent_micro_usd == 10_000
    assert "3. CALL calc(10 / 0.5) → 20" in gateway.messages[3]
    assert len(lines) == 4


# 每一步印出單號、模型、花費：拿去 audit 表對得到
def test_run_agent_logs_the_request_id_model_and_cost_of_each_step():
    result, gateway, lines = run([ok("FINAL 好", cost=1234, request_id="abc-123")])

    assert lines == ["1. [abc-123｜gpt-6-sol｜1234 micro-USD] FINAL 好"]


# 格式不對、叫了不存在的工具：都記成這一步的結果讓模型修正，迴圈不中斷
def test_run_agent_feeds_mistakes_back_to_the_model():
    replies = [ok("大概 20 倍"), ok("CALL search(價格)"), ok("FINAL 20 倍")]

    result, gateway, lines = run(replies)

    assert result.stop_reason == "final"
    assert "1. 格式不對" in gateway.messages[1]
    assert "錯誤：沒有這個工具：search" in gateway.messages[2]


# 第一道煞車：步數上限到了就停，不再送出
def test_run_agent_stops_at_the_step_limit():
    replies = [ok("CALL calc(1+1)")] * 5

    result, gateway, lines = run(replies, max_steps=3)

    assert result.stop_reason == "max_steps"
    assert len(gateway.messages) == 3


# 第二道煞車：累計花費到了預算就停；做完才知道一步多少錢，所以最後會超出一點
def test_run_agent_stops_when_its_own_budget_is_spent():
    replies = [ok("CALL calc(1+1)", cost=4000)] * 5

    result, gateway, lines = run(replies, budget=10_000)

    assert result.stop_reason == "budget"
    assert len(gateway.messages) == 3
    assert result.spent_micro_usd == 12_000


# 第三道煞車：Gateway 回 429 就停，不重試；自己的兩道都關掉（0）也一樣擋得住
def test_run_agent_stops_on_429_even_with_its_own_limits_off():
    replies = [ok("CALL calc(1+1)"), ok("CALL calc(2+2)"), GatewayReply(status=429, body={})]

    result, gateway, lines = run(replies, max_steps=0, budget=0)

    assert result.stop_reason == "quota"
    assert len(gateway.messages) == 3
    assert result.spent_micro_usd == 6000


# 其他錯誤（例如 401 Key 錯）也停，並說出狀態碼
def test_run_agent_stops_on_other_gateway_errors():
    result, gateway, lines = run([GatewayReply(status=401, body={})])

    assert result.stop_reason == "http_401"
    assert result.spent_micro_usd == 0
