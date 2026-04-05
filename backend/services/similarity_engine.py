"""
services/similarity_engine.py — PathFinder AI
Computes semantic similarity between resume skills and a job description
using Sentence-BERT (all-MiniLM-L6-v2).

The model is loaded once (lazy singleton) to avoid reloading on every request.
"""

import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_sbert_model() -> SentenceTransformer:
    """Load and cache the Sentence-BERT model."""
    logger.info(f"Loading Sentence-BERT model: {settings.sbert_model}")
    model = SentenceTransformer(settings.sbert_model)
    logger.info("Sentence-BERT model loaded successfully.")
    return model


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(vec_a, vec_b)
    norm = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    return float(dot / norm) if norm > 0 else 0.0


def compute_match(resume_skills: list[str], job_description: str) -> dict:
    """
    Computes how well the candidate's skills match the job description.

    Strategy:
    1. Encode the job description as a single embedding.
    2. Encode each resume skill as an embedding.
    3. Compute cosine similarity per skill.
    4. Skills above `MATCH_THRESHOLD` are "matched"; others need attention.
    5. Extract candidate missing skills by scanning the JD for skill nouns
       not present in the resume skill list.

    Returns:
        overall_score  : 0–100 int
        matched_skills : list[str]
        missing_skills : list[str]
        skill_scores   : dict[str, float] — per-skill similarity score
    """
    MATCH_THRESHOLD = 0.45   # tune this for better precision/recall

    model = _load_sbert_model()

    # Encode job description once
    jd_embedding: np.ndarray = model.encode(job_description, convert_to_numpy=True)

    skill_scores: dict[str, float] = {}
    matched: list[str] = []
    unmatched: list[str] = []

    for skill in resume_skills:
        skill_embedding: np.ndarray = model.encode(skill, convert_to_numpy=True)
        score = _cosine_similarity(skill_embedding, jd_embedding)
        skill_scores[skill] = round(score, 4)
        if score >= MATCH_THRESHOLD:
            matched.append(skill)
        else:
            unmatched.append(skill)

    # Derive a rough overall score: % of skills that matched, weighted by their scores
    if resume_skills:
        overall = np.mean([skill_scores[s] for s in matched]) * 100 if matched else 0.0
    else:
        overall = 0.0

    # Basic missing-skill detection: look for skill-bank tokens in JD not in resume
    from services.nlp_extractor import TECH_SKILLS_BANK
    import re
    jd_lower = job_description.lower()
    resume_lower = {s.lower() for s in resume_skills}
    missing = [
        skill for skill in TECH_SKILLS_BANK
        if re.search(rf"\b{re.escape(skill)}\b", jd_lower) and skill not in resume_lower
    ]

    logger.debug(
        f"Match score: {overall:.1f} | Matched: {len(matched)} | Missing: {len(missing)}"
    )

    return {
        "overall_score": round(overall),
        "matched_skills": matched,
        "missing_skills": missing[:15],    # top 15 gaps
        "skill_scores": skill_scores,
    }