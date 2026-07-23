import json
import logging
import datetime
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger("interview_evaluation_service")

class InterviewEvaluationService:
    @staticmethod
    async def evaluate_answer(
        interview_id: str,
        question_number: int,
        question: str,
        candidate_answer: str,
        exam: str,
        subject: str,
        difficulty: str,
        language: str = "English"
    ) -> dict:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = """You are an expert interviewer.

Evaluate candidate answers exactly like a real interview panel.

Never reveal the correct answer.

Never praise incorrect answers.

Score fairly.

If the answer is weak, ask one follow-up question.

If the answer is good enough, allow the interview to continue.

Interview Language:
{language}

Rules:
If language is Hindi:
- Speak only Hindi.
- Use natural spoken Hindi.
- Avoid unnecessary English words.
- Do not translate literally.
- Speak like a real Indian interviewer.

If language is English:
- Use fluent English.

Scoring Criteria:
- Technical Accuracy
- Completeness
- Communication
- Confidence
- Practical Knowledge

Return ONLY valid JSON.
Do not use markdown.
Do not explain anything outside JSON.

Return exactly:
{
  "score": 8,
  "technical_accuracy": 8,
  "communication": 7,
  "strengths": [
      "...",
      "..."
  ],
  "weaknesses":[
      "...",
      "..."
  ],
  "feedback":"...",
  "follow_up_required":true,
  "follow_up_question":"..."
}"""

        user_prompt = f"""Exam: {exam}
Subject: {subject}
Difficulty: {difficulty}

Question: {question}

Candidate Answer: {candidate_answer}"""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            result_content = response.choices[0].message.content
            evaluation = json.loads(result_content)
            
            # Save to MongoDB
            db = get_db()
            
            # Update the transcript document to include evaluation, or create an evaluation document
            # The requirement says: "Update interview document with: score, technical_accuracy, communication, strengths, weaknesses, feedback, follow_up_question, evaluation_timestamp"
            update_data = {
                "score": evaluation.get("score"),
                "technical_accuracy": evaluation.get("technical_accuracy"),
                "communication": evaluation.get("communication"),
                "strengths": evaluation.get("strengths", []),
                "weaknesses": evaluation.get("weaknesses", []),
                "feedback": evaluation.get("feedback"),
                "follow_up_required": evaluation.get("follow_up_required", False),
                "follow_up_question": evaluation.get("follow_up_question"),
                "evaluation_timestamp": datetime.datetime.utcnow(),
                "language": language
            }
            
            # Updating the live_interview_transcripts collection where the answer was just saved
            await db["live_interview_transcripts"].update_one(
                {"interview_id": interview_id, "question_number": question_number},
                {"$set": update_data},
                upsert=True
            )
            
            return evaluation
            
        except Exception as e:
            logger.exception(f"Error during interview evaluation: {e}")
            raise RuntimeError(f"Failed to evaluate answer: {str(e)}")
