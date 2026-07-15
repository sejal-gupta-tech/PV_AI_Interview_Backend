from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class InterviewSessionDB(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    exam: str
    subject: str
    language: str
    difficulty: str
    total_questions: int
    time_per_question: int
    interview_status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # New production-ready fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: Optional[str] = None
    user_agent: Optional[str] = None
    browser: Optional[str] = None
    ip_address: Optional[str] = None
    total_score: Optional[int] = None
    maximum_score: Optional[int] = None
    percentage: Optional[float] = None
    interview_mode: Optional[str] = None
    avatar_enabled: Optional[bool] = None
    camera_enabled: Optional[bool] = None
    microphone_enabled: Optional[bool] = None

class QuestionServedDB(BaseModel):
    session_id: str
    question_id: str
    question_text: Dict[str, str]
    options: List[Dict[str, Any]]
    correct_answer: str
    question_number: int
    timestamp: datetime
    
    # New production-ready fields
    category: Optional[str] = None
    difficulty: Optional[str] = None
    language: Optional[str] = None
    question_type: Optional[str] = None
    marks: Optional[int] = None
    negative_marks: Optional[int] = None
    served_at: Optional[datetime] = None

class UserAnswerDB(BaseModel):
    session_id: str
    question_id: str
    selected_option: str
    correct_option: str
    is_correct: bool
    explanation: Optional[Dict[str, str]] = None
    time_taken: float
    points_awarded: int
    answered_at: datetime
    
    # New production-ready fields
    answer_status: Optional[str] = None
    response_type: Optional[str] = None
    transcript: Optional[str] = None
    evaluation_source: Optional[str] = None

class FinalReportDB(BaseModel):
    session_id: str
    total_questions: int
    attempted: int
    correct: int
    wrong: int
    skipped: int
    score: int
    percentage: float
    completed_at: datetime
    
    # New production-ready fields
    total_time_taken: Optional[float] = None
    average_time_per_question: Optional[float] = None
    accuracy: Optional[float] = None
    performance_level: Optional[str] = None

class MonitoringEventDB(BaseModel):
    session_id: str
    event_type: str
    timestamp: datetime
    
    # New production-ready fields
    event_description: Optional[str] = None
    severity: Optional[str] = None
    screenshot_reference: Optional[str] = None
    event_time: Optional[datetime] = None
