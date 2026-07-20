from typing import List

# Configurable stage definitions. Could be loaded from DB later.
DEFAULT_STAGES = [
    "Introduction",
    "Motivation",
    "Teaching Philosophy",
    "Pedagogy",
    "Subject Knowledge",
    "Classroom Management",
    "Situational Questions",
    "Current Affairs",
    "Closing"
]

class InterviewStageService:
    @staticmethod
    def get_initial_stage() -> str:
        return DEFAULT_STAGES[0]
        
    @staticmethod
    def determine_next_stage(current_stage: str, questions_asked_in_stage: int, stages: List[str] = DEFAULT_STAGES) -> str:
        try:
            current_index = stages.index(current_stage)
        except ValueError:
            current_index = 0
            
        # Example progression logic: Advance stage every 2 questions
        if questions_asked_in_stage >= 2:
            if current_index + 1 < len(stages):
                return stages[current_index + 1]
                
        return current_stage
