from pydantic import BaseModel
from typing import List, Optional, Any

class SpeechGenerateRequest(BaseModel):
    text: str
    language: str = "hi-IN"

class Viseme(BaseModel):
    time_ms: int
    viseme: str

class SpeechGenerateResponse(BaseModel):
    audio_url: Optional[str] = None
    visemes: List[Viseme] = []
    provider: Optional[str] = None
    status: str = "not_configured"
