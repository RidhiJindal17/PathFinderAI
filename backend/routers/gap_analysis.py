"""
routers/gap_analysis.py — PathFinder AI  ·  Module II: Semantic Skill-Gap Analyzer
====================================================================================
HTTP routing for the skill-gap analysis feature.

Endpoints
---------
POST /api/gap/analyze
    Accepts {resume_skills, job_description}.
    Delegates to services/skill_gap_analyzer.analyze_gap().
    Returns a GapAnalysisResponse with match_score, matched_skills,
    bridge_skills (ranked), and job_skills_extracted.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from models.gap_analysis import GapAnalysisRequest, GapAnalysisResponse, BridgeSkill
from services.skill_gap_analyzer import analyze_gap

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=GapAnalysisResponse,
    summary="Analyze the skill gap between a resume and a job description",
    responses={
        200: {
            "description": "Gap analysis completed successfully",
            "model": GapAnalysisResponse,
        },
        422: {"description": "Validation error — job_description too short or missing fields"},
        500: {"description": "Internal error during embedding / analysis"},
    },
)
async def analyze_skill_gap(payload: GapAnalysisRequest) -> GapAnalysisResponse:
    """
    **Semantic Skill-Gap Analysis — the core of PathFinder AI.**

    ### What happens under the hood

    1. **JD skill extraction** — spaCy + keyword-bank scan identifies all
       skills mentioned in the job description.
    2. **Sentence-BERT encoding** — every resume skill and every JD skill is
       converted to a 384-dimensional dense vector using `all-MiniLM-L6-v2`.
    3. **Cosine-similarity matrix** — we compute pairwise similarity between
       all resume skills × all JD skills in a single batch operation.
    4. **Coverage scoring** — for each JD skill, we take the *best* match from
       the resume (max over all resume skill similarities).
    5. **Classification**:
       - Coverage ≥ 0.65 → **matched**
       - Coverage < 0.65 → **bridge skill** (gap to close)
    6. **Priority ranking** — bridge skills are sorted by urgency:
       - `high` (similarity < 0.30) — skill is almost completely absent
       - `medium` (0.30–0.50) — partial domain overlap
       - `low` (0.50–0.65) — close miss; candidate has a related skill

    ### Edge cases handled
    - Empty `resume_skills` → `match_score: 0`, all JD skills become high-priority bridges.
    - JD with no recognisable skill keywords → `match_score: 0` with an `analysis_note`.

    ### Typical usage flow
    ```
    POST /api/resume/parse   →   get resume_skills list
    POST /api/gap/analyze    →   pass resume_skills + job_description
    POST /api/feedback/generate  →  pass bridge_skills to Gemini for roadmap
    ```
    """
    logger.info(
        f"Gap analysis request — resume skills: {len(payload.resume_skills)}, "
        f"JD length: {len(payload.job_description)} chars"
    )

    try:
        result: dict = analyze_gap(
            resume_skills=payload.resume_skills,
            job_description=payload.job_description,
        )
    except RuntimeError as exc:
        # RuntimeError is raised when the SBERT model fails to load
        logger.error(f"Model load error during gap analysis: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The semantic analysis model could not be loaded. "
                f"Please check server logs. Detail: {exc}"
            ),
        )
    except Exception as exc:
        logger.exception(f"Unexpected error during gap analysis: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during analysis: {exc}",
        )

    # Deserialise bridge_skills dicts into BridgeSkill Pydantic objects
    bridge_skill_objects = [BridgeSkill(**bs) for bs in result.get("bridge_skills", [])]

    return GapAnalysisResponse(
        match_score          = result["match_score"],
        matched_skills       = result["matched_skills"],
        bridge_skills        = bridge_skill_objects,
        job_skills_extracted = result["job_skills_extracted"],
        total_job_skills     = result["total_job_skills"],
        total_resume_skills  = result["total_resume_skills"],
        analysis_note        = result.get("analysis_note"),
    )