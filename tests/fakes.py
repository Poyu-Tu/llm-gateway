"""Fake objects shared by tests."""

from types import SimpleNamespace

import httpx2
from openai import RateLimitError


# 假的 OpenAI：把收到的請求記下來，再回傳假的回應
# 回報的模型名稱預設就是請求指定的那一顆；要模擬「回報的名稱和指定的不同」時才另外給 reported_model
# error：每一顆模型都丟這個錯誤；errors：指定「哪一顆模型丟哪個錯誤」，沒列到的模型正常回答
# finish_reason：回答的結束原因；要模擬「被輸出上限截斷」時給 "length"
class FakeCompletions:
    """Stands in for client.chat.completions and records the requests."""

    def __init__(self, content="Hi there", has_details=True, error=None, reported_model=None, errors=None, finish_reason="stop"):
        self.last_request = None
        self.requests = []
        # 每一次請求是用哪一種重試設定送出的：None 是連線原本的設定，0 是「這一次不重試」
        self.retry_settings = []
        self.content = content
        self.has_details = has_details
        self.error = error
        self.reported_model = reported_model
        if errors is None:
            errors = {}
        self.errors = errors
        self.finish_reason = finish_reason

    def create(self, **kwargs):
        return self.answer(kwargs, None)

    # 真正處理請求的地方：先記下來，再決定要丟錯誤還是回答
    def answer(self, kwargs, max_retries):
        self.last_request = kwargs
        self.requests.append(kwargs)
        self.retry_settings.append(max_retries)
        if self.error:
            raise self.error
        if kwargs["model"] in self.errors:
            raise self.errors[kwargs["model"]]
        if self.has_details:
            details = SimpleNamespace(reasoning_tokens=0)
        else:
            details = None
        return SimpleNamespace(
            model=self.reported_model or kwargs["model"],
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content), finish_reason=self.finish_reason)],
            usage=SimpleNamespace(
                prompt_tokens=13,
                completion_tokens=11,
                completion_tokens_details=details,
            ),
        )

    # 依序列出每一次請求指定的模型，例如 ["big", "small"]
    def models_called(self):
        """Return the model of every request, in order."""
        names = []
        for request in self.requests:
            names.append(request["model"])
        return names


# 換過重試設定的連線用的窗口：請求照樣交給同一本筆記本，只是多記一筆「這次的重試設定」
class FakeCompletionsWithOptions:
    """Passes requests to the same FakeCompletions, together with the retry setting."""

    def __init__(self, completions, max_retries):
        self.completions = completions
        self.max_retries = max_retries

    def create(self, **kwargs):
        return self.completions.answer(kwargs, self.max_retries)


# 假的連線：和真的一樣有 with_options()，交回一條「只換了重試設定」的新連線，原本那一條不變
class FakeClient:
    """Stands in for the OpenAI client."""

    def __init__(self, completions):
        self.completions = completions
        self.chat = SimpleNamespace(completions=completions)

    # 和真的 SDK 一樣只收具名的參數：寫成 with_options(0) 會報錯
    def with_options(self, *, max_retries):
        door = FakeCompletionsWithOptions(self.completions, max_retries)
        return SimpleNamespace(chat=SimpleNamespace(completions=door))


# 建立假連線；同時回傳「連線」和「筆記本」，讓測試能檢查送出了什麼
def make_fake_client(content="Hi there", has_details=True, error=None, reported_model=None, errors=None, finish_reason="stop"):
    """Return the fake client and its completions, so tests can check the request."""
    completions = FakeCompletions(content, has_details, error, reported_model, errors, finish_reason)
    client = FakeClient(completions)
    return client, completions


# 造一個「供應商回 429」的錯誤，長得和 SDK 真的丟出來的一樣（有狀態碼、代碼、回應標頭）
# code 預設是限流；要模擬供應商的預算用完時，換成 project_spend_limit_exceeded 這類代碼
def make_rate_limit_error(code="rate_limit_exceeded", error_type="requests", retry_after=None):
    """Return the error the OpenAI SDK raises for a 429 response."""
    headers = {}
    if retry_after is not None:
        headers["retry-after"] = str(retry_after)
    request = httpx2.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx2.Response(429, headers=headers, request=request)
    return RateLimitError("fake 429", response=response, body={"code": code, "type": error_type})


# 假的資料庫：只把收到的寫入記下來，什麼都不存；讓不測額度的測試不需要 Docker
class FakeDynamoDB:
    """Stands in for a DynamoDB client and records the updates it receives."""

    def __init__(self):
        self.updates = []

    def update_item(self, **kwargs):
        self.updates.append(kwargs)
