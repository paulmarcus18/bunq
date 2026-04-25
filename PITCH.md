# deBunq · pitch deck script

For a 3–5 minute live presentation or as the spoken narration over the demo video. Each section has a target time, a visual, and the words to say. Read it once aloud before recording — the whole thing should feel like *one continuous story*, not a feature list.

---

## Slide 1 · The hook (15s)

**Visual:** plain title slide — *"deBunq · the scam shield inside bunq"*

**Say:**
> "Last year, Dutch banks lost over 100 million euros to authorised push-payment fraud — fake invoices, swapped IBANs, and 'Hi mom, I lost my phone' voice notes. None of that money gets refunded, because the user pressed pay. So the only place to stop the scam is **before the user pays**.
>
> Meet deBunq — the scam shield that lives inside the bunq app."

---

## Slide 2 · The user moment (20s)

**Visual:** WhatsApp screenshot of a "Hi mom" voice note with an unknown number, next to a screenshot of a phishing AON email.

**Say:**
> "These are the moments that break people. A voice note from someone claiming to be your son. An invoice that looks exactly like your insurance company. A QR code in an email demanding payment in two hours.
>
> bunq's user base — young, mobile-first, fast-payment culture — is *exactly* the demographic these scams target. And right now, no major banking app runs an AI scam check on the message **before** the payment screen."

---

## Slide 3 · What deBunq does (25s)

**Visual:** the deBunq inbox screen on an iPhone.

**Say:**
> "deBunq is a single button inside bunq. Forward a voice note, snap a photo of a bill, or paste a suspicious email. In about three seconds, Claude Sonnet 4.5 on AWS Bedrock returns a TrustScore from 0 to 100.
>
> Below 40 — bunq refuses to make the payment. Server-side. Not just hidden in the UI.
>
> Above 75 — bunq creates the payment in one tap, with a real sandbox API call you can see happen on screen.
>
> Same engine, three input formats — image, audio, text — opposite outcomes."

---

## Slide 4 · How it scores (30s)

**Visual:** TrustScore ring and the four sub-score bars, side by side.

**Say:**
> "The TrustScore isn't a single number Claude pulled out of the air. It's a weighted composite of four sub-scores Claude returns, each backed by concrete reasons.
>
> **Issuer authenticity** — does the sender match the IBAN holder? Thirty-five percent.
>
> **Urgency pressure** — is there a 'within 2 hours' or a 'don't tell anyone' in there? Thirty percent.
>
> **Payment-detail completeness** — IBAN, amount, reference, beneficiary — all consistent? Twenty percent.
>
> **Source-channel risk** — a printed PDF is safer than a screenshot is safer than a forwarded voice note. Fifteen percent.
>
> The frontend renders each sub-score as a bar and lists the reasons as ✓ green ticks and ✗ red flags. So the user doesn't just see *a number* — they see *why*."

---

## Slide 5 · Live demo, scenario A — voice scam (40s)

**Visual:** screen recording of the iPhone running deBunq.

**Say (while you do it):**
> "I forward a WhatsApp voice note saying *'Hi mom, this is your son, I lost my phone, please send 450 euros urgent and don't tell anyone.'*
>
> deBunq transcribes it locally with faster-whisper — the audio never leaves the phone. Then Claude reasons over the transcript with full context: family-impersonation pattern, urgency, secrecy request, no payment reference.
>
> TrustScore — eleven out of a hundred. Risk — blocked. Five red flags. The bunq pay button is greyed out and the server refuses to call the bunq API at all.
>
> *That money doesn't move.*"

---

## Slide 6 · Live demo, scenario B — legit invoice (45s)

**Visual:** continue the screen recording, now with a real AON invoice photo.

**Say (while you do it):**
> "Now the same engine on a real bill. I take a photo of an actual AON Student Insurance invoice with my iPhone — five megabytes, full resolution.
>
> Claude vision extracts the IBAN, amount, due date, reference, and issuer. The TrustScore comes back at 96.
>
> The blue card you see now is the bunq pre-flight — it shows the exact endpoint deBunq is *about* to call: `POST /v1/user/{id}/monetary-account/{id}/payment`. Sandbox badge, real API.
>
> I tap pay. The green receipt replaces it with a real bunq sandbox payment id — *3837492* — and the From / To rows show the real account I just paid from.
>
> Same Claude. Same scoring formula. Opposite outcome — because the inputs are genuinely different."

---

## Slide 7 · The stack (20s)

**Visual:** the architecture diagram from the README.

**Say:**
> "The whole thing is AWS plus Anthropic plus bunq.
>
> Claude Sonnet 4.5 on Bedrock — single call does vision, extraction, scoring, and reasoning. Audio runs through faster-whisper locally on CPU. Every bunq call is RSA-signed with a keypair we generate on first launch. We mod-97-validate every IBAN before bunq even sees it.
>
> Built solo over six hours."

---

## Slide 8 · Why this should win (25s)

**Visual:** the four judging criteria with the deBunq feature next to each.

**Say:**
> "**Innovation** — voice-note scam detection has never shipped in a banking app. Treating channel risk as a first-class trust dimension is new.
>
> **Impact** — this is a hundred-million-euro-a-year problem with a concrete blocking action, not just a warning banner.
>
> **Technical execution** — Claude vision, local Whisper, real bunq RSA-signed sandbox calls, all live, none mocked.
>
> **bunq integration** — full installation flow, real `POST /payment`, the endpoint shown on screen so judges can see the integration land.
>
> **Presentation** — every successful payment ends with a TrustScore receipt. Every block is explained. Every user moment is one tap."

---

## Slide 9 · Close (10s)

**Visual:** the title slide again with a QR code to your live demo URL (if you set one up).

**Say:**
> "deBunq. The scam shield, built into the bank where the money lives. Thanks."

---

## Quick prep checklist before you record

- [ ] Backend running, fresh terminal so you can show logs if needed.
- [ ] Frontend running, browser zoomed to look mobile-shaped if filming on desktop.
- [ ] **Three demo inputs ready in a notes file**: the voice note `.m4a`, the AON photo, the phishing email text.
- [ ] **Use a fresh payment reference** for the AON invoice (e.g. `497186-04699219-DEMO1`) so bunq doesn't reject as duplicate.
- [ ] Make sure you're logged into a sandbox account with a positive balance (`POST /bunq/sandbox-topup` if not).
- [ ] Practice the run-through twice without the camera. Then record in one take.
