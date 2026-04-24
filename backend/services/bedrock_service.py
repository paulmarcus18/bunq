from __future__ import annotations

import base64
import json
import os
import re
from typing import Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from models.schemas import AnalysisResponse, DocumentType, RecommendedAction, RiskLevel, Urgency


SYSTEM_PROMPT = """You are a financial document triage assistant for a banking app.
Analyze the provided financial document/email screenshot/photo.
Extract all payment/action details.
Classify document type.
Detect scam risk.
Recommend the safest action.
Return valid JSON only.
Never invent IBAN or amount. If uncertain, use null and lower confidence.
For suspicious documents, recommend mark_suspicious or review_manually.
Do not recommend immediate payment if risk is high."""


def _mock_analysis(optional_text: Optional[str]) -> AnalysisResponse:
    text = (optional_text or "").lower()
    risk = RiskLevel.high if any(word in text for word in ["urgent", "crypto", "gift card", "verify now"]) else RiskLevel.medium
    action = RecommendedAction.mark_suspicious if risk == RiskLevel.high else RecommendedAction.review_manually
    document_type = DocumentType.scam_risk if risk == RiskLevel.high else DocumentType.unknown
    urgency = Urgency.high if "today" in text or "immediately" in text else Urgency.medium

    return AnalysisResponse(
        document_type=document_type,
        sender="Demo sender" if optional_text else None,
        recipient_name=None,
        iban=None,
        amount=None,
        currency="EUR",
        due_date=None,
        payment_reference=None,
        urgency=urgency,
        risk_level=risk,
        recommended_action=action,
        summary="Demo analysis generated because Bedrock credentials or supported file content were unavailable.",
        reasoning="This fallback keeps the MVP usable locally while still favoring manual review for uncertain requests.",
        confidence=0.34,
    )


def _extract_json_block(raw_text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def _build_messages(
    file_bytes: Optional[bytes],
    content_type: Optional[str],
    optional_text: Optional[str],
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []

    if optional_text:
        content.append({"type": "text", "text": f"User-provided text context:\n{optional_text}"})

    if file_bytes and content_type and content_type.startswith("image/"):
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": content_type,
                    "data": base64.b64encode(file_bytes).decode("utf-8"),
                },
            }
        )

    content.append(
        {
            "type": "text",
            "text": (
                "Return JSON only with keys: "
                "document_type, sender, recipient_name, iban, amount, currency, due_date, "
                "payment_reference, urgency, risk_level, recommended_action, summary, reasoning, confidence."
            ),
        }
    )

    return [{"role": "user", "content": content}]


def _get_bedrock_client():
    region = os.getenv("AWS_REGION", "us-east-1")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    if not access_key or not secret_key:
        return None

    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


def analyze_document_with_claude(
    file_bytes: Optional[bytes],
    content_type: Optional[str],
    optional_text: Optional[str] = None,
) -> AnalysisResponse:
    client = _get_bedrock_client()
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")

    if client is None:
        return _mock_analysis(optional_text)

    try:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1200,
            "temperature": 0,
            "system": SYSTEM_PROMPT,
            "messages": _build_messages(file_bytes, content_type, optional_text),
        }
        response = client.invoke_model(modelId=model_id, body=json.dumps(body))
        payload = json.loads(response["body"].read().decode("utf-8"))
        text = "".join(
            block.get("text", "")
            for block in payload.get("content", [])
            if block.get("type") == "text"
        )
        return AnalysisResponse.model_validate(_extract_json_block(text))
    except (BotoCoreError, ClientError, ValueError, json.JSONDecodeError):
        return _mock_analysis(optional_text)
