from abc import ABC, abstractmethod
from typing import BinaryIO

class BaseTTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, **kwargs) -> BinaryIO:
        """
        Synthesizes text to a binary audio stream.
        """
        pass
