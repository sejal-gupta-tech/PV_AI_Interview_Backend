import logging
import io
import datetime
from fastapi import UploadFile
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger("speech_to_text_service")

class SpeechToTextService:
    @staticmethod
    async def transcribe_audio(interview_id: str, question_number: int, audio: UploadFile) -> str:
        """
        Transcribes the uploaded audio file using OpenAI's Whisper API and saves the record to MongoDB.
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Read the file content
        audio_content = await audio.read()
        if len(audio_content) == 0:
            raise ValueError("Audio file is empty")
            
        max_size_bytes = 25 * 1024 * 1024 # 25 MB
        if len(audio_content) > max_size_bytes:
            raise ValueError("Audio file size exceeds the 25MB limit")
            
        # The OpenAI API requires a file-like object with a name attribute
        file_obj = (audio.filename, io.BytesIO(audio_content))
        
        try:
            # Send to OpenAI
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=file_obj,
                response_format="text"
            )
            
            transcript = response.strip()
            
            # Save to MongoDB
            db = get_db()
            
            # We initialize the question text as empty string as it's not provided in the payload.
            # In a real system, we might look up the question text from the session.
            doc = {
                "interview_id": interview_id,
                "question_number": question_number,
                "question": "",
                "candidate_answer": transcript,
                "transcript": transcript,
                "created_at": datetime.datetime.utcnow()
            }
            
            await db["live_interview_transcripts"].insert_one(doc)
            
            return transcript
            
        except Exception as e:
            logger.exception(f"Error during audio transcription: {e}")
            raise RuntimeError(f"Failed to transcribe audio: {str(e)}")
