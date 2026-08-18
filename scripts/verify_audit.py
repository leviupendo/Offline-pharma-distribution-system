import sys
from pathlib import Path

# Allow `python scripts/verify_audit.py` to work from the repo root
# without requiring PYTHONPATH to be set manually.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.core.audit import verify_audit_chain

db = SessionLocal()
ok, bad_id = verify_audit_chain(db)
db.close()
if ok:
    print("AUDIT CHAIN: VALID")
else:
    print(f"AUDIT CHAIN: INVALID at record {bad_id}")
    raise SystemExit(1)
