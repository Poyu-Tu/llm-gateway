"""Choose which model answers a request."""
import re
from dataclasses import dataclass

from app.config import RoutingConfig


# 路由的結果：用哪一顆模型，以及為什麼（稽核和示範畫面都要說得出理由）
@dataclass(frozen=True)
class RouteDecision:
    """Which model to use and why it was chosen."""
    model: str
    reason: str

# 英文字母與數字：英文關鍵字的前面不能緊貼這些字（decode 不算 code）
ASCII_WORD_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"


# 文字裡有沒有這個關鍵字；英文關鍵字不能藏在別的字中間，中文關鍵字沒有這個限制
def contains_keyword(lowered: str, keyword: str) -> bool:
    """Return True when the keyword appears in the text and does not start inside a word."""
    keyword = keyword.lower()
    if keyword[0] not in ASCII_WORD_CHARS:
        return keyword in lowered
    pattern = r"(?<![a-z0-9])" + re.escape(keyword)
    return re.search(pattern, lowered) is not None


# 夠長或含關鍵字就用強模型，其餘用便宜模型；只看文字和規則，不碰網路和資料庫
def choose_model(text: str, routing: RoutingConfig) -> RouteDecision:
    """Return the model for the text, together with the reason."""
    if len(text) >= routing.min_chars:
        return RouteDecision(model=routing.strong_model, reason="length")

    # 英文關鍵字不分大小寫：兩邊都先轉成小寫再比
    lowered = text.lower()
    for keyword in routing.keywords:
        if contains_keyword(lowered, keyword):
            return RouteDecision(model=routing.strong_model, reason="keyword")
    return RouteDecision(model=routing.cheap_model, reason="default")