import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.prompt_builder import PromptBuilderService

class ConversationMemoryService:
    @staticmethod
    async def extract_and_update_memory(current_memory: dict, last_question: str, last_answer: str) -> dict:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        prompt = PromptBuilderService.build_memory_extraction_prompt(
            current_memory=current_memory,
            last_question=last_question,
            last_answer=last_answer
        )
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.3
        )
        
        result_content = response.choices[0].message.content
        try:
            updated_memory = json.loads(result_content)
            return updated_memory
        except Exception as e:
            print(f"Error parsing memory JSON: {e}")
            return current_memory
