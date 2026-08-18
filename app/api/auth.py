from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password
from app.core.audit import append_audit
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _as_aware_utc(dt: datetime | None) -> datetime | None:
    """SQLite drops the tz offset on DateTime(timezone=True) columns
    across a round trip (a value written as tz-aware UTC comes back
    naive), so comparing a freshly-read locked_until against
    datetime.now(timezone.utc) raised "can't compare offset-naive and
    offset-aware datetimes" on the very next login after a lockout was
    set. Everything this app ever writes is UTC, so treat a naive
    value as UTC rather than raising.
    """
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

@router.post("/login")
def login(payload: dict, db: Session = Depends(get_db)):
    username, password = payload.get("username",""), payload.get("password","")
    user = db.query(User).filter(User.username == username).first()
    now = datetime.now(timezone.utc)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    locked_until = _as_aware_utc(user.locked_until)
    if locked_until and locked_until > now:
        raise HTTPException(status_code=423, detail="Account temporarily locked")
    if not verify_password(password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.LOCKOUT_MINUTES)
            user.failed_attempts = 0
        append_audit(db, user.id, "LOGIN_FAILED", "USER", str(user.id), {})
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.failed_attempts = 0; user.locked_until = None
    append_audit(db, user.id, "LOGIN_SUCCESS", "USER", str(user.id), {})
    db.commit()
    token = jwt.encode({"sub": str(user.id), "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "username": user.username}
