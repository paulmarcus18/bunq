from __future__ import annotations

import base64
import json
import os
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Optional
import unicodedata
import uuid

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
        self.language = os.getenv("BUNQ_LANGUAGE", "en_US")
        self.region = os.getenv("BUNQ_REGION", "nl_NL")
        self.geolocation = os.getenv("BUNQ_GEOLOCATION", "0 0 0 0 000")

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
            "X-Bunq-Client-Request-Id": str(uuid.uuid4()),
            "X-Bunq-Geolocation": self.geolocation,
            "X-Bunq-Language": self.language,
            "X-Bunq-Region": self.region,
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
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "X-Bunq-Client-Request-Id": str(uuid.uuid4()),
            "X-Bunq-Geolocation": self.geolocation,
            "X-Bunq-Language": self.language,
            "X-Bunq-Region": self.region,
            "X-Bunq-Client-Authentication": token,
        }

    def _post_session(
        self,
        path: str,
        body: dict[str, Any],
        token: str,
        sign_body: bool = False,
    ) -> dict[str, Any]:
        body_text = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        headers = self._session_headers(token)
        if sign_body:
            private_key_pem, _ = self._ensure_keypair()
            headers["X-Bunq-Client-Signature"] = self._sign_body(private_key_pem, body_text)

        response = requests.post(
            f"{self.base_url}{path}",
            headers=headers,
            data=body_text,
            timeout=20,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"bunq POST {path} failed with {response.status_code}: {response.text}"
            ) from exc
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

    def _accounts_payload_for_session(self, session: dict[str, str]) -> dict[str, Any]:
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
        return self._accounts_payload_for_session(session)

    def _choose_account(
        self,
        accounts_payload: dict[str, Any],
        preferred_account_id: Optional[str] = None,
    ) -> tuple[str, dict[str, Any]]:
        accounts = accounts_payload.get("accounts", [])
        if not accounts:
            raise RuntimeError("No bunq monetary account available")
        if preferred_account_id:
            for account in accounts:
                if str(account.get("id")) == str(preferred_account_id):
                    return str(accounts_payload.get("user_id", "unknown")), account
            raise RuntimeError("Selected bunq account is no longer available")
        return str(accounts_payload.get("user_id", "unknown")), accounts[0]

    def _build_description(self, analysis: AnalysisResponse) -> str:
        base = (
            analysis.payment_description
            or analysis.payment_reference
            or analysis.summary
            or analysis.document_type.value.replace("_", " ")
        ).strip()
        reference = analysis.payment_reference.strip() if analysis.payment_reference else None
        if reference:
            base = f"{base[:90]} Ref {reference}"
        return self._sanitize_description(base)

    def _sanitize_description(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"[^A-Za-z0-9 ]+", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return (normalized or "FinPilot payment")[:140]

    def _payment_body(self, analysis: AnalysisResponse) -> dict[str, Any]:
        return {
            "amount": {
                "value": f"{analysis.amount:.2f}",
                "currency": analysis.currency,
            },
            "counterparty_alias": {
                "type": "IBAN",
                "value": analysis.beneficiary_iban,
                "name": analysis.beneficiary_name or analysis.issuer_name or "Detected beneficiary",
            },
            "description": self._build_description(analysis),
            "merchant_reference": analysis.payment_reference or "",
        }

    def _schedule_payload(self, due_date: Optional[str]) -> Optional[dict[str, Any]]:
        if not due_date:
            return None
        due = date.fromisoformat(due_date)
        schedule_day = due - timedelta(days=1)
        if schedule_day < date.today():
            schedule_day = date.today()
        start_at = datetime.combine(schedule_day, time(hour=9, minute=0, second=0))
        return {
            "time_start": start_at.strftime("%Y-%m-%d %H:%M:%S.000"),
            "recurrence_unit": "ONCE",
            "recurrence_size": 1,
        }

    def create_payment(
        self,
        analysis: AnalysisResponse,
        source_account_id: Optional[str] = None,
    ) -> dict[str, Any]:
        if not analysis.amount or not analysis.beneficiary_iban:
            raise RuntimeError("Payment requires amount and destination IBAN")

        if not self._is_configured():
            return {
                "mode": "mock",
                "status": "created",
                "bunq_action_type": "payment",
                "bunq_action_id": "mock-payment",
            }

        session = self._create_session()
        accounts_payload = self._accounts_payload_for_session(session)
        _, account = self._choose_account(accounts_payload, source_account_id)
        payload = self._post_session(
            f"/user/{session['user_id']}/monetary-account/{account['id']}/payment",
            self._payment_body(analysis),
            session["token"],
            sign_body=True,
        )
        payment = payload.get("Response", [{}])[0].get("Id", {})
        return {
            "mode": "live",
            "status": "created",
            "bunq_action_type": "payment",
            "bunq_action_id": str(payment.get("id", "")) or None,
            "account": account,
            "user_id": session["user_id"],
        }

    def create_schedule_payment(
        self,
        analysis: AnalysisResponse,
        source_account_id: Optional[str] = None,
    ) -> dict[str, Any]:
        if not analysis.amount or not analysis.beneficiary_iban or not analysis.due_date:
            raise RuntimeError("Scheduled payment requires amount, destination IBAN, and due date")

        if not self._is_configured():
            return {
                "mode": "mock",
                "status": "scheduled",
                "bunq_action_type": "schedule_payment",
                "bunq_action_id": "mock-schedule-payment",
            }

        session = self._create_session()
        accounts_payload = self._accounts_payload_for_session(session)
        _, account = self._choose_account(accounts_payload, source_account_id)
        body = {
            "payment": self._payment_body(analysis),
            "schedule": self._schedule_payload(analysis.due_date),
            "purpose": "PAYMENT",
        }
        payload = self._post_session(
            f"/user/{session['user_id']}/monetary-account/{account['id']}/schedule-payment",
            body,
            session["token"],
            sign_body=True,
        )
        schedule_payment = payload.get("Response", [{}])[0].get("Id", {})
        return {
            "mode": "live",
            "status": "scheduled",
            "bunq_action_type": "schedule_payment",
            "bunq_action_id": str(schedule_payment.get("id", "")) or None,
            "account": account,
            "user_id": session["user_id"],
        }

    def request_sandbox_money(
        self,
        amount: float = 100.0,
        source_account_id: Optional[str] = None,
    ) -> dict[str, Any]:
        if amount <= 0:
            raise RuntimeError("Sandbox top-up amount must be greater than zero")
        if amount > 500:
            raise RuntimeError("Sugar Daddy only accepts requests up to 500 EUR at a time")

        if not self._is_configured():
            return {
                "mode": "mock",
                "status": "requested",
                "request_id": "mock-sugardaddy-request",
                "amount": amount,
                "currency": "EUR",
            }

        session = self._create_session()
        accounts_payload = self._accounts_payload_for_session(session)
        _, account = self._choose_account(accounts_payload, source_account_id)
        body = {
            "amount_inquired": {
                "value": f"{amount:.2f}",
                "currency": "EUR",
            },
            "counterparty_alias": {
                "type": "EMAIL",
                "value": "sugardaddy@bunq.com",
                "name": "Sugar Daddy",
            },
            "description": "FinPilot sandbox topup",
            "allow_bunqme": False,
        }
        payload = self._post_session(
            f"/user/{session['user_id']}/monetary-account/{account['id']}/request-inquiry",
            body,
            session["token"],
            sign_body=True,
        )
        request_info = payload.get("Response", [{}])[0].get("Id", {})
        return {
            "mode": "live",
            "status": "requested",
            "request_id": str(request_info.get("id", "")) or None,
            "amount": amount,
            "currency": "EUR",
            "account": account,
            "user_id": session["user_id"],
        }

    def create_bank_account(
        self,
        description: str,
        country_iban: Optional[str] = None,
    ) -> dict[str, Any]:
        cleaned_description = description.strip()
        if not cleaned_description:
            raise RuntimeError("Bank account description is required")

        if not self._is_configured():
            return {
                "mode": "mock",
                "status": "created",
                "account": BunqAccountSummary(
                    id=f"mock-{uuid.uuid4()}",
                    description=cleaned_description,
                    balance="0",
                    currency="EUR",
                    iban=None,
                ).model_dump(),
            }

        session = self._create_session()
        body: dict[str, Any] = {
            "currency": "EUR",
            "description": cleaned_description,
        }
        if country_iban:
            body["country_iban"] = country_iban

        payload = self._post_session(
            f"/user/{session['user_id']}/monetary-account-bank",
            body,
            session["token"],
            sign_body=True,
        )
        account_id = str(payload.get("Response", [{}])[0].get("Id", {}).get("id", "")).strip()
        if not account_id:
            raise RuntimeError("bunq did not return the created account id")

        accounts_payload = self._accounts_payload_for_session(session)
        _, account = self._choose_account(accounts_payload, account_id)
        return {
            "mode": "live",
            "status": "created",
            "account": account,
            "user_id": session["user_id"],
        }

    def confirm_finpilot_action(
        self,
        analysis: AnalysisResponse,
        source_account_id: Optional[str] = None,
    ) -> dict[str, Any]:
        accounts_payload = self.get_accounts()
        user_id, account = self._choose_account(accounts_payload, source_account_id)

        if analysis.is_suspicious:
            return {
                "user_id": user_id,
                "account": account,
                "status": "blocked",
                "bunq_action_type": "manual_review",
                "bunq_action_id": None,
            }

        if analysis.auto_debit_detected:
            return {
                "user_id": user_id,
                "account": account,
                "status": "not_required",
                "bunq_action_type": "none",
                "bunq_action_id": None,
            }

        if analysis.recommended_action == "schedule_payment" and not analysis.due_date:
            return {
                "user_id": user_id,
                "account": account,
                "status": "prepared",
                "bunq_action_type": "manual_review",
                "bunq_action_id": None,
            }

        if not analysis.action_required:
            return {
                "user_id": user_id,
                "account": account,
                "status": "not_required",
                "bunq_action_type": "none",
                "bunq_action_id": None,
            }

        if (
            analysis.manual_payment_required
            and analysis.recommended_action in {"schedule_payment", "pay_now"}
            and analysis.amount
            and analysis.beneficiary_iban
        ):
            if analysis.recommended_action == "schedule_payment" and analysis.due_date:
                result = self.create_schedule_payment(analysis, source_account_id)
            else:
                result = self.create_payment(analysis, source_account_id)
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
