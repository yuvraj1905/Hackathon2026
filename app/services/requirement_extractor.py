"""
Use OpenRouter to structure freeform email text into the ProjectRequest
schema expected by the estimation pipeline.

Uses the same BaseAgent LLM infrastructure as the rest of the codebase.
"""

import json
import logging
from typing import Any, Dict, Optional

from app.agents.base_agent import BaseAgent
from app.models.email_models import ParsedRequirements

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """\
You are a requirements extraction assistant. You are given the raw text of an
email (and optional attachment text) sent to a software estimation service.

Your job is to extract structured project requirements that match the following
JSON schema:

{
  "additional_details": "<string — full project description, min 10 chars>",
  "build_options": ["<list of applicable options from: mobile, web, design, backend, admin>"],
  "additional_context": "<string or null — any extra context, constraints, or preferences>",
  "preferred_tech_stack": ["<list of specific technologies the sender mentions>"] or null,
  "timeline_constraint": "<string or null — e.g. '3 months', 'Q2 2026', 'ASAP'>",
  "needs_clarification": <boolean — true if the email is too vague to estimate>,
  "clarification_note": "<string — what information is missing, empty if needs_clarification is false>"
}

Rules:
1. The "additional_details" field MUST be at least 10 characters.  If the email
   is very short, expand it into a reasonable description using what context you
   have (e.g. "Build a mobile app for food delivery").
2. Only include build_options values from the allowed set.
3. Infer build_options from context when possible (e.g. "iOS app" → ["mobile"]).
4. Set needs_clarification=true only when the email has essentially no useful
   project information (e.g. "Hi, call me back").
5. Return ONLY valid JSON — no markdown fences, no commentary.
"""


class _RequirementExtractionAgent(BaseAgent):
    """Thin BaseAgent subclass — delegates entirely to call_llm + parse_json_response."""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": _EXTRACTION_PROMPT},
            {"role": "user", "content": input_data["user_message"]},
        ]
        raw = await self.call_llm(
            messages,
            response_format={"type": "json_object"},
            max_tokens=1024,
        )
        return self.parse_json_response(raw)


# Module-level singleton (lazy-init on first call to avoid import-time env check)
_agent: Optional[_RequirementExtractionAgent] = None


def _get_agent() -> _RequirementExtractionAgent:
    global _agent
    if _agent is None:
        _agent = _RequirementExtractionAgent()
    return _agent


async def extract_requirements(
    body_text: str,
    attachment_text: Optional[str] = None,
    subject: str = "",
) -> ParsedRequirements:
    """
    Call the LLM via OpenRouter to convert freeform email text into a
    ``ParsedRequirements`` object.

    Args:
        body_text:       Plain-text email body.
        attachment_text: Concatenated text extracted from attachments (if any).
        subject:         Email subject line (provides additional context).

    Returns:
        ``ParsedRequirements`` with structured fields.
    """
    # Assemble the user message
    parts: list[str] = []
    if subject:
        parts.append(f"Subject: {subject}")
    if body_text.strip():
        parts.append(f"Email body:\n{body_text.strip()}")
    if attachment_text and attachment_text.strip():
        parts.append(f"Attachment text:\n{attachment_text.strip()}")

    user_message = "\n\n---\n\n".join(parts) if parts else "(empty email)"

    agent = _get_agent()
    extracted = await agent.execute({"user_message": user_message})

    parsed = ParsedRequirements(**extracted)
    logger.info(
        "Requirements extracted: details_len=%d build_options=%s needs_clarification=%s",
        len(parsed.additional_details),
        parsed.build_options,
        parsed.needs_clarification,
    )
    return parsed
