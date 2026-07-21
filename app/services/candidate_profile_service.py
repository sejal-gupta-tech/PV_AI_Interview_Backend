import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.prompt_builder import PromptBuilderService
from app.schemas.live_interview import CandidateProfile, InterviewMetrics

class CandidateProfileService:
    @staticmethod
    async def evaluate_answer_and_update_profile(
        exam: str,
        current_profile: CandidateProfile, 
        current_metrics: InterviewMetrics,
        stage: str,
        difficulty: str,
        last_question: str, 
        last_answer: str
    ) -> dict:
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY or OPENAI_API_KEY is not configured")
            
        # We need to add evaluate_answer.txt builder to prompt_builder
        # Let's read it directly or via PromptBuilderService
        prompt_template = PromptBuilderService._read_prompt("evaluate_answer.txt")
        prompt = prompt_template.format(
            exam=exam,
            current_profile=current_profile.model_dump_json(),
            current_metrics=current_metrics.model_dump_json(),
            stage=stage,
            difficulty=difficulty,
            last_question=last_question,
            last_answer=last_answer
        )
        
        base_url = "https://api.groq.com/openai/v1" if settings.GROQ_API_KEY else None
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        from app.core.voice_config import voice_settings
        model = voice_settings.chat_model if settings.GROQ_API_KEY else "gpt-4o-mini"
        
        response = await client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.3
        )
        
        result_content = response.choices[0].message.content
        try:
            evaluation = json.loads(result_content)
            return evaluation
        except Exception as e:
            print(f"Error parsing evaluation JSON: {e}")
            return {
                "profile": current_profile.model_dump(),
                "metrics": current_metrics.model_dump(),
                "struggled": False
            }
