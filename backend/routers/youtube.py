"""
routers/youtube.py — PathFinder AI
Searches YouTube Data API v3 for free learning resources.
"""

from fastapi import APIRouter, HTTPException, Query, status
from models.youtube import YouTubeResourceResponse, YouTubeVideo
from services.youtube_service import search_videos

router = APIRouter()


@router.get(
    "/resources",
    response_model=YouTubeResourceResponse,
    summary="Find free YouTube learning resources for a skill",
)
async def get_learning_resources(
    skill: str = Query(..., description="Skill to search (e.g. 'python for beginners')"),
    max_results: int = Query(default=5, ge=1, le=10),
):
    """
    Queries the YouTube Data API v3 for tutorial videos matching the skill.
    Returns video title, channel, thumbnail URL, and direct YouTube link.
    Requires YOUTUBE_API_KEY in .env.
    """
    try:
        videos = await search_videos(skill=skill, max_results=max_results)
        video_objects = [YouTubeVideo(**v) for v in videos]
        return YouTubeResourceResponse(skill=skill, videos=video_objects)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"YouTube API error: {exc}",
        )