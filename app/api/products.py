from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.core.audit import append_audit
from app.models.models import Product, Role
from app.schemas.schemas import ProductCreate

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("")
def create_product(payload: ProductCreate, db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.PRODUCTION))):
    if db.query(Product).filter(Product.code == payload.code).first():
        raise HTTPException(409, "Product code already exists")
    if payload.standard_fill_weight_grams <= 0:
        raise HTTPException(400, "Fill weight must be positive")
    product = Product(**payload.model_dump())
    db.add(product); db.flush()
    append_audit(db, user.id, "PRODUCT_CREATED", "PRODUCT", str(product.id), {"code": product.code})
    db.commit()
    return product

@router.get("")
def list_products(db: Session = Depends(get_db), user=Depends(require_roles(
    Role.SYSTEM_ADMIN, Role.PRODUCTION, Role.QC_MANAGER, Role.WAREHOUSE, Role.ORDER_ENTRY, Role.AUDITOR, Role.GUEST
))):
    return db.query(Product).order_by(Product.code).all()
