# FinPilot Inbox

Mobile-first hackathon MVP for bunq: upload a financial document, screenshot, or pasted email, let multimodal AI triage it, then prepare a safe bunq action for review.

## Stack

- Frontend: Next.js + TypeScript + Tailwind
- Backend: FastAPI + Python
- AI: AWS Bedrock with Anthropic Claude
- Banking: bunq direct API with safe sandbox preparation flow
- Optional persistence: SQLite analysis history

## Project Structure

```text
frontend/
backend/
```

## Local Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

The API runs on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The app runs on `http://localhost:3000`.

## Environment Variables

Frontend:

```env
FINPILOT_BACKEND_URL=http://127.0.0.1:8000
```

Backend:

```env
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
BUNQ_API_KEY=
BUNQ_BASE_URL=https://public-api.sandbox.bunq.com/v1
BUNQ_PRIVATE_KEY_PATH=
BUNQ_PUBLIC_KEY_PATH=
SQLITE_PATH=backend/db/finpilot.db
```

## API Endpoints

- `GET /health`
- `POST /analyze-document`
- `POST /confirm-action`
- `GET /bunq/auth-test`
- `GET /bunq/accounts`

## Notes

- `POST /confirm-action` creates bunq sandbox actions, not real production money movement.
- If Bedrock or bunq credentials are missing, the app falls back to safe local mock behavior so the demo still works.
- bunq request signing uses exact JSON serialization for signed bodies.

## Phone Testing

To test on your phone on the same Wi-Fi network:

1. Run the backend normally on your laptop:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

2. Run the frontend:

```bash
cd frontend
npm run dev
```

3. Find your laptop LAN IP, then open this on your phone:

```text
http://<your-laptop-ip>:3000
```

The frontend proxies requests to the local FastAPI backend, so your phone only needs to reach the Next.js server. The upload card includes a `Use camera` button that opens the phone camera directly.
