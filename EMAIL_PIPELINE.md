# Email-to-Estimate Automation Pipeline

Automatically receive project requirements via email, generate estimates, and reply with a branded PDF proposal.

## Architecture

```
Sender emails requirements
        │
        ▼
SendGrid Inbound Parse
        │  webhook POST (multipart/form-data)
        ▼
POST /api/webhooks/inbound-email/{WEBHOOK_SECRET}
        │  returns 200 immediately
        ▼  (background task)
┌───────────────────────────────────────────┐
│  1. Parse email (sender, body, attachments)│
│  2. Extract attachment text (PDF/DOCX)     │
│  3. Claude structures raw text → schema    │
│  4. Run estimation pipeline (internal)     │
│  5. Render HTML → PDF proposal             │
│  6. Reply to sender with PDF attached      │
│  7. Notify sales (email + Slack)           │
│  8. Log everything to PostgreSQL           │
└───────────────────────────────────────────┘
```

## Setup

### 1. Environment Variables

Add these to your `.env` file:

```env
# SendGrid (required)
SENDGRID_API_KEY=SG.xxxx
SENDGRID_WEBHOOK_SECRET=a-long-random-string

# Anthropic (required — used for structuring email text)
ANTHROPIC_API_KEY=sk-ant-xxxx

# Email addresses
ESTIMATES_FROM_EMAIL=estimates@yourdomain.com
SALES_TEAM_EMAIL=sales@yourdomain.com

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxxx
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added: `sendgrid`, `anthropic`.

### 3. SendGrid Inbound Parse Configuration

1. Go to **SendGrid Dashboard → Settings → Inbound Parse**
2. Add a new host/URL:
   - **Receiving domain**: `yourdomain.com` (must have MX records pointing to SendGrid)
   - **Destination URL**: `https://your-api.com/api/webhooks/inbound-email/YOUR_WEBHOOK_SECRET`
   - Enable **POST the raw, full MIME message** (not required, but attachments need the default multipart mode)
3. Set up an MX record for your domain pointing to `mx.sendgrid.net`

### 4. SendGrid Mail Send (for replies)

1. Verify the sender identity for `ESTIMATES_FROM_EMAIL` in SendGrid
2. Ensure the API key has **Mail Send** permissions

### 5. Database

The `email_estimate_requests` table is created automatically on server startup. No manual migration needed.

## How It Works

### Webhook Flow

1. **Receive**: SendGrid posts the email as multipart/form-data to the webhook URL
2. **Authenticate**: The `{webhook_secret}` path parameter is validated against `SENDGRID_WEBHOOK_SECRET`
3. **Deduplicate**: The `Message-ID` header is checked against the database to skip retries
4. **Background**: Processing is handed off to `BackgroundTasks` and the webhook returns `{"status": "accepted"}` immediately
5. **Process**: The full pipeline runs asynchronously

### Processing Pipeline

| Step | Service | Description |
|------|---------|-------------|
| Parse | `main.py` webhook handler | Extract sender, subject, body, attachments from form data |
| Extract text | `document_parser.py` (reused) | Parse PDF/DOCX attachments into plain text |
| Structure | `requirement_extractor.py` | Claude converts freeform text into `ProjectRequest` schema |
| Estimate | `project_pipeline.py` (reused) | Run the full estimation pipeline internally |
| PDF | `proposal_renderer.py` + `proposal_pdf_service.py` (reused) | Generate branded PDF identical to webapp output |
| Reply | `email_service.py` | Send proposal PDF to sender with threading headers |
| Notify | `email_service.py` + `slack_service.py` | Alert sales team via email and Slack |
| Log | `email_pipeline.py` → `database.py` | Track status in `email_estimate_requests` table |

### Error Handling

| Scenario | Behavior |
|----------|----------|
| Empty email (no body, no attachments) | Reply asking for requirements |
| Unsupported attachment type | Reply listing accepted formats |
| Claude can't parse requirements | Reply + notify sales for manual review |
| Pipeline estimation fails | Retry 3x with exponential backoff, then error reply |
| PDF generation fails | Notify sales with raw data, reply that team will follow up |
| Email sending fails | Retry 3x, log error |
| Duplicate email (SendGrid retry) | Skip silently (dedup by Message-ID) |

### Retry Logic

Failed operations are retried up to 3 times with exponential backoff (2s, 4s, 8s):
- Requirement extraction (Claude API)
- Estimation pipeline
- Email sending (proposal reply)

### Database Table: `email_estimate_requests`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `message_id` | TEXT | Email Message-ID (unique, for dedup) |
| `sender_email` | TEXT | Sender address |
| `subject` | TEXT | Email subject |
| `raw_body` | TEXT | Plain-text body |
| `attachments_count` | INT | Number of attachments |
| `parsed_requirements` | JSONB | Structured requirements from Claude |
| `estimate_result` | JSONB | Full pipeline result |
| `pdf_generated` | BOOL | Whether PDF was created |
| `reply_sent` | BOOL | Whether reply was sent |
| `sales_notified` | BOOL | Whether sales was notified |
| `status` | TEXT | pending / processing / completed / failed |
| `error_message` | TEXT | Error details (if failed) |
| `created_at` | TIMESTAMPTZ | Row creation time |
| `updated_at` | TIMESTAMPTZ | Last update time |

## Files Added / Modified

### New Files
- `app/models/email_models.py` — Pydantic models for webhook data and parsed requirements
- `app/services/email_service.py` — SendGrid email sending (reply, sales notification, error)
- `app/services/slack_service.py` — Slack webhook notifications
- `app/services/requirement_extractor.py` — Claude-powered requirement structuring
- `app/services/email_pipeline.py` — End-to-end pipeline orchestrator
- `EMAIL_PIPELINE.md` — This documentation

### Modified Files
- `app/main.py` — Added `/api/webhooks/inbound-email/{webhook_secret}` route
- `app/config/settings.py` — Added email pipeline config vars
- `app/services/database.py` — Added `email_estimate_requests` table creation
- `requirements.txt` — Added `sendgrid`, `anthropic`

### Untouched
- Estimation pipeline, agents, models, templates, PDF generation — all reused as-is
- Frontend — no changes needed
