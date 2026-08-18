from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.models.models import AuditLog, Role

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("")
def audit_logs(db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.AUDITOR))):
    return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(500).all()
