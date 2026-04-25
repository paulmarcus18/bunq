from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DocumentType(str, Enum):
    fine = "fine"
    invoice = "invoice"
    utility_bill = "utility_bill"
    tax_letter = "tax_letter"


class RecommendedAction(str, Enum):
    pay_now = "pay_now"
    schedule_payment = "schedule_payment"
    review_manually = "review_manually"
    ignore = "ignore"


class AnalysisResponse(BaseModel):
    document_type: DocumentType = DocumentType.invoice
    issuer_name: Optional[str] = None
    beneficiary_name: Optional[str] = None
    beneficiary_iban: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "EUR"
    due_date: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_description: Optional[str] = None
    manual_payment_required: bool = False
    auto_debit_detected: bool = False
    recommended_action: RecommendedAction = RecommendedAction.review_manually
    summary: str = "Document analyzed."
    action_required: bool = False


class ConfirmActionRequest(BaseModel):
    analysis: AnalysisResponse


class PreparedAction(BaseModel):
    type: RecommendedAction
    bunq_action_type: str
    execution_state: str
    bunq_action_id: Optional[str] = None
    amount: Optional[float]
    currency: str
    beneficiary_name: Optional[str]
    beneficiary_iban: Optional[str]
    due_date: Optional[str]
    reference: Optional[str]
    description: Optional[str] = None


class ConfirmActionResponse(BaseModel):
    success: bool
    message: str
    bunq_user_id: str
    account_used: str
    account_iban: Optional[str] = None
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
