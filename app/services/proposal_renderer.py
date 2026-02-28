import logging
import re
from datetime import date
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config.settings import settings
from app.services.diagram_generator import DiagramGenerator

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _parse_markdown_email(value: str) -> tuple[str, str]:
    """
    Parse markdown-style email link into display and href.
    """
    match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", value.strip())
    if match:
        return match.group(1), match.group(2)
    return value, f"mailto:{value}"


def render_proposal(context: dict[str, Any]) -> str:
    """
    Render the proposal HTML from the Jinja2 template.

    Company settings are injected automatically — callers only need to provide
    project-specific context keys.

    Args:
        context: Dict with project data (features, tech stack, proposal fields, etc.)

    Returns:
        Rendered HTML string ready for PDF conversion or direct display.
    """
    email_display, email_href = _parse_markdown_email(settings.COMPANY_EMAIL)
    enriched = {
        "company_name": settings.COMPANY_NAME,
        "company_logo_url": settings.COMPANY_LOGO_URL,
        "company_email": email_display,
        "company_email_href": email_href,
        "company_phone": settings.COMPANY_PHONE,
        "company_address": settings.COMPANY_ADDRESS,
        "proposal_date": date.today().strftime("%B %d, %Y"),
        **context,
    }

    # Generate diagram HTML fragments
    enriched["architecture_diagram_html"] = DiagramGenerator.generate_architecture_diagram(
        enriched.get("tech_frontend", []),
        enriched.get("tech_backend", []),
        enriched.get("tech_database", []),
        enriched.get("tech_infrastructure", []),
        enriched.get("tech_third_party", []),
    )
    enriched["feature_category_diagram_html"] = DiagramGenerator.generate_feature_category_diagram(
        enriched.get("features", []),
        enriched.get("category_breakdown", {}),
    )
    enriched["phase_timeline_diagram_html"] = DiagramGenerator.generate_phase_timeline_diagram(
        enriched.get("phase_split", {}),
        enriched.get("timeline_weeks"),
        enriched.get("total_hours", 0),
    )

    template = _env.get_template("proposal_template.html")
    html = template.render(**enriched)

    logger.info("Proposal HTML rendered: %d characters", len(html))
    return html
