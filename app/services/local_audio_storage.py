import os
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import BinaryIO
from app.services.interfaces.audio_storage import BaseAudioStorage
from app.schemas.speech import AudioMetadata
from app.core.voice_config import voice_settings

MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "media" / "audio"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

class LocalAudioStorage(BaseAudioStorage):
    async def save(self, audio_stream: BinaryIO, filename: str, mime_type: str) -> AudioMetadata:
        file_path = MEDIA_DIR / filename
        
        # Save file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(audio_stream.read())
            
        file_size = os.path.getsize(file_path)
        
        # Basic heuristic for duration (this could be done better with mutagen/ffmpeg, but keeping simple for now)
        # Roughly 1MB is around 1 minute of standard MP3
        duration = round((file_size / 1024 / 1024) * 60, 2) if "mp3" in mime_type else 0.0

        return AudioMetadata(
            file_name=filename,
            duration=duration,
            sample_rate=voice_settings.sample_rate,
            mime_type=mime_type,
            created_at=datetime.utcnow().isoformat()
        )

    async def delete(self, filename: str) -> bool:
        file_path = MEDIA_DIR / filename
        if file_path.exists():
            os.remove(file_path)
            return True
        return False

    def get_url(self, filename: str) -> str:
        return f"/media/audio/{filename}"
