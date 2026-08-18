from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.models.models import Role
from app.core.audit import verify_audit_chain

router = APIRouter(prefix="/validation", tags=["Validation"])

@router.get("/audit-integrity")
def audit_integrity(db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.AUDITOR))):
    valid, bad_record = verify_audit_chain(db)
    return {"valid": valid, "first_invalid_record": bad_record}

@router.get("/status")
def validation_status(user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.AUDITOR))):
    return {
        "environment": "offline-local",
        "external_connectivity_required": False,
        "validation_state": "IMPLEMENTATION_BASELINE",
        "production_use_requires": [
            "documented IQ/OQ/PQ or equivalent validation",
            "approved SOPs",
            "backup/restore test evidence",
            "access-control verification",
            "audit-trail verification",
            "change-control approval",
            "user acceptance testing"
        ]
    }
