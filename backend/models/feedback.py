"""
models/feedback.py — PathFinder AI
Pydantic schemas for the AI Feedback feature (legacy stub — core feedback
is now handled by models/roadmap.py and models/analysis.py).
Kept for backwards compatibility with any existing router references.
"""

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    resume_skills:  list[str] = Field(..., description="Skills from the resume")
    missing_skills: list[str] = Field(..., description="Skills identified as gaps")
    job_title:      str       = Field(..., description="Target job title")
    match_score:    int       = Field(..., ge=0, le=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "resume_skills":  ["python", "sql"],
                "missing_skills": ["react", "typescript"],
                "job_title":      "Frontend Developer",
                "match_score":    40,
            }
        }
    }


class FeedbackResponse(BaseModel):
    xai_explanation:   str = Field(default="", description="Why skills are needed")
    learning_roadmap:  str = Field(default="", description="Free resource roadmap")
    motivational_tip:  str = Field(default="", description="Encouraging message")
    raw_response:      str = Field(default="", description="Raw Gemini output")