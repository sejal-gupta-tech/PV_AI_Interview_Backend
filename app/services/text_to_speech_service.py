import logging
import shutil
from pathlib import Path
from app.services.piper_tts_service import PiperTTSService

logger = logging.getLogger("text_to_speech_service")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_AUDIO_DIR = BASE_DIR / "uploads" / "audio"
UPLOADS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class TextToSpeechService:
    @staticmethod
    def generate_speech(text: str, language: str = "english") -> dict:
        """
        Converts text to speech using Piper and saves it to uploads/audio/.
        Returns the relative audio URL path.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TextToSpeechService")
            return {"voice_supported": False}
            
        try:
            # Generate the file using Piper TTS (which saves it in piper/output)
            result = PiperTTSService.generate_speech(text, language)
            
            if not result or not result.get("filename"):
                return {"voice_supported": False}
                
            filename = result["filename"]
            source_path = BASE_DIR / "piper" / "output" / filename
            dest_path = UPLOADS_AUDIO_DIR / filename
            
            # Move it to uploads/audio/ to satisfy requirements
            if source_path.exists():
                shutil.move(str(source_path), str(dest_path))
                
                return {
                    "audio_url": f"/uploads/audio/{filename}",
                    "voice": result.get("model_name", "Unknown"),
                    "language": result.get("language", language),
                    "generation_time": result.get("latency_ms", 0),
                    "voice_supported": True
                }
            else:
                logger.error(f"Piper generated filename {filename} but it does not exist at {source_path}")
                return {"voice_supported": False}
                
        except ValueError as e:
            if "PIPER_MODEL_NOT_FOUND" in str(e):
                logger.warning(f"Piper TTS Model not found: {e}")
                return {"voice_supported": False}
            logger.exception(f"TextToSpeechService failed to generate speech: {e}")
            return {"voice_supported": False}
        except Exception as e:
            logger.exception(f"TextToSpeechService failed to generate speech: {e}")
            return {"voice_supported": False}
