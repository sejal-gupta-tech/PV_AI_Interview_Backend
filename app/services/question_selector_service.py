import random
import logging
from typing import Optional
from app.core.database import get_db

logger = logging.getLogger("question_selector")

class QuestionSelectorService:
    @staticmethod
    async def initialize_technical_round(interview_id: str, limit: int = 5) -> bool:
        """
        Initializes the technical round for the given interview_id.
        Fetches all active questions from 'question_bank', shuffles them,
        limits them, and stores the state in 'interview_technical_state'.
        Returns True if successful, False if already initialized or no questions found.
        """
        db = get_db()
        
        # Check if already initialized
        existing = await db["interview_technical_state"].find_one({"interview_id": interview_id})
        if existing:
            return False
            
        # Fetch active questions from MongoDB
        cursor = db["question_bank"].find({"active": True})
        questions = await cursor.to_list(length=None)
        
        if not questions:
            logger.warning(f"No active questions found in question_bank for {interview_id}")
            return False
            
        # Extract just the question strings
        question_texts = [q.get("question") for q in questions if q.get("question")]
        
        # Shuffle randomly
        random.shuffle(question_texts)
        
        # Limit to 5 questions
        selected_questions = question_texts[:limit]
        
        # Store in state
        await db["interview_technical_state"].insert_one({
            "interview_id": interview_id,
            "technical_questions": selected_questions,
            "current_question_index": 0
        })
        
        logger.info(f"Initialized technical round for {interview_id} with {len(selected_questions)} questions.")
        return True

    @staticmethod
    async def is_initialized(interview_id: str) -> bool:
        db = get_db()
        existing = await db["interview_technical_state"].find_one({"interview_id": interview_id})
        return bool(existing)

    @staticmethod
    async def get_next_question(interview_id: str) -> Optional[str]:
        """
        Returns the next technical question.
        If all questions have been asked, returns None.
        """
        db = get_db()
        state = await db["interview_technical_state"].find_one({"interview_id": interview_id})
        if not state:
            return None
            
        questions = state.get("technical_questions", [])
        idx = state.get("current_question_index", 0)
        
        if idx < len(questions):
            return questions[idx]
        return None

    @staticmethod
    async def advance_question(interview_id: str):
        """
        Increments the current_question_index by 1.
        """
        db = get_db()
        await db["interview_technical_state"].update_one(
            {"interview_id": interview_id},
            {"$inc": {"current_question_index": 1}}
        )
