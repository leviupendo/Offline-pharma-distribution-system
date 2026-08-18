from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.core.audit import append_audit
from app.models.models import (
    AuditLog, BatchStatus, Customer, Inventory, Order, OrderAllocation,
    OrderLine, PacketProduction, Role, Batch,
)
from pydantic import BaseModel, Field

router = APIRouter(prefix="/recalls", tags=["Recalls"])

class RecallCreate(BaseModel):
    batch_id: str
    reason: str = Field(min_length=3, max_length=1000)

@router.post("")
def create_recall(payload: RecallCreate, db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.QC_MANAGER))):
    batch = db.query(Batch).filter(Batch.batch_id == payload.batch_id).first()
    if not batch:
        raise HTTPException(404, "Batch not found")
    if batch.status == BatchStatus.RECALLED:
        raise HTTPException(409, "Batch is already recalled")
    if batch.status == BatchStatus.REJECTED:
        raise HTTPException(409, "Rejected batches were never released and cannot be recalled")
    previous_status = batch.status
    batch.status = BatchStatus.RECALLED
    append_audit(db, user.id, "BATCH_RECALLED", "BATCH", str(batch.id), {
        "reason": payload.reason, "previous_status": previous_status.value
    })
    db.commit()
    return {"batch_id": batch.batch_id, "status": batch.status}

@router.get("/{batch_id}/impact")
def recall_impact(batch_id: str, db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.QC_MANAGER, Role.AUDITOR))):
    batch = db.query(Batch).filter(Batch.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(404, "Batch not found")

    # Inventory has no batch_id column; it's reached through
    # packet_production. Join through it to find affected stock still
    # on hand anywhere in the warehouse.
    inventory = (
        db.query(Inventory, PacketProduction)
        .join(PacketProduction, Inventory.packet_lot_id == PacketProduction.id)
        .filter(PacketProduction.batch_id == batch.id, Inventory.quantity_on_hand > 0)
        .all()
    )

    # This was previously hardcoded to an empty list, so a recall
    # report never actually showed which customer orders had already
    # received stock from the affected batch — the entire point of a
    # recall impact report. Trace Order -> OrderLine -> OrderAllocation
    # -> PacketProduction -> Batch to find every order that drew on
    # this batch, regardless of current inventory levels.
    order_rows = (
        db.query(Order, Customer, OrderAllocation)
        .join(Customer, Order.customer_id == Customer.id)
        .join(OrderLine, OrderLine.order_id == Order.id)
        .join(OrderAllocation, OrderAllocation.order_line_id == OrderLine.id)
        .join(PacketProduction, OrderAllocation.packet_lot_id == PacketProduction.id)
        .filter(PacketProduction.batch_id == batch.id)
        .all()
    )
    orders_seen = {}
    for order, customer, allocation in order_rows:
        entry = orders_seen.setdefault(order.id, {
            "order_id": order.order_id,
            "customer_ref": customer.customer_ref,
            "status": order.status.value,
            "affected_quantity": 0,
        })
        entry["affected_quantity"] += allocation.quantity

    return {
        "batch_id": batch.batch_id,
        "batch_status": batch.status.value,
        "inventory_on_hand": [
            {"location_id": inv.location_id, "quantity": inv.quantity_on_hand, "packet_lot_id": lot.packet_lot_id}
            for inv, lot in inventory
        ],
        "orders": list(orders_seen.values()),
    }
