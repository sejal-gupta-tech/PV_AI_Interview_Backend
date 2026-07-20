from fastapi import APIRouter
from app.core.database import get_db

router = APIRouter(prefix="/api/v1", tags=["Health"])

@router.get("/health")
async def health_check():
    # Check DB Connection
    db = get_db()
    db_status = "ok"
    try:
        await db.command("ping")
    except Exception:
        db_status = "error"
        
    return {
        "status": "active" if db_status == "ok" else "degraded",
        "database": db_status,
        "service": "PV AI Interview Backend"
    }
