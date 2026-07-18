from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.mock_interview import (
    MockQuestionRequest,
    MockQuestion,
    MockStartRequest,
    MockStartResponse,
    MockAnswerRequest,
    MockAnswerResponse,
    MockEndRequest,
    MockReportResponse
)
from app.services.question_generator import QuestionGeneratorService
from app.services.mock_interview_service import MockInterviewService

router = APIRouter(prefix="/api/mock-interview", tags=["Mock Interview"])

@router.post("/questions", response_model=List[MockQuestion])
async def generate_questions(request: MockQuestionRequest):
    try:
        return await QuestionGeneratorService.generate_questions(
            exam=request.exam,
            subject=request.subject,
            difficulty=request.difficulty,
            language=request.language,
            count=request.count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start", response_model=MockStartResponse)
async def start_mock_interview(request: MockStartRequest):
    try:
        session_id = await MockInterviewService.start_session(
            exam=request.exam,
            subject=request.subject,
            difficulty=request.difficulty,
            language=request.language,
            questions=request.questions
        )
        return MockStartResponse(session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/answer", response_model=MockAnswerResponse)
async def submit_mock_answer(request: MockAnswerRequest):
    try:
        is_correct = await MockInterviewService.submit_answer(
            session_id=request.session_id,
            question_id=request.question_id,
            selected_option=request.selected_option
        )
        return MockAnswerResponse(is_correct=is_correct)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end", response_model=MockReportResponse)
async def end_mock_interview(request: MockEndRequest):
    try:
        report = await MockInterviewService.complete_and_generate_report(
            session_id=request.session_id
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
