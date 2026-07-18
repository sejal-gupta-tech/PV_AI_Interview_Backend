from fastapi import APIRouter
from app.schemas.speech import SpeechGenerateRequest, SpeechGenerateResponse
from app.services.tts_service import SpeechService
from app.services.piper_tts_service import PiperTTSService

router = APIRouter(prefix="/api/v1/speech", tags=["Speech"])

@router.post("/generate", response_model=SpeechGenerateResponse)
async def generate_speech(request: SpeechGenerateRequest):
    return SpeechService.generate_speech(
        text=request.text,
        language=request.language
    )
@router.post("/piper")
async def generate_speech_piper(request: SpeechGenerateRequest):
    try:
        filename = PiperTTSService.generate_speech(
            text=request.text, 
            language=request.language
        )
        return {
            "status": "success",
            "filename": filename,
            "audio_url": f"/audio/{filename}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Piper TTS generation failed."
        }
