"""
routers/feedback.py — PathFinder AI
Legacy feedback endpoint — core XAI feedback is at POST /api/roadmap/generate.
This endpoint provides a simplified feedback call for backwards compatibility.
"""

from fastapi import APIRouter, HTTPException, status
from models.feedback import FeedbackRequest, FeedbackResponse
from services.gemini_service import generate_xai_roadmap

router = APIRouter()


@router.post(
    "/generate",
    response_model=FeedbackResponse,
    summary="Generate AI feedback for skill gaps (legacy — prefer /api/roadmap/generate)",
)
async def generate_feedback(payload: FeedbackRequest):
    """
    Simplified feedback endpoint.
    For full XAI explanations + 4-week plan, use POST /api/roadmap/generate instead.
    """
    bridge_skills = [
        {"skill": s, "similarity_score": 0.0, "priority": "high"}
        for s in payload.missing_skills
    ]
    resume_context = {
        "skills":             payload.resume_skills,
        "experience_summary": "",
    }
    try:
        result = generate_xai_roadmap(
            bridge_skills=bridge_skills,
            resume_context=resume_context,
            job_title=payload.job_title,
        )
        explanations = result.get("skill_explanations", [])
        roadmap_text = "\n".join(
            f"Week {w['week']}: {w['focus']} — {w['goal']}"
            for w in result.get("four_week_plan", [])
        )
        return FeedbackResponse(
            xai_explanation  = "; ".join(e.get("why_needed", "") for e in explanations),
            learning_roadmap = roadmap_text,
            motivational_tip = result.get("confidence_message", ""),
            raw_response     = "",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error: {exc}",
        )