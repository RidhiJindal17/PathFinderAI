"""
utils/validators.py — PathFinder AI
Shared input validation helpers used across routers and services.
"""

import re
import os


def is_valid_github_username(username: str) -> bool:
    """
    Validate a GitHub username against GitHub's official rules:
    - 1 to 39 characters long
    - Only alphanumeric characters or hyphens
    - Cannot start or end with a hyphen
    - Cannot contain consecutive hyphens (--)

    Parameters
    ----------
    username : str
        The GitHub username to validate.

    Returns
    -------
    bool
        True if valid, False otherwise.

    Examples
    --------
    is_valid_github_username("torvalds")      → True
    is_valid_github_username("my-user-123")   → True
    is_valid_github_username("-badstart")     → False
    is_valid_github_username("has--double")   → False
    is_valid_github_username("")              → False
    """
    if not username or len(username) > 39:
        return False
    pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,37}[a-zA-Z0-9])?$"
    return bool(re.match(pattern, username)) and "--" not in username


def is_valid_pdf_filename(filename: str) -> bool:
    """
    Check whether a filename ends with .pdf (case-insensitive).

    Parameters
    ----------
    filename : str
        The filename to check (e.g. "my_resume.PDF").

    Returns
    -------
    bool

    Examples
    --------
    is_valid_pdf_filename("resume.pdf")  → True
    is_valid_pdf_filename("resume.PDF")  → True
    is_valid_pdf_filename("resume.docx") → False
    """
    if not filename:
        return False
    return filename.lower().endswith(".pdf")


def is_valid_pdf_bytes(data: bytes) -> bool:
    """
    Check PDF magic bytes — real PDFs start with %PDF.
    Prevents non-PDF files being uploaded with a .pdf extension.

    Parameters
    ----------
    data : bytes
        First few bytes of the uploaded file.

    Returns
    -------
    bool
    """
    return data[:4] == b"%PDF"


def sanitise_skill_list(skills: list[str]) -> list[str]:
    """
    Clean and deduplicate a list of skill strings.

    Operations performed:
    - Strip leading/trailing whitespace from each skill
    - Convert to lowercase for consistent comparison
    - Remove empty strings
    - Remove duplicates (preserving first occurrence order)

    Parameters
    ----------
    skills : list[str]
        Raw skill strings, possibly messy.

    Returns
    -------
    list[str]
        Cleaned, deduplicated, lowercase skill list.

    Examples
    --------
    sanitise_skill_list(["Python", "python", "  SQL  ", "sql", "React"])
    → ["python", "sql", "react"]

    sanitise_skill_list(["", "  ", "python"])
    → ["python"]
    """
    seen: set[str] = set()
    cleaned: list[str] = []
    for skill in skills:
        if not isinstance(skill, str):
            continue
        s = skill.strip().lower()
        if s and s not in seen:
            seen.add(s)
            cleaned.append(s)
    return cleaned


def is_valid_email(email: str) -> bool:
    """
    Basic email format validation using regex.
    Not RFC 5322 complete — sufficient for resume parsing.

    Parameters
    ----------
    email : str

    Returns
    -------
    bool

    Examples
    --------
    is_valid_email("user@example.com") → True
    is_valid_email("not-an-email")     → False
    """
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def sanitise_job_title(title: str) -> str:
    """
    Strip and normalise a job title string.
    Removes leading/trailing whitespace and collapses internal spaces.

    Parameters
    ----------
    title : str

    Returns
    -------
    str
    """
    return re.sub(r"\s+", " ", title.strip())


def is_within_file_size_limit(file_bytes: bytes, max_mb: int = 5) -> bool:
    """
    Check whether file bytes are within the allowed size limit.

    Parameters
    ----------
    file_bytes : bytes
    max_mb : int
        Maximum allowed size in megabytes (default 5).

    Returns
    -------
    bool
    """
    max_bytes = max_mb * 1024 * 1024
    return len(file_bytes) <= max_bytes


def get_file_size_mb(file_bytes: bytes) -> float:
    """Return file size in megabytes, rounded to 2 decimal places."""
    return round(len(file_bytes) / (1024 * 1024), 2)