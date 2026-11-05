from app.config import ModelConfig

# 一百萬：單價是以「每一百萬個 token」報價的
MILLION = 1_000_000


# 要用一顆沒有設定（也就沒有單價）的模型時丟這個錯誤
class ModelNotConfiguredError(Exception):   # 專用的錯誤類別，看到這個名字就知道是「設定問題」，不是程式壞了
    """The model has no settings, so its price is unknown."""


# 呼叫模型之前先查它的設定：查不到就不該呼叫，「不知道多少錢」不能當成「不用錢」
def find_model_config(models: dict[str, ModelConfig], model: str) -> ModelConfig:
    """Return the settings for the model, or raise when it has none."""
    if model not in models: # 先查再拿：不直接寫 models[model]
        raise ModelNotConfiguredError(f"No settings for model: {model}")    # 訊息帶模型名稱：方便看日誌時知道是哪一顆
    return models[model]    # 回的是整份設定物件：之後呼叫模型、算錢，都帶著這同一份走（outcome.settings），所以「回答完才發現查不到單價」這種事不可能發生。


# 金額全程用整數算，無條件進位，避免小數誤差；額度就是靠這個數字扣的
def cost_micro_usd(settings: ModelConfig, input_tokens: int, output_tokens: int) -> int:
    """Return the cost of one call in micro-USD, rounded up to a whole number."""
    total = input_tokens * settings.input_price + output_tokens * settings.output_price # 先全部乘完、加完：只進位一次。
    result = total // MILLION   # 整數除法，直接丟掉小數，全程不碰浮點數。
    if total % MILLION != 0:    # 只有在除不盡（有零頭）時才 +1。
        result = result + 1
    return result