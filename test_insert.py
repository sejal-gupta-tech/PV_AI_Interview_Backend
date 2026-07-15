import asyncio
from fastapi.testclient import TestClient
from app.main import app

def run_test():
    with TestClient(app) as client:
        print("--- TRACING START_INTERVIEW ---", flush=True)
        response = client.post("/api/v1/interviews/start", json={
            "language": "english",
            "exam": "demo",
            "subject": "python",
            "topics": ["basics"],
            "difficulty": "easy",
            "total_questions": 1,
            "time_per_question_seconds": 60
        })
        if response.status_code != 200:
            print(f"Error starting: {response.json()}", flush=True)
            return
            
        data = response.json()
        session_id = data["session_id"]
        
        print("\n--- TRACING GET_QUESTION ---", flush=True)
        q_response = client.get(f"/api/v1/interviews/{session_id}/question")
        if q_response.status_code != 200:
            print(f"Error getting question: {q_response.json()}", flush=True)
            return
            
        q_data = q_response.json()
        question_id = q_data["question_id"]
        
        print("\n--- TRACING SUBMIT_ANSWER (and implicit completion) ---", flush=True)
        a_response = client.post(f"/api/v1/interviews/{session_id}/answer", json={
            "question_id": question_id,
            "selected_option": "A",
            "answer_method": "TEXT"
        })
        if a_response.status_code != 200:
            print(f"Error submitting answer: {a_response.json()}", flush=True)
            return
            
        print("\n--- TRACING SAVE_MONITORING_EVENT ---", flush=True)
        m_response = client.post(f"/api/v1/interviews/{session_id}/monitoring", json={
            "event_type": "TAB_SWITCH"
        })
        if m_response.status_code != 200:
            print(f"Error saving monitoring: {m_response.json()}", flush=True)
            
        print("\n--- ALL ENDPOINTS HIT ---", flush=True)

if __name__ == "__main__":
    run_test()
