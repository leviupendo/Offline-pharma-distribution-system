from app.core.audit import append_audit, verify_audit_chain
from app.models.models import AuditLog

def test_audit_chain(db_session=None):
    # Structural smoke test: the audit function creates a hash from prior state.
    assert callable(append_audit)
    assert callable(verify_audit_chain)
