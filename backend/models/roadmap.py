"""
models/roadmap.py — PathFinder AI  ·  Module III: XAI Feedback & Roadmap Generator
====================================================================================
Pydantic v2 request/response schemas for:
    POST /api/roadmap/generate   (XAI roadmap)
    POST /api/roadmap/translate  (Corporate Translator)
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED INPUT TYPES
# ══════════════════════════════════════════════════════════════════════════════

class BridgeSkillInput(BaseModel):
    """
    A single bridge-skill entry as produced by Module II's analyze_gap().
    Passed inside RoadmapRequest.bridge_skills.
    """
    skill: str = Field(..., description="Skill name, e.g. 'react'")
    similarity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Best cosine similarity from Module II (0.0 = completely absent).",
    )
    priority: str = Field(
        default="high",
        description="Gap urgency tier: 'high' | 'medium' | 'low'",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  ROADMAP REQUEST
# ══════════════════════════════════════════════════════════════════════════════

class RoadmapRequest(BaseModel):
    """
    Body for POST /api/roadmap/generate.

    Designed to accept the direct output of Module II's POST /api/gap/analyze
    response — just pass bridge_skills and append resume_skills + job_title.
    """
    bridge_skills: list[BridgeSkillInput] = Field(
        default_factory=list,
        description=(
            "Bridge skills from Module II's gap analysis. "
            "May be empty if the candidate is already a strong match."
        ),
    )
    resume_skills: list[str] = Field(
        default_factory=list,
        description="Skills extracted from the resume (Module I output).",
    )
    job_title: str = Field(
        ...,
        min_length=2,
        description="Target job title, e.g. 'React Frontend Developer'.",
    )
    experience_summary: str = Field(
        default="",
        description=(
            "Optional: brief summary of the candidate's work / project experience. "
            "Helps Gemini tailor the roadmap to the student's actual level."
        ),
    )

    @field_validator("resume_skills", mode="before")
    @classmethod
    def normalise_skills(cls, v: list) -> list[str]:
        """Strip whitespace and drop empty strings."""
        return [s.strip() for s in v if isinstance(s, str) and s.strip()]

    @field_validator("job_title", mode="before")
    @classmethod
    def strip_job_title(cls, v: str) -> str:
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "bridge_skills": [
                    {"skill": "react",      "similarity_score": 0.18, "priority": "high"},
                    {"skill": "typescript", "similarity_score": 0.21, "priority": "high"},
                    {"skill": "node.js",    "similarity_score": 0.36, "priority": "medium"},
                ],
                "resume_skills": ["python", "sql", "html", "css"],
                "job_title": "React Frontend Developer",
                "experience_summary": "Built two personal projects using HTML, CSS, Python Flask.",
            }
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
#  ROADMAP RESPONSE
# ══════════════════════════════════════════════════════════════════════════════

class SkillExplanation(BaseModel):
    """XAI explanation and learning metadata for one bridge skill."""

    skill: str = Field(..., description="The skill name.")
    why_needed: str = Field(
        ...,
        description=(
            "One sentence explaining exactly why this skill is required "
            "for the target role. This is the XAI (explainability) component."
        ),
    )
    youtube_query: str = Field(
        ...,
        description=(
            "A search query to paste into YouTube to find a free beginner course. "
            'Format: "<skill> for beginners full course free 2024"'
        ),
    )
    estimated_weeks: int = Field(
        ...,
        ge=1,
        le=4,
        description="Realistic weeks to reach working knowledge at ~1 hour/day.",
    )
    difficulty: str = Field(
        ...,
        description=(
            "Difficulty relative to the student's current level. "
            "'beginner' | 'intermediate' | 'advanced'"
        ),
    )


class WeeklyPlan(BaseModel):
    """One week in the 4-week learning plan."""

    week: int = Field(..., ge=1, le=4, description="Week number (1–4).")
    focus: str = Field(..., description="Skill(s) to study this week.")
    goal: str = Field(..., description="One specific, measurable learning goal for the week.")
    daily_time_minutes: int = Field(
        ...,
        ge=15,
        le=240,
        description="Recommended daily study time in minutes.",
    )


class RoadmapResponse(BaseModel):
    """
    Full response from POST /api/roadmap/generate.

    Fields
    ------
    skill_explanations
        One entry per bridge skill — XAI reason, YouTube query, time estimate,
        and difficulty tier.

    four_week_plan
        An ordered 4-week schedule distributing the bridge skills into
        logical, weekly learning milestones.

    confidence_message
        A single personalised, encouraging sentence for the candidate.

    no_gaps_found
        True when the input bridge_skills list was empty (perfect match scenario).

    parse_error
        True if Gemini's response could not be parsed as JSON.
        When True, error_message will contain details.

    error_message
        Populated only on API or parse errors.
    """
    skill_explanations: list[SkillExplanation] = Field(default_factory=list)
    four_week_plan:     list[WeeklyPlan]        = Field(default_factory=list)
    confidence_message: str                     = Field(default="")
    no_gaps_found:      bool                    = Field(default=False)
    parse_error:        bool                    = Field(default=False)
    error_message:      str | None              = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "example": {
                "skill_explanations": [
                    {
                        "skill": "react",
                        "why_needed": "React is the primary UI library used to build interactive, component-based interfaces in modern frontend developer roles.",
                        "youtube_query": "react for beginners full course free 2024",
                        "estimated_weeks": 3,
                        "difficulty": "beginner",
                    },
                    {
                        "skill": "typescript",
                        "why_needed": "TypeScript adds static typing to JavaScript, reducing bugs and making large codebases more maintainable — a must for professional React projects.",
                        "youtube_query": "typescript for beginners full course free 2024",
                        "estimated_weeks": 2,
                        "difficulty": "beginner",
                    },
                ],
                "four_week_plan": [
                    {
                        "week": 1,
                        "focus": "React fundamentals",
                        "goal": "Build a working to-do app using React hooks (useState, useEffect)",
                        "daily_time_minutes": 60,
                    },
                    {
                        "week": 2,
                        "focus": "TypeScript basics",
                        "goal": "Rewrite the to-do app in TypeScript with proper type annotations",
                        "daily_time_minutes": 60,
                    },
                    {
                        "week": 3,
                        "focus": "Node.js + REST APIs",
                        "goal": "Build a simple Express API with 3 endpoints and connect it to the React app",
                        "daily_time_minutes": 75,
                    },
                    {
                        "week": 4,
                        "focus": "Portfolio project",
                        "goal": "Deploy a full-stack mini app on Vercel/Railway and push code to GitHub",
                        "daily_time_minutes": 90,
                    },
                ],
                "confidence_message": "With your Python and SQL foundation you're already thinking like a developer — mastering React and TypeScript will open the door to your first frontend role very soon!",
                "no_gaps_found": False,
                "parse_error": False,
                "error_message": None,
            }
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
#  CORPORATE TRANSLATOR REQUEST / RESPONSE
# ══════════════════════════════════════════════════════════════════════════════

class TranslateRequest(BaseModel):
    """Body for POST /api/roadmap/translate."""

    informal_text: str = Field(
        ...,
        min_length=5,
        description="The candidate's informal description of their experience.",
    )

    @field_validator("informal_text", mode="before")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "informal_text": "I fixed my neighbor's computer when it was slow"
            }
        }
    }


class TranslateResponse(BaseModel):
    """Response from POST /api/roadmap/translate."""

    original_text:    str  = Field(..., description="The original informal input.")
    polished_text:    str  = Field(..., description="The high-impact, professional rewrite.")
    professional_text: str = Field(
        ...,
        description="Backward-compatible field for the rewritten bullet point.",
    )
    tone:             str  = Field(default="professional", description="The tone of the rewrite.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "original_text": "I fixed my neighbor's computer when it was slow",
                "polished_text": (
                    "Diagnosed and resolved system performance issues for ~3 local clients, "
                    "restoring full functionality and reducing downtime by ~60%."
                ),
                "professional_text": (
                    "Diagnosed and resolved system performance issues for ~3 local clients, "
                    "restoring full functionality and reducing downtime by ~60%."
                ),
                "tone": "professional"
            }
        }
    }