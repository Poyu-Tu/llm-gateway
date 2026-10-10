from app.config import ModelConfig

# 一百萬：單價是以「每一百萬個 token」報價的
MILLION = 1_000_000


# 要用一顆沒有設定（也就沒有單價）的模型時丟這個錯誤
class ModelNotConfiguredError(Exception):
    """The model has no settings, so its price is unknown."""


# 呼叫模型之前先查它的設定：查不到就不該呼叫，「不知道多少錢」不能當成「不用錢」
def find_model_config(models: dict[str, ModelConfig], model: str) -> ModelConfig:
    """Return the settings for the model, or raise when it has none."""
    if model not in models:
        raise ModelNotConfiguredError(f"No settings for model: {model}")
    return models[model]


# 金額全程用整數算，避免小數誤差；額度就是靠這個數字扣的
def cost_micro_usd(settings: ModelConfig, input_tokens: int, output_tokens: int) -> int:
    """Return the cost of one call in micro-USD, rounded up to a whole number."""
    total = input_tokens * settings.input_price + output_tokens * settings.output_price
    result = total // MILLION
    if total % MILLION != 0:
        result = result + 1
    return result