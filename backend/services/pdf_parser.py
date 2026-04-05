"""
services/pdf_parser.py — PathFinder AI
Extracts plain text from PDF bytes using PyPDF2.
"""

import io
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text(pdf_bytes: bytes) -> str:
    """
    Parses a PDF from raw bytes and returns all text content as a single string.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        Concatenated text from all pages, separated by newlines.

    Raises:
        ValueError: If the PDF cannot be read or has no extractable text.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as exc:
        logger.error(f"Failed to parse PDF: {exc}")
        raise ValueError(f"Invalid or corrupted PDF: {exc}") from exc

    pages_text: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
            pages_text.append(text)
        except Exception as exc:
            logger.warning(f"Could not extract text from page {i + 1}: {exc}")

    full_text = "\n".join(pages_text)
    logger.debug(f"Extracted {len(full_text)} characters from {len(reader.pages)} page(s).")
    return full_text