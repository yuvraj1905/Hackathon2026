"""
Document Cleaner Service

Uses LLM to clean and structure extracted document text:
- Fixes OCR/layout errors (garbled text, split words)
- Normalizes structure (headings, bullets, numbered lists)
- Preserves all content while improving readability
"""

import logging
from typing import Optional

from app.services.llm_client import llm_complete

logger = logging.getLogger(__name__)

CLEANUP_SYSTEM_PROMPT = """You are a document text cleaner. Your job is to clean and structure extracted document text while preserving ALL content.

Instructions:
1. Fix OCR/extraction errors (garbled characters, split words, broken sentences)
2. Normalize formatting (consistent headings, bullets, numbered lists)
3. Preserve ALL original content - do not summarize or remove anything
4. Keep tables as pipe-separated rows
5. Maintain the original document structure and hierarchy
6. Remove obvious artifacts (page numbers, repeated headers, watermarks)
7. Return ONLY the cleaned text, no explanations or metadata

The output should be clean, well-structured text that is easy to read and process."""


async def clean_extracted_text_with_llm(
    raw_text: str,
    model: str = "openai/gpt-4.1-nano",
    api_key: Optional[str] = None,
) -> str:
    """
    Clean and structure extracted document text using LLM.
    
    Args:
        raw_text: Raw extracted text from document parser
        model: LLM model to use (default: gpt-4.1-mini)
        api_key: OpenRouter API key (defaults to env var)
        
    Returns:
        Cleaned and structured text
        
    Raises:
        ValueError: If API call fails or returns invalid response
    """
    if not raw_text or not raw_text.strip():
        return raw_text
    
    logger.info("Starting LLM document cleanup: input_chars=%d", len(raw_text))
    
    messages = [
        {"role": "system", "content": CLEANUP_SYSTEM_PROMPT},
        {"role": "user", "content": f"Clean and structure this extracted document text:\n\n{raw_text}"},
    ]
    
    try:
        cleaned_text = await llm_complete(
            messages=messages,
            temperature=0.1,
            max_tokens=4000,
            model=model
        )
        
        logger.info(
            "LLM document cleanup complete: input_chars=%d output_chars=%d",
            len(raw_text),
            len(cleaned_text),
        )
        logger.debug("Cleaned content preview (first 500 chars): %s", cleaned_text[:500])
        
        return cleaned_text
        
    except Exception as e:
        logger.exception("Error during LLM cleanup")
        raise ValueError(f"LLM cleanup failed: {str(e)}") from e


def should_use_llm_cleanup(raw_text: str, file_size_bytes: int) -> bool:
    """
    Determine if LLM cleanup should be used based on extraction quality.
    
    Heuristics:
    - Very short text relative to file size suggests poor extraction
    - High ratio of special characters suggests garbled text
    
    Args:
        raw_text: Extracted text
        file_size_bytes: Original file size in bytes
        
    Returns:
        True if LLM cleanup is recommended
    """
    if not raw_text:
        return True
    
    text_len = len(raw_text)
    
    if file_size_bytes > 100_000 and text_len < 500:
        logger.info("LLM cleanup recommended: short extraction from large file")
        return True
    
    if text_len > 0:
        special_chars = sum(1 for c in raw_text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / text_len
        if special_ratio > 0.3:
            logger.info("LLM cleanup recommended: high special character ratio (%.2f)", special_ratio)
            return True
    
    return False
