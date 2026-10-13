"""M3 step 7: how much the routing rules save, worked out from the recorded test-set run.

Reads the result file from scripts/run_routing_eval.py; it does not call any model:
    uv run python -m scripts.routing_eval
"""

import json
from dataclasses import dataclass, replace
from pathlib import Path

from app.config import CONFIG_PATH, RoutingConfig, load_config
from app.router import choose_model

# 步驟 7 跑出來的結果檔：每一題、兩顆模型各自花了多少
RUN_PATH = Path(__file__).parent.parent / "docs" / "logs" / "m3-step7-routing-run.json"


# 一組規則的成績單：兩種總成本、省下的比例，以及送對、送錯了哪些題
@dataclass(frozen=True)
class RoutingSummary:
    """How one set of routing rules did on the test set."""
    all_strong: int
    routed: int
    saving_percent: float
    matched: int
    wasted: list[str]
    risky: list[str]


# 省下的比例：和「全部用強模型」比，少花了百分之幾（取到小數第一位）
def saving_percent(all_strong: int, routed: int) -> float:
    """Return how much cheaper routing is than using the strong model for everything, in percent."""
    if all_strong <= 0:
        raise ValueError("all_strong must be above zero")
    return round((all_strong - routed) / all_strong * 100, 1)


# 用一組規則重新分流每一題，加總兩種成本，再和本人的判斷對照
def summarize(rows: list[dict], routing: RoutingConfig) -> RoutingSummary:
    """Route every recorded question with the given rules and add up what it would cost."""
    all_strong = 0
    routed = 0
    matched = 0
    wasted = []
    risky = []

    for row in rows:
        # 這組規則會把這一題送去哪一顆（和 Gateway 用的是同一個路由函式）
        chosen = choose_model(row["masked"], routing).model

        # 兩種算法各加上這一題的成本：全部用強模型，以及規則選的那一顆
        all_strong = all_strong + row["answers"][routing.strong_model]["cost_micro_usd"]
        routed = routed + row["answers"][chosen]["cost_micro_usd"]

        # 本人判斷這一題應該由哪一顆回答
        if row["expected"] == "strong":
            expected_model = routing.strong_model
        else:
            expected_model = routing.cheap_model

        # 送對了；送錯的話，分成「多花錢」和「可能答不好」兩種
        if chosen == expected_model:
            matched = matched + 1
        elif chosen == routing.strong_model:
            wasted.append(row["id"])
        else:
            risky.append(row["id"])

    return RoutingSummary(
        all_strong=all_strong,
        routed=routed,
        saving_percent=saving_percent(all_strong, routed),
        matched=matched,
        wasted=wasted,
        risky=risky,
    )


# 完全照本人的判斷分流時要花多少：規則再怎麼調，送對的話最多就省到這裡
def perfect_routed(rows: list[dict], routing: RoutingConfig) -> int:
    """Return the cost when every question goes to the model it was labelled for."""
    total = 0
    for row in rows:
        if row["expected"] == "strong":
            model = routing.strong_model
        else:
            model = routing.cheap_model
        total = total + row["answers"][model]["cost_micro_usd"]
    return total


# 讀步驟 7 的結果檔，只要每一題的資料
def load_rows(path: Path) -> list[dict]:
    """Return the recorded questions from the result file."""
    with open(path, encoding="utf-8") as file:
        return json.load(file)["questions"]


# 10/12 以前的關鍵字：步驟 7 比較時的起點（R0）
OLD_KEYWORDS = ["分析", "比較", "評估", "設計", "架構", "程式碼", "除錯", "code", "debug"]


# 比較幾組規則：10/12 以前的規則、兩個候選，以及現在設定檔裡的規則
def main() -> None:
    """Print how each set of rules does on the recorded test set."""
    rows = load_rows(RUN_PATH)
    current = load_config(CONFIG_PATH).routing

    # 候選規則：只換關鍵字或字數門檻，其他沿用現在的設定
    keywords_r1 = ["分析", "請比較", "優缺點", "評估", "設計", "架構", "程式碼", "除錯", "code", "debug"]

    candidates = [
        ("R0 10/12 以前的規則", replace(current, keywords=OLD_KEYWORDS)),
        ("R1 「比較」換成「請比較」「優缺點」", replace(current, keywords=keywords_r1)),
        ("R2 現在的設定檔（10/13 定案）", current),
        ("R3 現在的設定檔，字數門檻改成 500", replace(current, min_chars=500)),
    ]

    first = summarize(rows, current)
    perfect = perfect_routed(rows, current)
    print(f"題數：{len(rows)}")
    print(f"全部用強模型：{first.all_strong} micro-USD")
    print(f"完全照判斷分流：{perfect} micro-USD，省 {saving_percent(first.all_strong, perfect)}%")
    print()
    for name, routing in candidates:
        result = summarize(rows, routing)
        print(f"{name}")
        print(f"    分流後 {result.routed} micro-USD，省 {result.saving_percent}%，送對 {result.matched} 題")
        print(f"    多花錢：{result.wasted}　可能答不好：{result.risky}")


if __name__ == "__main__":
    main()
