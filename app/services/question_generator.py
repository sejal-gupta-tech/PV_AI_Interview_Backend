import json
from typing import List
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.mock_interview import MockQuestion

class QuestionGeneratorService:
    @staticmethod
    async def generate_questions(exam: str, subject: str, difficulty: str, language: str, count: int) -> List[MockQuestion]:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""
        You are an expert examiner for {exam} exams.
        Generate exactly {count} Multiple Choice Questions (MCQs) for the subject "{subject}".
        Difficulty level: {difficulty}.
        Language: {language}.
        
        Rules:
        - Questions must follow the actual {exam} syllabus.
        - Avoid duplicates.
        - Avoid repeated options.
        - Generate explanations for the correct answer.
        
        Format the output strictly as a JSON object with a single key "questions" containing an array of question objects.
        Each question object must match this schema:
        {{
            "id": 1,
            "question": "string",
            "options": ["A", "B", "C", "D"],
            "correctAnswer": integer (0 to 3),
            "explanation": "string"
        }}
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.7
        )
        
        result_content = response.choices[0].message.content
        data = json.loads(result_content)
        
        questions = []
        for i, q in enumerate(data.get("questions", [])):
            q["id"] = i + 1
            questions.append(MockQuestion(**q))
            
        return questions
