from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from PIL import Image

from models.schemas import AnalysisResponse, DocumentType, RecommendedAction


logger = logging.getLogger(__name__)
MAX_BEDROCK_IMAGE_BYTES = 5 * 1024 * 1024


SYSTEM_PROMPT = """You are a financial document parser for a banking app.
Analyze the provided document, screenshot, or photo and extract only the fields needed to create a bunq payment or bunq scheduled payment.
Return valid JSON only.

Rules:
- document_type must be exactly one of: fine, invoice, utility_bill, tax_letter.
- Never return unknown. If the category is not obvious, choose the closest of those four.
- Never invent IBAN, amount, due date, or payment reference.
- due_date must be returned as YYYY-MM-DD.
- If the document says payment is due within N days and also shows an invoice or issue date, derive due_date from that information.
- If uncertain, return null.
- issuer_name is who issued the document.
- beneficiary_name is who should receive money from the user.
- beneficiary_iban is the destination payment IBAN only.
- payment_reference is the transfer reference / kenmerk / invoice number that should accompany the payment.
- payment_description is a short transfer description suitable for bunq.
- manual_payment_required is true only when the user is expected to make a manual bank payment.
- auto_debit_detected is true only when the document says the amount will be collected automatically or already debited.
- is_suspicious is true when the request looks like phishing, invoice fraud, spoofing, or social engineering.
- phishing_signals must be a short list of concrete warning signs, or an empty list when none are found.
- If auto_debit_detected is true, recommended_action must be ignore.
- If is_suspicious is true, recommended_action must be review_manually or ignore.
- If manual payment is required and the document includes amount and beneficiary_iban, choose pay_now or schedule_payment.
"""


def _mock_analysis(optional_text: Optional[str]) -> AnalysisResponse:
    return AnalysisResponse(
        document_type=DocumentType.invoice,
        issuer_name="Demo issuer" if optional_text else None,
        beneficiary_name=None,
        beneficiary_iban=None,
        amount=None,
        currency="EUR",
        due_date=None,
        payment_reference=None,
        payment_description=None,
        manual_payment_required=False,
        auto_debit_detected=False,
        is_suspicious=False,
        phishing_signals=[],
        recommended_action=RecommendedAction.review_manually,
        summary="Demo analysis generated because Bedrock was not available.",
        action_required=False,
    )


def _error_analysis(exc: Exception) -> AnalysisResponse:
    logger.exception("Bedrock analysis failed")
    return AnalysisResponse(
        document_type=DocumentType.invoice,
        issuer_name=None,
        beneficiary_name=None,
        beneficiary_iban=None,
        amount=None,
        currency="EUR",
        due_date=None,
        payment_reference=None,
        payment_description=None,
        manual_payment_required=False,
        auto_debit_detected=False,
        is_suspicious=False,
        phishing_signals=[],
        recommended_action=RecommendedAction.review_manually,
        summary=f"Bedrock analysis failed: {str(exc).strip()[:180]}",
        action_required=False,
    )


def _extract_json_block(raw_text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def _prepare_image_for_bedrock(
    file_bytes: Optional[bytes],
    content_type: Optional[str],
) -> tuple[Optional[bytes], Optional[str]]:
    if not file_bytes or not content_type or not content_type.startswith("image/"):
        return file_bytes, content_type

    if len(file_bytes) <= MAX_BEDROCK_IMAGE_BYTES:
        return file_bytes, content_type

    image = Image.open(io.BytesIO(file_bytes))

    if image.mode not in {"RGB", "L"}:
        # Flatten alpha/transparency onto a white background before JPEG compression.
        flattened = Image.new("RGB", image.size, "white")
        alpha_ready = image.convert("RGBA")
        flattened.paste(alpha_ready, mask=alpha_ready.getchannel("A"))
        image = flattened
    elif image.mode == "L":
        image = image.convert("RGB")

    width, height = image.size
    candidates = [
        (2200, 88),
        (1800, 82),
        (1600, 78),
        (1400, 74),
        (1200, 70),
        (1024, 66),
    ]

    for max_dimension, quality in candidates:
        scale = min(1.0, max_dimension / max(width, height))
        resized = image
        if scale < 1.0:
            resized = image.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.Resampling.LANCZOS,
            )

        output = io.BytesIO()
        resized.save(output, format="JPEG", optimize=True, quality=quality)
        compressed = output.getvalue()
        if len(compressed) <= MAX_BEDROCK_IMAGE_BYTES:
            return compressed, "image/jpeg"

    raise ValueError(
        "Uploaded image exceeds Bedrock's 5 MB image limit even after compression. "
        "Try cropping the image or taking a slightly smaller photo."
    )


def _normalize_choice(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "yes", "1", "manual", "required", "detected"}


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


def _parse_date_value(value: str) -> Optional[date]:
    text = value.strip()
    if not text:
        return None

    formats = (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y/%m/%d",
        "%Y.%m.%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_due_date(value: Any) -> Optional[str]:
    text = _normalize_text(value)
    if not text:
        return None

    parsed = _parse_date_value(text)
    if parsed:
        return parsed.isoformat()
    return text


def _normalize_document_type(value: Any) -> str:
    normalized = _normalize_choice(value)
    aliases = {
        "payment_notice": DocumentType.fine.value,
        "offence_notice": DocumentType.fine.value,
        "offense_notice": DocumentType.fine.value,
        "traffic_fine": DocumentType.fine.value,
        "speeding_ticket": DocumentType.fine.value,
        "parking_ticket": DocumentType.fine.value,
        "penalty": DocumentType.fine.value,
        "boete": DocumentType.fine.value,
        "ticket": DocumentType.fine.value,
        "invoice_reminder": DocumentType.invoice.value,
        "payment_reminder": DocumentType.invoice.value,
        "final_notice": DocumentType.invoice.value,
        "reminder": DocumentType.invoice.value,
        "insurance_letter": DocumentType.invoice.value,
        "insurance_invoice": DocumentType.invoice.value,
        "subscription_notice": DocumentType.invoice.value,
        "subscription_change": DocumentType.invoice.value,
        "bill": DocumentType.utility_bill.value,
        "water_bill": DocumentType.utility_bill.value,
        "energy_bill": DocumentType.utility_bill.value,
        "phone_bill": DocumentType.utility_bill.value,
        "mobile_bill": DocumentType.utility_bill.value,
        "internet_bill": DocumentType.utility_bill.value,
        "utility": DocumentType.utility_bill.value,
        "tax": DocumentType.tax_letter.value,
        "tax_bill": DocumentType.tax_letter.value,
        "assessment": DocumentType.tax_letter.value,
        "assessment_notice": DocumentType.tax_letter.value,
        "aanslagbiljet": DocumentType.tax_letter.value,
        "woz": DocumentType.tax_letter.value,
    }
    if normalized in {item.value for item in DocumentType}:
        return normalized
    return aliases.get(normalized, DocumentType.invoice.value)


def _classify_document_type(
    current_type: DocumentType,
    optional_text: Optional[str],
    issuer_name: Optional[str],
    summary: Optional[str],
) -> DocumentType:
    haystack = " ".join(
        part
        for part in [
            current_type.value if current_type else "",
            optional_text or "",
            issuer_name or "",
            summary or "",
        ]
        if part
    ).lower()

    fine_markers = [
        "fine",
        "ticket",
        "offence",
        "offense",
        "penalty",
        "speeding",
        "parking violation",
        "traffic violation",
        "boete",
    ]
    tax_markers = [
        "tax",
        "belasting",
        "aanslag",
        "aanslagbiljet",
        "woz",
        "assessment",
        "heffing",
        "rioolheffing",
        "afvalstoffenheffing",
        "waterschapsbelasting",
        "belastingsamenwerking",
        "municipal tax",
    ]
    utility_markers = [
        "utility",
        "water bill",
        "electricity",
        "energy",
        "gas",
        "internet",
        "mobile",
        "telecom",
        "phone bill",
        "kpn",
        "vodafone",
        "odido",
        "ziggo",
        "t mobile",
        "t-mobile",
    ]
    invoice_markers = [
        "invoice",
        "factuur",
        "reminder",
        "final notice",
        "payment reminder",
        "insurance",
        "premium",
        "renewal",
        "subscription",
        "aon",
    ]

    if any(marker in haystack for marker in fine_markers):
        return DocumentType.fine
    if any(marker in haystack for marker in tax_markers):
        return DocumentType.tax_letter
    if any(marker in haystack for marker in utility_markers):
        return DocumentType.utility_bill
    if any(marker in haystack for marker in invoice_markers):
        return DocumentType.invoice
    if current_type in {DocumentType.fine, DocumentType.invoice, DocumentType.utility_bill, DocumentType.tax_letter}:
        return current_type
    return DocumentType.invoice


def _normalize_recommended_action(value: Any) -> str:
    normalized = _normalize_choice(value)
    if normalized in {item.value for item in RecommendedAction}:
        return normalized
    return RecommendedAction.review_manually.value


def _normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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
            window = " ".join(lines[max(0, index - 2): min(len(lines), index + 3)]).lower()
            if any(
                marker in window
                for marker in [
                    "jouw rekeningnummer",
                    "your account number",
                    "afschrijven van je rekening",
                    "bankrekening waarmee",
                    "rekening waarvan",
                ]
            ):
                return True
    return False


def _is_generic_beneficiary(value: Optional[str]) -> bool:
    if not value:
        return True

    normalized = re.sub(r"\s+", " ", value).strip().lower()
    generic_values = {
        "this letter",
        "letter",
        "client",
        "customer",
        "policyholder",
        "insured",
        "beneficiary",
        "you",
        "recipient",
        "account holder",
    }
    return normalized in generic_values or normalized.startswith("this ")


def _normalize_analysis_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["document_type"] = _normalize_document_type(payload.get("document_type"))
    normalized["issuer_name"] = _normalize_text(payload.get("issuer_name") or payload.get("sender"))
    normalized["beneficiary_name"] = _normalize_text(payload.get("beneficiary_name") or payload.get("recipient_name"))
    normalized["beneficiary_iban"] = _normalize_text(payload.get("beneficiary_iban") or payload.get("iban"))
    normalized["amount"] = _normalize_amount(payload.get("amount"))
    currency = str(payload.get("currency") or "EUR").strip().upper()
    normalized["currency"] = currency if len(currency) == 3 else "EUR"
    normalized["due_date"] = _normalize_due_date(payload.get("due_date"))
    normalized["payment_reference"] = _normalize_text(payload.get("payment_reference"))
    normalized["payment_description"] = _normalize_text(payload.get("payment_description"))
    normalized["manual_payment_required"] = _normalize_bool(payload.get("manual_payment_required"))
    normalized["auto_debit_detected"] = _normalize_bool(
        payload.get("auto_debit_detected", payload.get("direct_debit_detected"))
    )
    normalized["is_suspicious"] = _normalize_bool(payload.get("is_suspicious"))
    raw_signals = payload.get("phishing_signals") or []
    if isinstance(raw_signals, list):
        normalized["phishing_signals"] = [str(signal).strip() for signal in raw_signals if str(signal).strip()]
    elif raw_signals:
        normalized["phishing_signals"] = [str(raw_signals).strip()]
    else:
        normalized["phishing_signals"] = []
    normalized["recommended_action"] = _normalize_recommended_action(payload.get("recommended_action"))
    normalized["summary"] = _normalize_text(payload.get("summary")) or "Document analyzed."
    normalized["action_required"] = False
    return normalized


def _infer_phishing_signals(
    optional_text: Optional[str],
    issuer_name: Optional[str],
    beneficiary_name: Optional[str],
    beneficiary_iban: Optional[str],
    amount: Optional[float],
    payment_reference: Optional[str],
) -> list[str]:
    signals: list[str] = []
    haystack = (optional_text or "").lower()

    pressure_markers = [
        "urgent",
        "immediately",
        "immediate action",
        "final warning",
        "today only",
        "expires today",
        "before midnight",
        "within 24 hours",
        "within 12 hours",
        "within 2 hours",
        "same day payment",
        "account will be suspended",
        "avoid legal action",
        "pay now to avoid closure",
        "your account will be blocked",
        "service interruption",
    ]
    if any(marker in haystack for marker in pressure_markers):
        signals.append("Pressure language pushes immediate payment.")

    spoof_markers = [
        "confirm your account",
        "verify your payment details",
        "security upgrade",
        "wallet",
        "crypto",
        "gift card",
        "click the secure link",
        "login to release payment",
        "refund available",
        "processing fee",
        "release payment",
        "updated bank details",
        "new iban",
        "temporary account",
        "scan the qr",
        "bit.ly",
        "tinyurl",
        "shorturl",
    ]
    if any(marker in haystack for marker in spoof_markers):
        signals.append("Message uses classic phishing or spoofing wording.")

    email_matches = re.findall(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", optional_text or "")
    suspicious_domains = [domain for domain in email_matches if any(bad in domain.lower() for bad in ["gmail.com", "outlook.com", "proton.me", "yahoo.com"])]
    if suspicious_domains and issuer_name:
        signals.append("Sender domain looks generic for a business payment request.")

    if email_matches and issuer_name:
        issuer_tokens = [
            token
            for token in re.findall(r"[a-z0-9]+", issuer_name.lower())
            if len(token) > 3 and token not in {"group", "ltd", "limited", "international", "nederland", "holding"}
        ]
        if issuer_tokens and not any(
            any(token in domain.lower() for token in issuer_tokens)
            for domain in email_matches
        ):
            signals.append("Sender domain does not clearly match the claimed issuer.")

    if issuer_name and beneficiary_name:
        issuer_norm = re.sub(r"[^a-z0-9]+", "", issuer_name.lower())
        beneficiary_norm = re.sub(r"[^a-z0-9]+", "", beneficiary_name.lower())
        if issuer_norm and beneficiary_norm and issuer_norm not in beneficiary_norm and beneficiary_norm not in issuer_norm:
            signals.append("Beneficiary does not clearly match the issuer.")

    if amount is not None and amount > 0 and beneficiary_iban and not payment_reference:
        signals.append("Manual payment is requested without a clear payment reference.")

    unique_signals: list[str] = []
    for signal in signals:
        if signal not in unique_signals:
            unique_signals.append(signal)
    return unique_signals


def _derive_action(analysis: AnalysisResponse, optional_text: Optional[str]) -> AnalysisResponse:
    issuer_name = analysis.issuer_name or _extract_company_like_name(optional_text)
    beneficiary_name = analysis.beneficiary_name
    document_type = _classify_document_type(
        analysis.document_type,
        optional_text,
        issuer_name,
        analysis.summary,
    )
    auto_debit_detected = analysis.auto_debit_detected or (
        optional_text is not None
        and any(
            marker in optional_text.lower()
            for marker in [
                "automatische incasso",
                "direct debit",
                "we will debit",
                "will be debited",
                "afgeschreven",
            ]
        )
    )

    if _is_generic_beneficiary(beneficiary_name):
        beneficiary_name = issuer_name or beneficiary_name

    due_date = analysis.due_date
    combined_text = "\n".join(part for part in [optional_text, analysis.summary] if part)
    relative_due_match = re.search(r"\bwithin\s+(\d{1,3})\s+days?\b", combined_text, re.IGNORECASE)
    if not relative_due_match:
        relative_due_match = re.search(r"\bbinnen\s+(\d{1,3})\s+dagen?\b", combined_text, re.IGNORECASE)

    if relative_due_match:
        explicit_due_patterns = [
            r"(?:due date|due on|payment due|vervaldag)\D*(\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})",
        ]
        explicit_due_date: Optional[date] = None
        for pattern in explicit_due_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                explicit_due_date = _parse_date_value(match.group(1))
                if explicit_due_date:
                    break

        if explicit_due_date:
            due_date = explicit_due_date.isoformat()
        else:
            invoice_date_patterns = [
                r"(?:invoice date|issue date|factuurdatum)\D*(\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})",
            ]
            base_date: Optional[date] = None
            for pattern in invoice_date_patterns:
                match = re.search(pattern, combined_text, re.IGNORECASE)
                if match:
                    base_date = _parse_date_value(match.group(1))
                    if base_date:
                        break

            if not base_date and due_date:
                base_date = _parse_date_value(due_date)

            if base_date:
                due_date = (base_date + timedelta(days=int(relative_due_match.group(1)))).isoformat()

    beneficiary_iban = analysis.beneficiary_iban
    if auto_debit_detected and _is_user_account_iban(beneficiary_iban, optional_text):
        beneficiary_iban = None

    phishing_signals = list(analysis.phishing_signals)
    inferred_signals = _infer_phishing_signals(
        optional_text,
        issuer_name,
        beneficiary_name,
        beneficiary_iban,
        analysis.amount,
        analysis.payment_reference,
    )
    for signal in inferred_signals:
        if signal not in phishing_signals:
            phishing_signals.append(signal)
    is_suspicious = analysis.is_suspicious or bool(phishing_signals)

    manual_payment_required = analysis.manual_payment_required
    if beneficiary_iban and not auto_debit_detected:
        manual_payment_required = True

    recommended_action = RecommendedAction.review_manually
    action_required = False

    if is_suspicious:
        recommended_action = RecommendedAction.review_manually
    elif auto_debit_detected:
        recommended_action = RecommendedAction.ignore
    elif analysis.amount is not None and beneficiary_iban and manual_payment_required:
        action_required = True
        recommended_action = RecommendedAction.pay_now
        if document_type == DocumentType.invoice and due_date:
            try:
                due = date.fromisoformat(due_date)
                if due > date.today():
                    recommended_action = RecommendedAction.schedule_payment
            except ValueError:
                recommended_action = RecommendedAction.schedule_payment
        elif document_type in {DocumentType.utility_bill, DocumentType.tax_letter, DocumentType.fine}:
            recommended_action = RecommendedAction.pay_now

    summary = analysis.summary
    if is_suspicious:
        summary = "Potential phishing detected. Review the payment request carefully before sending money."
    elif auto_debit_detected:
        summary = "Automatic debit detected. No manual bunq payment is needed."
    elif action_required:
        if recommended_action == RecommendedAction.schedule_payment:
            summary = "Invoice detected. A bunq scheduled payment can be created before the due date."
        else:
            summary = "Bill detected. A bunq payment can be created right away."
    elif not beneficiary_iban or analysis.amount is None:
        summary = "The document does not yet contain enough payment data for a bunq action."

    payment_description = analysis.payment_description or analysis.payment_reference or summary

    return analysis.model_copy(
        update={
            "issuer_name": issuer_name,
            "document_type": document_type,
            "beneficiary_name": beneficiary_name,
            "beneficiary_iban": beneficiary_iban,
            "due_date": due_date,
            "manual_payment_required": manual_payment_required,
            "auto_debit_detected": auto_debit_detected,
            "is_suspicious": is_suspicious,
            "phishing_signals": phishing_signals,
            "recommended_action": recommended_action,
            "summary": summary,
            "payment_description": payment_description,
            "action_required": action_required,
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
                "document_type, issuer_name, beneficiary_name, beneficiary_iban, amount, currency, due_date, "
                "payment_reference, payment_description, manual_payment_required, auto_debit_detected, "
                "is_suspicious, phishing_signals, recommended_action, summary."
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
        file_bytes, content_type = _prepare_image_for_bedrock(file_bytes, content_type)
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 900,
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
        return _derive_action(analysis, optional_text)
    except (BotoCoreError, ClientError, ValueError, json.JSONDecodeError) as exc:
        return _error_analysis(exc)
