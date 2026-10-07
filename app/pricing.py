# 一百萬：單價是以「每一百萬個 token」報價的
MILLION = 1_000_000

# 單價寫在 repo 裡，改價要經過版本紀錄；不從網路下載價格表
# 單位：每一百萬個 token 多少 micro-USD（Luna 輸入 $0.10 → 100_000，輸出 $0.50 → 500_000）
PRICES = {
    "gpt-6-luna": {"input": 100_000, "output": 500_000},
}


# 金額全程用整數算，避免小數誤差；額度就是靠這個數字扣的
def cost_micro_usd(model: str, input_tokens: int, output_tokens: int) -> int:
    """Return the cost of one call in micro-USD, rounded up to a whole number."""
    if model not in PRICES:
        raise ValueError(f"No price configured for model: {model}")
    price = PRICES[model]
    total = input_tokens * price["input"] + output_tokens * price["output"]
    result = total // MILLION
    if total % MILLION != 0:
        result = result + 1
    return result