from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Optional

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from models.schemas import AnalysisResponse, BunqAccountSummary, BunqAuthTestResponse


class BunqService:
    def __init__(self) -> None:
        self.base_url = os.getenv("BUNQ_BASE_URL", "https://public-api.sandbox.bunq.com/v1").rstrip("/")
        self.api_key = os.getenv("BUNQ_API_KEY")
        self.private_key_path = os.getenv("BUNQ_PRIVATE_KEY_PATH")
        self.public_key_path = os.getenv("BUNQ_PUBLIC_KEY_PATH")
        self.user_agent = "FinPilot Inbox Hackathon MVP/1.0"

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    def _ensure_keypair(self) -> tuple[str, str]:
        if self.private_key_path and self.public_key_path:
            private_path = Path(self.private_key_path)
            public_path = Path(self.public_key_path)
            if private_path.exists() and public_path.exists():
                return private_path.read_text(), public_path.read_text()

        keys_dir = Path(".bunq")
        keys_dir.mkdir(parents=True, exist_ok=True)
        private_path = keys_dir / "private_key.pem"
        public_path = keys_dir / "public_key.pem"

        if not private_path.exists() or not public_path.exists():
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            private_bytes = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
            public_bytes = key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            private_path.write_bytes(private_bytes)
            public_path.write_bytes(public_bytes)

        return private_path.read_text(), public_path.read_text()

    def _sign_body(self, private_key_pem: str, body_text: str) -> str:
        private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        signature = private_key.sign(
            body_text.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def _post_signed(
        self,
        path: str,
        body: dict[str, Any],
        token: Optional[str],
        private_key_pem: str,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        body_text = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "X-Bunq-Client-Signature": self._sign_body(private_key_pem, body_text),
        }
        if token:
            headers["X-Bunq-Client-Authentication"] = token
        if extra_headers:
            headers.update(extra_headers)

        response = requests.post(f"{self.base_url}{path}", headers=headers, data=body_text, timeout=20)
        response.raise_for_status()
        return response.json()

    def _session_headers(self, token: str) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "X-Bunq-Client-Authentication": token,
        }

    def _post_session(self, path: str, body: dict[str, Any], token: str) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}{path}",
            headers=self._session_headers(token),
            data=json.dumps(body, separators=(",", ":"), ensure_ascii=False),
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def _get_session(self, path: str, token: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.base_url}{path}",
            headers=self._session_headers(token),
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def auth_test(self) -> BunqAuthTestResponse:
        if not self._is_configured():
            return BunqAuthTestResponse(
                success=True,
                mode="mock",
                message="bunq API key not configured. Using mock bunq mode for local MVP development.",
            )

        try:
            session = self._create_session()
            return BunqAuthTestResponse(
                success=True,
                mode="live",
                message=f"bunq session ready for user {session['user_id']}.",
            )
        except Exception as exc:
            return BunqAuthTestResponse(
                success=False,
                mode="error",
                message=f"bunq auth failed: {exc}",
            )

    def _create_session(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("Missing BUNQ_API_KEY")

        private_key_pem, public_key_pem = self._ensure_keypair()
        installation = self._post_signed(
            "/installation",
            {"client_public_key": public_key_pem},
            token=None,
            private_key_pem=private_key_pem,
        )
        installation_token = installation["Response"][1]["Token"]["token"]

        self._post_signed(
            "/device-server",
            {
                "description": "FinPilot Inbox Hackathon MVP",
                "secret": self.api_key,
                "permitted_ips": ["*"],
            },
            token=installation_token,
            private_key_pem=private_key_pem,
        )
        session = self._post_signed(
            "/session-server",
            {"secret": self.api_key},
            token=installation_token,
            private_key_pem=private_key_pem,
        )
        token = session["Response"][1]["Token"]["token"]
        user_id = str(session["Response"][2]["UserPerson"]["id"])
        return {"token": token, "user_id": user_id}

    def get_accounts(self) -> dict[str, Any]:
        if not self._is_configured():
            return {
                "mode": "mock",
                "user_id": "demo-user",
                "accounts": [
                    BunqAccountSummary(
                        id="123",
                        description="bunq Free",
                        balance="1420.50",
                        currency="EUR",
                        iban="NL00BUNQ0123456789",
                    ).model_dump()
                ],
        }

        session = self._create_session()
        payload = self._get_session(
            f"/user/{session['user_id']}/monetary-account-bank",
            session["token"],
        )
        accounts: list[dict[str, Any]] = []
        for item in payload.get("Response", []):
            account = item.get("MonetaryAccountBank")
            if not account:
                continue
            accounts.append(
                BunqAccountSummary(
                    id=str(account["id"]),
                    description=account.get("description", "bunq account"),
                    balance=account.get("balance", {}).get("value", "0"),
                    currency=account.get("balance", {}).get("currency", "EUR"),
                    iban=account.get("alias", [{}])[0].get("value"),
                ).model_dump()
            )

        return {"mode": "live", "user_id": session["user_id"], "accounts": accounts}

    def _choose_account(self, accounts_payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        accounts = accounts_payload.get("accounts", [])
        if not accounts:
            raise RuntimeError("No bunq monetary account available")
        return str(accounts_payload.get("user_id", "unknown")), accounts[0]

    def _build_description(self, analysis: AnalysisResponse) -> str:
        base = (analysis.summary or analysis.document_type.value.replace("_", " ")).strip()
        reference = analysis.payment_reference.strip() if analysis.payment_reference else None
        if reference:
            return f"{base[:90]} | Ref {reference}"[:140]
        return base[:140]

    def _schedule_payload(self, due_date: Optional[str]) -> Optional[dict[str, Any]]:
        if not due_date:
            return None
        return {
            "time_start": f"{due_date} 09:00:00.000",
            "recurrence_unit": "ONCE",
            "recurrence_size": 1,
        }

    def create_draft_payment(self, analysis: AnalysisResponse) -> dict[str, Any]:
        if not analysis.amount or not analysis.iban:
            raise RuntimeError("Draft payment requires amount and destination IBAN")

        if not self._is_configured():
            return {
                "mode": "mock",
                "status": "prepared",
                "bunq_action_type": "draft_payment",
                "bunq_action_id": "mock-draft-payment",
            }

        session = self._create_session()
        accounts_payload = self.get_accounts()
        _, account = self._choose_account(accounts_payload)
        body: dict[str, Any] = {
            "status": "PENDING",
            "entries": [
                {
                    "amount": {
                        "value": f"{analysis.amount:.2f}",
                        "currency": analysis.currency,
                    },
                    "counterparty_alias": {
                        "type": "IBAN",
                        "value": analysis.iban,
                        "name": analysis.recipient_name or analysis.sender or "Detected payee",
                    },
                    "description": self._build_description(analysis),
                    "merchant_reference": analysis.payment_reference or "",
                }
            ],
            "number_of_required_accepts": 1,
        }
        schedule = self._schedule_payload(analysis.due_date)
        if schedule:
            body["schedule"] = schedule

        payload = self._post_session(
            f"/user/{session['user_id']}/monetary-account/{account['id']}/draft-payment",
            body,
            session["token"],
        )
        draft_payment = payload.get("Response", [{}])[0].get("Id", {})
        return {
            "mode": "live",
            "status": "prepared",
            "bunq_action_type": "draft_payment",
            "bunq_action_id": str(draft_payment.get("id", "")) or None,
            "account": account,
            "user_id": session["user_id"],
        }

    def create_request_inquiry(self, analysis: AnalysisResponse) -> dict[str, Any]:
        if not analysis.amount or not analysis.iban:
            raise RuntimeError("Request inquiry requires amount and counterparty alias")

        if not self._is_configured():
            return {
                "mode": "mock",
                "status": "prepared",
                "bunq_action_type": "request_inquiry",
                "bunq_action_id": "mock-request-inquiry",
            }

        session = self._create_session()
        accounts_payload = self.get_accounts()
        _, account = self._choose_account(accounts_payload)
        body = {
            "amount_inquired": {
                "value": f"{analysis.amount:.2f}",
                "currency": analysis.currency,
            },
            "counterparty_alias": {
                "type": "IBAN",
                "value": analysis.iban,
                "name": analysis.recipient_name or analysis.sender or "Detected counterparty",
            },
            "description": self._build_description(analysis),
            "allow_bunqme": False,
        }
        payload = self._post_session(
            f"/user/{session['user_id']}/monetary-account/{account['id']}/request-inquiry",
            body,
            session["token"],
        )
        request_inquiry = payload.get("Response", [{}])[0].get("Id", {})
        return {
            "mode": "live",
            "status": "prepared",
            "bunq_action_type": "request_inquiry",
            "bunq_action_id": str(request_inquiry.get("id", "")) or None,
            "account": account,
            "user_id": session["user_id"],
        }

    def confirm_finpilot_action(self, analysis: AnalysisResponse) -> dict[str, Any]:
        accounts_payload = self.get_accounts()
        user_id, account = self._choose_account(accounts_payload)

        if not analysis.action_required:
            return {
                "user_id": user_id,
                "account": account,
                "status": "not_required",
                "bunq_action_type": "none",
                "bunq_action_id": None,
            }

        if analysis.recommended_action in {"schedule_payment", "pay_now"} and analysis.amount and analysis.iban:
            result = self.create_draft_payment(analysis)
            result.setdefault("user_id", user_id)
            result.setdefault("account", account)
            return result

        if analysis.recommended_action == "request_money" and analysis.amount and analysis.iban:
            result = self.create_request_inquiry(analysis)
            result.setdefault("user_id", user_id)
            result.setdefault("account", account)
            return result

        return {
            "user_id": user_id,
            "account": account,
            "status": "prepared",
            "bunq_action_type": "manual_review",
            "bunq_action_id": None,
        }
