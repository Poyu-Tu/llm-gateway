"""M3 step 9 (S07): run the real Gateway, but make every call to the strong model answer 429.

This is a SIMULATION for the demo recording: the strong model never reaches OpenAI, the cheap
model is a real call. Run from the repo root on the personal PC only (it calls the real API):
    uv run --env-file .env python -m scripts.demo_fallback
"""

from types import SimpleNamespace

import httpx2
import uvicorn
from openai import RateLimitError

from app.config import CONFIG_PATH, load_config
from app.main import app, get_client

# 假裝被限流的是強模型；名稱從設定檔讀，不寫死
STRONG_MODEL = load_config(CONFIG_PATH).routing.strong_model


# 造一個「供應商回 429」的錯誤，長得和 SDK 真的丟出來的一樣
def make_fake_429() -> RateLimitError:
    """Return the error the OpenAI SDK raises for a rate-limit response."""
    request = httpx2.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx2.Response(429, headers={"retry-after": "7"}, request=request)
    return RateLimitError("simulated 429", response=response, body={"code": "rate_limit_exceeded", "type": "requests"})


# 包住真的 completions：問強模型就丟假的 429，問別的模型原封不動交給真的
class SimulatedLimitCompletions:
    """Raises a fake 429 for the strong model and passes every other request to the real client."""

    def __init__(self, real_completions):
        self.real_completions = real_completions

    def create(self, **kwargs):
        if kwargs["model"] == STRONG_MODEL:
            raise make_fake_429()
        return self.real_completions.create(**kwargs)


# 包住真的連線：和真的一樣有 with_options()，換過重試設定的連線也照樣「強模型被限流」
class SimulatedLimitClient:
    """Stands in for the OpenAI client; only the strong model is rate limited."""

    def __init__(self, real_client):
        self.real_client = real_client
        self.chat = SimpleNamespace(completions=SimulatedLimitCompletions(real_client.chat.completions))

    def with_options(self, *, max_retries):
        return SimulatedLimitClient(self.real_client.with_options(max_retries=max_retries))


# 領用窗口：換成「強模型被限流」的連線；真的連線照原本的方式建立
def get_simulated_client() -> SimulatedLimitClient:
    return SimulatedLimitClient(get_client())


# 啟動 Gateway：換掉連線，其他（驗證、額度、稽核、路由、降級）全部是真的
def main():
    """Print a banner so the recording shows this is a simulation, then start the Gateway."""
    app.dependency_overrides[get_client] = get_simulated_client
    print(f"SIMULATION: every call to {STRONG_MODEL} gets a fake 429. Calls to other models are real.", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
