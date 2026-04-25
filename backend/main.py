from __future__ import annotations

import io

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader

from models.schemas import AnalysisResponse, ConfirmActionRequest, ConfirmActionResponse, PreparedAction
from services.bedrock_service import analyze_document_with_claude
from services.bunq_service import BunqService
from services.transcription_service import transcribe_audio


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
    transcript: str | None = None
    input_modality = "document"

    if file is not None:
        file_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"
        if content_type == "application/pdf":
            pdf_text = _extract_pdf_text(file_bytes)
            extra_text = "\n\n".join(filter(None, [extra_text, pdf_text])) or None
            file_bytes = None
            content_type = None
        elif content_type.startswith("audio/") or (file.filename or "").lower().endswith(
            (".m4a", ".mp3", ".wav", ".webm", ".ogg")
        ):
            input_modality = "voice"
            try:
                transcript = transcribe_audio(file_bytes, file.filename)
            except Exception as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not transcribe audio: {exc}",
                ) from exc
            if not transcript:
                raise HTTPException(
                    status_code=400,
                    detail="Audio transcription was empty. Try a longer or clearer recording.",
                )
            voice_context = (
                "VOICE NOTE TRANSCRIPT (treat as a spoken request, not a printed document. "
                "Be alert to impersonation, urgency, gift-card requests, and 'new IBAN' scams):\n"
                f"{transcript}"
            )
            extra_text = "\n\n".join(filter(None, [extra_text, voice_context]))
            file_bytes = None
            content_type = None

    analysis = analyze_document_with_claude(file_bytes, content_type, extra_text)
    if transcript:
        analysis = analysis.model_copy(update={"transcript": transcript, "input_modality": "voice"})
    else:
        analysis = analysis.model_copy(update={"input_modality": input_modality})

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
        message = "Potential scam detected. deBunq blocked the bunq action and kept this request in manual review"
    elif bunq_result.get("status") == "iban_invalid":
        message = "deBunq could not verify the destination IBAN (failed mod-97 checksum). Action kept in manual review"
    elif bunq_result.get("bunq_action_type") == "manual_review":
        message = "User confirmation received. deBunq kept this action in manual review mode"
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
            bunq_endpoint=bunq_result.get("bunq_endpoint"),
            bunq_mode=str(bunq_result.get("mode", "live")),
            trust_score=analysis.trust_score,
            risk_level=analysis.risk_level.value,
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
