import logging
import traceback
from app.core.database import get_db
from app.models.mongodb_models import (
    InterviewSessionDB,
    QuestionServedDB,
    UserAnswerDB,
    FinalReportDB,
    MonitoringEventDB
)
from typing import Dict, Any

logger = logging.getLogger("uvicorn.error")

class InterviewRepository:
    
    @staticmethod
    async def create_session(session_data: InterviewSessionDB) -> None:
        db = get_db()
        if db is not None:
            try:
                logger.info("Saving interview session")
                result = await db["interviews"].insert_one(session_data.model_dump())
                logger.info(f"inserted_id: {result.inserted_id}, collection name: interviews")
            except Exception as e:
                logger.error(f"Error in create_session: {traceback.format_exc()}")
        else:
            logger.error("DB connection is None in create_session")

    @staticmethod
    async def save_question(question_data: QuestionServedDB) -> None:
        db = get_db()
        if db is not None:
            try:
                logger.info("Saving question")
                result = await db["questions"].insert_one(question_data.model_dump())
                logger.info(f"inserted_id: {result.inserted_id}, collection name: questions")
            except Exception as e:
                logger.error(f"Error in save_question: {traceback.format_exc()}")
        else:
            logger.error("DB connection is None in save_question")

    @staticmethod
    async def save_answer(answer_data: UserAnswerDB) -> None:
        db = get_db()
        if db is not None:
            try:
                logger.info("Saving answer")
                result = await db["answers"].insert_one(answer_data.model_dump())
                logger.info(f"inserted_id: {result.inserted_id}, collection name: answers")
            except Exception as e:
                logger.error(f"Error in save_answer: {traceback.format_exc()}")
        else:
            logger.error("DB connection is None in save_answer")

    @staticmethod
    async def save_report(report_data: FinalReportDB) -> None:
        db = get_db()
        if db is not None:
            try:
                logger.info("Saving report")
                result = await db["reports"].insert_one(report_data.model_dump())
                logger.info(f"inserted_id: {result.inserted_id}, collection name: reports")
            except Exception as e:
                logger.error(f"Error in save_report: {traceback.format_exc()}")
        else:
            logger.error("DB connection is None in save_report")

    @staticmethod
    async def save_monitoring_event(event_data: MonitoringEventDB) -> None:
        db = get_db()
        if db is not None:
            try:
                logger.info("Saving monitoring event")
                result = await db["monitoring_events"].insert_one(event_data.model_dump())
                logger.info(f"inserted_id: {result.inserted_id}, collection name: monitoring_events")
            except Exception as e:
                logger.error(f"Error in save_monitoring_event: {traceback.format_exc()}")
        else:
            logger.error("DB connection is None in save_monitoring_event")
