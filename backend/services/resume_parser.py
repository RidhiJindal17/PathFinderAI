"""
services/resume_parser.py — PathFinder AI  ·  Module I: Intelligent Resume Parser
===================================================================================
Master service that ties together PDF extraction, NLP entity recognition,
and keyword-based skill detection to return a fully structured resume dict.

Public API
----------
    extract_text_from_pdf(file_bytes: bytes)  -> str
    extract_entities(text: str)               -> dict
    extract_skills(text: str)                 -> list[str]
    extract_education(doc)                    -> list[str]
    extract_experience(doc)                   -> list[str]
    extract_projects(text: str)               -> list[str]
    parse_resume(file_bytes: bytes)           -> dict
"""

from __future__ import annotations

import io
import re
import logging
from functools import lru_cache

import spacy
from spacy.language import Language
from PyPDF2 import PdfReader

from config import settings

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  SKILL KEYWORD BANK  —  200 + skills across 10 categories
# ══════════════════════════════════════════════════════════════════════════════

SKILL_KEYWORDS: set[str] = {
    # ── Programming Languages ─────────────────────────────────────────────────
    "python", "javascript", "typescript", "java", "c", "c++", "c#", "go",
    "golang", "rust", "kotlin", "swift", "ruby", "php", "r", "scala",
    "perl", "matlab", "bash", "shell", "powershell", "dart", "elixir",
    "haskell", "lua", "groovy", "assembly",

    # ── Web Frontend ──────────────────────────────────────────────────────────
    "html", "css", "sass", "scss", "less", "react", "react.js", "reactjs",
    "angular", "vue", "vue.js", "vuejs", "next.js", "nextjs", "nuxt.js",
    "gatsby", "svelte", "tailwind", "tailwindcss", "bootstrap", "materialui",
    "material ui", "chakra ui", "webpack", "vite", "babel", "jquery",
    "redux", "zustand", "recoil", "graphql", "apollo",

    # ── Web Backend / APIs ────────────────────────────────────────────────────
    "fastapi", "django", "flask", "express", "express.js", "node.js",
    "nodejs", "spring", "spring boot", "laravel", "rails", "ruby on rails",
    "asp.net", "fastify", "hapi", "koa", "rest", "rest api", "restful",
    "graphql", "grpc", "websockets", "microservices", "soap",

    # ── Databases ─────────────────────────────────────────────────────────────
    "sql", "mysql", "postgresql", "postgres", "sqlite", "oracle",
    "mongodb", "mongoose", "redis", "cassandra", "dynamodb", "firebase",
    "firestore", "elasticsearch", "neo4j", "couchdb", "influxdb",
    "supabase", "planetscale", "prisma", "sqlalchemy", "hibernate",

    # ── Cloud & DevOps ────────────────────────────────────────────────────────
    "aws", "amazon web services", "gcp", "google cloud", "azure",
    "microsoft azure", "heroku", "vercel", "netlify", "digitalocean",
    "docker", "kubernetes", "k8s", "helm", "terraform", "ansible",
    "puppet", "chef", "vagrant", "jenkins", "github actions", "gitlab ci",
    "circleci", "travis ci", "ci/cd", "nginx", "apache", "linux",
    "ubuntu", "centos", "unix", "bash scripting",

    # ── Data Science / ML / AI ────────────────────────────────────────────────
    "machine learning", "deep learning", "artificial intelligence", "ai",
    "nlp", "natural language processing", "computer vision", "cv",
    "data science", "data analysis", "data engineering", "data mining",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
    "xgboost", "lightgbm", "catboost", "hugging face", "transformers",
    "bert", "gpt", "llm", "large language models", "langchain",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "opencv", "pillow", "spacy", "nltk", "gensim", "fasttext",
    "mlflow", "kubeflow", "airflow", "dbt",

    # ── Big Data ──────────────────────────────────────────────────────────────
    "spark", "apache spark", "hadoop", "hive", "kafka", "apache kafka",
    "flink", "storm", "presto", "redshift", "snowflake", "bigquery",
    "databricks",

    # ── Tools & Platforms ─────────────────────────────────────────────────────
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "trello", "notion", "figma", "postman", "swagger", "insomnia",
    "vs code", "intellij", "pycharm", "eclipse", "vim", "linux",
    "tableau", "power bi", "looker", "grafana", "kibana", "prometheus",
    "datadog", "new relic", "sentry",

    # ── Mobile Development ────────────────────────────────────────────────────
    "android", "ios", "react native", "flutter", "xamarin", "ionic",
    "swift", "objective-c", "kotlin",

    # ── Security ──────────────────────────────────────────────────────────────
    "cybersecurity", "penetration testing", "ethical hacking", "owasp",
    "ssl", "tls", "oauth", "jwt", "encryption", "cryptography",

    # ── HR & Business Management ──────────────────────────────────────────────
    "human resources", "hr", "recruitment", "hiring", "talent acquisition",
    "onboarding", "payroll", "employee relations", "performance management",
    "business analysis", "strategy", "finance", "accounting", "marketing",
    "sales", "customer success", "operations", "compliance", "training",

    # ── Soft Skills ───────────────────────────────────────────────────────────
    "communication", "leadership", "teamwork", "team player",
    "problem solving", "critical thinking", "time management",
    "project management", "agile", "scrum", "kanban", "waterfall",
    "mentoring", "collaboration", "presentation", "public speaking",
    "adaptability", "creativity", "attention to detail",
}

# Build a sorted list for deterministic output
_SKILLS_LIST: list[str] = sorted(SKILL_KEYWORDS)


# ══════════════════════════════════════════════════════════════════════════════
#  spaCy MODEL — loaded once, cached forever
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def _get_nlp() -> Language:
    """
    Load the spaCy language model once per process and cache it.
    Raises a clear RuntimeError if the model hasn't been downloaded yet.
    """
    model_name = settings.spacy_model
    try:
        nlp = spacy.load(model_name)
        logger.info(f"spaCy model '{model_name}' loaded successfully.")
        return nlp
    except OSError as exc:
        raise RuntimeError(
            f"spaCy model '{model_name}' not found. "
            f"Fix: python -m spacy download {model_name}"
        ) from exc


# ══════════════════════════════════════════════════════════════════════════════
#  1. PDF TEXT EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all readable text from a PDF supplied as raw bytes.

    Uses PyPDF2's PdfReader to iterate every page and concatenate the text.
    Silently skips pages that cannot be decoded (scanned/image pages).

    Parameters
    ----------
    file_bytes : bytes
        Raw bytes of the uploaded PDF file.

    Returns
    -------
    str
        Full extracted text, pages separated by newlines.
        Returns an empty string if nothing can be extracted (never raises).

    Raises
    ------
    ValueError
        If the bytes cannot be interpreted as a valid PDF at all.
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(f"Cannot read PDF — file may be corrupted: {exc}") from exc

    pages: list[str] = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
            pages.append(text)
        except Exception as exc:
            logger.warning(f"Skipping page {page_num} — extraction failed: {exc}")

    full_text = "\n".join(pages)
    logger.debug(
        f"PDF extraction complete — {len(reader.pages)} page(s), "
        f"{len(full_text):,} characters extracted."
    )
    return full_text


# ══════════════════════════════════════════════════════════════════════════════
#  2. ENTITY EXTRACTION  (name, email, phone)
# ══════════════════════════════════════════════════════════════════════════════

# Pre-compiled regex patterns for speed
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE
)
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-.]?)?"          # optional country code
    r"(?:\(?\d{3}\)?[\s\-.]?)"           # area code
    r"\d{3}[\s\-.]?\d{4}"               # local number
)


def extract_entities(text: str) -> dict:
    """
    Extract personal contact entities from resume text.

    Strategy
    --------
    - **Email**  : regex scan (reliable, format is universal)
    - **Phone**  : regex scan with flexible separators
    - **Name**   : first PERSON entity found by spaCy NER in the
                   first 500 characters (where names typically appear)

    Parameters
    ----------
    text : str
        Full resume text.

    Returns
    -------
    dict with keys:
        name  (str | None)
        email (str | None)
        phone (str | None)
    """
    # ── Email ─────────────────────────────────────────────────────────────────
    email_match = _EMAIL_RE.search(text)
    email = email_match.group(0).lower() if email_match else None

    # ── Phone ─────────────────────────────────────────────────────────────────
    phone_match = _PHONE_RE.search(text)
    phone = phone_match.group(0).strip() if phone_match else None

    # ── Name — spaCy PERSON entity in header region ───────────────────────────
    name: str | None = None
    header_text = text[:500]            # names almost always appear at the top
    try:
        nlp = _get_nlp()
        doc = nlp(header_text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                candidate = ent.text.strip()
                # Sanity check: real names are 2–5 words, no digits
                words = candidate.split()
                if 2 <= len(words) <= 5 and not any(ch.isdigit() for ch in candidate):
                    name = candidate
                    break
    except Exception as exc:
        logger.warning(f"Name extraction via spaCy failed: {exc}")

    logger.debug(f"Entities — name: {name!r}, email: {email!r}, phone: {phone!r}")
    return {"name": name, "email": email, "phone": phone}


# ══════════════════════════════════════════════════════════════════════════════
#  3. SKILL EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_skills(text: str) -> list[str]:
    """
    Match resume text against the SKILL_KEYWORDS bank using whole-word,
    case-insensitive regex search.

    Why regex over simple `in` substring check?
    - "r" as a standalone skill should NOT match inside "docker" or "array".
    - Word-boundary anchors (\\b) prevent false positives.

    Parameters
    ----------
    text : str
        Full resume text (already extracted from PDF).

    Returns
    -------
    list[str]
        Alphabetically sorted list of matched skill strings (lowercase).
        Returns an empty list if no skills are found — never raises.
    """
    if not text.strip():
        return []

    text_lower = text.lower()
    found: list[str] = []

    for skill in _SKILLS_LIST:
        # Escape special regex chars in skill names (e.g. "c++", "asp.net")
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, text_lower):
            found.append(skill)

    logger.debug(f"Skill extraction: {len(found)} skill(s) matched.")
    return found


# ══════════════════════════════════════════════════════════════════════════════
#  4. EDUCATION EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

_EDUCATION_KEYWORDS = frozenset({
    "bachelor", "b.tech", "b.e", "b.sc", "b.com", "ba", "bca",
    "master", "m.tech", "m.e", "m.sc", "mca", "mba", "m.com",
    "phd", "ph.d", "doctorate", "diploma", "degree", "university",
    "college", "institute", "school of", "10th", "12th", "hsc", "ssc",
    "higher secondary", "secondary", "matriculation", "graduation",
})


def extract_education(doc) -> list[str]:
    """
    Extract education entries from a spaCy Doc object.

    Looks for sentences that contain education-related keywords and
    collects ORG entities (institution names) within them.

    Parameters
    ----------
    doc : spacy.tokens.Doc
        A processed spaCy document of the full resume text.

    Returns
    -------
    list[str]
        Up to 6 education sentences/snippets, de-duplicated.
    """
    seen: set[str] = set()
    results: list[str] = []

    for sent in doc.sents:
        sent_lower = sent.text.lower()
        if any(kw in sent_lower for kw in _EDUCATION_KEYWORDS):
            clean = " ".join(sent.text.split())   # collapse internal whitespace
            if clean and clean not in seen and len(clean) > 10:
                seen.add(clean)
                results.append(clean)
            if len(results) >= 6:
                break

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  5. EXPERIENCE EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

_EXPERIENCE_KEYWORDS = frozenset({
    "experience", "worked", "work experience", "employment", "internship",
    "intern", "engineer", "developer", "analyst", "manager", "lead",
    "designed", "developed", "built", "implemented", "deployed",
    "maintained", "collaborated", "responsible", "achieved", "delivered",
    "created", "launched", "optimised", "optimized", "improved",
    "reduced", "increased", "led", "managed", "coordinated",
})


def extract_experience(doc) -> list[str]:
    """
    Extract work-experience bullet points from a spaCy Doc.

    Identifies sentences that contain action verbs or experience keywords
    and returns them as individual experience lines.

    Parameters
    ----------
    doc : spacy.tokens.Doc
        A processed spaCy document.

    Returns
    -------
    list[str]
        Up to 12 experience sentences, de-duplicated, length-filtered.
    """
    seen: set[str] = set()
    results: list[str] = []

    for sent in doc.sents:
        sent_lower = sent.text.lower()
        if any(kw in sent_lower for kw in _EXPERIENCE_KEYWORDS):
            clean = " ".join(sent.text.split())
            # Filter out very short fragments and edu sentences (avoid overlap)
            if (
                clean not in seen
                and 25 < len(clean) < 400
                and not any(ek in sent_lower for ek in ("university", "college", "degree"))
            ):
                seen.add(clean)
                results.append(clean)
            if len(results) >= 12:
                break

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  6. PROJECT EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

_PROJECT_SECTION_RE = re.compile(
    r"(?:projects?|personal projects?|academic projects?|key projects?)"
    r"[:\s\n]+(.*?)(?=\n[A-Z][A-Z\s]{3,}:|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_PROJECT_BULLET_RE = re.compile(r"(?:^|\n)[•\-\*▸►▪]\s*(.+)", re.MULTILINE)


def extract_projects(text: str) -> list[str]:
    """
    Extract project entries from resume text.

    Two strategies tried in order:
    1. Find a "Projects" section and extract bullet points within it.
    2. Fall back to scanning all lines that start with a bullet character.

    Parameters
    ----------
    text : str
        Full resume text.

    Returns
    -------
    list[str]
        Up to 8 project descriptions, cleaned and de-duplicated.
    """
    projects: list[str] = []
    seen: set[str] = set()

    # Strategy 1 — dedicated Projects section
    section_match = _PROJECT_SECTION_RE.search(text)
    if section_match:
        section_text = section_match.group(1)
        for bullet in _PROJECT_BULLET_RE.findall(section_text):
            clean = bullet.strip()
            if clean and clean not in seen and len(clean) > 15:
                seen.add(clean)
                projects.append(clean)

    # Strategy 2 — global bullet fallback if nothing found yet
    if not projects:
        for bullet in _PROJECT_BULLET_RE.findall(text):
            clean = bullet.strip()
            if clean and clean not in seen and len(clean) > 20:
                seen.add(clean)
                projects.append(clean)

    return projects[:8]


# ══════════════════════════════════════════════════════════════════════════════
#  7. MASTER PARSE FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def parse_resume(file_bytes: bytes) -> dict:
    """
    Master function — orchestrates all extraction steps and returns a
    single structured dict representing the full parsed resume.

    Pipeline
    --------
    1. PDF → raw text  (PyPDF2)
    2. Raw text → spaCy Doc  (NLP pipeline)
    3. Extract entities  (name, email, phone)
    4. Extract skills    (keyword bank, case-insensitive)
    5. Extract education (keyword + NER sentences)
    6. Extract experience(keyword sentences)
    7. Extract projects  (section + bullet detection)

    Parameters
    ----------
    file_bytes : bytes
        Raw bytes of the uploaded PDF resume.

    Returns
    -------
    dict with keys:
        name          str | None
        email         str | None
        phone         str | None
        skills        list[str]
        education     list[str]
        experience    list[str]
        projects      list[str]
        raw_text      str
        char_count    int
        parse_status  "success" | "partial" (if text is very short)

    Never raises — errors are caught and reflected in the returned dict.
    """
    result: dict = {
        "name": None,
        "email": None,
        "phone": None,
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "raw_text": "",
        "char_count": 0,
        "parse_status": "success",
    }

    # ── Step 1: Extract text ──────────────────────────────────────────────────
    try:
        raw_text = extract_text_from_pdf(file_bytes)
    except ValueError as exc:
        logger.error(f"PDF read failed: {exc}")
        result["parse_status"] = "error"
        result["error_detail"] = str(exc)
        return result

    result["raw_text"] = raw_text
    result["char_count"] = len(raw_text)

    # Graceful handling for near-empty PDFs (scanned / image-only)
    if len(raw_text.strip()) < 50:
        logger.warning("Very little text extracted — PDF may be scanned/image-based.")
        result["parse_status"] = "partial"
        return result   # return early with empty lists — no NLP needed

    # ── Step 2: Run spaCy ─────────────────────────────────────────────────────
    try:
        nlp = _get_nlp()
        # spaCy has a default max_length of 1,000,000 chars; truncate just in case
        doc = nlp(raw_text[:800_000])
    except Exception as exc:
        logger.error(f"spaCy processing failed: {exc}")
        # Still return what we can — skills + entities via regex
        result["skills"] = extract_skills(raw_text)
        entities = extract_entities(raw_text)
        result.update(entities)
        result["parse_status"] = "partial"
        return result

    # ── Step 3–7: Run all extractors ─────────────────────────────────────────
    entities = extract_entities(raw_text)
    result.update(entities)
    result["skills"]     = extract_skills(raw_text)
    result["education"]  = extract_education(doc)
    result["experience"] = extract_experience(doc)
    result["projects"]   = extract_projects(raw_text)

    logger.info(
        f"Resume parsed — skills: {len(result['skills'])}, "
        f"education: {len(result['education'])}, "
        f"experience: {len(result['experience'])}, "
        f"projects: {len(result['projects'])}"
    )
    return result
