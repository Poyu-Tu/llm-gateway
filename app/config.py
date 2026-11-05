"""Gateway settings, read from a TOML file that lives in the repo."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

# 設定檔和程式放在同一個資料夾：容器只複製 app/，放這裡才會一起進映像
CONFIG_PATH = Path(__file__).parent / "config.toml" # Path(__file__).parent 指的是「config.py 自己所在的資料夾」，也就是 app/。設定檔放在 app/ 裡，因為 Dockerfile 只複製 app/，放這裡才會一起打包進映像。


# 一顆模型的設定；單價的單位是「每一百萬個 token 多少 micro-USD」
@dataclass(frozen=True) # 讀完不能改
class ModelConfig:
    """Settings for one model."""
    reasoning_effort: str   # 推理強度
    max_completion_tokens: int  # 輸出上限
    input_price: int
    output_price: int


# 路由規則：哪兩顆模型、多長或含哪些字才用強模型
@dataclass(frozen=True) # 讀完不能改
class RoutingConfig:
    """Rules for choosing between the cheap and the strong model."""
    cheap_model: str
    strong_model: str
    min_chars: int  # 字數門檻
    keywords: list[str] # 關鍵字


# 整份設定：路由規則，加上每顆模型的設定（用模型名稱查）
@dataclass(frozen=True) # 讀完不能改
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
    # type(value) is not int：單價單位是 micro-USD，全程用整數算。有人把 $0.1 直接寫成 0.1，成本會差一百萬倍
    # or value <= 0：單價 0 等於免費，額度永遠扣不到；min_chars = 0 等於每句話都「夠長」，全部送強模型
    if type(value) is not int or value <= 0:
        raise ConfigError(f"{name} must be a whole number above zero")  # name 參數：錯誤訊息會寫出是哪一格


# 讀進來就檢查：設定有問題寧可起不來，也不要帶著錯的設定開始收錢
def check_config(config: GatewayConfig) -> None:
    """Raise ConfigError when the settings cannot be used safely."""
    routing = config.routing

    # 路由會選到的兩顆模型都要有設定，否則會選到一顆不知道多少錢的模型
    for model in [routing.cheap_model, routing.strong_model]:
        if model not in config.models:
            raise ConfigError(f"Routing uses a model with no settings: {model}")

    require_positive_int(routing.min_chars, "routing.min_chars")    # min_chars 要是正整數
    for name, model in config.models.items():
        require_positive_int(model.max_completion_tokens, f"{name}.max_completion_tokens")
        require_positive_int(model.input_price, f"{name}.input_price")
        require_positive_int(model.output_price, f"{name}.output_price")

    # 空白的關鍵字「出現在」每一句話裡：混進清單，所有請求都會被送去強模型
    for keyword in routing.keywords:
        if keyword.strip() == "":   # 空字串 "" 會「出現在」每一句話裡，" " 會出現在幾乎每一句英文裡，結果全部送強模型。strip() 把空字串和純空格一起擋。也順便保護了 contains_keyword()：它的 keyword[0] 遇到空字串會 IndexError
            raise ConfigError("routing.keywords must not contain a blank keyword")

        
# 把設定檔讀成上面三種物件
def load_config(path: Path) -> GatewayConfig:
    """Read the TOML file at path and return the settings."""
    # "rb" 二進位模式：tomllib 規定要用二進位模式開檔，它自己用 UTF-8 解碼。Windows 預設的編碼不是 UTF-8，用文字模式開，中文關鍵字（「分析」）就有可能出問題；
    # 而且文字模式會直接丟 TypeError: File must be opened in binary mode。
    with open(path, "rb") as file:
        data = tomllib.load(file)   # load 不是 loads：load 收的是檔案，loads 收的是字串。

    try:
        routing = RoutingConfig(
            cheap_model=data["routing"]["cheap_model"],
            strong_model=data["routing"]["strong_model"],
            min_chars=data["routing"]["min_chars"],
            keywords=data["routing"]["keywords"],
        )

        models = {}
        for name, fields in data["models"].items(): # 每個 [models.xxx] 做成一個 ModelConfig，用模型名當 key，新增一顆模型只要改 toml，不用改程式
            models[name] = ModelConfig(
                reasoning_effort=fields["reasoning_effort"],
                max_completion_tokens=fields["max_completion_tokens"],
                input_price=fields["input_price"],
                output_price=fields["output_price"],
            )
    except KeyError as exc: # 把「字典找不到 key」翻成「設定少了某格」
        raise ConfigError(f"Missing setting: {exc}")

    config = GatewayConfig(routing=routing, models=models)
    check_config(config)    # 讀完馬上檢查內容

    return config
