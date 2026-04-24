# Demo Assets

Curated fictional documents for the FinPilot Inbox demo.

Files:

- `fine_notice_demo.pdf`: should classify as a fine and suggest a safe bunq action.
- `mobile_invoice_demo.pdf`: should detect a legitimate invoice with direct debit already in place.
- `scam_refund_email_demo.pdf`: should classify as suspicious and avoid any bunq payment action.
- `refund_request_text_demo.txt`: optional pasted-text version of the scam flow.

Suggested demo order:

1. `mobile_invoice_demo.pdf`
2. `fine_notice_demo.pdf`
3. `scam_refund_email_demo.pdf`

Expected outcomes:

- Invoice: explain it, detect direct debit, do not prepare payment.
- Fine: extract payee / IBAN / amount / due date, then create bunq action only after user confirmation.
- Scam: mark suspicious and block payment action.
