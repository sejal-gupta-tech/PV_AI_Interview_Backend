from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api import health, interview, speech, mock_interview, session
from pathlib import Path
from fastapi.staticfiles import StaticFiles

import logging

logger = logging.getLogger("startup")
logger.setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    await connect_to_mongo()
    
    key_status = "Yes" if settings.OPENAI_API_KEY else "No"
    logger.info(f"OpenAI API Key Loaded: {key_status}")
    
    yield
    # Shutdown actions
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend Foundation for PV Classes AI Mock Interview",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local Next.js development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount media directory for audio file serving
media_dir = Path(__file__).resolve().parent.parent / "media"
media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

@app.get("/", include_in_schema=False)
async def root():
    # Redirect root to Swagger UI documentation
    return RedirectResponse(url="/docs")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Return empty to prevent 404 errors in browser
    return {}

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    base_dir = Path(__file__).resolve().parent.parent
    file_path = base_dir / "piper" / "output" / filename
    
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path, media_type="audio/wav")
    return {"status": "error", "message": "Audio file not found."}

# Include Routers
app.include_router(health.router)
app.include_router(interview.router)
app.include_router(speech.router)
app.include_router(mock_interview.router)
app.include_router(session.router)
