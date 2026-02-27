import logging
from typing import Optional

logger = logging.getLogger(__name__)

MAX_INPUT_CHARS = 20000


def build_final_description(
    manual_description: Optional[str],
    extracted_text: Optional[str]
) -> str:
    """
    Build one normalized description string from manual and/or extracted input.

    Rules:
    - both present: manual + additional document context section
    - only manual: manual
    - only extracted: extracted
    - neither: ValueError
    """
    manual = manual_description.strip() if manual_description else None
    extracted = extracted_text.strip() if extracted_text else None

    has_manual = bool(manual)
    has_extracted = bool(extracted)

    logger.debug(
        "Input presence check manual_present=%s file_present=%s",
        has_manual,
        has_extracted,
    )

    if has_manual and has_extracted:
        final_description = (
            f"{manual}\n\n"
            "Additional context from client documents:\n"
            f"{extracted}"
        )
        mode = "hybrid_input"
    elif has_manual:
        final_description = manual
        mode = "manual_only"
    elif has_extracted:
        final_description = extracted
        mode = "file_only"
    else:
        raise ValueError("Either manual_description or extracted_text is required")

    if len(final_description) > MAX_INPUT_CHARS:
        logger.debug(
            "Input fusion truncating description from %d to %d chars",
            len(final_description),
            MAX_INPUT_CHARS,
        )
        final_description = final_description[:MAX_INPUT_CHARS].rstrip()

    logger.debug(
        "Input fusion complete mode=%s manual_len=%d extracted_len=%d final_len=%d",
        mode,
        len(manual or ""),
        len(extracted or ""),
        len(final_description),
    )

    return final_description
