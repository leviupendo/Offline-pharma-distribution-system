from fastapi import APIRouter, Depends
from app.core.security import require_roles
from app.models.models import Role
from app.core.database import engine

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
def status(user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.AUDITOR))):
    return {
        "application": "Offline Pharmaceutical Distribution System",
        "database": engine.url.drivername,
        "mode": "LOCAL_ONLY",
        "status": "operational"
    }
