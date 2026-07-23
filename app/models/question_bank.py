from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class QuestionBankDBModel(BaseModel):
    exam: str
    subject: str
    topic: str
    subtopic: Optional[str] = None
    difficulty: str
    language: str
    question: str
    options: List[str]
    correctAnswer: int
    explanation: str
    marks: int = 1
    negativeMarks: float = 0.0
    verified: bool = False
    questionHash: str
    source: str = "AI_Generator"
    createdBy: str = "System"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class QuestionGenerationJobDBModel(BaseModel):
    job_id: str
    status: str = "Pending" # Pending, Running, Completed, Failed, Cancelled
    current_exam: Optional[str] = None
    current_subject: Optional[str] = None
    current_topic: Optional[str] = None
    current_difficulty: Optional[str] = None
    current_language: Optional[str] = None
    generated_count: int = 0
    saved_count: int = 0
    skipped_count: int = 0
    duplicate_count: int = 0
    failed_batches: int = 0
    total_batches: int = 0
    progress_percentage: float = 0.0
    started_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
