# Demo Assets

Curated fictional documents for the deBunq Inbox demo.

Files:

- `fine_notice_demo.pdf`: should classify as a fine and suggest a safe bunq action.
- `mobile_invoice_demo.pdf`: should detect a legitimate invoice with direct debit already in place.
- `scam_refund_email_demo.pdf`: should classify as suspicious and avoid any bunq payment action.
- `phishing_invoice_demo.html`: synthetic spoofed invoice reminder you can open and screenshot for the phishing flow.
- `phishing_invoice_demo.txt`: pasted-text version of the phishing invoice demo.
- `refund_request_text_demo.txt`: optional pasted-text version of the scam flow.

Suggested demo order:

1. `mobile_invoice_demo.pdf`
2. `fine_notice_demo.pdf`
3. `phishing_invoice_demo.html` (open it in a browser and take a screenshot on your phone)
4. `scam_refund_email_demo.pdf`

Expected outcomes:

- Invoice: explain it, detect direct debit, do not prepare payment.
- Fine: extract payee / IBAN / amount / due date, then create bunq action only after user confirmation.
- Phishing invoice: show warning signs and block Pay now / Schedule.
- Scam: mark suspicious and block payment action.
