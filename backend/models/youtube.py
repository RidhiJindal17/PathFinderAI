"""
models/youtube.py — PathFinder AI
Pydantic schemas for YouTube learning resources.
"""

from pydantic import BaseModel, Field


class YouTubeVideo(BaseModel):
    video_id:     str = Field(default="")
    title:        str = Field(default="")
    channel:      str = Field(default="")
    description:  str = Field(default="")
    thumbnail:    str = Field(default="")
    url:          str = Field(default="")
    published_at: str = Field(default="")


class YouTubeResourceResponse(BaseModel):
    skill:  str              = Field(...)
    videos: list[YouTubeVideo] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "skill": "python",
                "videos": [
                    {
                        "video_id":    "rfscVS0vtbw",
                        "title":       "Python for Beginners – Full Course",
                        "channel":     "freeCodeCamp.org",
                        "description": "Learn Python basics in this full course...",
                        "thumbnail":   "https://i.ytimg.com/vi/rfscVS0vtbw/mqdefault.jpg",
                        "url":         "https://www.youtube.com/watch?v=rfscVS0vtbw",
                        "published_at":"2022-03-15T00:00:00Z",
                    }
                ],
            }
        }
    }