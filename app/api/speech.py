from fastapi import APIRouter
from app.schemas.speech import SpeechGenerateRequest, SpeechGenerateResponse
from app.services.tts_service import SpeechService

router = APIRouter(prefix="/api/v1/speech", tags=["Speech"])

@router.post("/generate", response_model=SpeechGenerateResponse)
async def generate_speech(request: SpeechGenerateRequest):
    return SpeechService.generate_speech(
        text=request.text,
        language=request.language
    )
