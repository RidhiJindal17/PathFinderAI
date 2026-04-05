"""
services/nlp_extractor.py — PathFinder AI
Extracts skills, education, and experience from resume text using spaCy.

The spaCy model is loaded once at module import time (lazy singleton)
so it isn't reloaded on every request.
"""

import re
import logging
from functools import lru_cache

import spacy
from spacy.language import Language

from config import settings

logger = logging.getLogger(__name__)

# ── Skill keyword bank ────────────────────────────────────────────────────────
# Extend this list as needed. A production system would use a skills ontology
# like ESCO or a fine-tuned NER model.
TECH_SKILLS_BANK = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go",
    "rust", "kotlin", "swift", "r", "scala", "ruby", "php", "bash", "sql",

    # Web / Frontend
    "react", "angular", "vue", "html", "css", "tailwind", "bootstrap",
    "next.js", "gatsby", "webpack", "vite",

    # Backend / APIs
    "fastapi", "django", "flask", "express", "spring boot", "graphql", "rest",
    "grpc", "microservices",

    # Data / ML / AI
    "machine learning", "deep learning", "nlp", "computer vision",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "hugging face", "spacy", "nltk", "opencv", "matplotlib", "seaborn",

    # Databases
    "mongodb", "postgresql", "mysql", "sqlite", "redis", "elasticsearch",
    "firebase", "dynamodb", "cassandra",

    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "github actions",
    "jenkins", "terraform", "linux", "git",

    # Soft Skills
    "communication", "leadership", "teamwork", "problem solving",
    "project management", "agile", "scrum",
}


@lru_cache(maxsize=1)
def _load_nlp_model() -> Language:
    """Load the spaCy model once and cache it."""
    logger.info(f"Loading spaCy model: {settings.spacy_model}")
    try:
        nlp = spacy.load(settings.spacy_model)
        logger.info("spaCy model loaded successfully.")
        return nlp
    except OSError:
        logger.error(
            f"spaCy model '{settings.spacy_model}' not found. "
            f"Run: python -m spacy download {settings.spacy_model}"
        )
        raise


def extract_skills(text: str) -> dict:
    """
    Runs NLP on resume text and extracts:
    - skills      : matched against TECH_SKILLS_BANK (case-insensitive)
    - education   : ORG entities near degree keywords
    - experience  : ORG + DATE entity pairs (company + tenure)

    Returns a dict with keys: skills, education, experience.
    """
    nlp = _load_nlp_model()
    doc = nlp(text)

    # ── Skill extraction ──────────────────────────────────────────────────────
    text_lower = text.lower()
    found_skills = sorted(
        {skill for skill in TECH_SKILLS_BANK if re.search(rf"\b{re.escape(skill)}\b", text_lower)}
    )

    # ── Education extraction ──────────────────────────────────────────────────
    education_keywords = {"bachelor", "b.tech", "b.e", "master", "m.tech", "mba", "phd", "diploma", "degree"}
    education: list[str] = []
    for sent in doc.sents:
        sent_lower = sent.text.lower()
        if any(kw in sent_lower for kw in education_keywords):
            # Grab ORG entities in this sentence as institution names
            orgs = [ent.text for ent in sent.ents if ent.label_ == "ORG"]
            if orgs:
                education.append(f"{sent.text.strip()}")
            elif len(sent.text.strip()) < 200:  # fallback: include the sentence
                education.append(sent.text.strip())

    # ── Experience extraction ─────────────────────────────────────────────────
    experience: list[str] = []
    experience_keywords = {"experience", "worked", "internship", "intern", "engineer", "developer", "analyst"}
    for sent in doc.sents:
        sent_lower = sent.text.lower()
        if any(kw in sent_lower for kw in experience_keywords):
            if len(sent.text.strip()) > 20:
                experience.append(sent.text.strip())

    logger.debug(
        f"Extracted {len(found_skills)} skills, "
        f"{len(education)} education entries, "
        f"{len(experience)} experience entries."
    )

    return {
        "skills": found_skills,
        "education": education[:5],    # cap at 5 entries
        "experience": experience[:10], # cap at 10 entries
    }