from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.schemas.live_interview import (
    GenerateQuestionRequest, 
    GenerateQuestionResponse,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    LiveInterviewChatRequest,
    LiveInterviewChatResponse
)
from app.services.live_interview_ai_service import LiveInterviewAIService
from app.services.speech_to_text_service import SpeechToTextService
from app.services.interview_evaluation_service import InterviewEvaluationService
from app.services.text_to_speech_service import TextToSpeechService

router = APIRouter(prefix="/api/live-interview", tags=["Live Interview"])

@router.post("/generate-question", response_model=GenerateQuestionResponse)
async def generate_question(request: GenerateQuestionRequest):
    try:
        question = await LiveInterviewAIService.generate_question(
            exam=request.exam,
            subject=request.subject,
            difficulty=request.difficulty,
            language=request.language
        )
        
        # Phase 4: Generate Speech for the question
        tts_result = TextToSpeechService.generate_speech(question, request.language)
        
        return GenerateQuestionResponse(
            question=question,
            audio_url=tts_result.get("audio_url"),
            question_number=request.question_number,
            voice_supported=tts_result.get("voice_supported"),
            voice=tts_result.get("voice"),
            language=tts_result.get("language")
        )
    except ValueError as e:
        # Validation or configuration error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Internal server error (e.g. OpenAI failure)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe")
async def transcribe(
    interview_id: str = Form(...),
    question_number: int = Form(...),
    audio: UploadFile = File(...)
):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
        
    supported_extensions = [".wav", ".mp3", ".webm"]
    if not any(audio.filename.lower().endswith(ext) for ext in supported_extensions):
        raise HTTPException(status_code=400, detail="Unsupported audio type. Please upload .wav, .mp3, or .webm")
        
    try:
        transcript = await SpeechToTextService.transcribe_audio(
            interview_id=interview_id,
            question_number=question_number,
            audio=audio
        )
        return {
            "success": True,
            "transcript": transcript
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate", response_model=EvaluateAnswerResponse)
async def evaluate_answer(request: EvaluateAnswerRequest):
    try:
        evaluation = await InterviewEvaluationService.evaluate_answer(
            interview_id=request.interview_id,
            question_number=request.question_number,
            question=request.question,
            candidate_answer=request.candidate_answer,
            exam=request.exam,
            subject=request.subject,
            difficulty=request.difficulty,
            language=request.language
        )
        
        # Phase 4: Generate Speech for follow-up question if required
        tts_result = {}
        if evaluation.get("follow_up_required") and evaluation.get("follow_up_question"):
            # Default to english for follow-ups since language is not passed in EvaluateAnswerRequest
            tts_result = TextToSpeechService.generate_speech(evaluation["follow_up_question"], request.language)
            
        evaluation["follow_up_audio_url"] = tts_result.get("audio_url")
        evaluation["voice_supported"] = tts_result.get("voice_supported")
        evaluation["voice"] = tts_result.get("voice")
        evaluation["language"] = tts_result.get("language")
        
        return EvaluateAnswerResponse(**evaluation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=LiveInterviewChatResponse)
async def chat(request: LiveInterviewChatRequest):
    try:
        data = await LiveInterviewAIService.generate_chat_response(
            interview_id=request.interview_id,
            candidate_message=request.candidate_message,
            exam=request.exam,
            subject=request.subject,
            language=request.language,
            experience_level=request.experience_level,
            conversation_history=request.conversation_history
        )
        
        # Generate TTS audio for the AI's response
        tts_result = {}
        if data.get("interviewer_message"):
            tts_result = TextToSpeechService.generate_speech(data["interviewer_message"], request.language)
            
        return LiveInterviewChatResponse(
            stage=data.get("stage", "UNKNOWN"),
            interviewer_message=data.get("interviewer_message", ""),
            next_action=data.get("next_action", "WAIT_FOR_RESPONSE"),
            avatar=data.get("avatar", {}),
            audio_url=tts_result.get("audio_url"),
            voice_supported=tts_result.get("voice_supported"),
            voice=tts_result.get("voice"),
            language=tts_result.get("language")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
