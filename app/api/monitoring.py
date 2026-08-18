from fastapi import APIRouter, Depends
from app.core.security import require_roles
from app.models.models import Role

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@router.get("/posture")
def posture(user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.AUDITOR))):
    return {
        "internet_required": False,
        "remote_access_default": False,
        "telemetry": "disabled",
        "cloud_dependencies": False,
        "external_identity_provider": False,
        "local_only": True
    }
