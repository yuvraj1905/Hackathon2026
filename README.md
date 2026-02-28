# Neural Architects

AI-powered presales estimation platform with:
- **FastAPI backend** for estimation, proposal generation, and email webhook automation
- **Next.js frontend** for submitting requirements and viewing estimates/proposals

## Features

- AI-assisted project estimation pipeline
- Proposal export as HTML/PDF/Google Doc
- Email-to-estimate automation (SendGrid inbound webhook)
- PostgreSQL-backed persistence

## Tech Stack

- Backend: Python, FastAPI, Pydantic, PostgreSQL
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Integrations: Google Docs API, SendGrid, Anthropic

## Project Structure

```text
.
├── app/                   # FastAPI backend
├── frontend/              # Next.js frontend
├── requirements.txt       # Python dependencies
└── EMAIL_PIPELINE.md      # Email automation details
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- PostgreSQL

## Backend Setup

From project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the project root (example values):

```env
OPENROUTER_API_KEY=your_api_key_here
MODEL_NAME=openai/gpt-4o-mini
TEMPERATURE=0
DATABASE_URL=postgresql://user:password@localhost:5432/database

# Optional / integration-specific
SENDGRID_API_KEY=
SENDGRID_WEBHOOK_SECRET=
ANTHROPIC_API_KEY=
ESTIMATES_FROM_EMAIL=estimates@geekyants.com
SALES_TEAM_EMAIL=sales@geekyants.com
SLACK_WEBHOOK_URL=
```

Start backend:

```bash
uvicorn app.main:app --reload --port 8000
```

API base URL: `http://localhost:8000`

## Frontend Setup

From `frontend/`:

```bash
npm install
npm run dev
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID=your_google_oauth_client_id
```

Frontend URL: `http://localhost:3000`

## Main API Endpoints

- `GET /health`
- `POST /auth/login`
- `POST /estimate`
- `POST /modify`
- `GET /proposal/pdf/{request_id}`
- `GET /proposal/html/{request_id}`
- `GET /proposal/google-doc/{request_id}`
- `POST /api/webhooks/inbound-email/{webhook_secret}`

## Notes

- `app/credentials/service-account.json` is expected locally for Google Docs features and should not be committed.
- For full email webhook setup, see `EMAIL_PIPELINE.md`.
