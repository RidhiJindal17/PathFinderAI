"""
models/github.py — PathFinder AI  ·  Module IV: GitHub Portfolio Dashboard
===========================================================================
Pydantic v2 request/response schemas for GET /api/github/{username}.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════════════
#  SUB-MODELS
# ══════════════════════════════════════════════════════════════════════════════

class GitHubProfile(BaseModel):
    """Public profile information from GET /users/{username}."""

    name:         str | None = Field(default=None, description="Display name (may be null).")
    login:        str        = Field(...,           description="GitHub username / handle.")
    bio:          str | None = Field(default=None, description="Profile bio.")
    avatar_url:   str        = Field(default="",   description="Profile picture URL.")
    html_url:     str        = Field(default="",   description="GitHub profile page URL.")
    public_repos: int        = Field(default=0,    description="Number of public repositories.")
    followers:    int        = Field(default=0)
    following:    int        = Field(default=0)
    created_at:   str        = Field(default="",   description="ISO-8601 account creation date.")


class LanguageStat(BaseModel):
    """Language frequency entry from compute_language_stats()."""

    language:   str   = Field(..., description="Programming language name.")
    repo_count: int   = Field(..., ge=1, description="Number of own repos using this language.")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of own repos.")


class RepoSummary(BaseModel):
    """Condensed repository entry for the top_repos list."""

    name:        str        = Field(..., description="Repository name.")
    description: str        = Field(default="", description="Repository description.")
    language:    str | None = Field(default=None, description="Primary language (None if undetected).")
    stars:       int        = Field(default=0, description="Star count.")
    forks:       int        = Field(default=0, description="Fork count.")
    html_url:    str        = Field(default="", description="Repository URL on GitHub.")
    updated_at:  str        = Field(default="", description="ISO-8601 last-updated timestamp.")
    topics:      list[str]  = Field(default_factory=list, description="Repository topics/tags.")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN RESPONSE
# ══════════════════════════════════════════════════════════════════════════════

class GitHubPortfolioResponse(BaseModel):
    """
    Full portfolio summary returned by GET /api/github/{username}.

    Fields
    ------
    profile
        Public GitHub profile info (name, bio, avatar, follower counts).

    top_languages
        Up to N languages sorted by repo frequency — shows what the candidate
        actually codes in, not just what they claim on their resume.

    top_repos
        Top 5 repositories by star count — the candidate's most-recognised work.

    total_stars
        Cumulative stars across all own (non-fork) repos — a proxy for impact.

    total_forks
        Cumulative forks — indicates how often others build on their work.

    activity_level
        "active"   — pushed within the last 30 days
        "moderate" — last push was 31–180 days ago
        "inactive" — last push was more than 180 days ago

    skill_evidence
        Unique languages found across all own repos.  This is the "Proof of Work"
        list — concrete evidence the candidate has actually written code in these
        languages, supporting their resume skill claims.

    repo_count
        Total repos fetched (≤ 30 due to API pagination).
    """

    profile:        GitHubProfile         = Field(...)
    top_languages:  list[LanguageStat]    = Field(default_factory=list)
    top_repos:      list[RepoSummary]     = Field(default_factory=list)
    total_stars:    int                   = Field(default=0)
    total_forks:    int                   = Field(default=0)
    activity_level: Literal["active", "moderate", "inactive"] = Field(default="inactive")
    skill_evidence: list[str]             = Field(
        default_factory=list,
        description="Unique languages found across own repos — proof the skills are real.",
    )
    repo_count:     int                   = Field(default=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "profile": {
                    "name":         "Torvalds Linus",
                    "login":        "torvalds",
                    "bio":          "Just a software engineer",
                    "avatar_url":   "https://avatars.githubusercontent.com/u/1024025",
                    "html_url":     "https://github.com/torvalds",
                    "public_repos": 6,
                    "followers":    240000,
                    "following":    0,
                    "created_at":   "2011-09-03T15:26:22Z",
                },
                "top_languages": [
                    {"language": "C",      "repo_count": 3, "percentage": 60.0},
                    {"language": "Python", "repo_count": 2, "percentage": 40.0},
                ],
                "top_repos": [
                    {
                        "name":        "linux",
                        "description": "Linux kernel source tree",
                        "language":    "C",
                        "stars":       190000,
                        "forks":       57000,
                        "html_url":    "https://github.com/torvalds/linux",
                        "updated_at":  "2025-01-15T12:00:00Z",
                        "topics":      ["os", "kernel"],
                    }
                ],
                "total_stars":    191000,
                "total_forks":    58000,
                "activity_level": "active",
                "skill_evidence": ["C", "Python", "Shell"],
                "repo_count":     6,
            }
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
#  ERROR RESPONSE
# ══════════════════════════════════════════════════════════════════════════════

class GitHubErrorResponse(BaseModel):
    """Returned when the GitHub API call fails."""

    error:  str       = Field(..., description="Human-readable error message.")
    detail: str | None = Field(default=None)