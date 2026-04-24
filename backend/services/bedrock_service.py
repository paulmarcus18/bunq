from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from models.schemas import AnalysisResponse, DocumentType, RecommendedAction, RiskLevel, Urgency


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a financial document triage assistant for a banking app.
Analyze the provided financial document/email screenshot/photo.
Extract all payment/action details.
Classify document type.
Detect scam risk.
Recommend the safest action.
Return valid JSON only.
Never invent IBAN or amount. If uncertain, use null and lower confidence.
Infer the correct currency from the document if visible. Do not default to EUR when another currency is shown.
recipient_name must be the party the user would pay or request money from, not the customer name written on the document.
iban must be the destination payment IBAN only. Never return the user's own account number as the destination IBAN.
If the document says the amount will be debited automatically or by direct debit, mention that in the reasoning and avoid recommending pay_now.
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
        action_required=False,
        direct_debit_detected=False,
        decision_reasons=["Demo mode is active, so the result should be reviewed manually."],
    )


def _error_analysis(optional_text: Optional[str], exc: Exception) -> AnalysisResponse:
    logger.exception("Bedrock analysis failed")
    text = (optional_text or "").lower()
    urgency = Urgency.high if "today" in text or "immediately" in text else Urgency.medium
    message = str(exc).strip() or exc.__class__.__name__

    return AnalysisResponse(
        document_type=DocumentType.unknown,
        sender=None,
        recipient_name=None,
        iban=None,
        amount=None,
        currency="EUR",
        due_date=None,
        payment_reference=None,
        urgency=urgency,
        risk_level=RiskLevel.medium,
        recommended_action=RecommendedAction.review_manually,
        summary="Bedrock analysis failed, so the document needs manual review.",
        reasoning=f"AWS Bedrock error: {message[:180]}",
        confidence=0.0,
        action_required=False,
        direct_debit_detected=False,
        decision_reasons=["The AI analysis failed, so no payment action should be prepared automatically."],
    )


def _extract_json_block(raw_text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def _normalize_choice(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_document_type(value: Any) -> str:
    normalized = _normalize_choice(value)
    aliases = {
        "payment_notice": DocumentType.fine.value,
        "offence_notice": DocumentType.fine.value,
        "traffic_fine": DocumentType.fine.value,
        "speeding_ticket": DocumentType.fine.value,
        "ticket": DocumentType.fine.value,
        "bill": DocumentType.invoice.value,
        "utility": DocumentType.utility_bill.value,
        "tax": DocumentType.tax_letter.value,
        "subscription": DocumentType.subscription_change.value,
        "refund_notice": DocumentType.refund.value,
        "scam": DocumentType.scam_risk.value,
    }
    if normalized in {item.value for item in DocumentType}:
        return normalized
    return aliases.get(normalized, DocumentType.unknown.value)


def _normalize_level(value: Any, allowed: set[str], default: str) -> str:
    normalized = _normalize_choice(value)
    if normalized in allowed:
        return normalized
    titled = normalized.title()
    if titled.lower() in allowed:
        return titled.lower()
    return default


def _normalize_confidence(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0

    if numeric > 1:
        if numeric <= 10:
            return round(numeric / 10, 2)
        if numeric <= 100:
            return round(numeric / 100, 2)
        return 1.0
    if numeric < 0:
        return 0.0
    return round(numeric, 2)


def _normalize_amount(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    cleaned = re.sub(r"[^\d,.\-]", "", text)
    if cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    elif cleaned.count(",") > 0 and cleaned.count(".") > 0:
        cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def _normalize_analysis_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["document_type"] = _normalize_document_type(payload.get("document_type"))
    normalized["urgency"] = _normalize_level(
        payload.get("urgency"),
        {item.value for item in Urgency},
        Urgency.medium.value,
    )
    normalized["risk_level"] = _normalize_level(
        payload.get("risk_level"),
        {item.value for item in RiskLevel},
        RiskLevel.medium.value,
    )
    normalized["recommended_action"] = _normalize_choice(payload.get("recommended_action")) or RecommendedAction.review_manually.value
    if normalized["recommended_action"] not in {item.value for item in RecommendedAction}:
        normalized["recommended_action"] = RecommendedAction.review_manually.value
    normalized["confidence"] = _normalize_confidence(payload.get("confidence"))
    normalized["amount"] = _normalize_amount(payload.get("amount"))
    currency = str(payload.get("currency") or "EUR").strip().upper()
    normalized["currency"] = currency if len(currency) == 3 else "EUR"
    normalized["action_required"] = bool(payload.get("action_required", False))
    normalized["direct_debit_detected"] = bool(payload.get("direct_debit_detected", False))
    reasons = payload.get("decision_reasons")
    if isinstance(reasons, list):
        normalized["decision_reasons"] = [str(reason).strip() for reason in reasons if str(reason).strip()]
    else:
        normalized["decision_reasons"] = []
    return normalized


def _normalize_text_for_matching(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _contains_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def _detect_direct_debit(optional_text: Optional[str]) -> bool:
    if not optional_text:
        return False
    patterns = [
        "we schrijven dit bedrag",
        "automatische incasso",
        "automatisch af",
        "afschrijven van je rekening",
        "direct debit",
        "will be debited",
        "we will debit",
        "collected automatically",
    ]
    return _contains_any(optional_text, patterns)


def _looks_like_person_name(value: Optional[str]) -> bool:
    if not value:
        return False
    tokens = [token for token in re.split(r"\s+", value.strip()) if token]
    if not tokens or len(tokens) > 4:
        return False
    return all(any(char.isalpha() for char in token) for token in tokens)


def _extract_sender_from_text(optional_text: Optional[str]) -> Optional[str]:
    if not optional_text:
        return None

    patterns = [
        r"factuur\s+([A-Z][A-Za-z0-9.&\- ]{2,40})",
        r"invoice\s+from\s+([A-Z][A-Za-z0-9.&\- ]{2,40})",
        r"([A-Z][A-Za-z0-9.&\- ]{2,40}\s+B\.V\.)",
        r"([A-Z][A-Za-z0-9.&\- ]{2,40}\s+N\.V\.)",
    ]
    for pattern in patterns:
        match = re.search(pattern, optional_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_company_like_name(optional_text: Optional[str]) -> Optional[str]:
    if not optional_text:
        return None

    patterns = [
        r"from\s+([A-Z][A-Za-z0-9&.,'()\- ]{2,60})",
        r"invoice reminder from\s+([A-Z][A-Za-z0-9&.,'()\- ]{2,60})",
        r"final notice from\s+([A-Z][A-Za-z0-9&.,'()\- ]{2,60})",
        r"([A-Z][A-Za-z0-9&.,'()\- ]{2,60}\s+C\.V\.)",
        r"([A-Z][A-Za-z0-9&.,'()\- ]{2,60}\s+B\.V\.)",
        r"([A-Z][A-Za-z0-9&.,'()\- ]{2,60}\s+N\.V\.)",
        r"([A-Z][A-Za-z0-9&.,'()\- ]{2,60}\s+Ltd\.?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, optional_text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" .,-")
    return None


def _normalize_iban_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value).upper()


def _is_user_account_iban(iban: Optional[str], optional_text: Optional[str]) -> bool:
    if not iban or not optional_text:
        return False

    iban_token = _normalize_iban_token(iban)
    lines = optional_text.splitlines()
    for index, line in enumerate(lines):
        normalized_line = _normalize_iban_token(line)
        if iban_token and iban_token in normalized_line:
            window = " ".join(lines[max(0, index - 2): min(len(lines), index + 3)])
            normalized_window = _normalize_text_for_matching(window)
            if _contains_any(
                normalized_window,
                [
                    "jouw rekeningnummer",
                    "your account number",
                    "rekeningnummer kpn",
                    "we schrijven dit bedrag",
                    "afschrijven van je rekening",
                    "bankrekening waarmee",
                    "rekening waarvan",
                ],
            ):
                return True
    return False


def _apply_safety_rules(analysis: AnalysisResponse, optional_text: Optional[str]) -> AnalysisResponse:
    direct_debit_detected = _detect_direct_debit(optional_text) or analysis.direct_debit_detected
    sender_from_text = _extract_sender_from_text(optional_text)
    company_from_text = _extract_company_like_name(optional_text)
    reasons: list[str] = list(analysis.decision_reasons)

    recipient_name = analysis.recipient_name
    sender = analysis.sender or sender_from_text or company_from_text

    if (
        analysis.document_type in {DocumentType.invoice, DocumentType.utility_bill, DocumentType.unknown}
        and recipient_name
        and _looks_like_person_name(recipient_name)
        and company_from_text
    ):
        recipient_name = company_from_text
        reasons.append("The document appears to request payment to a company, so the beneficiary was corrected from the customer name.")

    if analysis.document_type == DocumentType.unknown and analysis.amount is not None and analysis.iban:
        analysis = analysis.model_copy(update={"document_type": DocumentType.invoice})
        reasons.append("The document includes a payable amount and destination IBAN, so it was treated as an invoice/reminder.")

    if analysis.document_type in {DocumentType.invoice, DocumentType.utility_bill} and direct_debit_detected:
        if analysis.iban and _is_user_account_iban(analysis.iban, optional_text):
            analysis.iban = None
            reasons.append("The detected IBAN appears to be the user's own account, not the payee destination.")

        if recipient_name and _looks_like_person_name(recipient_name) and sender:
            recipient_name = sender
            reasons.append("The named person appears to be the customer, so the payee was switched to the bill issuer.")

    recommended_action = analysis.recommended_action
    action_required = analysis.action_required

    if analysis.risk_level == RiskLevel.high:
        recommended_action = RecommendedAction.mark_suspicious
        action_required = False
        reasons.append("High-risk documents should not trigger a payment preparation flow.")
    elif direct_debit_detected:
        recommended_action = RecommendedAction.ignore if analysis.risk_level == RiskLevel.low else RecommendedAction.review_manually
        action_required = False
        reasons.append("The document indicates automatic collection or direct debit, so manual payment is not recommended.")
    elif (
        analysis.recommended_action == RecommendedAction.pay_now
        and analysis.amount is not None
        and analysis.iban
        and analysis.risk_level != RiskLevel.high
    ):
        recommended_action = RecommendedAction.pay_now
        action_required = True
        reasons.append("The document contains a payable amount, destination IBAN, and no high-risk warning, so payment can be confirmed by the user.")
    elif analysis.document_type == DocumentType.fine and analysis.amount is not None and analysis.risk_level != RiskLevel.high:
        recommended_action = RecommendedAction.schedule_payment
        action_required = True
        reasons.append("This looks like a legitimate fine with an amount due, so scheduling a payment is the safest next step.")
    elif analysis.document_type in {DocumentType.invoice, DocumentType.utility_bill} and analysis.amount is not None:
        recommended_action = RecommendedAction.review_manually
        action_required = True
        reasons.append("This appears to be a legitimate bill, but payment details should be checked before preparing a transfer.")

    if not reasons:
        reasons.append("The recommendation is based on the extracted payment details and risk assessment.")

    summary = analysis.summary
    if direct_debit_detected:
        summary = f"{summary.rstrip('.')} Automatic debit appears to be in place."

    reasoning = analysis.reasoning
    if direct_debit_detected and "direct debit" not in reasoning.lower() and "automatic" not in reasoning.lower():
        reasoning = f"{reasoning.rstrip('.')} The document also suggests automatic debit or direct debit."

    return analysis.model_copy(
        update={
            "sender": sender,
            "recipient_name": recipient_name,
            "recommended_action": recommended_action,
            "action_required": action_required,
            "direct_debit_detected": direct_debit_detected,
            "decision_reasons": reasons[:3],
            "summary": summary,
            "reasoning": reasoning,
        }
    )


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
    session_token = os.getenv("AWS_SESSION_TOKEN")
    if not access_key or not secret_key:
        return None

    client_kwargs: dict[str, Any] = {
        "region_name": region,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
    }
    if session_token:
        client_kwargs["aws_session_token"] = session_token

    return boto3.client("bedrock-runtime", **client_kwargs)


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
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read().decode("utf-8"))
        text = "".join(
            block.get("text", "")
            for block in payload.get("content", [])
            if block.get("type") == "text"
        )
        parsed = _extract_json_block(text)
        normalized = _normalize_analysis_payload(parsed)
        analysis = AnalysisResponse.model_validate(normalized)
        return _apply_safety_rules(analysis, optional_text)
    except (BotoCoreError, ClientError, ValueError, json.JSONDecodeError) as exc:
        return _error_analysis(optional_text, exc)
