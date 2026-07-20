from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.schemas.live_interview import LiveInterviewSessionDB, ConversationTurn

class SessionManagerService:
    @staticmethod
    async def create_session(session: LiveInterviewSessionDB):
        db = get_db()
        await db["live_interview_sessions"].insert_one(session.model_dump())

    @staticmethod
    async def get_session(session_id: str) -> Optional[dict]:
        db = get_db()
        session = await db["live_interview_sessions"].find_one({"session_id": session_id})
        return session


    @staticmethod
    async def update_profile_and_metrics(session_id: str, profile: dict, metrics: dict):
        db = get_db()
        await db["live_interview_sessions"].update_one(
            {"session_id": session_id},
            {"$set": {
                "profile": profile,
                "metrics": metrics
            }}
        )

    @staticmethod
    def _convert_turn_to_dict(turn: ConversationTurn) -> dict:
        d = turn.model_dump()
        if turn.timing:
            d["timing"] = turn.timing.model_dump()
        return d

    @staticmethod
    async def append_conversation_turn(session_id: str, turn: ConversationTurn):
        db = get_db()
        await db["live_interview_sessions"].update_one(
            {"session_id": session_id},
            {"$push": {"conversation": SessionManagerService._convert_turn_to_dict(turn)}}
        )

    @staticmethod
    async def update_stage_and_difficulty(session_id: str, new_stage: str, new_difficulty: str):
        db = get_db()
        await db["live_interview_sessions"].update_one(
            {"session_id": session_id},
            {"$set": {
                "current_stage": new_stage,
                "current_difficulty": new_difficulty
            }}
        )
