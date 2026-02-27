import asyncio
import logging
import re
from io import BytesIO
from pathlib import Path

import pandas as pd
from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_OUTPUT_CHARS = 12000
PARSE_TIMEOUT_SECONDS = 20


async def extract_text_from_upload(upload_file: UploadFile) -> str:
    """
    Extract clean text from an uploaded business document.

    Supported formats:
    - .pdf
    - .docx
    - .xlsx / .xls
    """
    filename = upload_file.filename or ""
    extension = Path(filename).suffix.lower()

    content = await upload_file.read()
    if not content:
        raise ValueError("Uploaded file is empty")

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    if extension == ".docx":
        text = await asyncio.wait_for(
            asyncio.to_thread(_extract_docx_text, content),
            timeout=PARSE_TIMEOUT_SECONDS,
        )
    elif extension == ".pdf":
        text = await asyncio.wait_for(
            asyncio.to_thread(_extract_pdf_text, content),
            timeout=PARSE_TIMEOUT_SECONDS,
        )
    elif extension in {".xlsx", ".xls"}:
        text = await asyncio.wait_for(
            asyncio.to_thread(_extract_excel_text, content, extension),
            timeout=PARSE_TIMEOUT_SECONDS,
        )
    else:
        raise ValueError("Unsupported file type. Allowed: .pdf, .docx, .xlsx, .xls")

    cleaned = _clean_text(text)
    if not cleaned:
        raise ValueError("No readable text extracted from uploaded file")

    if len(cleaned) > MAX_OUTPUT_CHARS:
        cleaned = cleaned[:MAX_OUTPUT_CHARS]

    logger.info(
        "Document parsed successfully: filename=%s extension=%s extracted_chars=%d",
        filename,
        extension,
        len(cleaned),
    )
    return cleaned


def _extract_docx_text(content: bytes) -> str:
    try:
        doc = Document(BytesIO(content))
        paragraphs = [
            p.text.strip()
            for p in doc.paragraphs
            if p.text and p.text.strip()
        ]
        return "\n".join(paragraphs)
    except Exception as exc:
        logger.exception("DOCX parsing failed")
        raise ValueError(f"Failed to parse DOCX: {exc}") from exc


def _extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        chunks: list[str] = []
        for idx, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                page_text = page_text.strip()
                if page_text:
                    chunks.append(page_text)
            except Exception:
                logger.warning("Skipping unreadable PDF page index=%d", idx)
        return "\n\n".join(chunks)
    except Exception as exc:
        logger.exception("PDF parsing failed")
        raise ValueError(f"Failed to parse PDF: {exc}") from exc


def _extract_excel_text(content: bytes, extension: str) -> str:
    try:
        engine = "openpyxl" if extension == ".xlsx" else "xlrd"
        sheets = pd.read_excel(BytesIO(content), sheet_name=None, engine=engine)

        lines: list[str] = []
        for sheet_name, df in sheets.items():
            if df is None or df.empty:
                continue
            lines.append(f"Sheet: {sheet_name}")
            for row in df.fillna("").astype(str).values.tolist():
                row_text = " | ".join(cell.strip() for cell in row if cell.strip())
                if row_text:
                    lines.append(row_text)
            lines.append("")
        return "\n".join(lines)
    except Exception as exc:
        logger.exception("Excel parsing failed")
        raise ValueError(f"Failed to parse Excel: {exc}") from exc


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
