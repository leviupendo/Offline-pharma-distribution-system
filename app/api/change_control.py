from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.security import require_roles
from app.core.audit import append_audit
from app.models.models import AuditLog, Role

router = APIRouter(prefix="/change-control", tags=["Change Control"])

class ChangeRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    reason: str = Field(min_length=3, max_length=2000)
    risk_level: str = "MEDIUM"

@router.post("")
def create_change(payload: ChangeRequest, db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.AUDITOR))):
    append_audit(db, user.id, "CHANGE_REQUEST_CREATED", "CHANGE_CONTROL", None, payload.model_dump())
    db.commit()
    return {"status": "PENDING_REVIEW", **payload.model_dump()}

@router.get("")
def list_change_events(db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.AUDITOR))):
    # Previously this returned a hardcoded placeholder note and no
    # actual data (`rows = ... if False else []`), so the endpoint
    # never listed anything despite being documented as change-control
    # event listing. Change requests are recorded as audit log entries
    # (see create_change above), so read them back from there.
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.action == "CHANGE_REQUEST_CREATED")
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return [
        {
            "id": row.id,
            "timestamp": row.timestamp,
            "user_id": row.user_id,
            "details": json.loads(row.details_json),
        }
        for row in rows
    ]
