import os
from dotenv import load_dotenv
import boto3

load_dotenv()

client = boto3.client(
    "bedrock",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

models = client.list_foundation_models()

for model in models["modelSummaries"]:
    print(model["modelId"])