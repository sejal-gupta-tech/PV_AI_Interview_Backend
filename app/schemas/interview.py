from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

# Requests
class InterviewStartRequest(BaseModel):
    language: str = Field(..., description="Allowed: english, hindi, both")
    exam: str
    subject: str
    topics: List[str]
    difficulty: str = Field(..., description="Allowed: easy, medium, hard")
    total_questions: int
    time_per_question_seconds: int = Field(default=60, ge=10, le=300)

class InterviewAnswerRequest(BaseModel):
    question_id: str
    selected_option: str
    answer_method: str = "VOICE"

# Responses
class InterviewStartResponse(BaseModel):
    session_id: str
    status: str
    language: str
    exam: str
    subject: str
    topics: List[str]
    difficulty: str
    total_questions: int
    time_per_question_seconds: int

class LocalizedText(BaseModel):
    en: str
    hi: str

class MCQOption(BaseModel):
    id: str
    text: LocalizedText

class QuestionResponse(BaseModel):
    question_id: str
    question_text: LocalizedText
    options: List[MCQOption]
    difficulty: str
    subject: str
    topic: str
    time_limit_seconds: int
    started_at: str
    expires_at: str
    provider_type: str
    ai_status: str

class AnswerResponse(BaseModel):
    correct: bool
    score: int
    explanation: Optional[LocalizedText] = None
    next_difficulty: str
    status: str

class InterviewCompleteResponse(BaseModel):
    session_id: str
    total_questions: int
    attempted: int
    correct: int
    wrong: int
    skipped: int
    score: int
    percentage: float
    completed_at: str

class MonitoringEventRequest(BaseModel):
    event_type: str

class MonitoringEventResponse(BaseModel):
    status: str
