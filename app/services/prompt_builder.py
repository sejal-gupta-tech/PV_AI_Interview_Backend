import os
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

class PromptBuilderService:
    @staticmethod
    def _read_prompt(filename: str) -> str:
        filepath = PROMPTS_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Prompt file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def build_interviewer_prompt(exam: str, candidate_name: str, subject: str, difficulty: str, stage: str, language: str) -> str:
        template = PromptBuilderService._read_prompt("interviewer.txt")
        return template.format(
            exam=exam,
            candidate_name=candidate_name,
            subject=subject,
            difficulty=difficulty,
            stage=stage,
            language=language
        )

    @staticmethod
    def build_followup_prompt(exam: str, candidate_name: str, subject: str, difficulty: str, stage: str, language: str, memory: dict, conversation_history: list) -> str:
        template = PromptBuilderService._read_prompt("followup.txt")
        
        memory_str = "\n".join([f"{k}: {v}" for k, v in memory.items()]) if memory else "No specific memory extracted yet."
        
        # Format conversation history
        history_str = ""
        for turn in reversed(conversation_history):
            history_str += f"{turn['role'].capitalize()}: {turn['content']}\n"
            
        return template.format(
            exam=exam,
            candidate_name=candidate_name,
            subject=subject,
            difficulty=difficulty,
            stage=stage,
            language=language,
            profile=memory_str,
            conversation_history=history_str.strip()
        )

    @staticmethod
    def build_memory_extraction_prompt(current_memory: dict, last_question: str, last_answer: str) -> str:
        template = PromptBuilderService._read_prompt("memory_extraction.txt")
        memory_str = "\n".join([f"{k}: {v}" for k, v in current_memory.items()]) if current_memory else "Empty"
        
        return template.format(
            current_memory=memory_str,
            last_question=last_question,
            last_answer=last_answer
        )
