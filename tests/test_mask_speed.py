"""Tests that masking stays fast on long crafted input (CodeQL: polynomial regular expression)."""

import time

from app.audit import mask

# 很長、但完全合法的輸入：5 萬個字元，修正前約 4 秒，修正後約 0.01 秒
LONG_LENGTH = 50_000
# 給 CI 的電腦留很大的餘裕：修正後快了好幾百倍，1 秒還超過就是又變回一個一個重掃
TIME_LIMIT_SECONDS = 1.0


# 量一次 mask() 花了幾秒
def seconds_to_mask(text):
    """Return how many seconds mask() takes on the text."""
    start = time.perf_counter()
    mask(text)
    return time.perf_counter() - start


# 一長串英文字母（信箱名字允許的字）、中間沒有 @：每個位置都重掃到底的話，時間會隨長度平方變長
def test_long_run_of_letters_is_masked_quickly():
    assert seconds_to_mask("a" * LONG_LENGTH) < TIME_LIMIT_SECONDS


# 一長串數字：數字也是信箱名字允許的字，同樣不能一個一個重掃
def test_long_run_of_digits_is_masked_quickly():
    assert seconds_to_mask("1" * LONG_LENGTH) < TIME_LIMIT_SECONDS


# 信箱緊貼在中文後面（中文前面沒有空格）仍然要遮：「前面不能是信箱的字」不能寫成「前面一定要是空白」
def test_email_right_after_chinese_is_still_masked():
    assert mask("寄到test@example.com謝謝") == "寄到[EMAIL]謝謝"


# 一般的寫法照舊：前後有空格、名字裡有點和加號
def test_ordinary_emails_are_still_masked():
    assert mask("x test@example.com y") == "x [EMAIL] y"
    assert mask("a.b+c@sub.example.co") == "[EMAIL]"


# 兩個 @ 連在一起時，結果和修正前一樣：只遮後面那個完整的信箱
def test_two_at_signs_give_the_same_result_as_before():
    assert mask("abc@def@ghi.com") == "abc@[EMAIL]"
