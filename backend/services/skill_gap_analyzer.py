"""
services/skill_gap_analyzer.py — PathFinder AI  ·  Module II: Semantic Skill-Gap Analyzer
===========================================================================================
Uses Sentence-Transformers (all-MiniLM-L6-v2) to produce dense vector embeddings for
every skill, then measures how well a candidate's resume covers a job description via
cosine similarity.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings

# Import the shared skill keyword bank from Module I — single source of truth
from services.resume_parser import SKILL_KEYWORDS, _get_nlp

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────
MATCH_THRESHOLD: float = 0.65   # cosine similarity ≥ this → skill is "matched"

# Priority bands for bridge skills (similarity below MATCH_THRESHOLD)
PRIORITY_HIGH_MAX: float   = 0.30   # sim < 0.30  → high priority gap
PRIORITY_MEDIUM_MAX: float = 0.50   # 0.30–0.50   → medium priority gap

# Sorted skill list for fast iteration
_SKILLS_LIST: list[str] = sorted(SKILL_KEYWORDS)


# ══════════════════════════════════════════════════════════════════════════════
#  1. MODEL LOADER
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def load_model() -> SentenceTransformer:
    model_name = settings.sbert_model
    logger.info(f"Loading Sentence-Transformer model: '{model_name}' …")
    try:
        model = SentenceTransformer(model_name)
        logger.info(f"✅ Sentence-Transformer '{model_name}' loaded and cached.")
        return model
    except Exception as exc:
        raise RuntimeError(f"Failed to load Sentence-Transformer '{model_name}': {exc}") from exc


# ══════════════════════════════════════════════════════════════════════════════
#  2. SKILL EXTRACTION FROM JOB DESCRIPTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_skills_from_jd(job_description: str) -> list[str]:
    if not job_description.strip():
        return []

    text_lower = job_description.lower()
    found: set[str] = set()

    # Layer 1: Keyword bank
    for skill in _SKILLS_LIST:
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, text_lower):
            found.add(skill)

    # Layer 2: spaCy entity fallback
    try:
        nlp = _get_nlp()
        doc = nlp(job_description[:5000])
        entity_labels = {"ORG", "PRODUCT", "WORK_OF_ART", "GPE"}
        for ent in doc.ents:
            if ent.label_ in entity_labels:
                normed = ent.text.strip().lower()
                if normed in SKILL_KEYWORDS:
                    found.add(normed)
    except Exception as exc:
        logger.warning(f"spaCy fallback failed: {exc}")

    if not found:
        logger.warning(f"[Analyzer] Zero skills found in JD text sample: {text_lower[:100]}")

    result = sorted(found)
    logger.info(f"✅ JD skill extraction: {len(result)} skill(s) found.")
    return result


# ══════════════════════════════════════════════════════════════════════════════
#  3. HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def compute_similarity(skill_a: str, skill_b: str, model: SentenceTransformer) -> float:
    if not skill_a.strip() or not skill_b.strip():
        return 0.0
    try:
        vecs: np.ndarray = model.encode([skill_a, skill_b], convert_to_numpy=True, normalize_embeddings=True)
        similarity = float(np.dot(vecs[0], vecs[1]))
        return max(0.0, min(1.0, similarity))
    except Exception:
        return 0.0

def _encode_skills(skills: list[str], model: SentenceTransformer) -> np.ndarray:
    return model.encode(skills, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)

def _cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.clip(a @ b.T, 0.0, 1.0)

def _assign_priority(skill: str, job_description: str) -> str:
    """
    Ranks skill gaps based on industry relevance and presence in JD.
    - HIGH: Direct JD mention or Core Role (React, Python, Java, etc.)
    - MEDIUM: Supporting Tools/APIs (Git, Docker, Testing)
    - LOW: Styling or Minor Utilities (CSS, Tailwind, Minor tools)
    """
    skill_lower = skill.lower().strip()
    jd_lower = job_description.lower()
    
    # Tier 1: Core Job Requirements (Direct Mentions or Fundamental Frameworks)
    CORE_TECH = {"react", "python", "javascript", "typescript", "java", "c++", "nodejs", "node.js", "machine learning", "ml", "sql", "data science", "fastapi", "django", "spring boot"}
    if skill_lower in jd_lower or skill_lower in CORE_TECH:
        return "HIGH"
    
    # Tier 2: Supporting Workflow / API Tools
    TOOLS = {"git", "github", "api", "rest", "graphql", "docker", "testing", "pytest", "jest", "cicd", "ci/cd", "postman"}
    if skill_lower in TOOLS or any(tool in skill_lower for tool in TOOLS):
        return "MEDIUM"
        
    # Tier 3: Default / Support / Styling
    return "LOW"


# ══════════════════════════════════════════════════════════════════════════════
#  4.  MAIN PUBLIC FUNCTION: analyze_gap
# ══════════════════════════════════════════════════════════════════════════════

def analyze_gap(resume_skills: list[str], job_description: str, jd_skills: list[str] | None = None) -> dict[str, Any]:
    """
    Core skill-gap analysis function with debug logging and robust match logic.
    If jd_skills is provided, it skips the automated extraction and uses them as-is.
    """
    # 1. Normalise
    normed_resume = sorted({s.strip().lower() for s in resume_skills if s.strip()})
    total_resume = len(normed_resume)

    # 2. Extract JD Skills (conditional on input)
    if jd_skills is None:
        jd_skills = extract_skills_from_jd(job_description)
    else:
        # Normalise provided skills too
        jd_skills = sorted({s.strip().lower() for s in jd_skills if s.strip()})
        
    total_jd = len(jd_skills)

    # ── Debug Log — CRITICAL for troubleshooting ─────────────────────────────
    logger.info(f"[Gap Analysis Debug] JD Skills Detected: {jd_skills}")
    logger.info(f"[Gap Analysis Debug] Resume Skills Found: {normed_resume}")

    # 3. Edge Case: No JD skills
    if total_jd == 0:
        logger.warning("No recognisable skills found in the JD.")
        return {
            "match_score": 0,
            "matched_skills": [],
            "bridge_skills": [],
            "job_skills_extracted": [],
            "total_job_skills": 0,
            "total_resume_skills": total_resume,
            "analysis_note": "I couldn't find any specific technical keywords in your job description. For a more accurate mentor verdict, try providing a more detailed version of the job requirements.",
        }

    # 4. Edge Case: Empty Resume
    if total_resume == 0:
        logger.info("Empty resume skills — all JD skills are gaps.")
        bridge_skills_final = [{"skill": s, "similarity_score": 0.0, "priority": "high"} for s in jd_skills]
        return {
            "match_score": 0,
            "matched_skills": [],
            "bridge_skills": bridge_skills_final,
            "job_skills_extracted": jd_skills,
            "total_job_skills": total_jd,
            "total_resume_skills": 0,
            "analysis_note": "It looks like your current resume might be missing a clear technical skills section. I've highlighted the critical job requirements so you can start bridging these gaps immediately.",
        }

    # 5. Semantic Analysis
    model = load_model()
    resume_vecs = _encode_skills(normed_resume, model)
    jd_vecs = _encode_skills(jd_skills, model)
    sim_matrix = _cosine_matrix(resume_vecs, jd_vecs)
    best_coverage = sim_matrix.max(axis=0)

    matched_skills_list = []
    bridge_skills_list = []

    for idx, jd_skill in enumerate(jd_skills):
        score = float(best_coverage[idx])
        if score >= MATCH_THRESHOLD:
            matched_skills_list.append(jd_skill)
        else:
            bridge_skills_list.append({
                "skill": jd_skill,
                "similarity_score": round(score, 4),
                "priority": _assign_priority(jd_skill, job_description),
            })

    # 6. Final Tally
    match_score = int(round(float(best_coverage.mean()) * 100))
    match_score = max(0, min(100, match_score))

    logger.info(f"Analysis Finished: Score {match_score}% | {len(matched_skills_list)} matched | {len(bridge_skills_list)} gaps")

    return {
        "match_score":          match_score,
        "matched_skills":       matched_skills_list,
        "bridge_skills":        bridge_skills_list,
        "job_skills_extracted": jd_skills,
        "total_job_skills":     total_jd,
        "total_resume_skills":  total_resume,
        "analysis_note":        None,
    }