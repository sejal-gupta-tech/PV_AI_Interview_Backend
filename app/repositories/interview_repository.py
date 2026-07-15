import traceback
import sys
from app.core.database import get_db
from app.models.mongodb_models import (
    InterviewSessionDB,
    QuestionServedDB,
    UserAnswerDB,
    FinalReportDB,
    MonitoringEventDB
)
from typing import Dict, Any

class InterviewRepository:
    
    @staticmethod
    async def create_session(session_data: InterviewSessionDB) -> None:
        db = get_db()
        if db is not None:
            print("Saving interview session", flush=True)
            try:
                result = await db["interviews"].insert_one(session_data.model_dump())
                print(f"inserted_id: {result.inserted_id} collection name: interviews", flush=True)
            except Exception as e:
                print("Exception in save_interview_session (create_session):", flush=True)
                traceback.print_exc(file=sys.stdout)
        else:
            print("db is None in create_session", flush=True)

    @staticmethod
    async def save_question(question_data: QuestionServedDB) -> None:
        db = get_db()
        if db is not None:
            print("Saving question", flush=True)
            try:
                result = await db["questions"].insert_one(question_data.model_dump())
                print(f"inserted_id: {result.inserted_id} collection name: questions", flush=True)
            except Exception as e:
                print("Exception in save_question:", flush=True)
                traceback.print_exc(file=sys.stdout)
        else:
            print("db is None in save_question", flush=True)

    @staticmethod
    async def save_answer(answer_data: UserAnswerDB) -> None:
        db = get_db()
        if db is not None:
            print("Saving answer", flush=True)
            try:
                result = await db["answers"].insert_one(answer_data.model_dump())
                print(f"inserted_id: {result.inserted_id} collection name: answers", flush=True)
            except Exception as e:
                print("Exception in save_answer:", flush=True)
                traceback.print_exc(file=sys.stdout)
        else:
            print("db is None in save_answer", flush=True)

    @staticmethod
    async def save_report(report_data: FinalReportDB) -> None:
        db = get_db()
        if db is not None:
            print("Saving report", flush=True)
            try:
                result = await db["reports"].insert_one(report_data.model_dump())
                print(f"inserted_id: {result.inserted_id} collection name: reports", flush=True)
            except Exception as e:
                print("Exception in save_report:", flush=True)
                traceback.print_exc(file=sys.stdout)
        else:
            print("db is None in save_report", flush=True)

    @staticmethod
    async def save_monitoring_event(event_data: MonitoringEventDB) -> None:
        db = get_db()
        if db is not None:
            print("Saving monitoring event", flush=True)
            try:
                result = await db["monitoring_events"].insert_one(event_data.model_dump())
                print(f"inserted_id: {result.inserted_id} collection name: monitoring_events", flush=True)
            except Exception as e:
                print("Exception in save_monitoring_event:", flush=True)
                traceback.print_exc(file=sys.stdout)
        else:
            print("db is None in save_monitoring_event", flush=True)
