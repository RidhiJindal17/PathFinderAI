"""
routers/analysis.py — PathFinder AI  ·  Combined Pipeline + MongoDB
====================================================================
The "one-stop" endpoint: upload a PDF, paste a JD, get a complete analysis.

Endpoints
---------
POST /api/analysis/full          Run the full 4-step pipeline, save to MongoDB
GET  /api/analysis/              List 10 most recent saved reports
GET  /api/analysis/{report_id}   Retrieve a saved report by UUID

Pipeline (POST /api/analysis/full)
-----------------------------------
Step 1  parse_resume()           PDF → skills / education / experience
Step 2  analyze_gap()            Sentence-BERT skill gap scoring
Step 3  generate_xai_roadmap()   Gemini XAI explanations + 4-week plan
Step 4  get_portfolio_summary()  GitHub portfolio (optional, non-fatal)
Step 5  save_report()            Persist to MongoDB, return report_id

Fault tolerance
---------------
- GitHub fetch is wrapped in a try/except — failure sets github_failed=True
  in pipeline_status but does NOT abort the response.
- Gemini errors are caught — roadmap fields are empty but the report still saves.
- MongoDB save failure is caught — report is still returned (without report_id saved).
- Overall 30-second asyncio.wait_for timeout on the entire pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from config import settings
from models.analysis import (
    BridgeSkillItem,
    CareerRoadmapItem,
    FullAnalysisResponse,
    PipelineStatus,
    ReportListItem,
    ReportListResponse,
    ResumeSummary,
    WeeklyPlanItem,
    XAIExplanation,
    MissingSkillDetailed,
    MissingSkillResource,
)
from services.database import get_report, list_reports, save_report
from services.gemini_service import generate_xai_roadmap, infer_required_skills
from services.github_service import get_portfolio_summary
from services.resume_parser import parse_resume
from services.skill_gap_analyzer import analyze_gap, extract_skills_from_jd
from services.resource_provider import generate_learning_path

logger = logging.getLogger(__name__)

router = APIRouter()

PIPELINE_TIMEOUT_SECS = 30   # overall timeout for the full pipeline


# ══════════════════════════════════════════════════════════════════════════════
#  INTERNAL PIPELINE RUNNER
# ══════════════════════════════════════════════════════════════════════════════

async def _run_pipeline(
    file_bytes: bytes,
    job_description: str,
    job_title: str,
    github_username: str | None,
) -> dict[str, Any]:
    """
    Execute the full PathFinder AI analysis pipeline and return a raw report dict.
    """
    status_tracker = PipelineStatus()
    report_id  = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    # ── Step 1: Parse Resume ──────────────────────────────────────────────────
    logger.info(f"[{report_id}] Step 1 — Parsing resume PDF …")
    resume_data = parse_resume(file_bytes)

    if resume_data.get("parse_status") == "error":
        raise ValueError(
            f"Could not extract text from the PDF: "
            f"{resume_data.get('error_detail', 'Unknown error')}. "
            "Please ensure the PDF is not scanned/image-only."
        )
    status_tracker.resume_parsed = True
    logger.info(f"[{report_id}] Step 1 ✅ — {len(resume_data.get('skills', []))} skills extracted")

    # ── Step 2: Hybrid Skill Extraction ───────────────────────────────────────
    logger.info(f"[{report_id}] Step 2 — Gathering job requirements (Hybrid) …")
    jd_skills = extract_skills_from_jd(job_description)
    
    # If the JD is too sparse (less than 3 skills identified), infer from job title
    if len(jd_skills) < 3:
        logger.info(f"[{report_id}] JD sparse ({len(jd_skills)} skills) — inferring from title: '{job_title}'")
        inferred = infer_required_skills(job_title)
        # Merge uniquely
        jd_skills = sorted(list(set(jd_skills + inferred)))
        logger.info(f"[{report_id}] Hybrid extraction complete — Total skills: {len(jd_skills)}")

    gap_data = analyze_gap(
        resume_skills=resume_data.get("skills", []),
        job_description=job_description,
        jd_skills=jd_skills,
    )
    status_tracker.gap_analyzed = True
    logger.info(
        f"[{report_id}] Step 2 ✅ — score: {gap_data['match_score']}/100, "
        f"bridge skills: {len(gap_data.get('bridge_skills', []))}"
    )

    # ── Step 3: XAI Roadmap via Gemini ───────────────────────────────────────
    logger.info(f"[{report_id}] Step 3 — Generating XAI roadmap via Gemini …")
    resume_context = {
        "skills":             resume_data.get("skills", []),
        "experience_summary": " ".join(resume_data.get("experience", []))[:500],
    }
    roadmap_data: dict[str, Any] = {}
    try:
        roadmap_data = generate_xai_roadmap(
            bridge_skills=gap_data.get("bridge_skills", []),
            resume_context=resume_context,
            job_title=job_title,
        )
        status_tracker.roadmap_generated = True
        logger.info(f"[{report_id}] Step 3 ✅ — roadmap generated")
    except Exception as exc:
        logger.warning(f"[{report_id}] Step 3 ⚠️  Gemini error (continuing): {exc}")
        roadmap_data = {
            "skill_explanations": [],
            "four_week_plan":     [],
            "confidence_message": "",
            "parse_error":        True,
        }

    # ── Step 4: GitHub Portfolio (optional, non-fatal) ────────────────────────
    github_data: dict | None = None
    if github_username and github_username.strip():
        logger.info(f"[{report_id}] Step 4 — Fetching GitHub portfolio for '{github_username}' …")
        try:
            github_data = await get_portfolio_summary(github_username.strip())
            status_tracker.github_fetched = True
            logger.info(f"[{report_id}] Step 4 ✅ — GitHub portfolio fetched")
        except Exception as exc:
            logger.warning(
                f"[{report_id}] Step 4 ⚠️  GitHub fetch failed (continuing): {exc}"
            )
            status_tracker.github_failed = True
            github_data = None
    else:
        status_tracker.github_skipped = True
        logger.info(f"[{report_id}] Step 4 — Skipped (no GitHub username provided)")

    # ── Assemble full report ──────────────────────────────────────────────────
    full_report: dict[str, Any] = {
        "report_id":  report_id,
        "created_at": created_at.isoformat(),
        "job_title":  job_title,

        # Gap analysis
        "match_score":    gap_data.get("match_score", 0),
        "matched_skills": gap_data.get("matched_skills", []),
        "bridge_skills":  gap_data.get("bridge_skills", []),

        # XAI roadmap (Legay)
        "xai_explanations":   roadmap_data.get("skill_explanations", []),
        "four_week_plan":     roadmap_data.get("four_week_plan", []),
        "confidence_message": roadmap_data.get("confidence_message", ""),

        # Upgraded Career Report
        "required_skills":         gap_data.get("job_skills_extracted", []),
        "missing_skills_detailed": roadmap_data.get("missing_skills_detailed", []),
        "resources":               [],   # Will be populated as final step
        "roadmap":                 roadmap_data.get("roadmap", []),
        "estimated_time":          roadmap_data.get("estimated_time", ""),
        "final_summary":           roadmap_data.get("final_summary", ""),
        "suitable_roles":          roadmap_data.get("suitable_roles", []),
        "confidence_score":        roadmap_data.get("confidence_score", ""),
        "skill_gap_percentage":    roadmap_data.get("skill_gap_percentage", 0),
        "analysis_note":           gap_data.get("analysis_note"),

        # Resume summary (lightweight)
        "resume_summary": {
            "name":             resume_data.get("name"),
            "email":            resume_data.get("email"),
            "skills":           resume_data.get("skills", []),
            "education_count":  len(resume_data.get("education", [])),
            "experience_count": len(resume_data.get("experience", [])),
            "projects_count":   len(resume_data.get("projects", [])),
        },

        # GitHub portfolio
        "github_portfolio": github_data,

        # Pipeline metadata
        "pipeline_status": status_tracker.model_dump(),
    }

    # ── Match Score Calibration ──────────────────────────────────────────────
    # If the AI identified real missing skills (bridge_skills or detailed list is non-empty)
    # but match_score is suspiciously high, we cap it.
    if (full_report["bridge_skills"] or full_report["missing_skills_detailed"]) and full_report["match_score"] >= 95:
        full_report["match_score"] = 85
    
    # If there are NO matched skills at all, match_score should be very low unless JD was empty
    if not full_report["matched_skills"] and full_report["bridge_skills"]:
        full_report["match_score"] = min(full_report["match_score"], 20)

    # ── Fallback for Missing Skills Detailed ──────────────────────────────────
    # If Gemini missed some skills but semantic search found them, don't leave it empty!
    if not full_report["missing_skills_detailed"] and full_report["bridge_skills"]:
        logger.info(f"[{report_id}] Applying semantic fallback for missing_skills_detailed")
        full_report["missing_skills_detailed"] = [
            {
               "skill": b["skill"],
               "why_important": "Critical requirement identified by Semantic Analysis.",
               "impact_if_missing": f"Gaps in {b['skill']} significantly reduce your role compatibility.",
               "priority": b["priority"].capitalize()
            }
            for b in full_report["bridge_skills"]
        ]

    # ── Final Resource Mapping (DOMAIN INDEPENDANT) ──────────────────────────
    # Map the finalized list of missing skills to our trusted learning links
    skill_names = [m["skill"] for m in full_report["missing_skills_detailed"]]
    full_report["resources"] = generate_learning_path(skill_names)
    
    # ── VERIFICATION ──────────────────────────────────────────────────────────
    logger.info(f"[{report_id}] VERIFICATION: resources count = {len(full_report['resources'])}")
    print(f"[{report_id}] VERIFICATION: Generated {len(full_report['resources'])} resource groups.")
    if full_report["resources"]:
        first = full_report["resources"][0]
        print(f"[{report_id}] VERIFICATION: First skill '{first['skill']}' has {len(first['resources'])} links.")

    # ── Step 5: Save to MongoDB ───────────────────────────────────────────────
    logger.info(f"[{report_id}] Step 5 — Saving report to MongoDB …")
    try:
        await save_report(full_report)
        status_tracker.report_saved = True
        full_report["pipeline_status"] = status_tracker.model_dump()
        logger.info(f"[{report_id}] Step 5 ✅ — Report saved")
    except Exception as exc:
        logger.warning(
            f"[{report_id}] Step 5 ⚠️  MongoDB save failed (returning anyway): {exc}"
        )

    return full_report


# ══════════════════════════════════════════════════════════════════════════════
#  POST /api/analysis/full
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/full",
    response_model=FullAnalysisResponse,
    summary="Run the complete PathFinder AI pipeline in a single request",
    responses={
        200: {"description": "Full analysis completed", "model": FullAnalysisResponse},
        400: {"description": "Invalid file or missing required fields"},
        408: {"description": "Pipeline timed out (30s limit)"},
        422: {"description": "Validation error"},
        500: {"description": "Internal pipeline error"},
    },
)
async def run_full_analysis(
    resume_file: UploadFile = File(
        ...,
        description="PDF resume file (max 5 MB)",
    ),
    job_description: str = Form(
        ...,
        description="Full text of the job description",
        min_length=20,
    ),
    job_title: str = Form(
        ...,
        description="Target job title (e.g. 'React Frontend Developer')",
        min_length=2,
    ),
    github_username: str = Form(
        default="",
        description="Optional GitHub username for portfolio evidence",
    ),
) -> FullAnalysisResponse:
    """
    **Run the complete PathFinder AI analysis pipeline in one request.**
    """
    filename = resume_file.filename or "resume.pdf"

    # ── File validation ───────────────────────────────────────────────────────
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are accepted. Received: '{filename}'",
        )

    file_bytes = await resume_file.read()

    if len(file_bytes) > settings.max_upload_size_bytes:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File is too large ({size_mb:.1f} MB). "
                f"Maximum allowed: {settings.max_upload_size_mb} MB."
            ),
        )

    if file_bytes[:4] != b"%PDF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file does not appear to be a valid PDF.",
        )

    logger.info(
        f"Full analysis request — job: '{job_title}', "
        f"file: '{filename}' ({len(file_bytes):,} bytes), "
        f"github: '{github_username or 'not provided'}'"
    )

    # ── Run pipeline with timeout ─────────────────────────────────────────────
    try:
        full_report = await asyncio.wait_for(
            _run_pipeline(
                file_bytes=file_bytes,
                job_description=job_description.strip(),
                job_title=job_title.strip(),
                github_username=github_username.strip() or None,
            ),
            timeout=PIPELINE_TIMEOUT_SECS,
        )
    except asyncio.TimeoutError:
        logger.error("Full analysis pipeline timed out after 30 seconds")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=(
                f"The analysis pipeline timed out after {PIPELINE_TIMEOUT_SECS} seconds. "
                "This can happen if the Gemini API is slow or the PDF is very large. "
                "Please try again."
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception(f"Unexpected pipeline error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred in the pipeline: {exc}",
        )

    # ── Deserialise into response model ───────────────────────────────────────
    return _build_response(full_report)


# ══════════════════════════════════════════════════════════════════════════════
#  GET /api/analysis/{report_id}
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{report_id}",
    response_model=FullAnalysisResponse,
    summary="Retrieve a saved analysis report by report_id",
)
async def get_analysis_report(report_id: str) -> FullAnalysisResponse:
    try:
        doc = await get_report(report_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not available: {exc}",
        )

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )

    return _build_response(doc)


# ══════════════════════════════════════════════════════════════════════════════
#  GET /api/analysis/
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/",
    response_model=ReportListResponse,
    summary="List the 10 most recent analysis reports",
)
async def list_analysis_reports(limit: int = 10) -> ReportListResponse:
    try:
        docs = await list_reports(limit=limit)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not available: {exc}",
        )

    items = [
        ReportListItem(
            report_id    = doc.get("report_id", ""),
            created_at   = doc.get("created_at", ""),
            job_title    = doc.get("job_title", ""),
            match_score  = doc.get("match_score", 0),
            candidate_name = doc.get("resume_summary", {}).get("name"),
            bridge_count = len(doc.get("bridge_skills", [])),
        )
        for doc in docs
    ]

    return ReportListResponse(count=len(items), reports=items)


# ══════════════════════════════════════════════════════════════════════════════
#  RESPONSE BUILDER HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _build_response(doc: dict) -> FullAnalysisResponse:
    """
    Convert a raw report dict into a validated FullAnalysisResponse Pydantic object.
    """
    # Bridge skills
    bridge_skills = [
        BridgeSkillItem(**bs) if isinstance(bs, dict) else bs
        for bs in doc.get("bridge_skills", [])
    ]

    # XAI explanations
    xai_raw = doc.get("xai_explanations") or doc.get("skill_explanations", [])
    xai_explanations = [
        XAIExplanation(**x) if isinstance(x, dict) else x
        for x in xai_raw
    ]

    # Weekly plan
    plan_raw = doc.get("four_week_plan", [])
    four_week_plan = [
        WeeklyPlanItem(**w) if isinstance(w, dict) else w
        for w in plan_raw
    ]

    # New Career Guide fields
    missing_detailed_raw = doc.get("missing_skills_detailed", [])
    missing_skills_detailed = [
        MissingSkillDetailed(**m) if isinstance(m, dict) else m
        for m in missing_detailed_raw
    ]

    resources_raw = doc.get("resources", [])
    resources = [
        MissingSkillResource(**r) if isinstance(r, dict) else r
        for r in resources_raw
    ]

    roadmap_raw = doc.get("roadmap", [])
    roadmap = [
        CareerRoadmapItem(**rm) if isinstance(rm, dict) else rm
        for rm in roadmap_raw
    ]

    # Resume summary
    rs_raw = doc.get("resume_summary") or {}
    resume_summary = ResumeSummary(**rs_raw) if isinstance(rs_raw, dict) else ResumeSummary()

    # Pipeline status
    ps_raw = doc.get("pipeline_status") or {}
    pipeline_status = PipelineStatus(**ps_raw) if isinstance(ps_raw, dict) else PipelineStatus()

    return FullAnalysisResponse(
        report_id               = doc.get("report_id", ""),
        created_at              = str(doc.get("created_at", "")),
        job_title               = doc.get("job_title", ""),
        match_score             = int(doc.get("match_score", 0)),
        matched_skills          = doc.get("matched_skills", []),
        bridge_skills           = bridge_skills,
        xai_explanations        = xai_explanations,
        four_week_plan          = four_week_plan,
        confidence_message      = doc.get("confidence_message", ""),
        
        missing_skills_detailed = missing_skills_detailed,
        resources               = resources,
        roadmap                 = roadmap,
        estimated_time          = doc.get("estimated_time", ""),
        final_summary           = doc.get("final_summary", ""),
        suitable_roles          = doc.get("suitable_roles", []),
        confidence_score        = doc.get("confidence_score", ""),
        skill_gap_percentage    = doc.get("skill_gap_percentage", 0),

        resume_summary          = resume_summary,
        github_portfolio        = doc.get("github_portfolio"),
        pipeline_status         = pipeline_status,
    )