from fastapi import APIRouter, HTTPException, Depends
import uuid
from typing import Dict, Any
from pydantic import BaseModel
from app.services.job_manager import JobManagerService
from app.services.pdf_extraction_service import PdfExtractionService
from app.core.config_loader import get_exam_config
import os

router = APIRouter(prefix="/api/question-bank", tags=["Question Bank Generation"])

@router.post("/start-generation")
async def start_generation(config: Dict[str, Any] = Depends(get_exam_config)):
    job_id = str(uuid.uuid4())
    try:
        result = await JobManagerService.start_generation(job_id, config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    try:
        status = await JobManagerService.get_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop/{job_id}")
async def stop_generation(job_id: str):
    try:
        # Verify job exists first
        status = await JobManagerService.get_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
            
        result = await JobManagerService.stop_generation(job_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ProcessPdfRequest(BaseModel):
    filename: str

@router.post("/process-pdf")
async def process_pdf(request: ProcessPdfRequest):
    try:
        from pathlib import Path
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        file_path = BASE_DIR / "uploads" / "question_bank" / request.filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {request.filename} not found in uploads/question_bank")
            
        pages = PdfExtractionService.extract_pages(str(file_path))
        questions = await PdfExtractionService.extract_questions(pages)
        
        return {
            "status": "success",
            "pages_processed": len(pages),
            "questions_extracted": len(questions),
            "questions": questions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
