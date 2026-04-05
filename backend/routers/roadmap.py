"""
routers/roadmap.py — PathFinder AI  ·  Module III: XAI Feedback & Roadmap Generator
=====================================================================================
HTTP routing for two endpoints:

    POST /api/roadmap/generate   — XAI skill explanations + 4-week learning plan
    POST /api/roadmap/translate  — Corporate Translator (informal → professional)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from models.roadmap import (
    RoadmapRequest,
    RoadmapResponse,
    SkillExplanation,
    WeeklyPlan,
    TranslateRequest,
    TranslateResponse,
)
from services.gemini_service import generate_xai_roadmap, translate_to_professional

logger = logging.getLogger(__name__)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
#  POST /api/roadmap/generate
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/generate",
    response_model=RoadmapResponse,
    summary="Generate XAI feedback and a 4-week learning roadmap via Gemini",
    responses={
        200: {"description": "Roadmap generated successfully", "model": RoadmapResponse},
        422: {"description": "Validation error — job_title missing or too short"},
        503: {"description": "Gemini API unavailable — check GEMINI_API_KEY"},
    },
)
async def generate_roadmap(payload: RoadmapRequest) -> RoadmapResponse:
    """
    **Generate an XAI-driven learning roadmap using Google Gemini 2.5 Flash.**

    ### What this endpoint does

    1. Receives the `bridge_skills` list from Module II's gap analysis.
    2. Builds a carefully engineered prompt with the student's context.
    3. Calls Gemini to produce:
       - **Per-skill explanations** — *why* each skill is needed (XAI),
         a YouTube search query for a free course, estimated weeks, and difficulty.
       - **4-week plan** — a week-by-week schedule with measurable goals.
       - **Confidence message** — personalised encouragement.
    4. Strips any Markdown fences from the response and parses JSON safely.

    ### Empty bridge_skills (perfect match scenario)
    If `bridge_skills` is empty, the API returns immediately with
    `no_gaps_found: true` and a congratulatory message — no Gemini call needed.

    ### Typical flow
    ```
    POST /api/resume/parse        →  get resume_skills, experience
    POST /api/gap/analyze         →  get bridge_skills, match_score
    POST /api/roadmap/generate    →  get xai explanations + 4-week plan
    ```

    ### Error handling
    - Returns `parse_error: true` in the response body (not HTTP 500) if
      Gemini's JSON cannot be parsed — so the frontend can show a retry message.
    - Returns HTTP 503 only if the Gemini API key is missing or the model fails
      to load entirely.
    """
    logger.info(
        f"Roadmap request — job: '{payload.job_title}', "
        f"bridge skills: {len(payload.bridge_skills)}, "
        f"resume skills: {len(payload.resume_skills)}"
    )

    # Serialise BridgeSkillInput objects → plain dicts for the service layer
    bridge_dicts = [bs.model_dump() for bs in payload.bridge_skills]

    # Build the resume_context dict the service expects
    resume_context = {
        "skills":             payload.resume_skills,
        "experience_summary": payload.experience_summary,
    }

    try:
        result: dict = generate_xai_roadmap(
            bridge_skills=bridge_dicts,
            resume_context=resume_context,
            job_title=payload.job_title,
        )
    except ValueError as exc:
        # ValueError is raised by get_gemini_client() when the API key is missing
        logger.error(f"Gemini configuration error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Gemini API is not configured: {exc}. "
                "Set GEMINI_API_KEY in your .env file."
            ),
        )
    except Exception as exc:
        logger.exception(f"Unexpected error in generate_roadmap: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {exc}",
        )

    # ── Deserialise into Pydantic objects ─────────────────────────────────────
    skill_exp_objects = [
        SkillExplanation(**se)
        for se in result.get("skill_explanations", [])
        if isinstance(se, dict) and not result.get("parse_error")
    ]
    weekly_plan_objects = [
        WeeklyPlan(**wp)
        for wp in result.get("four_week_plan", [])
        if isinstance(wp, dict) and not result.get("parse_error")
    ]

    return RoadmapResponse(
        skill_explanations = skill_exp_objects,
        four_week_plan     = weekly_plan_objects,
        confidence_message = result.get("confidence_message", ""),
        no_gaps_found      = result.get("no_gaps_found", False),
        parse_error        = result.get("parse_error", False),
        error_message      = result.get("error_message"),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  POST /api/roadmap/translate
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/translate",
    response_model=TranslateResponse,
    summary="Rewrite informal experience as a professional resume bullet point",
    responses={
        200: {"description": "Text translated successfully", "model": TranslateResponse},
        422: {"description": "informal_text too short or missing"},
        503: {"description": "Gemini API unavailable"},
    },
)
async def corporate_translator(payload: TranslateRequest) -> TranslateResponse:
    """
    **Corporate Translator — turn informal work descriptions into resume gold.**

    Submits the candidate's informal text to Gemini with a carefully engineered
    prompt that instructs it to:

    - Start with a strong past-tense **action verb**
    - Keep it to **one sentence** (max 25 words)
    - Add **measurable outcomes** where implied (with `~` for estimates)
    - Remove first-person pronouns (ATS-friendly)
    - Sound professional without exaggerating

    ### Example

    | Input | Output |
    |---|---|
    | *"I fixed my neighbor's computer when it was slow"* | *"Diagnosed and resolved system performance issues for ~3 local clients, restoring full functionality and reducing downtime by ~60%."* |
    | *"helped my college run the annual fest"* | *"Coordinated logistics and volunteer management for a ~500-attendee college annual fest, ensuring smooth event execution."* |

    ### Error handling
    Returns a descriptive error string in `professional_text` (not HTTP 500)
    if the Gemini API is temporarily unavailable — so the UI can show it inline.
    """
    logger.info(f"Translate request — input length: {len(payload.informal_text)} chars")

    try:
        result = translate_to_professional(payload.informal_text)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gemini API not configured: {exc}",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error in corporate_translator: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {exc}",
        )

    return TranslateResponse(
        original_text     = payload.informal_text,
        polished_text     = result["polished_text"],
        professional_text = result["polished_text"],
        tone              = result["tone"],
    )