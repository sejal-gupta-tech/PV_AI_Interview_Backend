from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
from app.schemas.speech import SpeechGenerateRequest, SpeechGenerateResponse, TTSRequest, TTSResponse, STTResponse
from app.services.tts_service import SpeechService
from app.services.piper_tts_service import PiperTTSService
from app.services.openai_tts_provider import OpenAITTSProvider
from app.services.openai_stt_provider import OpenAISTTProvider
from app.services.local_audio_storage import LocalAudioStorage

router = APIRouter(prefix="/api/v1/speech", tags=["Speech"])

@router.post("/tts", response_model=TTSResponse)
async def generate_speech_openai(request: TTSRequest):
    try:
        provider = OpenAITTSProvider()
        audio_stream = await provider.synthesize(text=request.text)
        
        storage = LocalAudioStorage()
        filename = f"{uuid.uuid4().hex}.mp3"
        metadata = await storage.save(audio_stream, filename, "audio/mpeg")
        
        return TTSResponse(
            audio_url=storage.get_url(filename),
            duration=metadata.duration,
            metadata=metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stt", response_model=STTResponse)
async def transcribe_speech_openai(file: UploadFile = File(...)):
    try:
        provider = OpenAISTTProvider()
        result = await provider.transcribe(audio_stream=file.file, filename=file.filename)
        return STTResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def voice_status():
    from app.core.voice_config import voice_settings
    return {
        "status": "online",
        "tts_model": voice_settings.TTS_MODEL,
        "stt_model": voice_settings.STT_MODEL,
        "tts_voice": voice_settings.TTS_VOICE
    }

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
