from __future__ import annotations

import io

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader

from models.schemas import AnalysisResponse, ConfirmActionRequest, ConfirmActionResponse, PreparedAction
from services.bedrock_service import analyze_document_with_claude
from services.bunq_service import BunqService


load_dotenv()


bunq_service = BunqService()


app = FastAPI(title="FinPilot Inbox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "FinPilot Inbox API"}


@app.post("/analyze-document", response_model=AnalysisResponse)
async def analyze_document(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
) -> AnalysisResponse:
    if file is None and not (text and text.strip()):
        raise HTTPException(status_code=400, detail="Upload a file or provide text")

    file_bytes: bytes | None = None
    content_type: str | None = None
    extra_text = text.strip() if text else None

    if file is not None:
        file_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"
        if content_type == "application/pdf":
            pdf_text = _extract_pdf_text(file_bytes)
            extra_text = "\n\n".join(filter(None, [extra_text, pdf_text])) or None
            file_bytes = None
            content_type = None

    analysis = analyze_document_with_claude(file_bytes, content_type, extra_text)

    return analysis


@app.post("/confirm-action", response_model=ConfirmActionResponse)
def confirm_action(payload: ConfirmActionRequest) -> ConfirmActionResponse:
    analysis = payload.analysis
    try:
        bunq_result = bunq_service.confirm_finpilot_action(
            analysis,
            payload.source_account_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    account = bunq_result.get("account", {})
    account_used = account.get("description", "No account available")
    user_id = str(bunq_result.get("user_id", "unknown"))

    message = "Prepared payment action for review"
    if bunq_result.get("bunq_action_type") == "payment":
        message = "bunq payment created after user confirmation"
    elif bunq_result.get("bunq_action_type") == "schedule_payment":
        message = "bunq scheduled payment created after user confirmation"
    elif bunq_result.get("status") == "blocked":
        message = "Potential phishing detected. FinPilot blocked the bunq action and kept this request in manual review"
    elif bunq_result.get("bunq_action_type") == "manual_review":
        message = "User confirmation received. FinPilot kept this action in manual review mode"
    elif bunq_result.get("status") == "not_required":
        message = "User confirmation received, but no bunq action was needed for this document"

    return ConfirmActionResponse(
        success=True,
        message=message,
        bunq_user_id=user_id,
        account_used=account_used,
        account_iban=account.get("iban"),
        prepared_action=PreparedAction(
            type=analysis.recommended_action,
            bunq_action_type=str(bunq_result.get("bunq_action_type", "none")),
            execution_state=str(bunq_result.get("status", "prepared")),
            bunq_action_id=bunq_result.get("bunq_action_id"),
            amount=analysis.amount,
            currency=analysis.currency,
            beneficiary_name=analysis.beneficiary_name,
            beneficiary_iban=analysis.beneficiary_iban,
            due_date=analysis.due_date,
            reference=analysis.payment_reference,
            description=analysis.payment_description or analysis.summary,
        ),
    )


@app.get("/bunq/auth-test")
def bunq_auth_test():
    return bunq_service.auth_test()


@app.get("/bunq/accounts")
def bunq_accounts():
    return bunq_service.get_accounts()


@app.post("/bunq/sandbox-topup")
def bunq_sandbox_topup(amount: float = 100.0):
    try:
        return bunq_service.request_sandbox_money(amount)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
