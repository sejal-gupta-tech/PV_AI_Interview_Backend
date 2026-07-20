from typing import List

DIFFICULTY_LEVELS = [
    "Easy",
    "Medium",
    "Advanced",
    "Scenario-Based",
    "Case Study"
]

class DifficultyService:
    @staticmethod
    def adjust_difficulty(current_difficulty: str, struggled: bool) -> str:
        try:
            current_index = DIFFICULTY_LEVELS.index(current_difficulty)
        except ValueError:
            current_index = 1 # Default to Medium
            
        if struggled:
            # Drop difficulty if they struggled, but not below Easy
            new_index = max(0, current_index - 1)
        else:
            # Increase difficulty slowly as they succeed
            new_index = min(len(DIFFICULTY_LEVELS) - 1, current_index + 1)
            
        return DIFFICULTY_LEVELS[new_index]
