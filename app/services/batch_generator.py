import json
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger("batch_generator")

class BatchGeneratorService:
    @staticmethod
    async def generate_batch(exam: str, subject: str, topic: str, difficulty: str, language: str, count: int = 25) -> List[Dict[str, Any]]:
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("API Key is not configured (Provide GROQ_API_KEY)")
            
        base_url = "https://api.groq.com/openai/v1" if api_key == settings.GROQ_API_KEY else None
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        is_special_ed = (exam == "KVS/NVS Special Educator" and subject == "Special Education")
        
        if is_special_ed:
            topic_instruction = f"""
CRITICAL SYLLABUS INSTRUCTION:
"Special Education" represents the complete syllabus, which includes all of the following topics:
- Child Development & Pedagogy
- Inclusive Education
- Educational Psychology
- Learning Disabilities
- Intellectual Disability
- Hearing Impairment
- Visual Impairment
- Autism Spectrum Disorder (ASD)
- Multiple Disabilities
- Assessment & Identification
- Individualized Education Programme (IEP)
- Teaching Methods for Children with Special Needs
- Assistive Technology
- Behaviour Management

You MUST generate questions that comprehensively cover ALL these major syllabus areas.
Distribute the {count} questions naturally and evenly across these topics.
Do NOT generate questions from only one topic. Ensure a balanced mix.
Avoid repeatedly selecting the same topic.
"""
            topic_schema = '"topic": "string (MUST be one of the specific syllabus topics listed above, e.g., \'Autism Spectrum Disorder (ASD)\')", '
        else:
            topic_instruction = f"Topic: {topic}"
            topic_schema = f'"topic": "{topic}",'

        prompt = f"""
You are an Expert AI Question Generation Engine specializing in Indian Government Competitive Examinations.

Your objective is to generate ORIGINAL, HIGH-QUALITY, EXAM-ORIENTED Multiple Choice Questions (MCQs) that strictly follow the latest official syllabus, exam pattern, and difficulty level.

Generate questions only for the following inputs:
Exam: {exam}
Subject: {subject}
{topic_instruction}
Difficulty: {difficulty}
Language: {language}
Number of Questions: {count}

------------------------------------------
QUESTION REQUIREMENTS
------------------------------------------
1. Generate EXACTLY {count} questions.
2. Generate ONLY in the selected language.
If language = English, everything must be English.
If language = Hindi, everything must be Hindi (Generate natural Hindi questions, do NOT just translate blindly).
3. Questions must be ORIGINAL.
4. Do not copy questions from websites, books, PDFs, coaching notes, or copyrighted material.
5. Follow the official pattern for the exam.
6. Avoid duplicate questions.
7. Randomly mix: Conceptual, Factual, Statement-based, Numerical (where applicable), Application-based.
8. Each question must contain exactly four options.
9. Exactly one option must be correct.
10. Randomize the position of the correct answer.
11. Add a concise explanation.
12. Return ONLY valid JSON.
13. No Markdown. No comments. No additional text.

------------------------------------------
OUTPUT FORMAT
------------------------------------------
{{
  "questions": [
    {{
      "exam": "{exam}",
      "subject": "{subject}",
      {topic_schema}
      "difficulty": "{difficulty}",
      "language": "{language}",
      "question": "string",
      "options": [
        "string",
        "string",
        "string",
        "string"
      ],
      "correct_answer": 0,
      "explanation": "string"
    }}
  ]
}}
"""
        try:
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
            
            return data.get("questions", [])
            
        except Exception as e:
            logger.error(f"Error generating batch: {e}")
            raise e
