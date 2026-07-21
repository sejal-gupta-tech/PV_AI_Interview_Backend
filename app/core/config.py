# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PV AI Interview Backend"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] = ["*"]
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_NAME: str = "pv_interview_db"
    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
