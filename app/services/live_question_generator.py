from openai import AsyncOpenAI
from app.core.config import settings
from app.services.prompt_builder import PromptBuilderService

class LiveQuestionGeneratorService:
    @staticmethod
    async def generate_first_question(exam: str, candidate_name: str, subject: str, difficulty: str, stage: str, language: str) -> str:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        prompt = PromptBuilderService.build_interviewer_prompt(
            exam=exam,
            candidate_name=candidate_name,
            subject=subject,
            difficulty=difficulty,
            stage=stage,
            language=language
        )
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()

    @staticmethod
    async def generate_followup_question(exam: str, candidate_name: str, subject: str, difficulty: str, stage: str, language: str, profile: dict, conversation_history: list) -> dict:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        prompt = PromptBuilderService.build_followup_prompt(
            exam=exam,
            candidate_name=candidate_name,
            subject=subject,
            difficulty=difficulty,
            stage=stage,
            language=language,
            memory=profile, # Reusing memory arg name for now
            conversation_history=conversation_history
        )
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7
        )
        
        import json
        result = response.choices[0].message.content.strip()
        try:
            return json.loads(result)
        except Exception:
            return {
                "question": result,
                "topic": "General",
                "follow_up_reason": "Fallback parsing error"
            }
