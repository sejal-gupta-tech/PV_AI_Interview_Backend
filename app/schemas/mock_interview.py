from pydantic import BaseModel, Field
from typing import List, Optional

class MockQuestionRequest(BaseModel):
    exam: str
    subject: str
    difficulty: str
    language: str
    count: int = 10

class MockQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    correctAnswer: int
    explanation: str

class MockStartRequest(BaseModel):
    exam: str
    subject: str
    difficulty: str
    language: str
    questions: List[MockQuestion]

class MockStartResponse(BaseModel):
    session_id: str
    message: str = "Mock interview session started"

class MockAnswerRequest(BaseModel):
    session_id: str
    question_id: int
    selected_option: int

class MockAnswerResponse(BaseModel):
    status: str = "success"
    is_correct: bool

class MockEndRequest(BaseModel):
    session_id: str

class ReportRecommendation(BaseModel):
    weak_topics: List[str]
    strong_topics: List[str]
    recommendations: List[str]
    ai_feedback: str

class MockReportResponse(BaseModel):
    session_id: str
    overall_score: int
    accuracy: float
    correct: int
    incorrect: int
    skipped: int
    weak_topics: List[str]
    strong_topics: List[str]
    recommendations: List[str]
    ai_feedback: str
