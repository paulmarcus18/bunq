from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    fine = "fine"
    invoice = "invoice"
    utility_bill = "utility_bill"
    tax_letter = "tax_letter"
    subscription_change = "subscription_change"
    refund = "refund"
    scam_risk = "scam_risk"
    unknown = "unknown"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RecommendedAction(str, Enum):
    pay_now = "pay_now"
    schedule_payment = "schedule_payment"
    request_money = "request_money"
    mark_suspicious = "mark_suspicious"
    review_manually = "review_manually"
    ignore = "ignore"


class AnalysisResponse(BaseModel):
    document_type: DocumentType = DocumentType.unknown
    sender: Optional[str] = None
    recipient_name: Optional[str] = None
    iban: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "EUR"
    due_date: Optional[str] = None
    payment_reference: Optional[str] = None
    urgency: Urgency = Urgency.low
    risk_level: RiskLevel = RiskLevel.medium
    recommended_action: RecommendedAction = RecommendedAction.review_manually
    summary: str = "Document analyzed."
    reasoning: str = "Not enough data to recommend a fully automated action."
    confidence: float = Field(default=0.2, ge=0.0, le=1.0)


class ConfirmActionRequest(BaseModel):
    analysis: AnalysisResponse


class PreparedAction(BaseModel):
    type: RecommendedAction
    amount: Optional[float]
    currency: str
    recipient: Optional[str]
    iban: Optional[str]
    due_date: Optional[str]
    reference: Optional[str]


class ConfirmActionResponse(BaseModel):
    success: bool
    message: str
    bunq_user_id: str
    account_used: str
    prepared_action: PreparedAction


class BunqAccountSummary(BaseModel):
    id: str
    description: str
    balance: str
    currency: str
    iban: Optional[str] = None


class BunqAuthTestResponse(BaseModel):
    success: bool
    mode: str
    message: str
