import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("config_loader")

class ExamConfigLoader:
    _cached_config: Dict[str, Any] = None
    
    @classmethod
    def load_all(cls, force_reload: bool = False) -> Dict[str, Any]:
        """
        Loads and merges all exam configuration JSON files from app/config/
        Validates the basic Exam -> Subject -> Topics structure.
        """
        if cls._cached_config is not None and not force_reload:
            return cls._cached_config
            
        merged_config = {}
        config_dir = Path(__file__).resolve().parent.parent / "config"
        
        for file_path in config_dir.glob("*.json"):
            if file_path.name == "exams.json":
                continue # Skip the old monolithic file if it's still lingering
                
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Schema validation
                for exam_name, exam_data in data.items():
                    if not isinstance(exam_data, dict):
                        raise ValueError(f"Invalid exam data for {exam_name}")
                        
                    for subject_name, subject_data in exam_data.items():
                        if not isinstance(subject_data, dict) or "topics" not in subject_data:
                            raise ValueError(f"Invalid subject data for {subject_name} in {exam_name}. Must contain 'topics'.")
                        if not isinstance(subject_data["topics"], list):
                            raise ValueError(f"'topics' must be a list for {subject_name} in {exam_name}")
                            
                    # Merge into global config
                    merged_config[exam_name] = exam_data
                    
            except Exception as e:
                logger.error(f"Error loading {file_path.name}: {e}")
                raise ValueError(f"Failed to load config {file_path.name}: {e}")
                
        cls._cached_config = merged_config
        return merged_config

def get_exam_config() -> Dict[str, Any]:
    """Dependency injection helper"""
    return ExamConfigLoader.load_all()
