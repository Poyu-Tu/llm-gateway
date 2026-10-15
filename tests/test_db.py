import boto3
import pytest

from app.db import make_dynamodb_client

# 練習場的網址：埠故意用 9999，函式把網址寫死就會被抓到
LOCAL_URL = "http://127.0.0.1:9999"
# AWS 東京區 DynamoDB 的網址：不給網址時 boto3 自己算出來的就是這個
TOKYO_DYNAMODB_URL = "https://dynamodb.ap-northeast-1.amazonaws.com"


# 這幾個測試只看連線物件的設定，不會真的連線；身分用假的，免得讀到這台電腦上真的 AWS 身分
@pytest.fixture(autouse=True)
def fake_aws_identity(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIA-FROM-THE-ROLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret-from-the-role")
    # boto3 會把找到的身分記起來重複用；清掉，確保每個測試都重新找、找到的是上面這組
    monkeypatch.setattr(boto3, "DEFAULT_SESSION", None)


# 沒設定要連哪裡就不連：boto3 的預設是連真的 AWS
def test_make_dynamodb_client_requires_target(monkeypatch):
    monkeypatch.delenv("DYNAMODB_TARGET", raising=False)

    with pytest.raises(KeyError):
        make_dynamodb_client()


# 寫網址：連那個網址
def test_make_dynamodb_client_uses_url_from_target(monkeypatch):
    monkeypatch.setenv("DYNAMODB_TARGET", LOCAL_URL)

    client = make_dynamodb_client()

    assert client.meta.endpoint_url == LOCAL_URL


# 寫網址：帳密用假的 local，不能用到這台電腦上真的 AWS 身分
def test_make_dynamodb_client_uses_dummy_credentials_for_a_url(monkeypatch):
    monkeypatch.setenv("DYNAMODB_TARGET", LOCAL_URL)

    client = make_dynamodb_client()

    # 讀連線物件裡簽名用的身分（boto3 沒有公開的讀法，這是內部欄位）
    assert client._request_signer._credentials.access_key == "local"


# 寫 aws：連東京區真的 DynamoDB
def test_make_dynamodb_client_uses_tokyo_for_aws(monkeypatch):
    monkeypatch.setenv("DYNAMODB_TARGET", "aws")

    client = make_dynamodb_client()

    assert client.meta.endpoint_url == TOKYO_DYNAMODB_URL
    assert client.meta.region_name == "ap-northeast-1"


# 寫 aws：身分交給 boto3 自己找（在 Fargate 上就是任務的 IAM 角色），不能用假的 local
def test_make_dynamodb_client_uses_the_real_identity_for_aws(monkeypatch):
    monkeypatch.setenv("DYNAMODB_TARGET", "aws")

    client = make_dynamodb_client()

    assert client._request_signer._credentials.access_key == "AKIA-FROM-THE-ROLE"


# 寫錯就報錯：大小寫不對、空的、不是網址，都不能被猜成任何一邊
@pytest.mark.parametrize("target", ["AWS", "", "dynamodb", "127.0.0.1:8001"])
def test_make_dynamodb_client_rejects_unknown_target(monkeypatch, target):
    monkeypatch.setenv("DYNAMODB_TARGET", target)

    with pytest.raises(ValueError, match="DYNAMODB_TARGET"):
        make_dynamodb_client()


# 資料庫連不上時要快點放棄：預設會重試到將近一分鐘，使用者等不了那麼久；雲端和練習場都一樣
@pytest.mark.parametrize("target", [LOCAL_URL, "aws"])
def test_make_dynamodb_client_gives_up_quickly(monkeypatch, target):
    monkeypatch.setenv("DYNAMODB_TARGET", target)

    client = make_dynamodb_client()

    assert client.meta.config.connect_timeout == 2
    assert client.meta.config.read_timeout == 5
    assert client.meta.config.retries == {"total_max_attempts": 2, "mode": "standard"}
