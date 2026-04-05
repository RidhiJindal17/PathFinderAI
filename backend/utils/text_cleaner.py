"""
utils/text_cleaner.py — PathFinder AI
Shared text pre-processing helpers used across services.
"""

import re
import unicodedata


def normalise(text: str) -> str:
    """
    Unicode-normalise, collapse whitespace, and strip leading/trailing spaces.
    Converts unicode ligatures (e.g. ﬁ → fi), collapses multiple spaces into
    one, and removes excessive blank lines.
    Safe to call on any string before NLP processing.

    Example:
        normalise("hello   world\\n\\n\\n") → "hello world"
    """
    text = unicodedata.normalize("NFKC", text)   # normalise unicode ligatures
    text = re.sub(r"[ \t]+", " ", text)           # collapse horizontal whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)         # collapse excess blank lines
    return text.strip()


def remove_special_chars(text: str, keep_punctuation: bool = False) -> str:
    """
    Remove non-alphanumeric characters from text.

    Parameters
    ----------
    text : str
        Input text to clean.
    keep_punctuation : bool
        If True, keeps common punctuation (.,;:()-).
        If False (default), removes everything except word chars and spaces.

    Example:
        remove_special_chars("Hello, World! #$%") → "Hello World "
        remove_special_chars("Hello, World!", keep_punctuation=True) → "Hello, World!"
    """
    if keep_punctuation:
        return re.sub(r"[^\w\s.,;:()\-]", "", text)
    return re.sub(r"[^\w\s]", "", text)


def truncate(text: str, max_chars: int = 1000) -> str:
    """
    Truncate text to at most max_chars characters.
    If truncated, appends '…' to indicate the text was cut.

    Parameters
    ----------
    text : str
        Input text.
    max_chars : int
        Maximum number of characters to keep (default: 1000).

    Example:
        truncate("hello world", max_chars=7) → "hello w…"
        truncate("hi", max_chars=100) → "hi"
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def split_into_sentences(text: str) -> list[str]:
    """
    Lightweight sentence splitter that doesn't require spaCy.
    Splits on sentence-ending punctuation followed by whitespace.
    Use only for pre-processing — for accurate NLP use spaCy's sentencizer.

    Parameters
    ----------
    text : str
        Input text to split.

    Returns
    -------
    list[str]
        List of sentence strings, stripped of whitespace, empty strings removed.

    Example:
        split_into_sentences("Hello world. How are you? I am fine!")
        → ["Hello world.", "How are you?", "I am fine!"]
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def clean_resume_text(text: str) -> str:
    """
    Full cleaning pipeline for resume text.
    Applies: normalise → remove control characters → collapse whitespace.
    Preserves alphanumeric content, punctuation, and newlines.

    Parameters
    ----------
    text : str
        Raw extracted PDF text.

    Returns
    -------
    str
        Cleaned text suitable for NLP processing.
    """
    # Remove control characters (except newlines and tabs)
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", " ", text)
    text = normalise(text)
    # Remove lines that are just symbols (e.g. "------" or "======")
    text = re.sub(r"^[\s\-_=*#|]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_emails(text: str) -> list[str]:
    """
    Extract all email addresses from a block of text.

    Returns
    -------
    list[str]
        List of unique email addresses found (lowercase).
    """
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    found = re.findall(pattern, text)
    return list({e.lower() for e in found})


def extract_phone_numbers(text: str) -> list[str]:
    """
    Extract phone number candidates from text.
    Matches international and Indian formats.

    Returns
    -------
    list[str]
        List of phone number strings found (may include separators).
    """
    pattern = (
        r"(?:\+?\d{1,3}[\s\-.]?)?"
        r"(?:\(?\d{3}\)?[\s\-.]?)"
        r"\d{3}[\s\-.]?\d{4}"
    )
    return re.findall(pattern, text)