from __future__ import annotations

import argparse

from dotenv import load_dotenv

from services.bunq_service import BunqService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create multiple bunq sandbox bank accounts for the FinPilot demo user.",
    )
    parser.add_argument(
        "names",
        nargs="*",
        help="Account descriptions to create. Defaults to three demo accounts.",
    )
    parser.add_argument(
        "--country-iban",
        dest="country_iban",
        default=None,
        help="Optional ISO country code for the generated IBAN country.",
    )
    return parser


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    account_names = args.names or [
        "Main account",
        "Bills account",
        "Travel account",
    ]

    service = BunqService()

    for name in account_names:
        result = service.create_bank_account(
            description=name,
            country_iban=args.country_iban,
        )
        account = result["account"]
        print(
            f"Created '{account['description']}' "
            f"(id={account['id']}, iban={account.get('iban') or 'n/a'}, "
            f"balance={account['balance']} {account['currency']})"
        )

    print("Done. Refresh FinPilot's bunq account picker to see the new accounts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
