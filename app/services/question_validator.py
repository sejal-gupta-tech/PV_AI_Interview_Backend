import logging
from typing import Dict, Any, Tuple, Set
from pydantic import BaseModel, Field, field_validator, ValidationError
from app.services.duplicate_checker import DuplicateCheckerService

logger = logging.getLogger("question_validator")

class QuestionValidationSchema(BaseModel):
    exam: str = Field(..., min_length=1, description="Exam cannot be empty")
    subject: str = Field(..., min_length=1, description="Subject cannot be empty")
    topic: str = Field(..., min_length=1, description="Topic cannot be empty")
    difficulty: str = Field(..., min_length=1, description="Difficulty cannot be empty")
    language: str = Field(..., min_length=1, description="Language cannot be empty")
    question: str = Field(..., min_length=20, description="Question length minimum 20 characters")
    options: list[str]
    correct_answer: int = Field(..., ge=0, le=3, description="Correct answer index must be between 0 and 3")
    explanation: str = Field(..., min_length=1, description="Explanation required and cannot be empty")

    @field_validator('options')
    @classmethod
    def validate_options(cls, v: list[str]) -> list[str]:
        if len(v) != 4:
            raise ValueError("Exactly four options are required")
        for opt in v:
            if not opt or len(opt.strip()) < 2:
                raise ValueError("Options length minimum 2 characters")
        
        unique_options = set(opt.strip().lower() for opt in v)
        if len(unique_options) != 4:
            raise ValueError("No duplicate options allowed")
            
        return v
        
    @field_validator('question', 'explanation', 'exam', 'subject', 'topic', 'difficulty', 'language')
    @classmethod
    def no_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("No empty values allowed")
        return v

class QuestionValidatorService:
    @staticmethod
    def validate(question_data: Dict[str, Any], expected_language: str, current_batch_hashes: Set[str]) -> Tuple[bool, str]:
        """
        Validate via Pydantic and perform contextual checks.
        Returns (is_valid: bool, error_message: str)
        """
        try:
            # 1. Pydantic validation
            validated_data = QuestionValidationSchema(**question_data)
            
            # 2. Language matches requested language
            if validated_data.language.strip().lower() != expected_language.strip().lower():
                return False, f"Language mismatch: Expected '{expected_language}', got '{validated_data.language}'"
                
            # 3. Question does not already exist inside current batch
            q_hash = DuplicateCheckerService.generate_hash(validated_data.question)
            if q_hash in current_batch_hashes:
                return False, "Duplicate question inside current batch"
                
            return True, "Valid"
            
        except ValidationError as e:
            # Format detailed pydantic errors
            error_details = []
            for err in e.errors():
                loc = ".".join([str(l) for l in err["loc"]])
                msg = err["msg"]
                error_details.append(f"{loc}: {msg}")
            
            error_str = " | ".join(error_details)
            return False, error_str
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            return False, f"Unexpected error: {str(e)}"
