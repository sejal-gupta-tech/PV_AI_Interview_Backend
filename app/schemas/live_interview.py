from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class TimingMetadata(BaseModel):
    question_start_time: Optional[datetime] = None
    answer_start_time: Optional[datetime] = None
    answer_end_time: Optional[datetime] = None
    response_delay_ms: Optional[int] = None
    speaking_duration_ms: Optional[int] = None

class CandidateProfile(BaseModel):
    name: str = ""
    education: str = ""
    target_exam: str = ""
    subject: str = ""
    motivation: str = ""
    strengths: List[str] = []
    weaknesses: List[str] = []
    communication_level: str = "Unknown"
    confidence_level: str = "Unknown"
    inconsistencies: List[str] = []

class InterviewMetrics(BaseModel):
    communication: int = 0
    confidence: int = 0
    subject_knowledge: int = 0
    teaching_skill: int = 0
    clarity: int = 0
    consistency: int = 0

class LiveInterviewStartRequest(BaseModel):
    candidate_name: str = ""
    candidate_email: Optional[str] = None
    exam: str = ""
    subject: str = ""
    language: str = "English"
    difficulty: str = "Medium"
    interview_mode: str = "Voice"
    duration: int = 20
    focus: str = "Subject Knowledge"

class LiveInterviewStartResponse(BaseModel):
    session_id: str
    status: str # "active" or "completed"
    first_question: str
    current_stage: str
    audio_url: Optional[str] = None
    candidate: dict = Field(default_factory=dict)
    stages: list = Field(default_factory=list)

class LiveInterviewAnswerRequest(BaseModel):
    session_id: str
    answer_text: str
    timing: Optional[TimingMetadata] = None

class LiveInterviewAnswerResponse(BaseModel):
    session_id: str
    next_question: str
    current_stage: str
    current_difficulty: str
    candidate_profile: CandidateProfile
    metrics: InterviewMetrics
    conversation_length: int
    audio_url: Optional[str] = None

from app.schemas.speech import AudioMetadata, VoiceState, StructuredError

class ProcessingMetrics(BaseModel):
    stt_ms: int = 0
    interview_ms: int = 0
    tts_ms: int = 0
    total_ms: int = 0

class ConversationTurn(BaseModel):
    role: str # "interviewer" or "candidate"
    content: str
    stage: str = "Unknown"
    topic: str = "General"
    difficulty: str = "Medium"
    follow_up_reason: str = ""
    candidate_audio: Optional[AudioMetadata] = None
    ai_audio: Optional[AudioMetadata] = None
    stt_confidence: Optional[float] = None
    processing_time: Optional[ProcessingMetrics] = None
    timing: Optional[TimingMetadata] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class VoiceStateResponse(BaseModel):
    request_id: str
    session_id: str
    transcript: str
    next_question: str
    audio_url: str
    metrics: InterviewMetrics
    candidate_profile: CandidateProfile
    voice_state: VoiceState
    turn: int
    processing: ProcessingMetrics
    error: Optional[StructuredError] = None

# Database Model for live_interview_sessions
class LiveInterviewSessionDB(BaseModel):
    session_id: str
    candidate_name: str
    exam: str
    subject: str
    language: str
    current_difficulty: str
    interview_mode: str
    duration: int
    focus: str = "Subject Knowledge"
    current_stage: str
    status: str = "active"
    retries: int = 0
    profile: CandidateProfile = Field(default_factory=CandidateProfile)
    metrics: InterviewMetrics = Field(default_factory=InterviewMetrics)
    conversation: List[ConversationTurn] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GenerateQuestionRequest(BaseModel):
    exam: str = Field(..., description="Name of the exam")
    subject: str = Field(..., description="Subject for the question")
    difficulty: str = Field(..., description="Difficulty level (e.g., Easy, Medium, Hard)")
    language: str = Field(..., description="Language for the question (e.g., English, Hindi)")
    question_number: int = Field(1, description="The current question number in the interview sequence")

class GenerateQuestionResponse(BaseModel):
    question: str = Field(..., description="The generated interview question")
    audio_url: Optional[str] = Field(None, description="The URL of the generated audio file")
    question_number: int = Field(..., description="The current question number")
    voice_supported: Optional[bool] = None
    voice: Optional[str] = None
    language: Optional[str] = None

class EvaluateAnswerRequest(BaseModel):
    interview_id: str
    question_number: int
    question: str
    candidate_answer: str
    exam: str
    subject: str
    difficulty: str
    language: str

class EvaluateAnswerResponse(BaseModel):
    score: int
    technical_accuracy: int
    communication: int
    strengths: List[str]
    weaknesses: List[str]
    feedback: str
    follow_up_required: bool
    follow_up_question: Optional[str] = None
    follow_up_audio_url: Optional[str] = None
    voice_supported: Optional[bool] = None
    voice: Optional[str] = None
    language: Optional[str] = None

class LiveInterviewChatRequest(BaseModel):
    interview_id: str
    candidate_message: str
    exam: str
    subject: str
    language: str = "English"
    experience_level: str = "Entry Level"
    conversation_history: List[Dict[str, str]] = []

class AvatarBehavior(BaseModel):
    emotion: str = "neutral"
    animation: str = "idle"
    gesture: str = "none"
    head_direction: str = "candidate"
    eye_contact: bool = True
    posture: str = "professional"
    speaking_speed: str = "normal"

class LiveInterviewChatResponse(BaseModel):
    stage: str
    interviewer_message: str
    next_action: str
    avatar: AvatarBehavior = Field(default_factory=AvatarBehavior)
    audio_url: Optional[str] = None
    voice_supported: Optional[bool] = None
    voice: Optional[str] = None
    language: Optional[str] = None
