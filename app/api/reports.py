from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import require_roles
from app.models.models import Batch, Inventory, Order, OrderStatus, PacketProduction, Role

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(require_roles(
    Role.SYSTEM_ADMIN, Role.QC_MANAGER, Role.PRODUCTION, Role.WAREHOUSE, Role.ORDER_ENTRY, Role.AUDITOR
))):
    return {
        "batches": db.query(func.count(Batch.id)).scalar() or 0,
        "released_batches": db.query(func.count(Batch.id)).filter(Batch.status == "RELEASED").scalar() or 0,
        "quarantine_batches": db.query(func.count(Batch.id)).filter(Batch.status == "QUARANTINE").scalar() or 0,
        "rejected_batches": db.query(func.count(Batch.id)).filter(Batch.status == "REJECTED").scalar() or 0,
        "packet_lots": db.query(func.count(PacketProduction.id)).scalar() or 0,
        "inventory_units": db.query(func.coalesce(func.sum(Inventory.quantity_on_hand), 0)).scalar() or 0,
        "open_orders": db.query(func.count(Order.id)).filter(Order.status.in_([
            OrderStatus.DRAFT, OrderStatus.ALLOCATED, OrderStatus.PICKED, OrderStatus.PACKED
        ])).scalar() or 0,
        "shipped_orders": db.query(func.count(Order.id)).filter(Order.status == OrderStatus.SHIPPED).scalar() or 0,
    }


@router.get("/expiry")
def expiry_report(db: Session = Depends(get_db), user=Depends(require_roles(
    Role.SYSTEM_ADMIN, Role.WAREHOUSE, Role.QC_MANAGER, Role.AUDITOR
))):
    rows = (
        db.query(Batch, Inventory, PacketProduction)
        .join(PacketProduction, PacketProduction.batch_id == Batch.id)
        .join(Inventory, Inventory.packet_lot_id == PacketProduction.id)
        .order_by(Batch.expiry_date.asc())
        .all()
    )
    return [{
        "batch_id": batch.batch_id,
        "expiry_date": batch.expiry_date,
        "status": batch.status,
        "packet_lot_id": lot.packet_lot_id,
        "quantity_on_hand": inv.quantity_on_hand,
        "location": inv.location_id,
    } for batch, inv, lot in rows]
