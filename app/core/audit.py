import hashlib, json
from datetime import datetime, timezone
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.models import AuditLog


def _canonical_timestamp(dt: datetime) -> str:
    """Normalize a timestamp to a fixed UTC ISO-8601 string.

    SQLite (the default, offline-friendly backend) does not actually
    preserve timezone-aware datetimes across a round trip even with
    DateTime(timezone=True) — a value hashed at write time as
    "...+00:00" comes back from the database as a naive datetime with
    no offset. PostgreSQL does preserve it. Without this normalization,
    hashes computed at write time and at verify time diverge purely
    because of which database backend is in use, and every untampered
    audit entry is reported as invalid. Assume naive datetimes are UTC
    (the only thing this codebase ever writes) and always compare in
    UTC so the chain is backend-independent.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def append_audit(db: Session, user_id: int | None, action: str, entity_type: str, entity_id: str | None, details: dict):
    previous = db.query(AuditLog).order_by(desc(AuditLog.id)).first()
    previous_hash = previous.entry_hash if previous else "GENESIS"
    timestamp = datetime.now(timezone.utc)
    payload = json.dumps(details, sort_keys=True, separators=(",", ":"))
    raw = "|".join([previous_hash, _canonical_timestamp(timestamp), str(user_id), action, entity_type, str(entity_id), payload])
    entry_hash = hashlib.sha256(raw.encode()).hexdigest()
    db.add(AuditLog(
        timestamp=timestamp, user_id=user_id, action=action, entity_type=entity_type,
        entity_id=entity_id, details_json=payload, previous_hash=previous_hash, entry_hash=entry_hash
    ))

def verify_audit_chain(db: Session):
    rows = db.query(AuditLog).order_by(AuditLog.id).all()
    previous = "GENESIS"
    for row in rows:
        payload = row.details_json
        raw = "|".join([previous, _canonical_timestamp(row.timestamp), str(row.user_id), row.action, row.entity_type, str(row.entity_id), payload])
        expected = hashlib.sha256(raw.encode()).hexdigest()
        if row.previous_hash != previous or row.entry_hash != expected:
            return False, row.id
        previous = row.entry_hash
    return True, None

