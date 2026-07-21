from typing import BinaryIO
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.voice_config import voice_settings
from app.services.interfaces.stt_provider import BaseSTTProvider
from app.schemas.speech import StructuredError
import tempfile
import os
import aiofiles

class OpenAISTTProvider(BaseSTTProvider):
    async def transcribe(self, audio_stream: BinaryIO, filename: str) -> dict:
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError(StructuredError(code="CONFIG_ERROR", message="GROQ_API_KEY or OpenAI API key missing", retry=False).model_dump_json())
            
        base_url = "https://api.groq.com/openai/v1" if settings.GROQ_API_KEY else None
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        # Whisper requires a file object with a name attribute, or a path.
        # We write it to a temp file first.
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_audio:
                temp_audio.write(audio_stream.read())
                temp_audio_path = temp_audio.name
                
            with open(temp_audio_path, "rb") as audio_file:
                response = await client.audio.transcriptions.create(
                    model=voice_settings.stt_model,
                    file=audio_file
                )
                
            os.remove(temp_audio_path)
            
            # OpenAI API returns text. Confidence is not natively supported by basic whisper-1 API 
            # unless using word timestamps. We'll mock confidence to 0.95 for now.
            return {
                "transcript": response.text,
                "confidence": 0.95,
                "language": "en"
            }
        except Exception as e:
            if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            raise ValueError(StructuredError(code="STT_FAILURE", message=str(e), retry=True).model_dump_json())
