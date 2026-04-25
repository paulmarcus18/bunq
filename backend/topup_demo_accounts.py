from __future__ import annotations

import argparse

from dotenv import load_dotenv

from services.bunq_service import BunqService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Top up bunq sandbox demo accounts with Sugar Daddy money.",
    )
    parser.add_argument(
        "--amount",
        type=float,
        default=100.0,
        help="Top-up amount per account in EUR. Sugar Daddy accepts up to 500 per request.",
    )
    parser.add_argument(
        "--include-funded",
        action="store_true",
        help="Also top up accounts that already have a positive balance.",
    )
    parser.add_argument(
        "--ids",
        nargs="*",
        default=None,
        help="Optional specific account ids to top up.",
    )
    return parser


def parse_balance(balance_value: str) -> float:
    try:
        return float(balance_value)
    except ValueError:
        return 0.0


def main() -> int:
    load_dotenv()
    args = build_parser().parse_args()

    service = BunqService()
    accounts_payload = service.get_accounts()
    accounts = accounts_payload.get("accounts", [])

    if args.ids:
        target_ids = {str(account_id) for account_id in args.ids}
        targets = [account for account in accounts if str(account.get("id")) in target_ids]
    elif args.include_funded:
        targets = accounts
    else:
        targets = [account for account in accounts if parse_balance(account.get("balance", "0")) <= 0]

    if not targets:
        print("No matching accounts need a top-up.")
        return 0

    for account in targets:
        result = service.request_sandbox_money(
            amount=args.amount,
            source_account_id=str(account["id"]),
        )
        print(
            f"Requested EUR {args.amount:.2f} for '{account['description']}' "
            f"(id={account['id']}, iban={account.get('iban') or 'n/a'}, "
            f"request_id={result.get('request_id') or 'n/a'})"
        )

    print("Done. Refresh FinPilot's bunq account picker to see updated balances.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
