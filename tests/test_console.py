"""Tests for the Demo Console page and its front-end safety (decision book 3.1, 4.4)."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATIC = Path("app/static")


# 首頁就是 Console：回 HTML，標題對
def test_console_page_is_served_at_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "LLM Gateway Console" in response.text


# 畫面的程式另外放一個檔，由 /static 提供（不寫在 HTML 裡，才能用嚴格的 CSP 禁止網頁內嵌程式）
def test_console_script_is_served_from_static():
    response = client.get("/static/console.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


# 4.4 點擊劫持：不准被別的網站用 iframe 嵌進去
def test_console_cannot_be_framed():
    response = client.get("/")

    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


# CSP：只准載入自己網站的程式和樣式，不准內嵌程式（就算有人塞進一段 <script>，瀏覽器也不執行）
# 指令名稱拼錯時瀏覽器只會默默略過、不報錯，所以每個指令都要在這裡檢查
def test_console_only_runs_its_own_script():
    csp = client.get("/").headers["content-security-policy"]

    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "base-uri 'none'" in csp
    assert "unsafe-inline" not in csp


# 瀏覽器不准猜檔案類型（不會把文字檔當成程式執行）
def test_responses_tell_the_browser_not_to_guess_types():
    for path in ["/", "/static/console.js", "/health"]:
        assert client.get(path).headers["x-content-type-options"] == "nosniff"


# 4.4 XSS：模型的回答是不可信的輸入，畫面一律用 textContent，程式裡不能出現 innerHTML
def test_console_script_never_uses_inner_html():
    script = (STATIC / "console.js").read_text(encoding="utf-8")

    assert "innerHTML" not in script
    assert "outerHTML" not in script
    assert "insertAdjacentHTML" not in script


# 4.4 API Key：只放 sessionStorage（關分頁就消失），不用 localStorage（關機後還在）
def test_console_keeps_the_key_only_for_the_session():
    script = (STATIC / "console.js").read_text(encoding="utf-8")

    assert "sessionStorage" in script
    assert "localStorage" not in script


# HTML 裡不能有內嵌的程式（CSP 也會擋，這裡先在測試抓）
def test_console_page_has_no_inline_script():
    page = (STATIC / "index.html").read_text(encoding="utf-8")

    assert "<script>" not in page
    assert "onclick" not in page.lower()


# HTML 裡不能寫 style="..."：CSP 的 style-src 'self' 會擋掉，畫面會默默跑版（樣式一律放 console.css）
def test_console_page_has_no_inline_style():
    page = (STATIC / "index.html").read_text(encoding="utf-8")

    assert "style=" not in page
    assert "<style" not in page


# 改版後不能沿用舊檔：CSS、JS 每次都要先跟伺服器確認（10/26 實際遇過：新 JS 配到瀏覽器快取的舊 CSS，畫面全亂）
def test_static_files_are_always_revalidated():
    for path in ["/", "/static/console.css", "/static/console.js"]:
        assert client.get(path).headers["cache-control"] == "no-cache"
