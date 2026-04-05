"""
services/gemini_service.py — PathFinder AI  ·  Module III: XAI Feedback & Roadmap Generator
==============================================================================================
Integrates with the Google Gemini 2.0 Flash API to power two features:

1. generate_xai_roadmap()
   Accepts the bridge_skills list from Module II plus resume context and a target
   job title.  Returns per-skill XAI explanations, difficulty ratings, 
   estimated learning time, and a structured roadmap.

2. translate_to_professional()
   "Corporate Translator" — rewrites an informal experience description into a
   single polished, ATS-friendly bullet-point achievement statement.

3. infer_required_skills()
   Generates a list of 8-12 skills for a job title if the JD is weak or missing.
"""

from __future__ import annotations

import json
import logging
import re
import time
from functools import lru_cache
from typing import Any

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
_MAX_RETRIES = 1          # retry once on transient failures
_RETRY_DELAY = 2.0        # seconds between retries
_MAX_TOKENS  = 4096       # generous limit for the roadmap JSON


# ══════════════════════════════════════════════════════════════════════════════
#  1. GEMINI CLIENT  — configured once, reused across requests
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def get_gemini_client() -> genai.GenerativeModel:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    genai.configure(api_key=settings.gemini_api_key)

    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config=genai.GenerationConfig(
            temperature=0.4,
            top_p=0.9,
            max_output_tokens=_MAX_TOKENS,
        ),
    )
    logger.info(f"Gemini client configured — model: '{settings.gemini_model}'")
    return model


# ══════════════════════════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _call_gemini(prompt: str) -> str:
    model = get_gemini_client()
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                logger.warning(f"Retry {attempt + 1}: {exc}")
                time.sleep(_RETRY_DELAY)
            else:
                logger.error(f"Failed after retries: {exc}")

    raise RuntimeError(f"Gemini API unavailable: {last_exc}") from last_exc


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = re.sub(r"^`|`$", "", text)
    return text.strip()


def _safe_parse_json(raw: str) -> dict[str, Any]:
    cleaned = _strip_json_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(f"JSON parse failed: {exc}")
        return {"parse_error": True, "raw_response": raw[:1000]}


# ══════════════════════════════════════════════════════════════════════════════
#  2. XAI ROADMAP GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_xai_roadmap(
    bridge_skills: list[dict],
    resume_context: dict,
    job_title: str,
) -> dict[str, Any]:
    if not bridge_skills:
        return {
            "skill_explanations": [],
            "four_week_plan":     [],
            "confidence_message": f"Great match for {job_title}!",
            "no_gaps_found": True,
            "parse_error":   False,
        }

    resume_skills_str = ", ".join(resume_context.get("skills", [])) or "not specified"
    experience_str    = (resume_context.get("experience_summary") or "").strip() or "not specified"

    bridge_list_str = "\n".join(
        f"  - {bs['skill']} (priority: {bs.get('priority', 'high')})"
        for bs in bridge_skills
    )

    prompt = f"""You are a supportive, experienced Human Career Mentor for a "{job_title}" role.
Resume Context: {resume_skills_str}
Experience: {experience_str}
Skill Gaps:
{bridge_list_str}

TASK:
1. Provide 'why_important' and 'impact_if_missing' for EACH gap.
2. Create a 3-stage roadmap.
3. Provide 'estimated_time' (Rule: 1-2 skills: 2-4 weeks, 3-5: 1-3 months, 6+: 3-6 months).
4. Provide 'final_summary' (Mentor Verdict).

RULES FOR 'final_summary' (IMPORTANT):
- START with a positive acknowledgment of their existing foundation (e.g., "You have a solid start with {resume_skills_str}...").
- IDENTIFY the most critical missing skills from the gaps list.
- EXPLAIN the impact: why these gaps might cause them to be overlooked for a "{job_title}" role.
- END with actionable guidance on what they should prioritize next.
- TONE: Encouraging, honest, and professional. Avoid sounding like a machine.
- LENGTH: Exactly 2–3 lines.

JSON SCHEMA:
{{
  "missing_skills_detailed": [{{ "skill": "...", "why_important": "...", "impact_if_missing": "...", "priority": "..." }}],
  "roadmap": [{{ "stage": "...", "skills": [], "duration": "..." }}],
  "estimated_time": "...",
  "final_summary": "...",
  "suitable_roles": ["Role A", "Role B"],
  "match_score": 85
}}

If the candidate's match_score is below 50%, the 'final_summary' should be exceptionally supportive, and the 'suitable_roles' should suggest career pivots where their current skills are highly valued immediately.
"""

    try:
        raw_response = _call_gemini(prompt)
        parsed = _safe_parse_json(raw_response)
    except Exception as exc:
        return {"parse_error": True, "error_message": str(exc)}

    # Normalise fields
    parsed.setdefault("missing_skills_detailed", [])
    parsed.setdefault("roadmap", [])
    parsed.setdefault("estimated_time", "2-3 months")
    parsed.setdefault("final_summary", "You've got a solid foundation. Focusing on these high-priority gaps will significantly improve your selection chances!")
    parsed.setdefault("suitable_roles", [])
    parsed.setdefault("match_score", 0)
    
    return parsed


# ── Skill Templates for fallback ──────────────────────────────────────────────
SKILL_TEMPLATES: dict[str, list[str]] = {
    "frontend developer":     ["html", "css", "javascript", "react", "typescript", "git", "rest api"],
    "backend developer":      ["python", "node.js", "databases", "fastapi", "docker", "rest api", "sql"],
    "data scientist":         ["python", "machine learning", "statistics", "pandas", "sql", "data analysis"],
    "cybersecurity analyst": ["networking", "network security", "encryption", "linux", "cybersecurity"],
    "ui/ux designer":         ["figma", "user research", "prototyping", "adobe xd", "wireframing"],
    "full stack developer":   ["html", "css", "javascript", "node.js", "react", "sql", "git"],
}

def infer_required_skills(job_title: str) -> list[str]:
    """
    Generate 8–12 relevant technical skills for a given job title via Gemini.
    """
    title_clean = job_title.lower().strip()
    
    prompt = f"""Given the job title: "{job_title}", generate a list of 8–12 critical technical skills required for this role.
    Return ONLY a simple comma-separated list of skills. No explanation."""

    try:
        raw = _call_gemini(prompt)
        skills = [s.strip().lower() for s in raw.split(",") if s.strip()]
        if len(skills) >= 3:
            return skills
    except Exception:
        pass

    # Fallback Template
    for key, template in SKILL_TEMPLATES.items():
        if key in title_clean or title_clean in key:
            return template

    return ["communication", "problem solving", "git", "linux"]


# ══════════════════════════════════════════════════════════════════════════════
#  3. CORPORATE TRANSLATOR
# ══════════════════════════════════════════════════════════════════════════════

def translate_to_professional(informal_text: str) -> dict[str, str]:
    """
    Rewrite an informal description as a high-impact professional resume bullet point.
    """
    if not informal_text.strip():
        return {"polished_text": "No input provided.", "tone": "neutral"}

    prompt = f"""You are a Senior Technical Recruiter and ATS Optimization Expert.
    
    TASK:
    Upgrade the following informal experience into a HIGH-IMPACT, ATS-OPTIMIZED resume bullet point.
    
    RULES:
    1. START with a strong action verb (e.g., Achieved, Developed, Led, Built, Completed, Implemented, Spearheaded, Orchestrated).
    2. EXPAND short sentences into meaningful professional statements.
    3. INCLUDE domain-specific keywords and technical terminology.
    4. INFER and ADD implied impact: mention specific skills gained, tools used, or quantifiable outcomes (use '~' for estimated numbers).
    5. LENGTH: 1–2 lines max.
    6. TONE: Professional, impressive, and recruiter-ready.
    7. DO NOT just rewrite words; transform them into a professional achievement.
    
    INPUT: "{informal_text.strip()}"
    
    OUTPUT FORMAT (JSON):
    {{
      "polished_text": "The high-impact bullet point",
      "tone": "professional"
    }}
    """

    try:
        raw_response = _call_gemini(prompt)
        parsed = _safe_parse_json(raw_response)
        
        # If parsing failed or returned error dict, handle it
        if parsed.get("parse_error") or "polished_text" not in parsed:
            # Fallback for non-JSON or malformed response
            text = raw_response.strip()
            text = re.sub(r"^```(json)?", "", text, flags=re.IGNORECASE)
            text = re.sub(r"```$", "", text)
            text = re.sub(r"^[•\-\*\"`']+\s*", "", text.strip())
            return {"polished_text": text.strip().strip('"'), "tone": "professional"}
            
        return {
            "polished_text": parsed["polished_text"],
            "tone": parsed.get("tone", "professional")
        }
    except Exception as exc:
        logger.error(f"Translation failed: {exc}")
        return {"polished_text": f"Error: {str(exc)}", "tone": "error"}