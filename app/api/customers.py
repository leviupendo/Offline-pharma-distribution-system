from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.core.audit import append_audit
from app.models.models import Customer, Role
from app.schemas.schemas import CustomerCreate

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post("")
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.ORDER_ENTRY))):
    if db.query(Customer).filter(Customer.customer_ref == payload.customer_ref).first():
        raise HTTPException(409, "Customer reference already exists")
    customer = Customer(**payload.model_dump())
    db.add(customer); db.flush()
    append_audit(db, user.id, "CUSTOMER_CREATED", "CUSTOMER", str(customer.id), {"customer_ref": customer.customer_ref})
    db.commit()
    return customer

@router.get("")
def list_customers(db: Session = Depends(get_db), user=Depends(require_roles(
    Role.SYSTEM_ADMIN, Role.ORDER_ENTRY, Role.WAREHOUSE, Role.AUDITOR
))):
    return db.query(Customer).order_by(Customer.customer_ref).all()
