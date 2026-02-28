"""Post formatted notifications to Slack via incoming webhook."""

import logging

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


async def notify_slack(
    sender_email: str,
    subject: str,
    total_hours: float,
    proposal_sent: bool,
) -> None:
    """
    Post a formatted message to the configured Slack webhook.

    No-ops silently when ``SLACK_WEBHOOK_URL`` is not set.
    """
    url = settings.SLACK_WEBHOOK_URL
    if not url:
        return

    status_emoji = ":white_check_mark:" if proposal_sent else ":warning:"
    status_text = "Proposal auto-sent" if proposal_sent else "Proposal could not be sent — manual follow-up needed"

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":incoming_envelope: New Inbound Estimate Request",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*From:*\n{sender_email}"},
                    {"type": "mrkdwn", "text": f"*Subject:*\n{subject or '(no subject)'}"},
                    {"type": "mrkdwn", "text": f"*Estimated Hours:*\n{int(total_hours)}"},
                    {"type": "mrkdwn", "text": f"*Status:*\n{status_emoji} {status_text}"},
                ],
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        logger.info("Slack notification sent for request from %s", sender_email)
    except Exception:
        logger.exception("Failed to send Slack notification")
