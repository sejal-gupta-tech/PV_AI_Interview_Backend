import subprocess
import uuid
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PIPER_DIR = BASE_DIR / "piper"
VOICES_DIR = PIPER_DIR / "voices"
OUTPUT_DIR = PIPER_DIR / "output"
PIPER_EXE = PIPER_DIR / "piper.exe"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class PiperTTSService:
    @staticmethod
    def generate_speech(text: str, language: str) -> str:
        if language.lower() == "hindi":
            model_path = VOICES_DIR / "hi_IN-rohan-medium.onnx"
        else:
            model_path = VOICES_DIR / "en_US-lessac-medium.onnx"
            
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
            
            stdout, stderr = process.communicate(input=text)
            
            if process.returncode != 0:
                raise Exception(f"Piper error: {stderr}")
                
            return filename
        except Exception as e:
            raise Exception(f"Piper TTS generation failed: {str(e)}")
