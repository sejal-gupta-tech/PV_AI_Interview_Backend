import asyncio
import uuid
import httpx
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    async with httpx.AsyncClient() as client:
        # Start server locally in background before this script?
        # Actually I can just start the server myself in another task, 
        # but let's try calling it on port 8000 assuming it's running, 
        # or I can just import the FastAPI app and use httpx ASGITransport
        from app.main import app
        from httpx import ASGITransport
        from app.core.database import connect_to_mongo, close_mongo_connection
        
        await connect_to_mongo()
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            print("1. Testing /start")
            res = await client.post("/api/v1/interviews/start", json={
                "language": "english",
                "exam": "demo",
                "subject": "math",
                "topics": ["algebra"],
                "difficulty": "easy",
                "total_questions": 1,
                "time_per_question_seconds": 60
            })
            print(res.status_code, res.json())
            session_id = res.json().get("session_id")
            
            if not session_id:
                return

            print("2. Testing /question")
            res2 = await client.get(f"/api/v1/interviews/{session_id}/question")
            print(res2.status_code, res2.json())
            question_id = res2.json().get("question_id")

            print("3. Testing /answer (which also triggers complete due to total_questions=1)")
            res3 = await client.post(f"/api/v1/interviews/{session_id}/answer", json={
                "question_id": question_id,
                "selected_option": "A",
                "answer_method": "TEXT"
            })
            print(res3.status_code, res3.json())

            print("4. Testing /monitoring")
            res4 = await client.post(f"/api/v1/interviews/{session_id}/monitoring", json={
                "event_type": "camera_off"
            })
            print(res4.status_code, res4.json())
            
        await close_mongo_connection()

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main())
