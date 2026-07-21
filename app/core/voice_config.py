from pydantic_settings import BaseSettings

class VoiceConfig(BaseSettings):
    chat_model: str = "llama-3.3-70b-versatile"
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"
    stt_model: str = "whisper-large-v3"
    audio_format: str = "mp3"
    sample_rate: int = 24000
    max_audio_size_mb: int = 10
    
    class Config:
        env_prefix = "VOICE_"

voice_settings = VoiceConfig()
