"""Fake objects shared by tests."""

from types import SimpleNamespace


# 假的 OpenAI：把收到的請求記下來，再回傳假的回應
# 回報的模型名稱預設就是請求指定的那一顆；要模擬「回報的名稱和指定的不同」時才另外給 reported_model
class FakeCompletions:
    """Stands in for client.chat.completions and records the requests."""

    def __init__(self, content="Hi there", has_details=True, error=None, reported_model=None):
        self.last_request = None
        self.requests = []
        self.content = content
        self.has_details = has_details
        self.error = error
        self.reported_model = reported_model

    def create(self, **kwargs):
        self.last_request = kwargs
        self.requests.append(kwargs)
        if self.error:
            raise self.error
        if self.has_details:
            details = SimpleNamespace(reasoning_tokens=0)
        else:
            details = None
        return SimpleNamespace(
            model=self.reported_model or kwargs["model"],
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))],
            usage=SimpleNamespace(
                prompt_tokens=13,
                completion_tokens=11,
                completion_tokens_details=details,
            ),
        )


# 建立假連線；同時回傳「連線」和「筆記本」，讓測試能檢查送出了什麼
def make_fake_client(content="Hi there", has_details=True, error=None, reported_model=None):
    """Return the fake client and its completions, so tests can check the request."""
    completions = FakeCompletions(content, has_details, error, reported_model)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


# 假的資料庫：只把收到的寫入記下來，什麼都不存；讓不測額度的測試不需要 Docker
class FakeDynamoDB:
    """Stands in for a DynamoDB client and records the updates it receives."""

    def __init__(self):
        self.updates = []

    def update_item(self, **kwargs):
        self.updates.append(kwargs)