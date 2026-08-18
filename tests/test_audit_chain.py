from app.core.audit import append_audit, verify_audit_chain
from app.core.database import Base, SessionLocal, engine


def _fresh_db():
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_audit_chain_valid_after_db_round_trip():
    """Regression test: previously, verify_audit_chain always reported
    a freshly written, untampered chain as INVALID on SQLite, because
    the hash was computed from timestamp.isoformat() before the row
    was committed (tz-aware, e.g. "...+00:00") but recomputed from the
    same field after a reload from SQLite (naive, no offset). The two
    strings differed, so every legitimate entry failed verification.
    """
    db = _fresh_db()
    append_audit(db, None, "TEST_ACTION", "TEST_ENTITY", "1", {"k": "v"})
    db.commit()

    # Use a brand new session so the row is genuinely reloaded from the
    # database rather than served from SQLAlchemy's identity map.
    db.close()
    fresh_db = _fresh_db()
    ok, bad_id = verify_audit_chain(fresh_db)
    fresh_db.close()

    assert ok is True
    assert bad_id is None


def test_audit_chain_detects_tampering():
    db = _fresh_db()
    append_audit(db, None, "TEST_ACTION_1", "TEST_ENTITY", "1", {"k": "v"})
    append_audit(db, None, "TEST_ACTION_2", "TEST_ENTITY", "2", {"k": "v"})
    db.commit()
    db.close()

    from app.models.models import AuditLog

    tamper_db = _fresh_db()
    row = tamper_db.query(AuditLog).order_by(AuditLog.id).first()
    row.action = "TAMPERED"
    tampered_id = row.id
    tamper_db.commit()
    tamper_db.close()

    verify_db = _fresh_db()
    ok, bad_id = verify_audit_chain(verify_db)
    verify_db.close()

    assert ok is False
    assert bad_id == tampered_id
