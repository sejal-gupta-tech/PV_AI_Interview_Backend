from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PV AI Interview Backend"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_NAME: str = "pv_interview_db"
    
    class Config:
        env_file = ".env"

settings = Settings()
