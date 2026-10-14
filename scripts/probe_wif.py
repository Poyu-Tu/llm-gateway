"""One-off probe before M4: can the gateway call OpenAI with workload identity instead of an API key?

Run from the repo root on the personal PC only (it calls AWS STS and the real API).
Do NOT load .env: this probe must work without an OpenAI API key.

    $env:OPENAI_IDENTITY_PROVIDER_ID = "<from OpenAI organization settings>"
    $env:OPENAI_SERVICE_ACCOUNT_ID = "<from the project's service account>"
    $env:OPENAI_WIF_AUDIENCE = "<the audience you typed into OpenAI>"
    uv run python -m scripts.probe_wif
"""

import base64
import json
import os

import boto3
from openai import OpenAI

# 區域固定東京；STS 一定要用地區網址，OpenAI 的文件寫明全球網址不支援
REGION = "ap-northeast-1"
STS_ENDPOINT = f"https://sts.{REGION}.amazonaws.com"
# AWS 開出來的身分證明只活 5 分鐘：夠 SDK 拿去換一次 OpenAI 的通行證就好
TOKEN_LIFETIME_SECONDS = 300
# 只用便宜模型問一句；這次要證明的是「通不通」，不是回答品質
PROBE_MODEL = "gpt-6-luna"
PROBE_PROMPT = "Say hi in five words."


# 向 AWS 要一張身分證明（JWT）；用的是這台電腦目前登入的 AWS 身分
def get_aws_identity_token() -> str:
    """Return a short-lived JWT from AWS STS for the configured audience."""
    sts = boto3.client("sts", region_name=REGION, endpoint_url=STS_ENDPOINT)
    response = sts.get_web_identity_token(
        Audience=[os.environ["OPENAI_WIF_AUDIENCE"]],
        SigningAlgorithm="ES384",
        DurationSeconds=TOKEN_LIFETIME_SECONDS,
    )
    return response["WebIdentityToken"]


# 只解開 JWT 中間那段來看內容，不驗證簽章；token 本身絕對不印出來
def read_claims(token: str) -> dict:
    """Return the payload of a JWT without verifying it, for display only."""
    payload = token.split(".")[1]
    # base64 的長度要是 4 的倍數，JWT 會把結尾的 = 拿掉，這裡補回去
    payload = payload + "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


# 第一段：AWS 給不給身分證明；第二段：OpenAI 收不收，chat.completions 能不能用
def main() -> None:
    """Check each link of the keyless path and print what happened."""
    if os.environ.get("OPENAI_API_KEY"):
        print("STOP: OPENAI_API_KEY is set. Run without --env-file, so the probe cannot fall back to the key.")
        return

    token = get_aws_identity_token()
    claims = read_claims(token)
    print("[1] AWS 開出身分證明")
    print(f"    iss: {claims.get('iss')}")
    print(f"    aud: {claims.get('aud')}")
    print(f"    sub: {claims.get('sub')}")
    print(f"    有效秒數: {claims.get('exp', 0) - claims.get('iat', 0)}")

    client = OpenAI(
        workload_identity={
            "identity_provider_id": os.environ["OPENAI_IDENTITY_PROVIDER_ID"],
            "service_account_id": os.environ["OPENAI_SERVICE_ACCOUNT_ID"],
            "provider": {"token_type": "jwt", "get_token": get_aws_identity_token},
        },
        max_retries=0,
        timeout=60,
    )
    response = client.chat.completions.create(
        model=PROBE_MODEL,
        messages=[{"role": "user", "content": PROBE_PROMPT}],
        reasoning_effort="none",
        max_completion_tokens=50,
    )
    usage = response.usage
    print("[2] OpenAI 收下身分證明，chat.completions 有回答")
    print(f"    回報的模型: {response.model}")
    print(f"    結束原因: {response.choices[0].finish_reason}")
    print(f"    輸入 {usage.prompt_tokens}、輸出 {usage.completion_tokens} 個 token")
    print(f"    回答: {response.choices[0].message.content}")


if __name__ == "__main__":
    main()
