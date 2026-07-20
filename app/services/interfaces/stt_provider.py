from abc import ABC, abstractmethod
from typing import BinaryIO

class BaseSTTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_stream: BinaryIO, filename: str) -> dict:
        """
        Transcribes a binary audio stream and returns the transcription payload.
        Expected format: {"transcript": str, "confidence": float, "language": str}
        """
        pass
