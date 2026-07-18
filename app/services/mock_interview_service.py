import uuid
import datetime
from typing import List, Dict, Any
from app.core.database import get_db
from app.schemas.mock_interview import MockQuestion, MockReportResponse
from openai import AsyncOpenAI
from app.core.config import settings

class MockInterviewService:
    @staticmethod
    async def save_generated_questions(session_id: str, questions: List[MockQuestion]):
        db = get_db()
        docs = [{"session_id": session_id, **q.model_dump()} for q in questions]
        if docs:
            await db["generated_questions"].insert_many(docs)

    @staticmethod
    async def start_session(exam: str, subject: str, difficulty: str, language: str, questions: List[MockQuestion]) -> str:
        db = get_db()
        session_id = str(uuid.uuid4())
        
        # Save session
        await db["mock_interviews"].insert_one({
            "session_id": session_id,
            "exam": exam,
            "subject": subject,
            "difficulty": difficulty,
            "language": language,
            "total_questions": len(questions),
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        })
        
        # Save questions
        await MockInterviewService.save_generated_questions(session_id, questions)
        
        return session_id

    @staticmethod
    async def submit_answer(session_id: str, question_id: int, selected_option: int) -> bool:
        db = get_db()
        
        # Check correct answer
        question = await db["generated_questions"].find_one({"session_id": session_id, "id": question_id})
        if not question:
            raise ValueError("Question not found")
            
        is_correct = question["correctAnswer"] == selected_option
        
        # Save answer
        await db["user_answers"].insert_one({
            "session_id": session_id,
            "question_id": question_id,
            "selected_option": selected_option,
            "is_correct": is_correct,
            "answered_at": datetime.datetime.now(datetime.timezone.utc)
        })
        
        return is_correct

    @staticmethod
    async def complete_and_generate_report(session_id: str) -> MockReportResponse:
        db = get_db()
        
        session = await db["mock_interviews"].find_one({"session_id": session_id})
        if not session:
            raise ValueError("Session not found")
            
        answers_cursor = db["user_answers"].find({"session_id": session_id})
        answers = await answers_cursor.to_list(length=None)
        
        total_questions = session["total_questions"]
        attempted = len(answers)
        correct = sum(1 for a in answers if a["is_correct"])
        incorrect = attempted - correct
        skipped = total_questions - attempted
        
        accuracy = (correct / attempted * 100) if attempted > 0 else 0
        overall_score = correct
        
        # Generate AI Feedback
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""
        Generate a personalized performance report for a student who took a {session['exam']} exam in {session['subject']}.
        Total Questions: {total_questions}
        Correct: {correct}
        Incorrect: {incorrect}
        Skipped: {skipped}
        
        Return a JSON object with:
        - "weak_topics": array of strings (max 3)
        - "strong_topics": array of strings (max 3)
        - "recommendations": array of strings (max 3 actionable tips)
        - "ai_feedback": A short personalized paragraph summarizing their performance.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        import json
        feedback_data = json.loads(response.choices[0].message.content)
        
        report_doc = {
            "session_id": session_id,
            "overall_score": overall_score,
            "accuracy": round(accuracy, 2),
            "correct": correct,
            "incorrect": incorrect,
            "skipped": skipped,
            "weak_topics": feedback_data.get("weak_topics", []),
            "strong_topics": feedback_data.get("strong_topics", []),
            "recommendations": feedback_data.get("recommendations", []),
            "ai_feedback": feedback_data.get("ai_feedback", ""),
            "generated_at": datetime.datetime.now(datetime.timezone.utc)
        }
        
        await db["reports"].insert_one(report_doc)
        
        return MockReportResponse(**report_doc)
