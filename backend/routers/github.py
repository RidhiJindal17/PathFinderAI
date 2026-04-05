"""
routers/github.py — PathFinder AI  ·  Module IV: GitHub Portfolio Dashboard
============================================================================
HTTP routing for the GitHub Portfolio feature.

Endpoints
---------
GET /api/github/{username}
    Fetches a complete portfolio summary for the given GitHub username.
    Results are served from a 1-hour in-memory cache when available.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Path, Query, status

from models.github import GitHubErrorResponse, GitHubPortfolioResponse
from services.github_service import get_portfolio_summary

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{username}",
    response_model=GitHubPortfolioResponse,
    summary="Fetch GitHub portfolio evidence dashboard for a user",
    responses={
        200: {
            "description": "Portfolio fetched successfully",
            "model":       GitHubPortfolioResponse,
        },
        404: {
            "description": "GitHub user not found",
            "model":       GitHubErrorResponse,
        },
        429: {
            "description": "GitHub API rate limit exceeded",
            "model":       GitHubErrorResponse,
        },
        502: {
            "description": "GitHub API returned an unexpected error",
        },
    },
)
async def get_github_portfolio(
    username: str = Path(
        ...,
        description="GitHub username to fetch (e.g. 'torvalds')",
        min_length=1,
        max_length=39,
    ),
) -> GitHubPortfolioResponse:
    """
    **Fetch a GitHub user's Portfolio Evidence Dashboard.**

    ### What this endpoint returns

    | Field | Description |
    |---|---|
    | `profile` | Name, bio, avatar, follower counts |
    | `top_languages` | Languages ranked by repo count with percentages |
    | `top_repos` | Top 5 repos by star count |
    | `total_stars` | Total stars across all own repos |
    | `total_forks` | Total forks — shows how widely used their code is |
    | `activity_level` | `active` / `moderate` / `inactive` based on recency |
    | `skill_evidence` | Unique languages — **proof the resume skills are real** |

    ### Caching
    Results are cached in memory for **1 hour**.  Repeated calls for the same
    username within that window return instantly without hitting GitHub.

    ### Rate limiting
    Without a GITHUB_TOKEN the GitHub API allows 60 requests/hr per IP.
    Set `GITHUB_TOKEN` in `.env` to raise this to 5,000 req/hr.

    ### Usage in PathFinder AI
    Call this endpoint after the skill-gap analysis to show the recruiter
    concrete evidence that the candidate has actually written code in the
    languages they listed on their resume.
    """
    logger.info(f"GitHub portfolio request for username: '{username}'")

    try:
        summary = await get_portfolio_summary(username)

    except ValueError as exc:
        # 404 — user not found
        logger.warning(f"GitHub user not found: '{username}' — {exc}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error":  f"GitHub user '{username}' not found.",
                "detail": (
                    "Make sure the username is spelled correctly and the "
                    "account is public. GitHub usernames are case-insensitive."
                ),
            },
        )

    except PermissionError as exc:
        # 403 / 429 — rate limited
        logger.warning(f"GitHub rate limit hit for '{username}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error":  "GitHub API rate limit exceeded.",
                "detail": (
                    "The server has hit GitHub's unauthenticated rate limit (60 req/hr). "
                    "Set GITHUB_TOKEN in the .env file to increase this to 5,000 req/hr. "
                    "Get a free token at: https://github.com/settings/tokens"
                ),
            },
        )

    except Exception as exc:
        logger.exception(f"Unexpected error fetching GitHub portfolio for '{username}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API returned an unexpected error: {exc}",
        )

    # ── Deserialise into Pydantic response model ──────────────────────────────
    from models.github import GitHubProfile, LanguageStat, RepoSummary

    return GitHubPortfolioResponse(
        profile        = GitHubProfile(**summary["profile"]),
        top_languages  = [LanguageStat(**l) for l in summary["top_languages"]],
        top_repos      = [RepoSummary(**r)  for r in summary["top_repos"]],
        total_stars    = summary["total_stars"],
        total_forks    = summary["total_forks"],
        activity_level = summary["activity_level"],
        skill_evidence = summary["skill_evidence"],
        repo_count     = summary["repo_count"],
    )