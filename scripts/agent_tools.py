"""M7: the three local tools of the small agent. They only read the repo's config; nothing goes over the network."""

import ast
import operator

from app.audit import mask
from app.config import GatewayConfig
from app.router import choose_model

# 一百萬：config.toml 的單價是「每一百萬個 token 多少 micro-USD」，換成「每一百萬個 token 多少美元」也是除以它
MILLION = 1_000_000

# calc 只認得這四種運算；呼叫函式、取屬性、次方等其他寫法一律拒絕
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

# 算式最多幾個字：太長的算式不收
MAX_EXPRESSION_CHARS = 100


# 工具用不了這個參數時丟這個錯誤；訊息會原樣送回給模型，讓它下一步自己修正
class ToolError(Exception):
    """The tool cannot run with this argument."""


# 這個問題在 Gateway 會走哪個模型：跟 Gateway 一樣先遮罩、再用同一支 choose_model() 和同一份設定
def tool_route(question: str, config: GatewayConfig) -> str:
    """Return the model the Gateway would choose for the question, and why."""
    if question.strip() == "":
        raise ToolError("route 需要一個問題")
    decision = choose_model(mask(question), config.routing)
    return f"{decision.model}（理由：{decision.reason}）"


# 這個模型的單價：讀 config.toml，換算成「美元／百萬 token」；查不到就列出有哪些模型
def tool_price(model: str, config: GatewayConfig) -> str:
    """Return the input and output price of the model in USD per million tokens."""
    settings = config.models.get(model)
    if settings is None:
        known = "、".join(sorted(config.models))
        raise ToolError(f"沒有這個模型：{model}（有：{known}）")
    input_usd = settings.input_price / MILLION
    output_usd = settings.output_price / MILLION
    return f"輸入 {input_usd:g}、輸出 {output_usd:g}（美元／百萬 token）"


# 一層一層算：只有數字和加減乘除（加上負號）能過，其他東西一出現就停
def evaluate(node: ast.AST) -> float:
    """Return the value of a parsed expression made only of numbers, + - * / and brackets."""
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = evaluate(node.left)
        right = evaluate(node.right)
        return OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -evaluate(node.operand)
    raise ToolError("calc 只能用數字、+ - * / 和括號")


# 計算機：不用 eval()；eval 會執行任何 Python 程式，模型給的字串不能直接拿去跑
def safe_calc(expression: str) -> str:
    """Return the value of a simple arithmetic expression as text."""
    if len(expression) > MAX_EXPRESSION_CHARS:
        raise ToolError(f"算式太長（最多 {MAX_EXPRESSION_CHARS} 字）")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise ToolError("calc 看不懂這個算式")
    try:
        value = evaluate(tree.body)
    except ZeroDivisionError:
        raise ToolError("不能除以 0")
    return f"{value:.10g}"


# 照名稱叫工具；工具名稱或參數不對都回一段「錯誤：……」，不讓迴圈中斷
def run_tool(name: str, argument: str, config: GatewayConfig) -> str:
    """Run the named tool and return its result, or an error message for the model."""
    try:
        if name == "route":
            return tool_route(argument, config)
        if name == "price":
            return tool_price(argument, config)
        if name == "calc":
            return safe_calc(argument)
        raise ToolError(f"沒有這個工具：{name}（有：route、price、calc）")
    except ToolError as exc:
        return f"錯誤：{exc}"