from fastapi import APIRouter, HTTPException, UploadFile, File
import time
import uuid
from app.schemas.live_interview import (
    LiveInterviewStartRequest,
    LiveInterviewStartResponse,
    LiveInterviewAnswerRequest,
    LiveInterviewAnswerResponse,
    VoiceStateResponse,
    LiveInterviewSessionDB
)
from app.services.interview_engine import InterviewEngineService
from app.services.voice_orchestrator import VoiceOrchestrator
from app.services.openai_tts_provider import OpenAITTSProvider
from app.services.local_audio_storage import LocalAudioStorage
from app.core.database import get_db

import logging
logger = logging.getLogger("backend_initialization")
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api/live-interview", tags=["Live Interview"])

@router.post("/start", response_model=LiveInterviewStartResponse)
async def start_live_interview(request: LiveInterviewStartRequest):
    try:
        # Check and log missing fields
        missing_fields = []
        if not request.candidate_name: missing_fields.append("candidate_name")
        if not request.exam: missing_fields.append("exam")
        if not request.subject: missing_fields.append("subject")
        if not request.language: missing_fields.append("language")
        
        if missing_fields:
            logger.warning(f"Frontend is missing the following fields in /start request: {', '.join(missing_fields)}")
            
        logger.info(f"Session Creation: Starting session for {request.candidate_name or 'Unknown'}")
        result = await InterviewEngineService.start_session(
            candidate_name=request.candidate_name or "Unknown",
            candidate_email=request.candidate_email,
            exam=request.exam or "Unknown",
            subject=request.subject or "Unknown",
            language=request.language or "English",
            difficulty=request.difficulty or "Medium",
            interview_mode=request.interview_mode or "Voice",
            duration=request.duration or 20
        )
        logger.info(f"First Question Generation: Generated question: {result['first_question']}")
        
        # Generate TTS for first question
        logger.info("TTS Generation: Synthesizing first question audio...")
        
        tts_provider = OpenAITTSProvider()
        storage = LocalAudioStorage()
        request_id = str(uuid.uuid4())
        
        tts_stream = await tts_provider.synthesize(text=result["first_question"])
        tts_filename = f"ai_first_{request_id}.mp3"
        
        logger.info(f"Audio File Saving: Saving to {tts_filename}...")
        await storage.save(tts_stream, tts_filename, "audio/mpeg")
        
        result["audio_url"] = storage.get_url(tts_filename)
        
        logger.info(f"Final API Response: Returning active session {result['session_id']}")
        return LiveInterviewStartResponse(**result)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Initialization Failed: {error_msg}")
        
        # If the error is already a JSON string from our providers, parse it. Otherwise wrap it.
        if "StructuredError" in error_msg or "TTS_FAILURE" in error_msg or "CONFIG_ERROR" in error_msg:
            raise HTTPException(status_code=500, detail=error_msg)
            
        raise HTTPException(status_code=500, detail={"code": "INITIALIZATION_FAILED", "message": error_msg, "retry": True})

@router.post("/answer", response_model=LiveInterviewAnswerResponse)
async def submit_live_answer(request: LiveInterviewAnswerRequest):
    try:
        result = await InterviewEngineService.process_answer(
            session_id=request.session_id,
            answer_text=request.answer_text,
            timing=request.timing
        )
        return LiveInterviewAnswerResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/{session_id}/voice", response_model=VoiceStateResponse)
async def process_voice_answer(session_id: str, file: UploadFile = File(...)):
    """
    Process a voice answer for an active interview session.
    """
    try:
        response = await VoiceOrchestrator.process_voice_turn(
            session_id=session_id,
            audio_stream=file.file,
            filename=file.filename,
            mime_type=file.content_type
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resume/{session_id}")
async def resume_session(session_id: str):
    db = get_db()
    session = await db["live_interview_sessions"].find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return LiveInterviewSessionDB(**session).model_dump()

@router.get("/status/{session_id}")
async def get_session_status(session_id: str):
    db = get_db()
    session = await db["live_interview_sessions"].find_one({"session_id": session_id}, {"status": 1, "current_stage": 1, "retries": 1})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return {
        "status": session.get("status", "active"),
        "current_stage": session.get("current_stage"),
        "retries": session.get("retries", 0)
    }
