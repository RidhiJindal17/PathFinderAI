"""
main.py — PathFinder AI
FastAPI application entry point.
Run with: uvicorn main:app --reload
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings

from routers.resume import router as resume_router
from routers.feedback import router as feedback_router
from routers.github import router as github_router
from routers.youtube import router as youtube_router
from routers.translator import router as translator_router
from routers.gap_analysis import router as gap_analysis_router
from routers.roadmap import router as roadmap_router
from routers.analysis import router as analysis_router

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if not settings.is_production else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pathfinder")


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code before `yield` runs on startup.
    Code after `yield` runs on shutdown.
    """
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("🚀 PathFinder AI starting up …")

    # Ensure the upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"📁 Upload directory ready: {settings.upload_dir}")

    # Connect to MongoDB
    try:
        from services.database import connect_db
        await connect_db()
        logger.info("✅ MongoDB connection established")
    except Exception as exc:
        logger.warning(f"⚠️  MongoDB not connected (continuing anyway): {exc}")

    # Warm-up NLP models so the first real request isn't slow
    try:
        from services.resume_parser import _get_nlp
        _get_nlp()
        logger.info("✅ spaCy model loaded and cached")
    except Exception as exc:
        logger.warning(f"⚠️  spaCy model warm-up failed (will retry on first request): {exc}")

    try:
        from services.skill_gap_analyzer import load_model
        load_model()
        logger.info("✅ Sentence-BERT model (skill_gap_analyzer) loaded and cached")
    except Exception as exc:
        logger.warning(f"⚠️  Sentence-BERT warm-up failed (will retry on first request): {exc}")

    try:
        from services.gemini_service import get_gemini_client
        get_gemini_client()
        logger.info("✅ Gemini client configured and cached")
    except ValueError:
        logger.warning("⚠️  GEMINI_API_KEY not set — Gemini features will be unavailable")
    except Exception as exc:
        logger.warning(f"⚠️  Gemini warm-up failed: {exc}")

    yield  # ── Application runs here ─────────────────────────────────────────

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("🛑 PathFinder AI shutting down …")
    try:
        from services.database import disconnect_db
        await disconnect_db()
    except Exception:
        pass


# ── FastAPI app instance ───────────────────────────────────────────────────────
app = FastAPI(
    title="PathFinder AI",
    description=(
        "AI-powered career navigation system for underprivileged job seekers. "
        "Resume parsing · Skill gap analysis · XAI feedback · Learning roadmaps."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
    lifespan=lifespan,
)


# ── CORS Middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,   # reads from ALLOWED_ORIGINS in .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Core routes ───────────────────────────────────────────────────────────────
@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    response_description="Service is alive",
)
async def health_check():
    """
    Quick health check endpoint used by load balancers and CI pipelines.
    Returns HTTP 200 when the server is up and running.
    """
    return {"status": "ok", "project": "PathFinder AI"}


@app.get("/api/report/{report_id}", tags=["Full Analysis"])
async def get_report_shortcut(report_id: str):
    """
    Synonym for GET /api/analysis/{report_id} as requested for easier integration.
    """
    from routers.analysis import get_analysis_report
    return await get_analysis_report(report_id)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return JSONResponse(
        content={
            "message": "Welcome to PathFinder AI 🧭",
            "docs": "/docs",
            "health": "/health",
        }
    )


# ── Feature routers ───────────────────────────────────────────────────────────
app.include_router(analysis_router,     prefix="/api/analysis",   tags=["Full Analysis"])
app.include_router(resume_router,       prefix="/api/resume",     tags=["Resume"])
app.include_router(gap_analysis_router, prefix="/api/gap",        tags=["Skill Gap Analysis"])
app.include_router(roadmap_router,      prefix="/api/roadmap",    tags=["XAI Roadmap & Translator"])
app.include_router(feedback_router,     prefix="/api/feedback",   tags=["AI Feedback"])
app.include_router(github_router,       prefix="/api/github",     tags=["GitHub"])
app.include_router(youtube_router,      prefix="/api/youtube",    tags=["YouTube"])
app.include_router(translator_router,   prefix="/api/translator", tags=["Corporate Translator"])


# ── Dev entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=not settings.is_production,
        log_level="debug" if not settings.is_production else "info",
    )