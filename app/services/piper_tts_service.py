import subprocess
import uuid
import time
import logging
from pathlib import Path
from app.core.voice_config import voice_settings

logger = logging.getLogger("piper_tts")
logger.setLevel(logging.INFO)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PIPER_DIR = BASE_DIR / "piper"
VOICES_DIR = PIPER_DIR / "voices"
OUTPUT_DIR = PIPER_DIR / "output"
PIPER_EXE = PIPER_DIR / "piper.exe"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class PiperTTSService:
    _models_cache = {
        "english": [],
        "hindi": [],
        "other": []
    }
    _initialized = False

    @classmethod
    def _initialize_cache(cls):
        if cls._initialized:
            return
            
        if not VOICES_DIR.exists():
            logger.warning(f"Voices directory not found: {VOICES_DIR}")
            cls._initialized = True
            return

        for file in VOICES_DIR.glob("*.onnx"):
            filename = file.name.lower()
            if filename.startswith("en_"):
                cls._models_cache["english"].append(file)
            elif filename.startswith("hi_"):
                cls._models_cache["hindi"].append(file)
            else:
                cls._models_cache["other"].append(file)
                
        logger.info(f"PiperTTSService: Scanned voices. English: {len(cls._models_cache['english'])}, Hindi: {len(cls._models_cache['hindi'])}, Other: {len(cls._models_cache['other'])}")
        cls._initialized = True

    @classmethod
    def _select_model(cls, language: str) -> Path:
        cls._initialize_cache()
        
        category = "english"
        if language.lower() == "hindi":
            category = "hindi"
            
        models = cls._models_cache.get(category, [])
        if not models:
            raise ValueError(f"PIPER_MODEL_NOT_FOUND: No Piper models found for language category: {category}")
            
        # Select configured default if multiple exist, else first available
        configured_default = getattr(voice_settings, "tts_voice", "").lower()
        if configured_default and configured_default != "alloy":
            for model in models:
                if configured_default in model.name.lower():
                    return model
                    
        return models[0]

    @classmethod
    def generate_speech(cls, text: str, language: str) -> dict:
        start_time = time.time()
        
        model_path = cls._select_model(language)
            
        filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = OUTPUT_DIR / filename
        
        try:
            # Use safe subprocess call
            process = subprocess.Popen(
                [str(PIPER_EXE), "-m", str(model_path), "-f", str(output_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            
            stdout, stderr = process.communicate(input=text + "\n")
            
            if not output_path.exists():
                raise Exception(f"Piper failed to create output file. stderr: {stderr}")
                
            latency_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Piper TTS Generation | Selected Voice: {model_path.name} | "
                f"Language: {language} | Output: {filename} | Latency: {latency_ms}ms"
            )
                
            return {
                "filename": filename,
                "model_name": model_path.name,
                "latency_ms": latency_ms,
                "language": language
            }
        except ValueError as e:
            raise e # Structured API error propagated
        except Exception as e:
            raise Exception(f"Piper TTS generation failed: {str(e)}")
