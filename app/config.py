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


# 把設定檔讀成上面三種物件
def load_config(path: Path) -> GatewayConfig:
    """Read the TOML file at path and return the settings."""
    with open(path, "rb") as file:
        data = tomllib.load(file)

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

    return GatewayConfig(routing=routing, models=models)