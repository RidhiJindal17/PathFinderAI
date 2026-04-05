"""
models/gap_analysis.py — PathFinder AI  ·  Module II: Semantic Skill-Gap Analyzer
===================================================================================
Pydantic v2 request/response schemas for POST /api/gap/analyze.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# ══════════════════════════════════════════════════════════════════════════════
#  REQUEST
# ══════════════════════════════════════════════════════════════════════════════

class GapAnalysisRequest(BaseModel):
    """
    Body for POST /api/gap/analyze.

    Both fields are required.  ``resume_skills`` may be the direct output of
    Module I's ``parse_resume()["skills"]`` list.
    """

    resume_skills: list[str] = Field(
        ...,
        description=(
            "Skills extracted from the candidate's resume "
            "(output of POST /api/resume/parse → data.skills). "
            "May be an empty list — the analyzer handles that gracefully."
        ),
        examples=[["python", "sql", "html", "css"]],
    )
    job_description: str = Field(
        ...,
        min_length=10,
        description="Full text of the job description. Minimum 10 characters.",
        examples=[(
            "We are looking for a React developer with experience in TypeScript, "
            "Node.js, REST APIs, and Git."
        )],
    )

    @field_validator("resume_skills", mode="before")
    @classmethod
    def normalise_skills(cls, v: list) -> list[str]:
        """Strip whitespace and remove empty strings from the input list."""
        return [s.strip() for s in v if isinstance(s, str) and s.strip()]

    @field_validator("job_description", mode="before")
    @classmethod
    def strip_jd(cls, v: str) -> str:
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "resume_skills": ["python", "sql", "html", "css"],
                "job_description": (
                    "We are looking for a React developer with experience in "
                    "TypeScript, Node.js, REST APIs, and Git."
                ),
            }
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
#  BRIDGE SKILL ITEM
# ══════════════════════════════════════════════════════════════════════════════

class BridgeSkill(BaseModel):
    """
    A single skill gap entry.

    ``similarity_score`` reflects how close the candidate's best resume skill
    was to this job requirement (0.0 = no overlap, 1.0 = perfect match).
    Scores below 0.65 are considered gaps.
    """

    skill: str = Field(..., description="The skill keyword found in the job description.")
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Best cosine similarity between this JD skill and any resume skill. "
            "Always < 0.65 for bridge skills."
        ),
    )
    priority: Literal["high", "medium", "low"] = Field(
        ...,
        description=(
            "Gap urgency tier based on similarity_score. "
            "high: < 0.30  |  medium: 0.30–0.50  |  low: 0.50–0.65"
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "skill": "react",
                "similarity_score": 0.1823,
                "priority": "high",
            }
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
#  RESPONSE
# ══════════════════════════════════════════════════════════════════════════════

class GapAnalysisResponse(BaseModel):
    """
    Full response returned by POST /api/gap/analyze.

    Fields
    ------
    match_score
        0–100 integer.  Computed as the mean of the best-coverage cosine
        similarities for all JD skills, scaled to percentage.
        A score of 70+ means good alignment; below 40 = significant upskilling needed.

    matched_skills
        JD skills where the candidate's best resume match scored ≥ 0.65.

    bridge_skills
        JD skills below the 0.65 threshold, ranked highest-priority first.
        Each entry carries a ``similarity_score`` and a ``priority`` tier.

    job_skills_extracted
        All skill keywords detected in the job description.

    total_job_skills / total_resume_skills
        Raw counts — useful for calculating coverage % on the frontend.

    analysis_note
        Non-null only for edge-case responses (empty JD, unrecognised JD skills,
        empty resume).  Carry a user-friendly explanation.
    """

    match_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall skill coverage score (0–100).",
    )
    matched_skills: list[str] = Field(
        default_factory=list,
        description="JD skills that are well-covered by the resume (similarity ≥ 0.65).",
    )
    bridge_skills: list[BridgeSkill] = Field(
        default_factory=list,
        description=(
            "Skills the candidate needs to learn, ordered highest-priority first. "
            "Each entry includes the skill name, similarity score, and priority tier."
        ),
    )
    job_skills_extracted: list[str] = Field(
        default_factory=list,
        description="All skill keywords detected in the job description.",
    )
    total_job_skills: int = Field(
        ...,
        ge=0,
        description="Total number of skills found in the job description.",
    )
    total_resume_skills: int = Field(
        ...,
        ge=0,
        description="Total number of skills provided from the resume.",
    )
    analysis_note: str | None = Field(
        default=None,
        description="Human-readable note for edge-case responses. Null on normal runs.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "match_score": 34,
                "matched_skills": ["python", "sql", "git"],
                "bridge_skills": [
                    {"skill": "react",      "similarity_score": 0.1823, "priority": "high"},
                    {"skill": "typescript", "similarity_score": 0.2104, "priority": "high"},
                    {"skill": "node.js",    "similarity_score": 0.3571, "priority": "medium"},
                    {"skill": "rest api",   "similarity_score": 0.5812, "priority": "low"},
                ],
                "job_skills_extracted": ["react", "typescript", "node.js", "rest api", "python", "sql", "git"],
                "total_job_skills": 7,
                "total_resume_skills": 4,
                "analysis_note": None,
            }
        }
    }