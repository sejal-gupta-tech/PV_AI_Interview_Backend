import json
from typing import List
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.mock_interview import MockQuestion
from app.core.config_loader import get_exam_config

class QuestionGeneratorService:
    @staticmethod
    async def generate_questions(exam: str, subject: str, difficulty: str, language: str, count: int) -> List[MockQuestion]:
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("API Key is not configured (Provide GROQ_API_KEY)")
            
        base_url = "https://api.groq.com/openai/v1" if api_key == settings.GROQ_API_KEY else None
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        config = get_exam_config()
        exam_data = config.get(exam, {})
        subject_data = exam_data.get(subject, {})
        topics = subject_data.get("topics", [])
        topics_str = "\n".join([f"- {t}" for t in topics]) if topics else "Topics not explicitly defined, choose appropriate topics."
        
        prompt = f"""
You are an Expert AI Question Generation Engine specializing in Indian Government Competitive Examinations.

Your objective is to generate ORIGINAL, HIGH-QUALITY, EXAM-ORIENTED Multiple Choice Questions (MCQs) that strictly follow the latest official syllabus, exam pattern, and difficulty level.

Supported Languages:
- English
- Hindi

Supported Difficulty Levels:
- Easy
- Medium
- Hard

Generate questions only for the following inputs:

Exam:
{exam}

Subject:
{subject}

Difficulty:
{difficulty}

Language:
{language}

Number of Questions:
{count}

------------------------------------------
SYLLABUS GUIDELINES
------------------------------------------
Use the latest official syllabus and commonly accepted topic structures for {exam}.
If the topic is not provided, automatically choose an appropriate topic from the subject.

{subject} Topics:
{topics_str}

------------------------------------------
QUESTION REQUIREMENTS
------------------------------------------
1. Generate EXACTLY {count} questions.
2. Generate ONLY in the selected language.
If language = English
Everything must be English.
If language = Hindi
Everything must be Hindi.
Do NOT translate English questions.
Generate natural Hindi questions.
3. Questions must be ORIGINAL.
4. Do not copy questions from websites, books, PDFs, coaching notes, or copyrighted material.
5. Follow the official SSC pattern.
6. Questions should resemble real SSC exams in style and difficulty.
7. Avoid duplicate questions.
8. Randomly mix:
- Conceptual
- Factual
- Statement-based
- Numerical (where applicable)
- Application-based
9. Each question must contain exactly four options.
10. Exactly one option must be correct.
11. Randomize the position of the correct answer.
12. Add a concise explanation.
13. Return ONLY valid JSON.
14. No Markdown.
15. No comments.
16. No additional text.

------------------------------------------
OUTPUT FORMAT
------------------------------------------
{{
  "questions": [
    {{
      "exam": "",
      "subject": "",
      "topic": "",
      "difficulty": "",
      "language": "",
      "question": "",
      "options": [
        "",
        "",
        "",
        ""
      ],
      "correct_answer": 0,
      "explanation": ""
    }}
  ]
}}
"""
        model_name = "llama-3.3-70b-versatile" if api_key == settings.GROQ_API_KEY else "gpt-4o-mini"
        
        response = await client.chat.completions.create(
            model=model_name,
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
            questions.append(MockQuestion(
                id=i + 1,
                question=q.get("question", ""),
                options=q.get("options", []),
                correctAnswer=q.get("correct_answer", 0),
                explanation=q.get("explanation", "")
            ))
            
        return questions
