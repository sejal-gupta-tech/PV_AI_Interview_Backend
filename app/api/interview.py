from fastapi import APIRouter, HTTPException
from app.schemas.interview import (
    InterviewStartRequest, 
    InterviewStartResponse,
    QuestionResponse,
    InterviewAnswerRequest,
    AnswerResponse
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/api/v1/interviews", tags=["Interviews"])

@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest):
    return InterviewService.start_session(
        language=request.language,
        exam=request.exam,
        subject=request.subject,
        topics=request.topics,
        difficulty=request.difficulty,
        total_questions=request.total_questions,
        time_per_question_seconds=request.time_per_question_seconds
    )

@router.get("/{session_id}/question", response_model=QuestionResponse)
async def get_question(session_id: str):
    try:
        return InterviewService.get_question(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, request: InterviewAnswerRequest):
    try:
        return InterviewService.submit_answer(
            session_id=session_id,
            question_id=request.question_id,
            selected_option=request.selected_option,
            answer_method=request.answer_method
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
