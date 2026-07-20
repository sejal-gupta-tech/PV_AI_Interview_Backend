import uuid
from app.schemas.live_interview import LiveInterviewSessionDB, ConversationTurn, CandidateProfile, InterviewMetrics, TimingMetadata
from app.services.session_manager import SessionManagerService
from app.services.candidate_profile_service import CandidateProfileService
from app.services.live_question_generator import LiveQuestionGeneratorService
from app.services.interview_stage_service import InterviewStageService
from app.services.difficulty_service import DifficultyService

class InterviewEngineService:
    @staticmethod
    async def start_session(candidate_name: str, candidate_email: str | None, exam: str, subject: str, language: str, difficulty: str, interview_mode: str, duration: int) -> dict:
        session_id = str(uuid.uuid4())
        initial_stage = InterviewStageService.get_initial_stage()
        
        # 1. Generate First Question
        first_question = await LiveQuestionGeneratorService.generate_first_question(
            exam=exam,
            candidate_name=candidate_name,
            subject=subject,
            difficulty=difficulty,
            stage=initial_stage,
            language=language
        )
        
        # 2. Create Session DB Object
        turn = ConversationTurn(
            role="interviewer", 
            content=first_question,
            stage=initial_stage,
            topic="Introduction",
            difficulty=difficulty
        )
        session_db = LiveInterviewSessionDB(
            session_id=session_id,
            candidate_name=candidate_name,
            exam=exam,
            subject=subject,
            language=language,
            current_difficulty=difficulty,
            interview_mode=interview_mode,
            duration=duration,
            current_stage=initial_stage,
            profile=CandidateProfile(name=candidate_name, target_exam=exam, subject=subject),
            metrics=InterviewMetrics(),
            conversation=[turn]
        )
        
        # 3. Save to DB
        await SessionManagerService.create_session(session_db)
        
        from app.services.interview_stage_service import DEFAULT_STAGES
        
        stages_array = [
            {"name": stage, "status": "active" if stage == initial_stage else "pending"}
            for stage in DEFAULT_STAGES
        ]
        
        return {
            "session_id": session_id,
            "status": "active",
            "first_question": first_question,
            "current_stage": initial_stage,
            "candidate": {
                "name": candidate_name, 
                "email": candidate_email or "",
                "exam": exam, 
                "subject": subject, 
                "language": language,
                "mode": interview_mode,
                "difficulty": difficulty,
                "duration": duration
            },
            "stages": stages_array
        }

    @staticmethod
    async def process_answer(session_id: str, answer_text: str, timing: TimingMetadata = None) -> dict:
        # 1. Fetch Session
        session = await SessionManagerService.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
            
        current_stage = session["current_stage"]
        current_difficulty = session["current_difficulty"]
            
        # 2. Store Candidate Answer
        candidate_turn = ConversationTurn(
            role="candidate", 
            content=answer_text,
            stage=current_stage,
            difficulty=current_difficulty,
            timing=timing
        )
        await SessionManagerService.append_conversation_turn(session_id, candidate_turn)
        session["conversation"].append(candidate_turn.model_dump())
        
        # 3. Extract Memory / Evaluate Answer (Can be async later if latency is an issue)
        last_question = ""
        for t in reversed(session["conversation"]):
            if t["role"] == "interviewer":
                last_question = t["content"]
                break
                
        # Parse existing profile and metrics
        current_profile = CandidateProfile(**session.get("profile", {}))
        current_metrics = InterviewMetrics(**session.get("metrics", {}))
        
        evaluation = await CandidateProfileService.evaluate_answer_and_update_profile(
            exam=session["exam"],
            current_profile=current_profile,
            current_metrics=current_metrics,
            stage=current_stage,
            difficulty=current_difficulty,
            last_question=last_question,
            last_answer=answer_text
        )
        
        new_profile = evaluation.get("profile", current_profile.model_dump())
        new_metrics = evaluation.get("metrics", current_metrics.model_dump())
        struggled = evaluation.get("struggled", False)
        
        await SessionManagerService.update_profile_and_metrics(session_id, new_profile, new_metrics)
        session["profile"] = new_profile
        session["metrics"] = new_metrics
        
        # 4. Determine Next Stage and Difficulty
        questions_in_stage = sum(1 for t in session["conversation"] if t["role"] == "interviewer" and t.get("stage") == current_stage)
        
        next_stage = InterviewStageService.determine_next_stage(current_stage, questions_in_stage)
        next_difficulty = DifficultyService.adjust_difficulty(current_difficulty, struggled)
        
        if next_stage != current_stage or next_difficulty != current_difficulty:
            await SessionManagerService.update_stage_and_difficulty(session_id, next_stage, next_difficulty)
            session["current_stage"] = next_stage
            session["current_difficulty"] = next_difficulty

        # 4.5 Check for Completion
        # If the stage hasn't changed but we are at the final stage, and the required questions are met, end it.
        # The prompt said: "If current_stage == 'Closing', return status: 'completed'"
        # Wait, determine_next_stage returns the SAME stage if it's the last one.
        # Let's see if we've asked enough questions in the "Closing" stage.
        if next_stage == "Closing" and sum(1 for t in session["conversation"] if t["role"] == "interviewer" and t.get("stage") == "Closing") >= 1:
            # End of interview
            completion_msg = "Thank you for attending this AI interview. Your interview has been completed successfully. We are now preparing your detailed performance report."
            interviewer_turn = ConversationTurn(
                role="interviewer", 
                content=completion_msg,
                stage="Closing",
                topic="Conclusion",
                difficulty=session["current_difficulty"]
            )
            await SessionManagerService.append_conversation_turn(session_id, interviewer_turn)
            
            # Update session status
            db = get_db()
            await db["live_interview_sessions"].update_one(
                {"session_id": session_id},
                {"$set": {"status": "completed"}}
            )

            return {
                "session_id": session_id,
                "status": "completed",
                "next_question": completion_msg,
                "current_stage": "Closing",
                "current_difficulty": session["current_difficulty"],
                "candidate_profile": CandidateProfile(**session["profile"]),
                "metrics": InterviewMetrics(**session["metrics"]),
                "conversation_length": len(session["conversation"]) // 2 + 1
            }
            
        # 5. Generate Follow-up Question
        next_q_data = await LiveQuestionGeneratorService.generate_followup_question(
            exam=session["exam"],
            candidate_name=session["candidate_name"],
            subject=session["subject"],
            difficulty=session["current_difficulty"],
            stage=session["current_stage"],
            language=session["language"],
            profile=session["profile"],
            conversation_history=session["conversation"][-6:] # Keep context window small
        )
        
        next_question_text = next_q_data.get("question", "")
        next_topic = next_q_data.get("topic", "General")
        follow_up_reason = next_q_data.get("follow_up_reason", "")
        
        # 6. Store AI Question
        interviewer_turn = ConversationTurn(
            role="interviewer", 
            content=next_question_text,
            stage=session["current_stage"],
            topic=next_topic,
            difficulty=session["current_difficulty"],
            follow_up_reason=follow_up_reason
        )
        await SessionManagerService.append_conversation_turn(session_id, interviewer_turn)
        
        return {
            "session_id": session_id,
            "next_question": next_question_text,
            "current_stage": session["current_stage"],
            "current_difficulty": session["current_difficulty"],
            "candidate_profile": CandidateProfile(**session["profile"]),
            "metrics": InterviewMetrics(**session["metrics"]),
            "conversation_length": len(session["conversation"]) // 2 + 1
        }
