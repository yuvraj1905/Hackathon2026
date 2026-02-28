"""Send emails via the SendGrid v3 Mail Send API."""

import base64
import logging
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    ContentId,
    Disposition,
    FileContent,
    FileName,
    FileType,
    Header,
    Mail,
)

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _get_client() -> SendGridAPIClient:
    if not settings.SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY is not configured")
    return SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)


def send_proposal_reply(
    to_email: str,
    subject: str,
    body_html: str,
    pdf_bytes: bytes,
    pdf_filename: str = "proposal.pdf",
    original_message_id: str = "",
) -> None:
    """
    Reply to the original sender with the proposal PDF attached.

    Sets In-Reply-To / References headers so the reply threads correctly
    in the sender's inbox.
    """
    message = Mail(
        from_email=settings.ESTIMATES_FROM_EMAIL,
        to_emails=to_email,
        subject=f"Re: {subject}" if not subject.startswith("Re:") else subject,
        html_content=body_html,
    )

    # Thread the reply
    if original_message_id:
        message.header = [
            Header("In-Reply-To", original_message_id),
            Header("References", original_message_id),
        ]

    # Attach proposal PDF
    encoded_pdf = base64.b64encode(pdf_bytes).decode("ascii")
    attachment = Attachment(
        FileContent(encoded_pdf),
        FileName(pdf_filename),
        FileType("application/pdf"),
        Disposition("attachment"),
    )
    message.attachment = attachment

    client = _get_client()
    response = client.send(message)
    logger.info(
        "Proposal reply sent: to=%s status=%s",
        to_email,
        response.status_code,
    )


def send_sales_notification(
    sender_email: str,
    subject: str,
    requirements_summary: str,
    estimate_summary: str,
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: str = "proposal.pdf",
) -> None:
    """
    Notify the sales team about a new inbound estimate request.

    Includes sender info, parsed requirements, estimate summary, and
    the proposal PDF (when available).
    """
    html = (
        "<h2>New Inbound Estimate Request</h2>"
        f"<p><strong>From:</strong> {sender_email}</p>"
        f"<p><strong>Subject:</strong> {subject}</p>"
        "<hr/>"
        f"<h3>Parsed Requirements</h3><p>{requirements_summary}</p>"
        "<hr/>"
        f"<h3>Estimate Summary</h3><p>{estimate_summary}</p>"
    )

    message = Mail(
        from_email=settings.ESTIMATES_FROM_EMAIL,
        to_emails=settings.SALES_TEAM_EMAIL,
        subject=f"[Auto-Estimate] New request from {sender_email}",
        html_content=html,
    )

    if pdf_bytes:
        encoded_pdf = base64.b64encode(pdf_bytes).decode("ascii")
        attachment = Attachment(
            FileContent(encoded_pdf),
            FileName(pdf_filename),
            FileType("application/pdf"),
            Disposition("attachment"),
        )
        message.attachment = attachment

    client = _get_client()
    response = client.send(message)
    logger.info(
        "Sales notification sent: to=%s status=%s",
        settings.SALES_TEAM_EMAIL,
        response.status_code,
    )


def send_error_reply(to_email: str, subject: str, error_html: str) -> None:
    """Send a friendly error reply when processing fails."""
    message = Mail(
        from_email=settings.ESTIMATES_FROM_EMAIL,
        to_emails=to_email,
        subject=f"Re: {subject}" if not subject.startswith("Re:") else subject,
        html_content=error_html,
    )
    client = _get_client()
    response = client.send(message)
    logger.info(
        "Error reply sent: to=%s status=%s",
        to_email,
        response.status_code,
    )
