from abc import ABC, abstractmethod
from typing import BinaryIO
from app.schemas.speech import AudioMetadata

class BaseAudioStorage(ABC):
    @abstractmethod
    async def save(self, audio_stream: BinaryIO, filename: str, mime_type: str) -> AudioMetadata:
        pass

    @abstractmethod
    async def delete(self, filename: str) -> bool:
        pass

    @abstractmethod
    def get_url(self, filename: str) -> str:
        pass
