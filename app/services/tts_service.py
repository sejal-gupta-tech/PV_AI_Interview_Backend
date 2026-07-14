from app.schemas.speech import SpeechGenerateResponse

class SpeechService:
    @staticmethod
    def generate_speech(text: str, language: str) -> SpeechGenerateResponse:
        # Currently NOT_CONFIGURED
        # Do not generate fake audio, do not claim lip sync
        return SpeechGenerateResponse(
            audio_url=None,
            visemes=[],
            provider=None,
            status="not_configured"
        )
