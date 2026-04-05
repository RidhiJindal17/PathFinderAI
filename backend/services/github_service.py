"""
services/github_service.py — PathFinder AI  ·  Module IV: GitHub Portfolio Dashboard
======================================================================================
Fetches a GitHub user's public profile, repositories, and language statistics
using the GitHub REST API v3.  All calls are async (httpx.AsyncClient).

Features
--------
- Optional GITHUB_TOKEN authentication (raises rate limit from 60 → 5000 req/hr)
- In-memory cache with 1-hour TTL — repeated calls for the same username skip the API
- Graceful handling of 404 (user not found) and 403/429 (rate limited)
- Repos with null language are handled — never cause KeyError or crashes
- User-Agent header on every request (required by GitHub API ToS)

Public API
----------
    fetch_github_profile(username)          → dict
    fetch_repositories(username)            → list[dict]
    compute_language_stats(repos)           → list[dict]
    get_portfolio_summary(username)         → dict
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
GITHUB_API_BASE = "https://api.github.com"
REPOS_PER_PAGE  = 30        # GitHub max is 100; 30 gives a representative sample
CACHE_TTL_SECS  = 3600      # 1 hour in-memory cache per username
TOP_REPOS_COUNT = 5         # number of top repos to surface in the summary

# Activity thresholds (days since most recent repo was updated)
ACTIVE_DAYS   = 30
MODERATE_DAYS = 180

# ── In-memory cache ───────────────────────────────────────────────────────────
# Structure: { username_lower: {"data": dict, "cached_at": float} }
_cache: dict[str, dict[str, Any]] = {}


def _get_headers() -> dict[str, str]:
    """
    Build the request headers required by the GitHub API.

    GitHub requires a User-Agent header on every request.
    If GITHUB_TOKEN is set in the environment, it is included as a Bearer
    token which raises the rate limit from 60 to 5,000 requests per hour.

    Returns
    -------
    dict[str, str]
        Headers dict ready to pass to httpx.
    """
    headers = {
        "Accept":             "application/vnd.github+json",
        "User-Agent":         "PathFinder-AI/1.0 (career-navigation-app)",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def _check_cache(username: str) -> dict | None:
    """
    Return cached portfolio summary for ``username`` if still within TTL.

    Parameters
    ----------
    username : str
        GitHub username (case-insensitive — stored lowercase).

    Returns
    -------
    dict or None
        Cached data dict, or None if not cached / expired.
    """
    key   = username.lower()
    entry = _cache.get(key)
    if entry and (time.monotonic() - entry["cached_at"]) < CACHE_TTL_SECS:
        logger.debug(f"Cache hit for GitHub user '{username}'")
        return entry["data"]
    return None


def _write_cache(username: str, data: dict) -> None:
    """Write ``data`` into the in-memory cache for ``username``."""
    _cache[username.lower()] = {"data": data, "cached_at": time.monotonic()}


def _handle_github_error(response: httpx.Response, username: str) -> None:
    """
    Inspect a non-2xx GitHub API response and raise the appropriate exception.

    Raises
    ------
    ValueError
        For 404 — user not found.
    PermissionError
        For 403 / 429 — rate limited.
    httpx.HTTPStatusError
        For any other unexpected HTTP error.
    """
    if response.status_code == 404:
        raise ValueError(f"GitHub user '{username}' does not exist or is private.")
    if response.status_code in (403, 429):
        reset_ts = response.headers.get("X-RateLimit-Reset", "unknown")
        raise PermissionError(
            f"GitHub API rate limit exceeded for user '{username}'. "
            f"Rate limit resets at Unix timestamp: {reset_ts}. "
            "Set GITHUB_TOKEN in your .env to increase the limit to 5,000 req/hr."
        )
    response.raise_for_status()


# ══════════════════════════════════════════════════════════════════════════════
#  1. FETCH USER PROFILE
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_github_profile(username: str) -> dict[str, Any]:
    """
    Fetch a GitHub user's public profile via GET /users/{username}.

    Parameters
    ----------
    username : str
        GitHub username (case-insensitive).

    Returns
    -------
    dict with keys:
        name          str | None    Display name
        login         str           GitHub handle
        bio           str | None    Profile bio
        avatar_url    str           Profile picture URL
        html_url      str           GitHub profile page URL
        public_repos  int           Number of public repositories
        followers     int
        following     int
        created_at    str           ISO-8601 account creation date

    Raises
    ------
    ValueError        If user not found (404).
    PermissionError   If rate limited (403 / 429).
    """
    url = f"{GITHUB_API_BASE}/users/{username}"
    logger.debug(f"Fetching GitHub profile: {url}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=_get_headers())

    if not response.is_success:
        _handle_github_error(response, username)

    data = response.json()
    return {
        "name":         data.get("name"),
        "login":        data.get("login", username),
        "bio":          data.get("bio"),
        "avatar_url":   data.get("avatar_url", ""),
        "html_url":     data.get("html_url", ""),
        "public_repos": data.get("public_repos", 0),
        "followers":    data.get("followers", 0),
        "following":    data.get("following", 0),
        "created_at":   data.get("created_at", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  2. FETCH REPOSITORIES
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_repositories(username: str) -> list[dict[str, Any]]:
    """
    Fetch the most recently updated public repositories for ``username``.

    Excludes forked repositories by default (they represent others' work,
    not the candidate's own contributions).

    Parameters
    ----------
    username : str
        GitHub username.

    Returns
    -------
    list[dict]
        Up to ``REPOS_PER_PAGE`` repos, each with:
            name         str
            description  str          "" if None
            language     str | None   None if GitHub could not detect a language
            stars        int
            forks        int
            html_url     str
            updated_at   str          ISO-8601 timestamp
            topics       list[str]    repo topics/tags (may be empty)
            is_fork      bool

    Raises
    ------
    ValueError        If user not found (404).
    PermissionError   If rate limited (403 / 429).
    """
    url    = f"{GITHUB_API_BASE}/users/{username}/repos"
    params = {
        "sort":      "updated",
        "direction": "desc",
        "per_page":  REPOS_PER_PAGE,
        "type":      "owner",    # only repos the user owns (not org repos)
    }
    logger.debug(f"Fetching repos for '{username}': {url}")

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers=_get_headers(), params=params)

    if not response.is_success:
        _handle_github_error(response, username)

    raw: list[dict] = response.json()

    repos: list[dict] = []
    for repo in raw:
        repos.append({
            "name":        repo.get("name", ""),
            "description": (repo.get("description") or "").strip(),
            "language":    repo.get("language"),           # None if undetected — intentional
            "stars":       repo.get("stargazers_count", 0),
            "forks":       repo.get("forks_count", 0),
            "html_url":    repo.get("html_url", ""),
            "updated_at":  repo.get("updated_at", ""),
            "topics":      repo.get("topics") or [],
            "is_fork":     repo.get("fork", False),
        })

    logger.debug(f"Fetched {len(repos)} repos for '{username}'")
    return repos


# ══════════════════════════════════════════════════════════════════════════════
#  3. LANGUAGE STATISTICS
# ══════════════════════════════════════════════════════════════════════════════

def compute_language_stats(repos: list[dict]) -> list[dict[str, Any]]:
    """
    Compute top programming languages by repository count from a list of repos.

    Repos where ``language`` is None (GitHub could not detect a language —
    common for documentation or config-only repos) are silently skipped.
    Forked repos are excluded so the stats reflect the user's own work.

    Parameters
    ----------
    repos : list[dict]
        Raw repo list as returned by ``fetch_repositories()``.

    Returns
    -------
    list[dict]
        Top languages sorted by repo_count descending, each entry:
            language    str    Language name (e.g. "Python")
            repo_count  int    Number of own (non-fork) repos using this language
            percentage  float  Rounded to 1 decimal place

    Examples
    --------
    >>> compute_language_stats([
    ...     {"language": "Python", "is_fork": False},
    ...     {"language": "Python", "is_fork": False},
    ...     {"language": "JavaScript", "is_fork": False},
    ...     {"language": None, "is_fork": False},
    ... ])
    [
        {"language": "Python",     "repo_count": 2, "percentage": 66.7},
        {"language": "JavaScript", "repo_count": 1, "percentage": 33.3},
    ]
    """
    # Count languages — skip None and forks
    counts: dict[str, int] = {}
    for repo in repos:
        if repo.get("is_fork"):
            continue
        lang = repo.get("language")
        if lang:                         # None → skip gracefully
            counts[lang] = counts.get(lang, 0) + 1

    total = sum(counts.values())
    if total == 0:
        return []

    sorted_langs = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    return [
        {
            "language":   lang,
            "repo_count": count,
            "percentage": round((count / total) * 100, 1),
        }
        for lang, count in sorted_langs
    ]


# ══════════════════════════════════════════════════════════════════════════════
#  4.  ACTIVITY LEVEL
# ══════════════════════════════════════════════════════════════════════════════

def _compute_activity_level(repos: list[dict]) -> str:
    """
    Classify the user's recent activity as active / moderate / inactive.

    Uses the ``updated_at`` timestamp of the most recently pushed-to repo.

    Parameters
    ----------
    repos : list[dict]
        Repo list (already sorted by updated_at descending).

    Returns
    -------
    str  one of "active", "moderate", "inactive"
    """
    if not repos:
        return "inactive"

    # Repos are sorted by updated_at desc — take the first valid timestamp
    for repo in repos:
        ts = repo.get("updated_at", "")
        if not ts:
            continue
        try:
            last_updated = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            now          = datetime.now(timezone.utc)
            days_ago     = (now - last_updated).days

            if days_ago <= ACTIVE_DAYS:
                return "active"
            if days_ago <= MODERATE_DAYS:
                return "moderate"
            return "inactive"
        except ValueError:
            continue

    return "inactive"


# ══════════════════════════════════════════════════════════════════════════════
#  5.  MASTER FUNCTION — get_portfolio_summary
# ══════════════════════════════════════════════════════════════════════════════

async def get_portfolio_summary(username: str) -> dict[str, Any]:
    """
    Orchestrate all GitHub API calls and return a complete portfolio summary.

    This is the single function called by the router. Results are cached
    in memory for 1 hour so repeated requests for the same username do not
    hit the GitHub API every time.

    Pipeline
    --------
    1. Check in-memory cache (1-hour TTL) — return immediately if fresh.
    2. Fetch user profile via GET /users/{username}.
    3. Fetch up to 30 repos via GET /users/{username}/repos.
    4. Compute language statistics (non-fork repos only).
    5. Pick top 5 repos by star count.
    6. Compute total stars, total forks, activity level.
    7. Build skill_evidence — unique languages as a "proof of skills" list.
    8. Write result to cache and return.

    Parameters
    ----------
    username : str
        GitHub username (case-insensitive).

    Returns
    -------
    dict with keys:

    profile         dict        name, login, bio, avatar_url, html_url,
                                public_repos, followers, following, created_at
    top_languages   list[dict]  [{language, repo_count, percentage}] sorted desc
    top_repos       list[dict]  top 5 repos by stars
                                [{name, description, language, stars, forks,
                                  html_url, updated_at, topics}]
    total_stars     int         sum of stars across all fetched repos
    total_forks     int         sum of forks across all fetched repos
    activity_level  str         "active" | "moderate" | "inactive"
    skill_evidence  list[str]   unique languages found — the "proof of skills"
    repo_count      int         total repos fetched (≤ 30)

    Raises
    ------
    ValueError        If GitHub user not found (404).
    PermissionError   If GitHub API rate limit exceeded.
    """
    # ── Cache check ───────────────────────────────────────────────────────────
    cached = _check_cache(username)
    if cached:
        return cached

    logger.info(f"Building GitHub portfolio for '{username}' ...")

    # ── Parallel-ish fetch: profile first, then repos ─────────────────────────
    # (We could use asyncio.gather, but sequential keeps error handling cleaner
    #  and both calls are fast — profile is tiny, repos is paginated at 30)
    profile = await fetch_github_profile(username)
    repos   = await fetch_repositories(username)

    # ── Language stats (own repos only) ──────────────────────────────────────
    own_repos   = [r for r in repos if not r.get("is_fork")]
    lang_stats  = compute_language_stats(repos)

    # ── Top repos by star count ───────────────────────────────────────────────
    top_repos = sorted(own_repos, key=lambda r: r.get("stars", 0), reverse=True)
    top_repos = [
        {
            "name":        r["name"],
            "description": r["description"],
            "language":    r["language"],
            "stars":       r["stars"],
            "forks":       r["forks"],
            "html_url":    r["html_url"],
            "updated_at":  r["updated_at"],
            "topics":      r["topics"],
        }
        for r in top_repos[:TOP_REPOS_COUNT]
    ]

    # ── Aggregates ────────────────────────────────────────────────────────────
    total_stars = sum(r.get("stars", 0) for r in own_repos)
    total_forks = sum(r.get("forks", 0) for r in own_repos)

    # ── Activity level ────────────────────────────────────────────────────────
    activity_level = _compute_activity_level(repos)   # use all repos for recency

    # ── Skill evidence — unique non-null languages ────────────────────────────
    skill_evidence = sorted({
        r["language"]
        for r in own_repos
        if r.get("language")
    })

    # ── Assemble result ───────────────────────────────────────────────────────
    summary: dict[str, Any] = {
        "profile":        profile,
        "top_languages":  lang_stats,
        "top_repos":      top_repos,
        "total_stars":    total_stars,
        "total_forks":    total_forks,
        "activity_level": activity_level,
        "skill_evidence": skill_evidence,
        "repo_count":     len(repos),
    }

    _write_cache(username, summary)
    logger.info(
        f"Portfolio built for '{username}' — "
        f"{len(repos)} repos, {len(lang_stats)} languages, "
        f"activity: {activity_level}"
    )
    return summary