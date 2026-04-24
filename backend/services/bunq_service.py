from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Optional

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from models.schemas import BunqAccountSummary, BunqAuthTestResponse


class BunqService:
    def __init__(self) -> None:
        self.base_url = os.getenv("BUNQ_BASE_URL", "https://public-api.sandbox.bunq.com/v1").rstrip("/")
        self.api_key = os.getenv("BUNQ_API_KEY")
        self.private_key_path = os.getenv("BUNQ_PRIVATE_KEY_PATH")
        self.public_key_path = os.getenv("BUNQ_PUBLIC_KEY_PATH")

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
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Bunq-Client-Signature": self._sign_body(private_key_pem, body_text),
        }
        if token:
            headers["X-Bunq-Client-Authentication"] = token
        if extra_headers:
            headers.update(extra_headers)

        response = requests.post(f"{self.base_url}{path}", headers=headers, data=body_text, timeout=20)
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
        headers = {"X-Bunq-Client-Authentication": session["token"]}
        response = requests.get(
            f"{self.base_url}/user/{session['user_id']}/monetary-account-bank",
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
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
