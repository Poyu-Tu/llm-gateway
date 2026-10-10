"""Gateway settings, read from a TOML file that lives in the repo."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

# 設定檔和程式放在同一個資料夾：容器只複製 app/，放這裡才會一起進映像
CONFIG_PATH = Path(__file__).parent / "config.toml"


# 一顆模型的設定；單價的單位是「每一百萬個 token 多少 micro-USD」
@dataclass(frozen=True)
class ModelConfig:
    """Settings for one model."""
    reasoning_effort: str
    max_completion_tokens: int
    input_price: int
    output_price: int


# 路由規則：哪兩顆模型、多長或含哪些字才用強模型
@dataclass(frozen=True)
class RoutingConfig:
    """Rules for choosing between the cheap and the strong model."""
    cheap_model: str
    strong_model: str
    min_chars: int
    keywords: list[str]


# 整份設定：路由規則，加上每顆模型的設定（用模型名稱查）
@dataclass(frozen=True)
class GatewayConfig:
    """Everything read from the config file."""
    routing: RoutingConfig
    models: dict[str, ModelConfig]


# 設定檔有問題時丟這個錯誤：一看就知道是設定的問題，不是程式壞了
class ConfigError(Exception):
    """The config file is missing a setting or holds a value that cannot be used."""


# 單價、上限、門檻都要是大於 0 的整數：寫成小數或 0，成本會算錯，甚至變成免費
def require_positive_int(value, name: str) -> None:
    """Raise ConfigError unless the value is a whole number above zero."""
    if type(value) is not int or value <= 0:
        raise ConfigError(f"{name} must be a whole number above zero")


# 讀進來就檢查：設定有問題寧可起不來，也不要帶著錯的設定開始收錢
def check_config(config: GatewayConfig) -> None:
    """Raise ConfigError when the settings cannot be used safely."""
    routing = config.routing

    # 路由會選到的兩顆模型都要有設定，否則會選到一顆不知道多少錢的模型
    for model in [routing.cheap_model, routing.strong_model]:
        if model not in config.models:
            raise ConfigError(f"Routing uses a model with no settings: {model}")

    require_positive_int(routing.min_chars, "routing.min_chars")
    for name, model in config.models.items():
        require_positive_int(model.max_completion_tokens, f"{name}.max_completion_tokens")
        require_positive_int(model.input_price, f"{name}.input_price")
        require_positive_int(model.output_price, f"{name}.output_price")

    # 空白的關鍵字「出現在」每一句話裡：混進清單，所有請求都會被送去強模型
    for keyword in routing.keywords:
        if keyword.strip() == "":
            raise ConfigError("routing.keywords must not contain a blank keyword")

        
# 把設定檔讀成上面三種物件
def load_config(path: Path) -> GatewayConfig:
    """Read the TOML file at path and return the settings."""
    with open(path, "rb") as file:
        data = tomllib.load(file)

    try:
        routing = RoutingConfig(
            cheap_model=data["routing"]["cheap_model"],
            strong_model=data["routing"]["strong_model"],
            min_chars=data["routing"]["min_chars"],
            keywords=data["routing"]["keywords"],
        )

        models = {}
        for name, fields in data["models"].items():
            models[name] = ModelConfig(
                reasoning_effort=fields["reasoning_effort"],
                max_completion_tokens=fields["max_completion_tokens"],
                input_price=fields["input_price"],
                output_price=fields["output_price"],
            )
    except KeyError as exc:
        raise ConfigError(f"Missing setting: {exc}")

    config = GatewayConfig(routing=routing, models=models)
    check_config(config)

    return  config