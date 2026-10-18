"""How the gateway proves who it is to OpenAI."""

import boto3
import pytest
from botocore.stub import Stubber

from app import openai_auth
from app.openai_auth import (
    get_aws_identity_token,
    make_openai_client,
    read_openai_auth,
)

# SDK 在身分聯盟模式下放在 api_key 的固定字樣（openai 3.19.2）：代表「這個連線沒有金鑰」
WORKLOAD_IDENTITY_PLACEHOLDER = "workload-identity-auth"


# ---- read_openai_auth()：一定要明講 ----


@pytest.mark.parametrize("value", ["api_key", "workload_identity"])
def test_read_openai_auth_accepts_the_two_modes(monkeypatch, value):
    monkeypatch.setenv("OPENAI_AUTH", value)

    assert read_openai_auth() == value


def test_read_openai_auth_requires_the_setting(monkeypatch):
    monkeypatch.delenv("OPENAI_AUTH", raising=False)

    with pytest.raises(KeyError):
        read_openai_auth()


# 大小寫、空白、舊名字、空字串都不收：寫錯就停，不猜
@pytest.mark.parametrize("value", ["API_KEY", "api_key ", "key", "wif", ""])
def test_read_openai_auth_rejects_anything_else(monkeypatch, value):
    monkeypatch.setenv("OPENAI_AUTH", value)

    with pytest.raises(ValueError):
        read_openai_auth()


# ---- make_openai_client()：兩種模式 ----


def test_api_key_mode_uses_the_key_from_the_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")

    client = make_openai_client("api_key", max_retries=0, timeout=60)

    assert client.api_key == "sk-test-not-a-real-key"
    assert client.workload_identity is None
    assert client.max_retries == 0
    assert client.timeout == 60


def set_workload_identity_env(monkeypatch):
    monkeypatch.setenv("OPENAI_IDENTITY_PROVIDER_ID", "idp-test")
    monkeypatch.setenv("OPENAI_SERVICE_ACCOUNT_ID", "svc-test")


def test_workload_identity_mode_uses_the_aws_token(monkeypatch):
    set_workload_identity_env(monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = make_openai_client("workload_identity", max_retries=0, timeout=60)

    assert client.workload_identity["identity_provider_id"] == "idp-test"
    assert client.workload_identity["service_account_id"] == "svc-test"
    assert client.workload_identity["provider"]["token_type"] == "jwt"
    assert client.workload_identity["provider"]["get_token"] is get_aws_identity_token
    assert client.max_retries == 0
    assert client.timeout == 60


# 雲端就算環境裡剛好有金鑰，也不能拿來用：用了等於身分聯盟形同虛設
def test_workload_identity_mode_ignores_an_api_key(monkeypatch):
    set_workload_identity_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")

    client = make_openai_client("workload_identity", max_retries=0, timeout=60)

    assert client.api_key == WORKLOAD_IDENTITY_PLACEHOLDER


def test_workload_identity_mode_requires_the_ids(monkeypatch):
    monkeypatch.delenv("OPENAI_IDENTITY_PROVIDER_ID", raising=False)
    monkeypatch.setenv("OPENAI_SERVICE_ACCOUNT_ID", "svc-test")

    with pytest.raises(KeyError):
        make_openai_client("workload_identity", max_retries=0, timeout=60)


def test_make_openai_client_rejects_an_unknown_mode():
    with pytest.raises(ValueError):
        make_openai_client("wif", max_retries=0, timeout=60)


# ---- get_aws_identity_token()：向東京的 STS 要一張給 OpenAI 用的 5 分鐘證明 ----


def test_identity_token_comes_from_the_regional_sts(monkeypatch):
    monkeypatch.setenv("OPENAI_WIF_AUDIENCE", "llm-gateway-capstone")
    # 假的 AWS 身分：Stubber 不會真的連線，但建立連線物件要有值
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")

    made = []
    real_client = boto3.client

    # 攔下 boto3.client：照原樣建連線，再掛上 Stubber，事先寫好「應該收到什麼、回什麼」
    def stubbed_client(*args, **kwargs):
        client = real_client(*args, **kwargs)
        stubber = Stubber(client)
        stubber.add_response(
            "get_web_identity_token",
            {"WebIdentityToken": "header.payload.signature", "Expiration": "2026-10-18T00:05:00Z"},
            {
                "Audience": ["llm-gateway-capstone"],
                "SigningAlgorithm": "ES384",
                "DurationSeconds": 300,
            },
        )
        stubber.activate()
        made.append(client)
        return client

    monkeypatch.setattr(openai_auth.boto3, "client", stubbed_client)

    token = get_aws_identity_token()

    assert token == "header.payload.signature"
    assert made[0].meta.endpoint_url == "https://sts.ap-northeast-1.amazonaws.com"
    assert made[0].meta.region_name == "ap-northeast-1"
