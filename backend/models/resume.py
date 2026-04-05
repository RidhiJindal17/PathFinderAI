"""
models/resume.py — PathFinder AI  ·  Module I: Intelligent Resume Parser
=========================================================================
Pydantic v2 request/response schemas for the /api/resume/parse endpoint.
"""

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════════════
#  RESPONSE SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class ParsedResume(BaseModel):
    """
    Fully structured representation of a parsed resume.
    All list fields default to [] — missing sections never cause errors.
    """

    # ── Contact Information ───────────────────────────────────────────────────
    name: str | None = Field(
        default=None,
        description="Full name detected in the resume header (via spaCy PERSON entity).",
    )
    email: str | None = Field(
        default=None,
        description="Email address extracted via regex.",
    )
    phone: str | None = Field(
        default=None,
        description="Phone number extracted via regex.",
    )

    # ── Core Sections ─────────────────────────────────────────────────────────
    skills: list[str] = Field(
        default_factory=list,
        description=(
            "Detected technical and soft skills matched against a 200+ keyword bank. "
            "Always lowercase, alphabetically sorted."
        ),
    )
    education: list[str] = Field(
        default_factory=list,
        description="Education entries extracted from the resume.",
    )
    experience: list[str] = Field(
        default_factory=list,
        description="Work experience bullet points / sentences.",
    )
    projects: list[str] = Field(
        default_factory=list,
        description="Project descriptions found in a Projects section or as bullet points.",
    )

    # ── Meta ──────────────────────────────────────────────────────────────────
    raw_text: str = Field(default="", description="Full text extracted from the PDF.")
    char_count: int = Field(default=0, description="Number of characters extracted.")
    parse_status: Literal["success", "partial", "error"] = Field(default="success")
    error_detail: str | None = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Priya Sharma",
                "email": "priya.sharma@email.com",
                "phone": "+91-9876543210",
                "skills": ["python", "fastapi", "mongodb", "react", "docker", "machine learning", "sql"],
                "education": ["B.Tech in Computer Science — XYZ University, 2024 (CGPA: 8.7)"],
                "experience": [
                    "Developed a REST API using FastAPI and MongoDB for an e-commerce platform.",
                    "Internship at ABC Corp — built data pipelines using Python and Apache Spark.",
                ],
                "projects": [
                    "PathFinder AI — AI career navigation system using FastAPI, spaCy, and Google Gemini.",
                ],
                "raw_text": "Priya Sharma\npriya.sharma@email.com\n...",
                "char_count": 3241,
                "parse_status": "success",
                "error_detail": None,
            }
        }
    }


class ResumeParseResponse(BaseModel):
    """Top-level HTTP response returned by POST /api/resume/parse."""

    success: bool = Field(default=True)
    filename: str = Field(..., description="Original filename of the uploaded PDF.")
    data: ParsedResume = Field(..., description="The fully parsed resume object.")


class ResumeParseError(BaseModel):
    """Returned when the file upload is rejected before parsing begins."""

    success: bool = Field(default=False)
    error: str = Field(..., description="Human-readable error message.")
    detail: str | None = Field(default=None)