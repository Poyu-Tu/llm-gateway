"""How the gateway proves who it is to OpenAI: an API key (local) or AWS workload identity (cloud)."""

import os

import boto3
from botocore.config import Config
from openai import OpenAI

# OPENAI_AUTH 只收這兩個字：本機用 .env 的金鑰；雲端用 AWS 的身分換 OpenAI 的通行證（不用金鑰）
API_KEY_AUTH = "api_key"
WORKLOAD_IDENTITY_AUTH = "workload_identity"

# 區域固定東京；STS 一定要用地區網址：OpenAI 的文件寫明全球網址開不出這種證明
REGION = "ap-northeast-1"
STS_ENDPOINT = f"https://sts.{REGION}.amazonaws.com"

# AWS 開的身分證明只活 5 分鐘：夠 SDK 拿去換一次 OpenAI 的通行證就好（任務角色的政策也限 300 秒）
TOKEN_LIFETIME_SECONDS = 300
# 簽章演算法：AWS 這個功能支援 ES384 與 RS256，身分聯盟探測時用的是 ES384
SIGNING_ALGORITHM = "ES384"

# 向 STS 要證明的連線：連不上就快點放棄，跟資料庫一樣不讓使用者乾等
STS_CONFIG = Config(
    connect_timeout=2,
    read_timeout=5,
    retries={"total_max_attempts": 2, "mode": "standard"},
)


# 用哪一種方式向 OpenAI 證明身分，一定要明講：沒設或寫錯就報錯，不讓程式自己猜
def read_openai_auth() -> str:
    """Return the OpenAI auth mode named in the environment."""
    auth = os.environ["OPENAI_AUTH"]
    if auth not in (API_KEY_AUTH, WORKLOAD_IDENTITY_AUTH):
        raise ValueError(f"OPENAI_AUTH must be 'api_key' or 'workload_identity', got: {auth!r}")
    return auth


# 向 AWS 要一張身分證明（JWT）；在 Fargate 上，身分就是任務角色。證明本身不印、不記
def get_aws_identity_token() -> str:
    """Return a short-lived JWT from the regional AWS STS endpoint for the OpenAI audience."""
    sts = boto3.client("sts", region_name=REGION, endpoint_url=STS_ENDPOINT, config=STS_CONFIG)
    response = sts.get_web_identity_token(
        Audience=[os.environ["OPENAI_WIF_AUDIENCE"]],
        SigningAlgorithm=SIGNING_ALGORITHM,
        DurationSeconds=TOKEN_LIFETIME_SECONDS,
    )
    return response["WebIdentityToken"]


# 建 OpenAI 連線：金鑰模式交給 SDK 讀 OPENAI_API_KEY；身分聯盟模式完全不看金鑰
# SDK 會自己拿證明去換通行證，快到期時再換，所以整個程式共用這一個連線就好
def make_openai_client(auth: str, max_retries: int, timeout: float) -> OpenAI:
    """Return an OpenAI client that authenticates the way `auth` says."""
    if auth == API_KEY_AUTH:
        return OpenAI(max_retries=max_retries, timeout=timeout)

    if auth == WORKLOAD_IDENTITY_AUTH:
        return OpenAI(
            workload_identity={
                "identity_provider_id": os.environ["OPENAI_IDENTITY_PROVIDER_ID"],
                "service_account_id": os.environ["OPENAI_SERVICE_ACCOUNT_ID"],
                "provider": {"token_type": "jwt", "get_token": get_aws_identity_token},
            },
            max_retries=max_retries,
            timeout=timeout,
        )

    raise ValueError(f"Unknown OpenAI auth mode: {auth!r}")
