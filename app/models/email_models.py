"""Pydantic models for the inbound-email estimation pipeline."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class EmailEstimateStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class InboundAttachment(BaseModel):
    """Metadata for a single attachment from SendGrid Inbound Parse."""

    filename: str
    content_type: str
    size: int = 0


class InboundEmailData(BaseModel):
    """Parsed representation of a SendGrid Inbound Parse webhook payload."""

    model_config = ConfigDict(str_strip_whitespace=True)

    sender_email: str = Field(..., description="Sender email address")
    sender_name: str = Field("", description="Sender display name")
    to_email: str = Field("", description="Recipient address")
    subject: str = Field("", description="Email subject line")
    body_plain: str = Field("", description="Plain-text body")
    body_html: str = Field("", description="HTML body")
    message_id: str = Field("", description="Original Message-ID header for threading")
    attachments: List[InboundAttachment] = Field(default_factory=list)
    # Raw file bytes keyed by filename (not persisted, only used in-memory)
    attachment_bytes: Dict[str, bytes] = Field(default_factory=dict, exclude=True)


class ParsedRequirements(BaseModel):
    """Structured requirements extracted by LLM from freeform email text."""

    model_config = ConfigDict(str_strip_whitespace=True)

    additional_details: str = Field("", description="Project description (≥10 chars)")
    build_options: List[str] = Field(default_factory=list)
    additional_context: Optional[str] = Field(None)
    preferred_tech_stack: Optional[List[str]] = Field(None)
    timeline_constraint: Optional[str] = Field(None)
    needs_clarification: bool = Field(
        False, description="True when information was too sparse for a complete extraction"
    )
    clarification_note: str = Field(
        "", description="Human-readable note about what's missing"
    )
