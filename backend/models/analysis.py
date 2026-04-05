"""
models/analysis.py — PathFinder AI  ·  Combined Pipeline + MongoDB
===================================================================
Pydantic v2 schemas for:
    POST /api/analysis/full    (full pipeline)
    GET  /api/analysis/{id}    (retrieve report)
    GET  /api/analysis/        (list reports)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════════════
#  PIPELINE STATUS — tracks which steps completed
# ══════════════════════════════════════════════════════════════════════════════

class PipelineStatus(BaseModel):
    """
    Step-by-step completion tracking for the full analysis pipeline.
    Each field is True once that step finishes successfully.
    """
    resume_parsed:    bool = Field(default=False, description="Step 1: PDF parsed + NLP complete")
    gap_analyzed:     bool = Field(default=False, description="Step 2: Skill gap computed")
    roadmap_generated:bool = Field(default=False, description="Step 3: Gemini XAI roadmap generated")
    github_fetched:   bool = Field(default=False, description="Step 4: GitHub portfolio fetched (optional)")
    report_saved:     bool = Field(default=False, description="Step 5: Report saved to MongoDB")
    github_skipped:   bool = Field(default=False, description="True if no github_username was provided")
    github_failed:    bool = Field(default=False, description="True if GitHub fetch failed (non-fatal)")


# ══════════════════════════════════════════════════════════════════════════════
#  RESUME SUMMARY  (lightweight subset stored in the report)
# ══════════════════════════════════════════════════════════════════════════════

class ResumeSummary(BaseModel):
    """Lightweight resume snapshot stored inside the full report."""

    name:             str | None  = Field(default=None)
    email:            str | None  = Field(default=None)
    skills:           list[str]   = Field(default_factory=list)
    education_count:  int         = Field(default=0, ge=0)
    experience_count: int         = Field(default=0, ge=0)
    projects_count:   int         = Field(default=0, ge=0)


# ══════════════════════════════════════════════════════════════════════════════
#  BRIDGE SKILL  (re-used from gap analysis output)
# ══════════════════════════════════════════════════════════════════════════════

class BridgeSkillItem(BaseModel):
    skill:            str   = Field(...)
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    priority:         str   = Field(default="high")


# ══════════════════════════════════════════════════════════════════════════════
#  XAI EXPLANATION  (per-skill roadmap entry)
# ══════════════════════════════════════════════════════════════════════════════

class XAIExplanation(BaseModel):
    skill:           str = Field(...)
    why_needed:      str = Field(default="")
    youtube_query:   str = Field(default="")
    estimated_weeks: int = Field(default=2, ge=1, le=4)
    difficulty:      str = Field(default="beginner")

class MissingSkillDetailed(BaseModel):
    skill:             str = Field(...)
    why_important:     str = Field(default="", description="Why this skill matters for the role")
    impact_if_missing: str = Field(default="", description="Career impact if this skill is missing")
    priority:          str = Field(default="High")

class ResourceLink(BaseModel):
    title: str = Field(..., description="E.g. 'React Full Course (YouTube)'")
    url:   str = Field(..., description="Google/YouTube search URL")
    type:  str = Field(..., description="'video' | 'article' | 'docs'")

class MissingSkillResource(BaseModel):
    skill:          str = Field(...)
    estimated_time: str = Field(default="2-4 weeks")
    resources:      list[ResourceLink] = Field(default_factory=list)

# ══════════════════════════════════════════════════════════════════════════════
#  WEEKLY PLAN ITEM
# ══════════════════════════════════════════════════════════════════════════════

class CareerResource(BaseModel):
    title: str = Field(..., description="E.g. 'React for Beginners by freeCodeCamp'")
    link:  str = Field(..., description="A direct URL or meaningful search query")

class CareerRoadmapItem(BaseModel):
    stage:     str = Field(..., description="Beginner | Intermediate | Advanced")
    skills:    list[str] = Field(default_factory=list)
    duration:  str = Field(..., description="e.g. '2 weeks'")
    topics:    list[str] = Field(default_factory=list)
    resources: list[CareerResource] = Field(default_factory=list)

class WeeklyPlanItem(BaseModel):
    week:               int = Field(..., ge=1, le=4)
    focus:              str = Field(...)
    goal:               str = Field(...)
    daily_time_minutes: int = Field(default=120, ge=15, le=480)


# ══════════════════════════════════════════════════════════════════════════════
#  FULL REPORT RESPONSE
# ══════════════════════════════════════════════════════════════════════════════

class FullAnalysisResponse(BaseModel):
    """
    Complete analysis report returned by POST /api/analysis/full
    and by GET /api/analysis/{report_id}.

    This is the single source of truth for what a "PathFinder AI report" contains.
    It is also the document stored in MongoDB (minus pipeline_status which is
    response-only metadata).
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    report_id:  str      = Field(..., description="UUID4 string — use to retrieve this report.")
    created_at: str      = Field(..., description="ISO-8601 UTC timestamp of report creation.")
    job_title:  str      = Field(..., description="Target job title the candidate is pursuing.")

    # ── Gap Analysis ──────────────────────────────────────────────────────────
    match_score:      int             = Field(..., ge=0, le=100,
                                             description="0–100 overall skill coverage score.")
    matched_skills:   list[str]       = Field(default_factory=list)
    bridge_skills:    list[BridgeSkillItem] = Field(default_factory=list)

    # ── XAI Roadmap (Backward Compatibility) ──────────────────────────────────
    xai_explanations:   list[XAIExplanation]  = Field(default_factory=list)
    four_week_plan:     list[WeeklyPlanItem]  = Field(default_factory=list)
    confidence_message: str                   = Field(default="")
    
    # ── Upgraded Career Report (NEW) ──────────────────────────────────────────
    required_skills:         list[str]                  = Field(default_factory=list, description="Consolidated list of skills required for this job")
    missing_skills_detailed: list[MissingSkillDetailed] = Field(default_factory=list)
    resources:               list[MissingSkillResource] = Field(default_factory=list)
    roadmap:                 list[CareerRoadmapItem]    = Field(default_factory=list)
    estimated_time:          str                        = Field(default="")
    final_summary:           str                        = Field(default="", description="Mentor summary of why you are not job-ready yet")
    suitable_roles:          list[str]                  = Field(default_factory=list, description="Alternative roles based on resume skills")
    confidence_score:        str                        = Field(default="")
    skill_gap_percentage:    int                        = Field(default=0, ge=0, le=100)
    analysis_note:           str | None                 = Field(default=None)

    # ── Resume Summary ────────────────────────────────────────────────────────
    resume_summary: ResumeSummary = Field(default_factory=ResumeSummary)

    # ── GitHub Portfolio ──────────────────────────────────────────────────────
    github_portfolio: dict[str, Any] | None = Field(
        default=None,
        description="GitHub portfolio summary, or null if username not provided / fetch failed.",
    )

    # ── Pipeline Metadata ─────────────────────────────────────────────────────
    pipeline_status: PipelineStatus = Field(
        default_factory=PipelineStatus,
        description="Which pipeline steps completed. Useful for debugging partial failures.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_id":   "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "created_at":  "2025-01-15T10:30:00+00:00",
                "job_title":   "React Frontend Developer",
                "match_score": 34,
                "matched_skills":   ["python", "sql", "git"],
                "missing_skills_detailed": [
                    {
                        "skill": "React",
                        "why_needed": "Used for building frontend UI in modern web apps",
                        "impact_if_missing": "You cannot build interactive web applications required for this role",
                        "priority": "High"
                    }
                ],
                "resources": [
                    {
                        "skill": "React",
                        "youtube_video": "https://www.youtube.com/watch?v=Ke90Tje7VS0",
                        "course": "https://www.freecodecamp.org/learn/front-end-development-libraries/react/",
                        "documentation": "https://react.dev"
                    }
                ],
                "roadmap": [
                    {
                        "stage": "Beginner",
                        "skills": ["HTML", "CSS", "JS Basics"],
                        "duration": "2 weeks"
                    },
                    {
                        "stage": "Intermediate",
                        "skills": ["React Hooks", "State Management"],
                        "duration": "1 month"
                    }
                ],
                "estimated_time": "With 2–3 hours daily, you can become job-ready in 2–3 months",
                "confidence_score": "Your foundational knowledge is strong, but React is critical.",
                "resume_summary": {
                    "name":             "Priya Sharma",
                    "email":            "priya@example.com",
                    "skills":           ["python", "sql", "html", "css"],
                    "education_count":  1,
                    "experience_count": 2,
                    "projects_count":   2,
                },
                "github_portfolio": None,
                "pipeline_status": {
                    "resume_parsed":     True,
                    "gap_analyzed":      True,
                    "roadmap_generated": True,
                    "github_fetched":    False,
                    "report_saved":      True,
                    "github_skipped":    True,
                    "github_failed":     False,
                },
            }
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT LIST ITEM  (lightweight summary for GET /api/analysis/)
# ══════════════════════════════════════════════════════════════════════════════

class ReportListItem(BaseModel):
    """Lightweight report summary for the listing endpoint."""

    report_id:    str      = Field(...)
    created_at:   str      = Field(...)
    job_title:    str      = Field(...)
    match_score:  int      = Field(...)
    candidate_name: str | None = Field(default=None)
    bridge_count: int      = Field(default=0, description="Number of bridge skills to close.")


class ReportListResponse(BaseModel):
    """Response for GET /api/analysis/."""

    count:   int                  = Field(...)
    reports: list[ReportListItem] = Field(default_factory=list)