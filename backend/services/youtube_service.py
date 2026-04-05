"""
services/youtube_service.py — PathFinder AI
Searches YouTube Data API v3 for free learning resources.
"""

import logging
import httpx

from config import settings

logger = logging.getLogger(__name__)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


async def search_videos(skill: str, max_results: int = 5) -> list[dict]:
    """
    Queries YouTube Data API v3 for tutorial videos matching the given skill.

    Args:
        skill       : skill or topic to search (e.g. "Python for beginners")
        max_results : number of videos to return (1–10)

    Returns:
        List of video dicts: title, channel, thumbnail, url, video_id

    Raises:
        httpx.HTTPStatusError on API errors.
    """
    if not settings.youtube_api_key:
        logger.warning("YOUTUBE_API_KEY not set — returning empty results.")
        return []

    params = {
        "part": "snippet",
        "q": f"{skill} tutorial free",
        "type": "video",
        "maxResults": max_results,
        "relevanceLanguage": "en",
        "videoEmbeddable": "true",
        "key": settings.youtube_api_key,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(YOUTUBE_SEARCH_URL, params=params)

    response.raise_for_status()
    items = response.json().get("items", [])

    videos = []
    for item in items:
        video_id = item.get("id", {}).get("videoId", "")
        snippet = item.get("snippet", {})
        videos.append({
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "description": snippet.get("description", "")[:200],
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "published_at": snippet.get("publishedAt", ""),
        })

    logger.debug(f"Found {len(videos)} YouTube videos for skill: '{skill}'")
    return videos