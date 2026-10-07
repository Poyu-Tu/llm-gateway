import os

import boto3
from botocore.client import BaseClient

# 區域固定東京，和之後上雲一致
REGION = "ap-northeast-1"

# 練習場用的假帳密：DynamoDB Local 不驗證真假，但一定要有值
# 明確帶入，boto3 才不會去找這台電腦上真的 AWS 身分來用
LOCAL_ACCESS_KEY = "local"
LOCAL_SECRET_KEY = "local"

# 表名只寫在這一處，別處一律用常數：常數名稱打錯會直接報錯，字串打錯只會變成「找不到資料表」
API_KEYS_TABLE = "api_keys"
QUOTAS_TABLE = "quotas"
AUDIT_TABLE = "audit"


# 要連哪裡一定要明講：沒設定就報錯，不讓 boto3 照預設去連真的 AWS
def make_dynamodb_client() -> BaseClient:
    """Return a DynamoDB client for the endpoint named in the environment."""
    endpoint = os.environ["DYNAMODB_ENDPOINT_URL"]
    client = boto3.client(
        "dynamodb",
        endpoint_url=endpoint,
        region_name=REGION,
        aws_access_key_id=LOCAL_ACCESS_KEY,
        aws_secret_access_key=LOCAL_SECRET_KEY,
    )
    return client