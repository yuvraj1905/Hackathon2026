"""
End-to-end email estimation pipeline.

Orchestrates: inbound parsing → requirement extraction → estimation →
PDF generation → reply email → sales notification → database logging.

Designed to run as a background task so the webhook can return 200 immediately.
"""

import asyncio
import json
import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from app.config.settings import settings
from app.models.email_models import InboundEmailData, ParsedRequirements
from app.services.database import db
from app.services.document_parser import (
    _clean_text,
    _extract_docx_text,
    _extract_pdf_text,
)
from app.services.email_service import (
    send_error_reply,
    send_proposal_reply,
    send_sales_notification,
)
from app.services.input_fusion_service import build_final_description
from app.services.proposal_pdf_service import ProposalPDFService
from app.services.proposal_renderer import render_proposal
from app.services.requirement_extractor import extract_requirements
from app.services.slack_service import notify_slack

logger = logging.getLogger(__name__)

_pdf_service = ProposalPDFService()

# ── Retry helpers ────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # seconds


async def _retry_async(coro_factory, label: str, retries: int = MAX_RETRIES):
    """
    Call *coro_factory()* (which returns a coroutine) with exponential backoff.

    Returns the coroutine result on success, or re-raises on final failure.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(retries):
        try:
            return await coro_factory()
        except Exception as exc:
            last_exc = exc
            delay = RETRY_BASE_DELAY ** (attempt + 1)
            logger.warning(
                "%s attempt %d/%d failed (%s), retrying in %ds...",
                label,
                attempt + 1,
                retries,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]


# ── Database helpers ─────────────────────────────────────────────────

async def _insert_request(email: InboundEmailData) -> str:
    """Insert a new row and return the UUID primary key."""
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO email_estimate_requests
                (message_id, sender_email, subject, raw_body, attachments_count, status)
            VALUES ($1, $2, $3, $4, $5, 'processing')
            RETURNING id::text
            """,
            email.message_id or None,
            email.sender_email,
            email.subject,
            email.body_plain,
            len(email.attachments),
        )
        return row["id"]


async def _update_request(row_id: str, **fields: Any) -> None:
    """Update one or more columns on an existing row."""
    set_parts: list[str] = []
    values: list[Any] = []
    idx = 1
    for col, val in fields.items():
        set_parts.append(f"{col} = ${idx}")
        values.append(val)
        idx += 1
    values.append(row_id)
    sql = (
        f"UPDATE email_estimate_requests SET {', '.join(set_parts)}, "
        f"updated_at = now() WHERE id::text = ${idx}"
    )
    async with db.pool.acquire() as conn:
        await conn.execute(sql, *values)


async def _message_id_exists(message_id: str) -> bool:
    """Check for duplicate emails (SendGrid retries)."""
    if not message_id:
        return False
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM email_estimate_requests WHERE message_id = $1",
            message_id,
        )
        return row is not None


# ── Attachment text extraction ───────────────────────────────────────

def _extract_attachment_text(filename: str, content: bytes) -> str:
    """
    Extract text from a single attachment file.

    Re-uses the existing PDF / DOCX parsers from document_parser.
    """
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _clean_text(_extract_pdf_text(content))
    if ext == ".docx":
        return _clean_text(_extract_docx_text(content))
    logger.info("Skipping unsupported attachment type: %s", ext)
    return ""


# ── Reply body builders ─────────────────────────────────────────────

def _build_success_reply_html(
    sender_name: str,
    total_hours: float,
    min_hours: float,
    max_hours: float,
    timeline_weeks: Any,
) -> str:
    name = sender_name or "there"
    return (
        f"<p>Hi {name},</p>"
        f"<p>Thank you for reaching out! We've reviewed the requirements you shared and "
        f"prepared an initial project estimate.</p>"
        f"<p><strong>Estimated effort:</strong> {int(total_hours)} hours "
        f"(range: {int(min_hours)}–{int(max_hours)} hours)<br/>"
        f"<strong>Estimated timeline:</strong> {timeline_weeks} weeks</p>"
        f"<p>Please find the detailed proposal attached as a PDF.</p>"
        f"<p>A member of our sales team will follow up shortly to discuss next steps, "
        f"answer any questions, and schedule a discovery call.</p>"
        f"<p>Best regards,<br/>{settings.COMPANY_NAME}</p>"
    )


def _build_error_reply_html(sender_name: str) -> str:
    name = sender_name or "there"
    return (
        f"<p>Hi {name},</p>"
        f"<p>Thank you for your email. Unfortunately we couldn't automatically process "
        f"your request at this time. Our team has been notified and will review your "
        f"requirements manually.</p>"
        f"<p>Someone from our team will reach out to you shortly.</p>"
        f"<p>Best regards,<br/>{settings.COMPANY_NAME}</p>"
    )


def _build_empty_email_reply_html(sender_name: str) -> str:
    name = sender_name or "there"
    return (
        f"<p>Hi {name},</p>"
        f"<p>Thanks for reaching out! It looks like your email didn't contain enough "
        f"detail for us to generate an estimate.</p>"
        f"<p>Please include your project requirements in the email body or attach a "
        f"PDF or DOCX document describing what you'd like to build, and we'll get "
        f"back to you with a proposal.</p>"
        f"<p>Best regards,<br/>{settings.COMPANY_NAME}</p>"
    )


def _build_unsupported_format_reply_html(sender_name: str, filenames: list[str]) -> str:
    name = sender_name or "there"
    bad_files = ", ".join(filenames)
    return (
        f"<p>Hi {name},</p>"
        f"<p>We received your email but couldn't process the attached file(s): "
        f"<strong>{bad_files}</strong>.</p>"
        f"<p>We currently accept <strong>PDF</strong> and <strong>DOCX</strong> "
        f"attachments. Please re-send with a supported format and we'll generate "
        f"your estimate.</p>"
        f"<p>Best regards,<br/>{settings.COMPANY_NAME}</p>"
    )


# ── Main pipeline ───────────────────────────────────────────────────

async def process_inbound_email(
    email: InboundEmailData,
    pipeline,  # ProjectPipeline instance (injected from main.py)
) -> None:
    """
    Full background pipeline: parse → extract → estimate → PDF → reply → notify.

    This function never raises — all errors are caught, logged, and reported
    via error reply + sales notification.
    """
    row_id: Optional[str] = None

    try:
        # ── Deduplication ────────────────────────────────────────
        if await _message_id_exists(email.message_id):
            logger.info("Duplicate email skipped: message_id=%s", email.message_id)
            return

        # ── DB: insert tracking row ──────────────────────────────
        row_id = await _insert_request(email)
        logger.info(
            "Email pipeline started: row_id=%s from=%s subject=%s",
            row_id,
            email.sender_email,
            email.subject,
        )

        # ── Validate: non-empty content ──────────────────────────
        has_body = bool(email.body_plain.strip())
        has_attachments = bool(email.attachment_bytes)

        if not has_body and not has_attachments:
            logger.warning("Empty email from %s", email.sender_email)
            _try_send(
                send_error_reply,
                email.sender_email,
                email.subject,
                _build_empty_email_reply_html(email.sender_name),
            )
            await _update_request(row_id, status="failed", error_message="Empty email")
            return

        # ── Validate: attachment types ───────────────────────────
        unsupported: list[str] = []
        for att in email.attachments:
            ext = Path(att.filename).suffix.lower()
            if ext not in {".pdf", ".docx"}:
                unsupported.append(att.filename)

        if unsupported and not has_body:
            # Only attachments, and all unsupported
            _try_send(
                send_error_reply,
                email.sender_email,
                email.subject,
                _build_unsupported_format_reply_html(email.sender_name, unsupported),
            )
            await _update_request(
                row_id, status="failed",
                error_message=f"Unsupported attachments: {unsupported}",
            )
            return

        # ── Extract attachment text ──────────────────────────────
        attachment_texts: list[str] = []
        for filename, content in email.attachment_bytes.items():
            try:
                text = await asyncio.to_thread(
                    _extract_attachment_text, filename, content,
                )
                if text:
                    attachment_texts.append(text)
            except Exception:
                logger.exception("Failed to extract text from %s", filename)

        combined_attachment_text = "\n\n".join(attachment_texts) if attachment_texts else None

        # ── Step 2: Requirement extraction (Claude) ──────────────
        parsed: ParsedRequirements = await _retry_async(
            lambda: extract_requirements(
                body_text=email.body_plain,
                attachment_text=combined_attachment_text,
                subject=email.subject,
            ),
            label="requirement_extraction",
        )

        await _update_request(
            row_id,
            parsed_requirements=json.dumps(parsed.model_dump(), default=str),
        )

        if parsed.needs_clarification:
            logger.info("Requirements need clarification for %s", email.sender_email)
            _try_send(
                send_error_reply,
                email.sender_email,
                email.subject,
                (
                    f"<p>Hi {email.sender_name or 'there'},</p>"
                    f"<p>Thank you for your email. We couldn't fully parse your requirements "
                    f"from the information provided.</p>"
                    f"<p><em>{parsed.clarification_note}</em></p>"
                    f"<p>Our team will review your request manually and follow up shortly.</p>"
                    f"<p>Best regards,<br/>{settings.COMPANY_NAME}</p>"
                ),
            )
            # Still notify sales even on partial parse
            _try_send(
                send_sales_notification,
                email.sender_email,
                email.subject,
                parsed.additional_details or "(insufficient detail)",
                f"Needs clarification: {parsed.clarification_note}",
            )
            await _update_request(
                row_id,
                status="failed",
                reply_sent=True,
                sales_notified=True,
                error_message=f"Needs clarification: {parsed.clarification_note}",
            )
            return

        # ── Step 3: Build description and run pipeline ───────────
        final_description = build_final_description(
            parsed.additional_details,
            combined_attachment_text,
        )

        pipeline_input: Dict[str, Any] = {
            "description": final_description,
            "additional_context": parsed.additional_context,
            "preferred_tech_stack": parsed.preferred_tech_stack,
            "build_options": parsed.build_options or [],
        }

        result: Dict[str, Any] = await _retry_async(
            lambda: pipeline.run(pipeline_input),
            label="estimation_pipeline",
        )

        await _update_request(
            row_id,
            estimate_result=json.dumps(result, default=str),
        )

        # ── Step 4: Generate PDF ─────────────────────────────────
        pdf_bytes: Optional[bytes] = None
        try:
            context = _build_proposal_context(result)
            html = render_proposal(context)
            pdf_bytes = await asyncio.to_thread(_pdf_service.generate_pdf, html)
            await _update_request(row_id, pdf_generated=True)
        except Exception:
            logger.exception("PDF generation failed for row_id=%s", row_id)

        # ── Step 5: Reply to sender ──────────────────────────────
        estimation = result.get("estimation", {})
        proposal = result.get("proposal", {})
        planning = result.get("planning", {})

        total_hours = estimation.get("total_hours", 0)
        min_hours = estimation.get("min_hours", 0)
        max_hours = estimation.get("max_hours", 0)
        timeline_weeks = proposal.get(
            "timeline_weeks", planning.get("timeline_weeks", "TBD"),
        )

        reply_sent = False
        if pdf_bytes:
            try:
                await _retry_async(
                    lambda: asyncio.to_thread(
                        send_proposal_reply,
                        email.sender_email,
                        email.subject,
                        _build_success_reply_html(
                            email.sender_name,
                            total_hours,
                            min_hours,
                            max_hours,
                            timeline_weeks,
                        ),
                        pdf_bytes,
                        "proposal.pdf",
                        email.message_id,
                    ),
                    label="send_proposal_reply",
                )
                reply_sent = True
                await _update_request(row_id, reply_sent=True)
            except Exception:
                logger.exception("Failed to send proposal reply for row_id=%s", row_id)
        else:
            # PDF failed — tell sender the team will follow up
            _try_send(
                send_error_reply,
                email.sender_email,
                email.subject,
                _build_error_reply_html(email.sender_name),
            )

        # ── Step 6: Notify sales ─────────────────────────────────
        requirements_summary = parsed.additional_details[:500]
        estimate_summary = (
            f"Total: {int(total_hours)} hrs (range {int(min_hours)}–{int(max_hours)}), "
            f"Timeline: {timeline_weeks} weeks, "
            f"Features: {len(estimation.get('features', []))}"
        )

        try:
            await asyncio.to_thread(
                send_sales_notification,
                email.sender_email,
                email.subject,
                requirements_summary,
                estimate_summary,
                pdf_bytes,
            )
            await _update_request(row_id, sales_notified=True)
        except Exception:
            logger.exception("Failed to send sales notification for row_id=%s", row_id)

        # Slack (fire-and-forget)
        try:
            await notify_slack(
                email.sender_email,
                email.subject,
                total_hours,
                reply_sent,
            )
        except Exception:
            logger.exception("Slack notification failed for row_id=%s", row_id)

        # ── Done ─────────────────────────────────────────────────
        await _update_request(row_id, status="completed")
        logger.info("Email pipeline completed: row_id=%s", row_id)

    except Exception:
        logger.exception("Email pipeline failed for sender=%s", email.sender_email)
        if row_id:
            try:
                await _update_request(
                    row_id,
                    status="failed",
                    error_message="Unhandled pipeline error",
                )
            except Exception:
                logger.exception("Failed to update DB status after error")

        # Best-effort error reply
        _try_send(
            send_error_reply,
            email.sender_email,
            email.subject,
            _build_error_reply_html(email.sender_name),
        )
        # Best-effort sales notification
        _try_send(
            send_sales_notification,
            email.sender_email,
            email.subject,
            email.body_plain[:500] if email.body_plain else "(no body)",
            "Pipeline failed — manual review needed",
        )


def _try_send(fn, *args, **kwargs) -> None:
    """Call a sync email function, swallowing exceptions."""
    try:
        fn(*args, **kwargs)
    except Exception:
        logger.exception("Email send failed (best-effort): fn=%s", fn.__name__)


# ── Proposal context builder (mirrors _build_proposal_context in main.py) ─

def _build_proposal_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the Jinja2 template context from a pipeline result dict.

    This duplicates the logic in ``app.main._build_proposal_context`` to
    keep the email pipeline self-contained — if the source function is ever
    refactored into a shared module, this can be replaced.
    """
    proposal = data.get("proposal", {})
    estimation = data.get("estimation", {})
    tech_stack = data.get("tech_stack", {})
    domain_detection = data.get("domain_detection", {})
    planning = data.get("planning", {})

    detected_domain = (
        str(domain_detection.get("detected_domain", "Unknown"))
        .replace("_", " ")
        .title()
    )

    return {
        "request_id": data.get("request_id", "N/A"),
        "project_title": f"{detected_domain} Platform",
        "detected_domain": detected_domain,
        "executive_summary": proposal.get("executive_summary", ""),
        "proposed_solution": proposal.get("proposed_solution", ""),
        "scope_of_work": proposal.get("scope_of_work", ""),
        "deliverables": proposal.get("deliverables", []),
        "risks": proposal.get("risks", []),
        "mitigation_strategies": proposal.get("mitigation_strategies", []),
        "features": estimation.get("features", []),
        "total_hours": estimation.get("total_hours", 0),
        "min_hours": estimation.get("min_hours", 0),
        "max_hours": estimation.get("max_hours", 0),
        "confidence_score": estimation.get("confidence_score", 0),
        "assumptions": estimation.get("assumptions", []),
        "tech_frontend": tech_stack.get("frontend", []),
        "tech_backend": tech_stack.get("backend", []),
        "tech_database": tech_stack.get("database", []),
        "tech_infrastructure": tech_stack.get("infrastructure", []),
        "tech_third_party": tech_stack.get("third_party_services", []),
        "tech_justification": tech_stack.get("justification", ""),
        "team_composition": proposal.get(
            "team_composition", planning.get("team_recommendation", {}),
        ),
        "timeline_weeks": proposal.get(
            "timeline_weeks", planning.get("timeline_weeks", "TBD"),
        ),
        "phase_split": planning.get("phase_split", {}),
        "category_breakdown": planning.get("category_breakdown", {}),
    }
