from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class VoiceState(str, Enum):
    INITIALIZING = "INITIALIZING"
    AI_SPEAKING = "AI_SPEAKING"
    WAITING_FOR_CANDIDATE = "WAITING_FOR_CANDIDATE"
    RECORDING = "RECORDING"
    TRANSCRIBING = "TRANSCRIBING"
    EVALUATING = "EVALUATING"
    GENERATING_QUESTION = "GENERATING_QUESTION"
    GENERATING_SPEECH = "GENERATING_SPEECH"
    READY = "READY"
    ERROR = "ERROR"

class AudioMetadata(BaseModel):
    file_name: str
    duration: float
    sample_rate: int
    mime_type: str
    created_at: str

class TTSRequest(BaseModel):
    text: str
    language: str = "en"

class TTSResponse(BaseModel):
    audio_url: str
    duration: float
    metadata: Optional[AudioMetadata] = None

class STTResponse(BaseModel):
    transcript: str
    confidence: float
    language: str

class SpeechGenerateRequest(BaseModel):
    text: str
    language: str = "en"

class SpeechGenerateResponse(BaseModel):
    audio_url: Optional[str]
    visemes: List[dict] = []
    provider: Optional[str]
    status: str

class StructuredError(BaseModel):
    code: str
    message: str
    retry: bool
