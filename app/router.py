"""Choose which model answers a request."""
import re
from dataclasses import dataclass

from app.config import RoutingConfig


# 路由的結果：用哪一顆模型，以及為什麼（稽核和示範畫面都要說得出理由）
@dataclass(frozen=True) # frozen=True 後面的程式不能偷改
class RouteDecision:
    """Which model to use and why it was chosen."""
    model: str  # 用哪一顆
    reason: str # 為什麼選他

# 英文字母與數字：英文關鍵字的前面不能緊貼這些字（decode 不算 code）
ASCII_WORD_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"   # 只列小寫字母加數字


# 文字裡有沒有這個關鍵字；英文關鍵字不能藏在別的字中間，中文關鍵字沒有這個限制
def contains_keyword(lowered: str, keyword: str) -> bool:
    """Return True when the keyword appears in the text and does not start inside a word."""
    keyword = keyword.lower()
    if keyword[0] not in ASCII_WORD_CHARS:  # 看第一個字：判斷這個關鍵字是英文還是中文，決定走哪條路。
        return keyword in lowered   # 中文路：單純找子字串，所以 abc分析、3分析 都算
    # (?<![a-z0-9]) 往前看一個字，不能是英文字母或數字。它只檢查、不吃字。如果關鍵字在整句的最前面，前面沒有字，也算通過。
    # re.escape(keyword)：把關鍵字裡的符號當成字面意思。不 escape 的話，a.b 裡的 . 在正規表示式裡代表「任何一個字」，axb 也會中。
    pattern = r"(?<![a-z0-9])" + re.escape(keyword)
    return re.search(pattern, lowered) is not None


# 夠長或含關鍵字就用強模型，其餘用便宜模型；只看文字和規則，不碰網路和資料庫
def choose_model(text: str, routing: RoutingConfig) -> RouteDecision:   # routing（規則從設定檔來，不寫死在函式裡）
    """Return the model for the text, together with the reason."""
    if len(text) >= routing.min_chars:  # 先看長度
        return RouteDecision(model=routing.strong_model, reason="length")

    # 英文關鍵字不分大小寫：兩邊都先轉成小寫再比
    lowered = text.lower()  # 英文不分大小寫
    for keyword in routing.keywords:
        if contains_keyword(lowered, keyword):  # 再看關鍵字
            return RouteDecision(model=routing.strong_model, reason="keyword")
    return RouteDecision(model=routing.cheap_model, reason="default")