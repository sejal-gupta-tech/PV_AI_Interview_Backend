from pydantic_settings import BaseSettings

class VoiceConfig(BaseSettings):
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"
    stt_model: str = "whisper-1"
    audio_format: str = "mp3"
    sample_rate: int = 24000
    max_audio_size_mb: int = 10
    
    class Config:
        env_prefix = "VOICE_"

voice_settings = VoiceConfig()
