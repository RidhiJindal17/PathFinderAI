"""
routers/resume.py — PathFinder AI  ·  Module I: Intelligent Resume Parser
==========================================================================
HTTP routing for the Resume feature.

Endpoints
---------
POST /api/resume/parse
    Accepts a multipart/form-data PDF upload.
    Validates file type and size.
    Delegates to services/resume_parser.py.
    Returns a structured ResumeParseResponse JSON.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from config import settings
from models.resume import ParsedResume, ResumeParseError, ResumeParseResponse
from services.resume_parser import parse_resume

logger = logging.getLogger(__name__)

router = APIRouter()

# Accepted MIME types for PDF files
# (browsers sometimes send "application/octet-stream" for PDFs)
_ACCEPTED_CONTENT_TYPES: frozenset[str] = frozenset({
    "application/pdf",
    "application/octet-stream",
    "binary/octet-stream",
})


@router.post(
    "/parse",
    response_model=ResumeParseResponse,
    summary="Upload a PDF resume and extract structured information",
    responses={
        200: {"description": "Resume successfully parsed", "model": ResumeParseResponse},
        413: {"description": "File too large", "model": ResumeParseError},
        422: {"description": "Invalid file type (not a PDF)", "model": ResumeParseError},
        500: {"description": "Internal parsing error"},
    },
)
async def parse_resume_endpoint(
    file: UploadFile = File(
        ...,
        description="PDF resume file (max 5 MB)",
    ),
):
    """
    **Upload a PDF resume to extract structured career information.**

    The pipeline:
    1. Validate the file is a PDF and within the size limit.
    2. Extract raw text from all pages using PyPDF2.
    3. Run spaCy NER to detect name, email, phone.
    4. Match text against a 200+ skill keyword bank.
    5. Extract education, experience, and project sections.

    **Returns** a JSON object containing:
    - `name`, `email`, `phone` — contact info
    - `skills` — list of detected skills
    - `education` — education entries
    - `experience` — work experience sentences
    - `projects` — project descriptions
    - `parse_status` — `"success"` | `"partial"` | `"error"`

    **Notes:**
    - Scanned / image-only PDFs will return `parse_status: "partial"` with empty lists.
    - Maximum upload size is controlled by the `MAX_UPLOAD_SIZE_MB` env variable (default 5 MB).
    """

    filename: str = file.filename or "resume.pdf"

    # ── Validation 1: File extension ─────────────────────────────────────────
    if not filename.lower().endswith(".pdf"):
        logger.warning(f"Rejected upload — not a PDF filename: {filename!r}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "error": "Invalid file type. Only PDF files are accepted.",
                "detail": f"Filename '{filename}' does not end with .pdf",
            },
        )

    # ── Read file bytes ───────────────────────────────────────────────────────
    file_bytes: bytes = await file.read()

    # ── Validation 2: File size ───────────────────────────────────────────────
    max_bytes = settings.max_upload_size_bytes
    if len(file_bytes) > max_bytes:
        size_mb = len(file_bytes) / (1024 * 1024)
        logger.warning(
            f"Rejected upload — file too large: {size_mb:.1f} MB "
            f"(limit: {settings.max_upload_size_mb} MB)"
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "success": False,
                "error": (
                    f"File is too large ({size_mb:.1f} MB). "
                    f"Maximum allowed size is {settings.max_upload_size_mb} MB."
                ),
                "detail": None,
            },
        )

    # ── Validation 3: MIME type (secondary check) ─────────────────────────────
    content_type = (file.content_type or "").lower()
    # Also peek at the first 4 bytes — real PDFs start with b"%PDF"
    pdf_magic = file_bytes[:4] == b"%PDF"

    if content_type not in _ACCEPTED_CONTENT_TYPES and not pdf_magic:
        logger.warning(f"Rejected upload — MIME type not PDF: {content_type!r}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "error": "Invalid file type. Only PDF files are accepted.",
                "detail": f"Received content-type: {content_type}",
            },
        )

    # ── Parse ─────────────────────────────────────────────────────────────────
    logger.info(f"Parsing resume: {filename!r} ({len(file_bytes):,} bytes)")

    try:
        parsed: dict = parse_resume(file_bytes)
    except Exception as exc:
        logger.exception(f"Unexpected error parsing {filename!r}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while parsing the resume: {exc}",
        )

    # ── Build response ────────────────────────────────────────────────────────
    return ResumeParseResponse(
        success=True,
        filename=filename,
        data=ParsedResume(**parsed),
    )