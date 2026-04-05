"""
models/translator.py — PathFinder AI
Pydantic schemas for the Corporate Translator feature.
Note: The primary translator endpoint lives at POST /api/roadmap/translate
and uses models/roadmap.py schemas. This file is for the legacy
/api/translator/translate endpoint stub.
"""

from pydantic import BaseModel, Field


class TranslatorRequest(BaseModel):
    informal_text: str = Field(
        ...,
        min_length=5,
        description="The candidate's informal description of their experience",
    )
    target_role: str = Field(
        default="",
        description="Optional target job title to guide the rewrite",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "informal_text": "i used to fix computers for my neighbours",
                "target_role":   "IT Support Engineer",
            }
        }
    }


class TranslatorResponse(BaseModel):
    original:      str = Field(..., description="The original informal text")
    polished_text: str = Field(..., description="The high-impact, professional rewrite")
    professional:  str = Field(..., description="Backward-compatible field for rewritten bullet point")
    tone:          str = Field(default="professional", description="The tone of the rewrite")