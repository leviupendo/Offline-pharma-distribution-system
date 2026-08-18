from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, require_roles
from app.core.audit import append_audit
from app.models.models import User, Role
from app.schemas.schemas import UserCreate

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("")
def create_user(payload: UserCreate, db: Session = Depends(get_db), admin=Depends(require_roles(Role.SYSTEM_ADMIN))):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(409, "Username already exists")
    user = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.flush()
    append_audit(db, admin.id, "USER_CREATED", "USER", str(user.id), {"role": payload.role.value})
    db.commit()
    return {"id": user.id, "username": user.username, "role": user.role}


@router.post("/{user_id}/disable")
def disable_user(user_id: int, db: Session = Depends(get_db), admin=Depends(require_roles(Role.SYSTEM_ADMIN))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "Administrator cannot disable their own account")
    user.is_active = False
    append_audit(db, admin.id, "USER_DISABLED", "USER", str(user.id), {})
    db.commit()
    return {"status": "disabled", "user_id": user.id}


@router.get("")
def list_users(db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.AUDITOR))):
    return db.query(User).all()
