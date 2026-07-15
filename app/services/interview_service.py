import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from app.schemas.interview import (
    InterviewStartResponse, 
    QuestionResponse, 
    AnswerResponse,
    LocalizedText,
    MCQOption,
    InterviewCompleteResponse
)
from app.services.question_provider import DevelopmentFallbackProvider
from app.services.question_validation_service import QuestionValidationService
from app.models.mongodb_models import (
    InterviewSessionDB,
    QuestionServedDB,
    UserAnswerDB,
    FinalReportDB,
    MonitoringEventDB
)
from app.repositories.interview_repository import InterviewRepository

_sessions: Dict[str, Dict[str, Any]] = {}
DIFFICULTIES = ["easy", "medium", "hard"]
MAX_RETRIES = 3

provider = DevelopmentFallbackProvider()

class InterviewService:
    @staticmethod
    async def start_session(language: str, exam: str, subject: str, topics: List[str], difficulty: str, total_questions: int, time_per_question_seconds: int) -> InterviewStartResponse:
        session_id = str(uuid.uuid4())
        
        _sessions[session_id] = {
            "session_id": session_id,
            "language": language,
            "exam": exam,
            "subject": subject,
            "topics": topics,
            "difficulty": difficulty,
            "total_questions": total_questions,
            "time_per_question_seconds": time_per_question_seconds,
            "score": 0,
            "correct_streak": 0,
            "wrong_streak": 0,
            "questions_answered": 0,
            "asked_question_ids": [],
            "active_question": None
        }
        
        now_utc = datetime.now(timezone.utc)
        db_session = InterviewSessionDB(
            session_id=session_id,
            exam=exam,
            subject=subject,
            language=language,
            difficulty=difficulty,
            total_questions=total_questions,
            time_per_question=time_per_question_seconds,
            interview_status="started",
            started_at=now_utc
        )
        await InterviewRepository.create_session(db_session)
        
        return InterviewStartResponse(
            session_id=session_id,
            status="started",
            language=language,
            exam=exam,
            subject=subject,
            topics=topics,
            difficulty=difficulty,
            total_questions=total_questions,
            time_per_question_seconds=time_per_question_seconds
        )
        
    @staticmethod
    def _finalize_timeout(session: Dict[str, Any]):
        # Reset streaks
        session["correct_streak"] = 0
        session["wrong_streak"] = 0
        
        # Mark timed out
        session["active_question"]["timed_out"] = True
        session["active_question"]["answered"] = True
        session["questions_answered"] += 1
        # Leave difficulty unchanged

    @staticmethod
    async def get_question(session_id: str) -> QuestionResponse:
        session = _sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
            
        now_utc = datetime.now(timezone.utc)
        
        # 1. Check if there is an active question
        if session.get("active_question"):
            active = session["active_question"]
            
            # 2. Check if active question has expired
            expires_at = datetime.fromisoformat(active["expires_at"])
            
            if not active["answered"]:
                if now_utc > expires_at:
                    # Mark as timeout and allow flow to generate a NEW question below
                    InterviewService._finalize_timeout(session)
                else:
                    # Return the active question with the EXACT SAME timer
                    # Scrub correct_option before returning
                    return QuestionResponse(
                        question_id=active["question_id"],
                        question_text=active["safe_question_payload"]["question_text"],
                        options=active["safe_question_payload"]["options"],
                        difficulty=active["safe_question_payload"]["difficulty"],
                        subject=active["safe_question_payload"]["subject"],
                        topic=active["safe_question_payload"]["topic"],
                        time_limit_seconds=session["time_per_question_seconds"],
                        started_at=active["started_at"],
                        expires_at=active["expires_at"],
                        provider_type=active["provider_type"],
                        ai_status=active["safe_question_payload"]["ai_status"]
                    )
        
        # 3. Generate a NEW question
        current_difficulty = session["difficulty"]
        raw_question = None
        
        for attempt in range(MAX_RETRIES):
            q = provider.get_question(
                exam=session["exam"],
                subject=session["subject"],
                topics=session["topics"],
                difficulty=current_difficulty,
                language=session["language"],
                excluded_ids=session["asked_question_ids"],
                session_context=session
            )
            
            # Validation
            if QuestionValidationService.validate_provider_output(q, session["language"]):
                if q["question_id"] not in session["asked_question_ids"]:
                    raw_question = q
                    break
                    
        if not raw_question:
            raise RuntimeError("Failed to generate a valid question from the provider.")
            
        session["asked_question_ids"].append(raw_question["question_id"])
        
        started_at = datetime.now(timezone.utc)
        expires_at = started_at + timedelta(seconds=session["time_per_question_seconds"])
        
        # Safely store, keeping the correct_option SERVER SIDE
        session["active_question"] = {
            "question_id": raw_question["question_id"],
            "correct_option": raw_question["correct_option"],
            "explanation": raw_question["explanation"],
            "started_at": started_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "answered": False,
            "timed_out": False,
            "provider_type": raw_question["provider_type"],
            "safe_question_payload": raw_question
        }
        
        question_served = QuestionServedDB(
            session_id=session_id,
            question_id=raw_question["question_id"],
            question_text=raw_question["question_text"],
            options=raw_question["options"],
            correct_answer=raw_question["correct_option"],
            question_number=len(session["asked_question_ids"]),
            timestamp=started_at
        )
        await InterviewRepository.save_question(question_served)
        
        return QuestionResponse(
            question_id=raw_question["question_id"],
            question_text=raw_question["question_text"],
            options=raw_question["options"],
            difficulty=raw_question["difficulty"],
            subject=raw_question["subject"],
            topic=raw_question["topic"],
            time_limit_seconds=session["time_per_question_seconds"],
            started_at=session["active_question"]["started_at"],
            expires_at=session["active_question"]["expires_at"],
            provider_type=raw_question["provider_type"],
            ai_status=raw_question["ai_status"]
        )

    @staticmethod
    async def submit_answer(session_id: str, question_id: str, selected_option: str, answer_method: str) -> AnswerResponse:
        session = _sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
            
        active = session.get("active_question")
        if not active or active["question_id"] != question_id:
            raise ValueError("Invalid or inactive question_id")
            
        if active["answered"]:
            raise ValueError("Question already answered or timed out")
            
        now_utc = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(active["expires_at"])
        
        if now_utc > expires_at:
            InterviewService._finalize_timeout(session)
            
            timeout_answer = UserAnswerDB(
                session_id=session_id,
                question_id=question_id,
                selected_option="",
                correct_option=active["correct_option"],
                is_correct=False,
                explanation=active["explanation"],
                time_taken=session["time_per_question_seconds"],
                points_awarded=0,
                answered_at=now_utc
            )
            await InterviewRepository.save_answer(timeout_answer)
            
            if session["questions_answered"] >= session["total_questions"]:
                await InterviewService.complete_interview(session_id)
                
            return AnswerResponse(
                correct=False,
                score=session["score"],
                explanation=None,
                next_difficulty=session["difficulty"],
                status="timeout"
            )
            
        # Valid Answer flow
        active["answered"] = True
        session["questions_answered"] += 1
        
        is_correct = selected_option.upper() == active["correct_option"].upper()
        
        if is_correct:
            session["score"] += 10
            session["correct_streak"] += 1
            session["wrong_streak"] = 0
        else:
            session["wrong_streak"] += 1
            session["correct_streak"] = 0

        # Adaptive difficulty logic
        current_diff_idx = DIFFICULTIES.index(session["difficulty"])
        next_difficulty = session["difficulty"]
        
        if session["correct_streak"] >= 2:
            if current_diff_idx < len(DIFFICULTIES) - 1:
                next_difficulty = DIFFICULTIES[current_diff_idx + 1]
            session["correct_streak"] = 0
        elif session["wrong_streak"] >= 2:
            if current_diff_idx > 0:
                next_difficulty = DIFFICULTIES[current_diff_idx - 1]
            session["wrong_streak"] = 0
            
        session["difficulty"] = next_difficulty
        
        time_taken = (now_utc - datetime.fromisoformat(active["started_at"])).total_seconds()
        
        user_answer = UserAnswerDB(
            session_id=session_id,
            question_id=question_id,
            selected_option=selected_option,
            correct_option=active["correct_option"],
            is_correct=is_correct,
            explanation=active["explanation"],
            time_taken=time_taken,
            points_awarded=10 if is_correct else 0,
            answered_at=now_utc
        )
        await InterviewRepository.save_answer(user_answer)
        
        if session["questions_answered"] >= session["total_questions"]:
            await InterviewService.complete_interview(session_id)
        
        return AnswerResponse(
            correct=is_correct,
            score=session["score"],
            explanation=active["explanation"],
            next_difficulty=next_difficulty,
            status="answered"
        )
        
    @staticmethod
    async def complete_interview(session_id: str) -> FinalReportDB:
        session = _sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
            
        now_utc = datetime.now(timezone.utc)
        
        correct = session["score"] // 10
        wrong = session["questions_answered"] - correct
        percentage = (session["score"] / (session["total_questions"] * 10)) * 100 if session["total_questions"] > 0 else 0
        
        report = FinalReportDB(
            session_id=session_id,
            total_questions=session["total_questions"],
            attempted=session["questions_answered"],
            correct=correct,
            wrong=wrong,
            skipped=session["total_questions"] - session["questions_answered"],
            score=session["score"],
            percentage=percentage,
            completed_at=now_utc
        )
        await InterviewRepository.save_report(report)
        return report

    @staticmethod
    async def save_monitoring_event(session_id: str, event_type: str) -> None:
        now_utc = datetime.now(timezone.utc)
        event = MonitoringEventDB(
            session_id=session_id,
            event_type=event_type,
            timestamp=now_utc
        )
        await InterviewRepository.save_monitoring_event(event)

