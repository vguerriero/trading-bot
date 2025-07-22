import os
import boto3

SSM_NS = "/trading-bot/prod"

PARAMS = [
    "ALPACA_PAPER_KEY",
    "ALPACA_PAPER_SECRET",
    "ALPACA_LIVE_KEY",
    "ALPACA_LIVE_SECRET",
    "SEC_API_KEY",
    "FRED_API_KEY",
    "NEWSDATA_API_KEY",
    "AUDIT_BUCKET_ARN",
]

def load_secrets(region="us-east-1"):
    """Fetch secrets from AWS SSM Parameter Store and inject into env."""
    ssm = boto3.client("ssm", region_name=region)
    paths = [f"{SSM_NS}/{k}" for k in PARAMS]
    resp = ssm.get_parameters(Names=paths, WithDecryption=True)
    for p in resp["Parameters"]:
        key = p["Name"].split("/")[-1]
        os.environ[key] = p["Value"]
    missing = set(PARAMS) - {p["Name"].split("/")[-1] for p in resp["Parameters"]}
    if missing:
        raise RuntimeError(f"Missing parameters in SSM: {missing}")

if __name__ == "__main__":
    load_secrets()
    print("All secrets loaded!")