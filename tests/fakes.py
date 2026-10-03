"""Fake objects shared by tests."""

from types import SimpleNamespace


# 假的 OpenAI：把收到的請求記下來，再回傳固定的假回應
class FakeCompletions:
    """Stands in for client.chat.completions and records the request."""

    def __init__(self, content="Hi there", has_details=True, error=None):
        self.last_request = None
        self.content = content
        self.has_details = has_details
        self.error = error

    def create(self, **kwargs):
        self.last_request = kwargs
        if self.error:
            raise self.error
        if self.has_details:
            details = SimpleNamespace(reasoning_tokens=0)
        else:
            details = None
        return SimpleNamespace(
            model="gpt-6-luna",
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))],
            usage=SimpleNamespace(
                prompt_tokens=13,
                completion_tokens=11,
                completion_tokens_details=details,
            ),
        )


# 建立假連線；同時回傳「連線」和「筆記本」，讓測試能檢查送出了什麼
def make_fake_client(content="Hi there", has_details=True, error=None):
    """Return the fake client and its completions, so tests can check the request."""
    completions = FakeCompletions(content, has_details, error)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions