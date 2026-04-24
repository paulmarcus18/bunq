import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

region = os.getenv("AWS_REGION", "us-east-1")
model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")

client = boto3.client("bedrock-runtime", region_name=region)

body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 300,
    "messages": [
        {
            "role": "user",
            "content": "Reply with only this JSON: {\"ok\": true, \"message\": \"Claude works\"}"
        }
    ],
}

response = client.invoke_model(
    modelId=model_id,
    body=json.dumps(body),
    contentType="application/json",
    accept="application/json",
)

result = json.loads(response["body"].read())
print(json.dumps(result, indent=2))
print("Using model:", model_id)