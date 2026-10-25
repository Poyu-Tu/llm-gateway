"""Prometheus metrics for the Gateway (M6)."""
from prometheus_client import CollectorRegistry, Counter, Histogram

# 自己的一本計數簿：只放這五個指標，不附預設的程序資訊（少給一點系統細節）
REGISTRY = CollectorRegistry()

# 五個指標（決策書 5.2）；名字結尾的 _total 由套件自己加
REQUESTS = Counter("llm_requests", "Chat requests", ["user", "model", "status"], registry=REGISTRY)
TOKENS = Counter("llm_tokens", "Tokens used", ["user", "model", "kind"], registry=REGISTRY)
COST = Counter("llm_cost_usd", "Cost in USD", ["user", "model"], registry=REGISTRY)
# 延遲分格：從 0.5 秒到 64 秒；強模型寫滿輸出上限約 32 秒
DURATION = Histogram(
    "llm_request_duration_seconds",
    "Chat request duration",
    ["status"],
    buckets=(0.5, 1, 2, 4, 8, 16, 32, 64),
    registry=REGISTRY,
)
REJECTED = Counter("llm_rate_limit_rejected", "Requests stopped by quota or provider limits", ["reason"], registry=REGISTRY)


# 一個請求結束時記一次：用稽核紀錄裡已經有的欄位，不碰問題內容
# model 優先用實際回答的那一顆；還沒回答就用路由選的；連路由都還沒走到（額度擋下）就是 none
def observe_request(record: dict, seconds: float) -> None:
    """Update the counters from one finished request's audit record."""
    status = record["status"]
    model = record.get("model") or record.get("routed_model") or "none"
    user = record["user_id"]
    REQUESTS.labels(user=user, model=model, status=status).inc()
    DURATION.labels(status=status).observe(seconds)
    if status == "quota_exceeded":
        REJECTED.labels(reason="quota").inc()
    if record.get("error_type") == "RateLimitError":
        REJECTED.labels(reason="provider").inc()
    # 成功才有用量和成本；成本存的是 micro-USD，換成美元給 Grafana 直接看
    if status == "ok":
        TOKENS.labels(user=user, model=model, kind="input").inc(record["input_tokens"])
        TOKENS.labels(user=user, model=model, kind="output").inc(record["output_tokens"])
        TOKENS.labels(user=user, model=model, kind="reasoning").inc(record["reasoning_tokens"])
        COST.labels(user=user, model=model).inc(record["cost_micro_usd"] / 1_000_000)
