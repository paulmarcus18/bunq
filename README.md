# deBunq · the scam shield inside bunq

**Submission to bunq Hackathon 7.0 — Multimodal AI · April 25, 2026**

deBunq is a multimodal AI scam shield that lives inside the bunq app. Before any money moves, every payment request the user receives — a paper bill, a screenshot of an invoice, a phishing email, or a forwarded WhatsApp voice note from someone claiming to need money — is scored by Claude on four trust axes. **Low score → bunq payment is blocked. High score → one-tap pay through the real bunq sandbox API.**

## The problem we're solving

Dutch banks lose **hundreds of millions of euros every year** to authorised push-payment fraud: fake invoices with a swapped IBAN, "Hi mom, I lost my phone, send €450 urgent" voice notes, and phishing emails that mimic KPN, the Belastingdienst, or AON Student Insurance.

bunq users — young, mobile-first, fast-payment culture — are the most exposed demographic. **No major banking app today runs a multimodal scam check on the message *before* the user pays.** That gap is what deBunq fills.

## Why this is multimodal AI, not just AI

Scams arrive in different formats and the format itself carries signal. A 15-second voice note demanding money is *intrinsically* riskier than a printed utility bill, and an AI that doesn't reason about the channel misses half the picture. deBunq treats audio, image, and text as first-class inputs that all flow into the same trust judgement:

| Modality | How it enters the app | What runs on it |
|---|---|---|
| **Image** (bill, screenshot, photo) | Camera or upload | Claude Sonnet 4.5 vision on AWS Bedrock |
| **Audio** (forwarded voice note) | Upload `.m4a` / `.mp3` / `.webm` | `faster-whisper` (local CPU, no audio leaves the device) → Claude |
| **Text** (pasted email or chat) | Textarea | Claude directly |

All three paths produce the same `AnalysisResponse` shape, so the rest of the UI (TrustScore, account picker, bunq pre-flight, bunq receipt) works identically regardless of how the request arrived.

## The TrustScore

Every payment request is scored on four axes (each 0–100, higher = safer). Claude returns the sub-scores; the backend composes the final TrustScore as a weighted average:

| Sub-score | Weight | What it measures |
|---|---|---|
| **Issuer authenticity** | 35% | Known business / matching domain / IBAN consistency with claimed issuer |
| **Urgency pressure** | 30% | "URGENT", "today only", emotional pressure, secrecy asks, family-emergency framing |
| **Payment-detail completeness** | 20% | IBAN + amount + reference + clear beneficiary all present and consistent |
| **Source-channel risk** | 15% | Official PDF safer than screenshot safer than forwarded voice note |

`risk_level` then determines what bunq is allowed to do:

- **`safe`** — score ≥ 75 and Claude is not flagging the request → bunq action button enabled
- **`caution`** — score 40–74 → manual review, no automatic action
- **`blocked`** — score < 40 or `is_suspicious=true` → bunq API call refused server-side, not just hidden in the UI

## Three live scenarios

| Input | TrustScore | Outcome |
|---|---|---|
| Real AON / KPN / TU/e invoice (paste or photo) | **89–98** safe | Pre-flight card → real `POST /payment` on bunq sandbox → green receipt with bunq id |
| WhatsApp voice note: *"Hi mom, lost my phone, send €450 urgent, don't tell anyone"* | **8–15** blocked | Indigo transcript card + rose ring + family-emergency red flags listed |
| Phishing email: spoofed sender + new IBAN + 2-hour ultimatum + bit.ly link | **10–15** blocked | Rose ring, 6+ red flags, bunq button disabled with `"TrustScore X/100 — bunq payment blocked"` |

## Stack

- **Frontend** — Next.js 15 + TypeScript + Tailwind, mobile-first single-page UI with framer-motion animations and a circular TrustScore ring as the hero element.
- **Backend** — FastAPI + Pydantic with composite TrustScore math and IBAN mod-97 validation.
- **AI** — AWS Bedrock invoking **Claude Sonnet 4.5** (`us.anthropic.claude-sonnet-4-5-20250929-v1:0`) via the cross-region inference profile. Single call does vision + extraction + scoring + reasoning.
- **Audio** — `faster-whisper` (`base.en`, int8 quantized) running on the host CPU. ~2-3s for a 10-second voice note. Audio never leaves the machine.
- **Banking** — bunq Public API on the sandbox base URL with full **RSA request signing**, generated keypair, automatic device + session installation. Real `POST /payment` and `POST /schedule-payment` calls produce real bunq sandbox payment ids.

## Architecture

```
                    ┌─────────────────────────────────────────┐
   Image / PDF ───► │                                         │
   Pasted text ───► │   POST /analyze-document  (FastAPI)     │
   Voice note  ───► │                                         │
                    │   ┌───────────────┐  ┌───────────────┐  │
                    │   │ faster-whisper│  │  PDF.text     │  │
                    │   └───────┬───────┘  └───────┬───────┘  │
                    │           ▼                  ▼          │
                    │      ┌───────────────────────────────┐  │
                    │      │  Claude Sonnet 4.5 / Bedrock  │  │
                    │      │  • vision + reasoning         │  │
                    │      │  • returns trust_breakdown    │  │
                    │      └─────────────┬─────────────────┘  │
                    │                    ▼                    │
                    │     composite weighted TrustScore       │
                    └─────────────────┬───────────────────────┘
                                      ▼
                          ┌───────────────────────┐
                          │  TrustScore card +    │
                          │  bunq pre-flight card │
                          └───────────┬───────────┘
                                      │ user taps confirm
                                      ▼
                       ┌─────────────────────────────────┐
                       │  POST /confirm-action            │
                       │  • IBAN mod-97 validation        │
                       │  • bunq POST /payment OR         │
                       │    bunq POST /schedule-payment   │
                       └───────────────┬─────────────────┘
                                       ▼
                          bunq sandbox creates real id
                                       │
                                       ▼
                                bunq receipt card
                                (bunq id, endpoint,
                                 TrustScore, mode)
```

| Criterion | Weight | Where you see it in the build |
|---|---|---|
| **Innovation & Creativity** | 25% | Voice-note scam check is brand new for banking apps. Composite four-axis trust math is more rigorous than a single LLM yes/no. Treats source-channel itself as a signal. |
| **Impact & Usefulness** | 30% | Targets a real €100M+ Dutch fraud problem. Concrete *blocking* action — the bunq API call is refused, not just dimmed in the UI. Works for the actual demographic that gets hit (mobile-first, fast-payment users). |
| **Technical Execution** | 20% | Sonnet 4.5 + faster-whisper + bunq RSA-signed requests + IBAN mod-97 — all live, none mocked. iPhone-photo image compression keeps Bedrock's 5 MB base64 limit honoured. |
| **bunq Integration** | 15% | Full RSA installation + device + session flow. Real `POST /payment` and `POST /schedule-payment` against the sandbox. The actual bunq endpoint path is shown to the user on the pre-flight + receipt cards for transparency. |
| **Presentation & Pitch** | 10% | TrustScore ring as hero, sub-score bars, ✓/✗ reasons, bunq pre-flight + receipt cards built like real bunq transaction confirmations, sandbox badge so judges know it's not real money. |

## Local setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in AWS + bunq sandbox keys
uvicorn main:app --reload
```

The API runs on `http://localhost:8000`. First analyze-with-audio call downloads the `base.en` Whisper model (~150 MB, cached after).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The app runs on `http://localhost:3000`.

### Required environment variables

```env
# AWS Bedrock — Claude Sonnet 4.5 via cross-region inference profile
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...           # optional, for SSO sessions
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0

# Local Whisper transcription (no third-party audio API)
WHISPER_MODEL_SIZE=base.en
WHISPER_COMPUTE_TYPE=int8

# bunq sandbox API
BUNQ_API_KEY=sandbox_...
BUNQ_BASE_URL=https://public-api.sandbox.bunq.com/v1
```

### Mobile testing

Plain HTTP works on the same Wi-Fi as your laptop:

```bash
hostname -I | awk '{print $1}'
```

Then open `http://<that-ip>:3000` from your phone. Camera + audio-file uploads work over plain HTTP.

For HTTPS (required if you re-add an in-browser audio recorder), use a Cloudflare tunnel:

```bash
~/cloudflared tunnel --url http://localhost:3000
```

The wildcard `*.trycloudflare.com` is already in `next.config.ts` `allowedDevOrigins`.

## API surface

- `GET /health`
- `POST /analyze-document` — accepts `file` (image, PDF, audio) or `text` form fields
- `POST /confirm-action` — creates a real bunq sandbox payment / schedule
- `GET /bunq/accounts`
- `GET /bunq/auth-test`
- `POST /bunq/sandbox-topup`

## Safety rails (server-side, not just UI)

- bunq sandbox only — production credentials are never accepted.
- IBAN mod-97 checksum runs before any bunq POST. Malformed IBANs never hit the bank.
- Whisper runs locally — audio bytes never leave the host.
- `is_suspicious=true` from Claude OR `trust_score < 40` → `confirm-action` returns a `blocked` / `manual_review` result and skips the bunq POST entirely.
- bunq RSA keypair is generated on first run and stored under `.bunq/`; signing is exact-bytes JSON to satisfy bunq's verifier.
- Image uploads are compressed before being base64-encoded so iPhone photos (5–8 MB) fit Bedrock's 5 MB encoded limit.

## What is intentionally **not** in this MVP

- No production bunq credentials.
- No persistence beyond sandbox state — every analysis is stateless.
- No ML training — entirely zero-shot Claude + a deterministic composite formula.
- No fancy onboarding screens; the rest of the bunq app is mocked for context.
- No phishing-block keyword lists — the regex heuristics from earlier prototypes were stripped so all scam reasoning lives in the Claude prompt.

## Demo video

A 2–4 minute walkthrough hitting all three scenarios is included with the Devpost submission. The video shows:

1. Real AON invoice photo from an iPhone → 96/100 → real bunq sandbox payment created with a visible bunq id.
2. WhatsApp voice note "Hi mom, lost my phone" upload → indigo transcript → 11/100 → bunq blocked.
3. Phishing email paste → 13/100 → red flags listed → bunq blocked.

## Credits

Built solo for **bunq Hackathon 7.0 — Multimodal AI** (April 25, 2026), powered by **AWS** and **Anthropic**.
