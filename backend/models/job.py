"""
models/job.py — PathFinder AI
Pydantic schemas for the Job Match feature.
Note: Core matching logic is in models/gap_analysis.py (Module II).
This file provides the legacy job matching schemas.
"""

from pydantic import BaseModel, Field


class JobMatchRequest(BaseModel):
    resume_skills:   list[str] = Field(..., description="Skills from the resume")
    job_description: str       = Field(..., description="Full job description text")

    model_config = {
        "json_schema_extra": {
            "example": {
                "resume_skills":   ["python", "sql", "pandas"],
                "job_description": "Looking for a Data Analyst with Python, SQL, Tableau...",
            }
        }
    }


class JobMatchResponse(BaseModel):
    overall_score:  int              = Field(..., ge=0, le=100)
    matched_skills: list[str]        = Field(default_factory=list)
    missing_skills: list[str]        = Field(default_factory=list)
    skill_scores:   dict[str, float] = Field(
        default_factory=dict,
        description="Per-skill cosine similarity score (0.0–1.0)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "overall_score":  62,
                "matched_skills": ["python", "sql", "pandas"],
                "missing_skills": ["tableau", "power bi"],
                "skill_scores":   {"python": 0.81, "sql": 0.74},
            }
        }
    }