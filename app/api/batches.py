from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.core.audit import append_audit
from app.models.models import Batch, BatchStatus, Role
from app.schemas.schemas import BatchCreate, QCDecision

router = APIRouter(prefix="/batches", tags=["Batches"])


@router.post("")
def create_batch(payload: BatchCreate, db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.PRODUCTION))):
    if db.query(Batch).filter(Batch.batch_id == payload.batch_id).first():
        raise HTTPException(409, "Batch already exists")
    if payload.expiry_date <= payload.production_date:
        raise HTTPException(400, "Expiry date must be after production date")
    b = Batch(**payload.model_dump(), status=BatchStatus.QUARANTINE)
    db.add(b)
    db.flush()
    append_audit(db, user.id, "BATCH_CREATED", "BATCH", str(b.id), {"batch_id": b.batch_id, "status": b.status.value})
    db.commit()
    return b


@router.post("/{batch_pk}/qc")
def qc_decision(batch_pk: int, payload: QCDecision, db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.QC_MANAGER))):
    b = db.get(Batch, batch_pk)
    if not b:
        raise HTTPException(404, "Batch not found")
    if b.status != BatchStatus.QUARANTINE:
        raise HTTPException(409, "Only quarantine batches can receive an initial QC decision")
    if payload.decision not in (BatchStatus.RELEASED, BatchStatus.REJECTED):
        raise HTTPException(400, "QC decision must be RELEASED or REJECTED")
    if not payload.qc_results.strip():
        raise HTTPException(400, "QC results are required")
    b.status = payload.decision
    b.qc_results = payload.qc_results
    append_audit(db, user.id, f"BATCH_{payload.decision.value}", "BATCH", str(b.id), {"results": payload.qc_results})
    db.commit()
    return b


@router.get("")
def list_batches(db: Session = Depends(get_db), user=Depends(require_roles(
    Role.SYSTEM_ADMIN, Role.PRODUCTION, Role.QC_MANAGER, Role.WAREHOUSE, Role.AUDITOR, Role.GUEST
))):
    return db.query(Batch).order_by(Batch.expiry_date.asc()).all()
