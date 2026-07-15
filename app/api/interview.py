from fastapi import APIRouter, HTTPException
from app.schemas.interview import (
    InterviewStartRequest, 
    InterviewStartResponse,
    QuestionResponse,
    InterviewAnswerRequest,
    AnswerResponse,
    InterviewCompleteResponse,
    MonitoringEventRequest,
    MonitoringEventResponse
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/api/v1/interviews", tags=["Interviews"])

@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest):
    return await InterviewService.start_session(
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
        return await InterviewService.get_question(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, request: InterviewAnswerRequest):
    try:
        return await InterviewService.submit_answer(
            session_id=session_id,
            question_id=request.question_id,
            selected_option=request.selected_option,
            answer_method=request.answer_method
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{session_id}/complete", response_model=InterviewCompleteResponse)
async def complete_interview(session_id: str):
    try:
        # Await the async report generation and save
        report = await InterviewService.complete_interview(session_id)
        return InterviewCompleteResponse(
            session_id=report.session_id,
            total_questions=report.total_questions,
            attempted=report.attempted,
            correct=report.correct,
            wrong=report.wrong,
            skipped=report.skipped,
            score=report.score,
            percentage=report.percentage,
            completed_at=report.completed_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{session_id}/monitoring", response_model=MonitoringEventResponse)
async def save_monitoring_event(session_id: str, request: MonitoringEventRequest):
    try:
        await InterviewService.save_monitoring_event(session_id, request.event_type)
        return MonitoringEventResponse(status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
