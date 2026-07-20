from io import BytesIO
from typing import BinaryIO
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.voice_config import voice_settings
from app.services.interfaces.tts_provider import BaseTTSProvider
from app.schemas.speech import StructuredError

class OpenAITTSProvider(BaseTTSProvider):
    async def synthesize(self, text: str, **kwargs) -> BinaryIO:
        if not settings.OPENAI_API_KEY:
            raise ValueError(StructuredError(code="CONFIG_ERROR", message="OpenAI API key missing", retry=False).model_dump_json())
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        try:
            response = await client.audio.speech.create(
                model=voice_settings.tts_model,
                voice=voice_settings.tts_voice,
                input=text,
                response_format=voice_settings.audio_format
            )
            audio_data = response.read()
            return BytesIO(audio_data)
        except Exception as e:
            raise ValueError(StructuredError(code="TTS_FAILURE", message=str(e), retry=True).model_dump_json())
