import time
import uuid
import logging
from typing import BinaryIO
from app.services.openai_stt_provider import OpenAISTTProvider
from app.services.piper_tts_service import PiperTTSService
from app.services.local_audio_storage import LocalAudioStorage
from app.services.interview_engine import InterviewEngineService
from app.services.response_builder import ResponseBuilder
from app.schemas.live_interview import ProcessingMetrics
from app.schemas.speech import VoiceState, StructuredError
from app.core.voice_config import voice_settings
from app.core.database import get_db
from app.core.logging import setup_logger

logger = setup_logger("voice_pipeline")

class VoiceOrchestrator:
    @staticmethod
    async def process_voice_turn(session_id: str, audio_stream: BinaryIO, filename: str, mime_type: str):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        stt_ms = interview_ms = tts_ms = 0
        
        storage = LocalAudioStorage()
        stt_provider = OpenAISTTProvider()
        # tts_provider removed
        
        try:
            # 1. Validation & Storage (Audio Recording)
            if not filename or not audio_stream:
                raise ValueError("Audio stream missing. Audio Recording stage failed.")
            
            candidate_metadata = await storage.save(audio_stream, f"candidate_{request_id}_{filename}", mime_type)
            audio_stream.seek(0) # Reset file pointer for STT

            # 2. STT
            stt_start = time.time()
            stt_result = await stt_provider.transcribe(audio_stream, filename)
            stt_ms = int((time.time() - stt_start) * 1000)
            
            transcript = stt_result.get("transcript", "")
            confidence = stt_result.get("confidence", 0.0)

            if not transcript.strip():
                # Handle empty transcript (silence/noise)
                db = get_db()
                session = await db["live_interview_sessions"].find_one({"session_id": session_id})
                retries = session.get("retries", 0) if session else 0
                
                if retries >= 3:
                    return ResponseBuilder.build_error(
                        request_id, session_id, "MAX_RETRIES_EXCEEDED", "Could not hear the candidate after multiple attempts.", retry=False
                    )
                    
                await db["live_interview_sessions"].update_one(
                    {"session_id": session_id},
                    {"$inc": {"retries": 1}}
                )
                
                fallback_msg = "I couldn't hear you clearly. Could you please repeat your answer?"
                
                tts_start = time.time()
                lang = session.get("language", "English") if session else "English"
                tts_result = PiperTTSService.generate_speech(text=fallback_msg, language=lang)
                tts_filename = tts_result["filename"]
                tts_ms = int((time.time() - tts_start) * 1000)
                
                return ResponseBuilder.build_voice_state(
                    request_id=request_id,
                    session_id=session_id,
                    transcript="",
                    next_question=fallback_msg,
                    audio_url=f"/audio/{tts_filename}",
                    metrics=session.get("metrics", {}),
                    profile=session.get("profile", {}),
                    voice_state=VoiceState.WAITING_FOR_CANDIDATE,
                    turn=len(session.get("conversation", [])) // 2 + 1 if session else 1,
                    processing=ProcessingMetrics(stt_ms=stt_ms, tts_ms=tts_ms, total_ms=stt_ms+tts_ms)
                )

            # Reset retries on successful speech
            db = get_db()
            await db["live_interview_sessions"].update_one(
                {"session_id": session_id},
                {"$set": {"retries": 0}}
            )

            # 3. Interview Engine
            engine_start = time.time()
            engine_result = await InterviewEngineService.process_answer(
                session_id=session_id, 
                answer_text=transcript, 
                timing=None
            )
            interview_ms = int((time.time() - engine_start) * 1000)
            next_question = engine_result.get("next_question", "")

            # 4. TTS
            tts_start = time.time()
            session = await db["live_interview_sessions"].find_one({"session_id": session_id})
            lang = session.get("language", "English") if session else "English"
                
            tts_result = PiperTTSService.generate_speech(text=next_question, language=lang)
            tts_filename = tts_result["filename"]
            tts_ms = int((time.time() - tts_start) * 1000)

            total_ms = int((time.time() - start_time) * 1000)
            
            processing = ProcessingMetrics(
                stt_ms=stt_ms,
                interview_ms=interview_ms,
                tts_ms=tts_ms,
                total_ms=total_ms
            )
            
            question_number = engine_result.get("conversation_length", 1)
            audio_url = f"/audio/{tts_filename}"
            has_question = "YES" if next_question else "NO"
            
            # Use structured JSON logging
            logger.info(
                "Interview pipeline execution completed",
                extra={
                    "structured_data": {
                        "Session ID": session_id,
                        "Candidate ID": request_id,
                        "Question Number": question_number,
                        "Interview Language": lang,
                        "Prompt Language": lang,
                        "Question": next_question,
                        "Transcript": transcript,
                        "Evaluation": engine_result.get("metrics").model_dump(),
                        "Voice Model": "Piper",
                        "Generated Audio": tts_filename,
                        "Audio URL": audio_url,
                        "LLM Response Time": interview_ms,
                        "Piper Time": tts_ms,
                        "Total Processing Time": total_ms
                    }
                }
            )
            
            # 5. Response Builder
            return ResponseBuilder.build_voice_state(
                request_id=request_id,
                session_id=session_id,
                transcript=transcript,
                next_question=next_question,
                audio_url=audio_url,
                metrics=engine_result.get("metrics").model_dump(),
                profile=engine_result.get("candidate_profile").model_dump(),
                voice_state=VoiceState.WAITING_FOR_CANDIDATE,
                turn=question_number,
                processing=processing
            )
            
        except ValueError as e:
            logger.error(f"[{request_id}] ValueError: {str(e)}")
            return ResponseBuilder.build_error(request_id, session_id, "VALIDATION_ERROR", str(e))
        except Exception as e:
            import traceback
            logger.error(f"[{request_id}] Unexpected Error: {traceback.format_exc()}")
            return ResponseBuilder.build_error(request_id, session_id, "INTERNAL_ERROR", f"Error: {str(e)}")
