"""
routers/translator.py — PathFinder AI
Legacy Corporate Translator endpoint.
Primary translator is at POST /api/roadmap/translate.
"""

from fastapi import APIRouter, HTTPException, status
from models.translator import TranslatorRequest, TranslatorResponse
from services.gemini_service import translate_to_professional

router = APIRouter()


@router.post(
    "/translate",
    response_model=TranslatorResponse,
    summary="Rewrite informal experience into professional language (also at /api/roadmap/translate)",
)
async def translate_experience(payload: TranslatorRequest):
    """
    Accepts informal work experience and rewrites it as a professional
    resume bullet point using Google Gemini.
    """
    if not payload.informal_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="informal_text cannot be empty.",
        )
    try:
        result = translate_to_professional(
            informal_text=payload.informal_text,
        )
        return TranslatorResponse(
            original=payload.informal_text,
            professional=result["polished_text"],
            polished_text=result["polished_text"],
            tone=result["tone"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error: {exc}",
        )