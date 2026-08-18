from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc
from app.core.database import get_db
from app.core.security import require_roles
from app.core.audit import append_audit
from app.models.models import (
    Batch, Customer, Inventory, InventoryMovement, Order, OrderAllocation,
    OrderLine, OrderStatus, PacketProduction, ProofOfDelivery, Role
)
from app.schemas.schemas import OrderCreate, StatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("")
def create_order(payload: OrderCreate, db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.ORDER_ENTRY))):
    customer = db.query(Customer).filter(Customer.customer_ref == payload.customer_ref, Customer.active == True).first()
    if not customer:
        raise HTTPException(404, "Customer reference not found")
    if db.query(Order).filter(Order.order_id == payload.order_id).first():
        raise HTTPException(409, "Order already exists")

    order = Order(order_id=payload.order_id, customer_id=customer.id)
    db.add(order)
    db.flush()
    for line in payload.lines:
        order.lines.append(OrderLine(requested_quantity=line.requested_quantity))
    append_audit(db, user.id, "ORDER_CREATED", "ORDER", str(order.id), {
        "order_id": order.order_id, "customer_ref": customer.customer_ref, "line_count": len(order.lines)
    })
    db.commit()
    return order


@router.post("/{order_pk}/allocate")
def allocate(order_pk: int, db: Session = Depends(get_db), user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.ORDER_ENTRY, Role.WAREHOUSE))):
    order = db.get(Order, order_pk)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status not in (OrderStatus.DRAFT, OrderStatus.ALLOCATED):
        raise HTTPException(409, "Order cannot be allocated in its current state")

    # Allocation is deliberately FEFO and only considers released batches.
    for line in order.lines:
        already = sum(a.quantity for a in line.allocations)
        remaining = line.requested_quantity - already
        if remaining <= 0:
            continue

        rows = (
            db.query(Inventory, PacketProduction, Batch)
            .join(PacketProduction, Inventory.packet_lot_id == PacketProduction.id)
            .join(Batch, PacketProduction.batch_id == Batch.id)
            .filter(
                Inventory.status == "AVAILABLE",
                Inventory.quantity_on_hand > 0,
                Batch.status == "RELEASED",
            )
            .order_by(asc(Batch.expiry_date), asc(PacketProduction.id))
            .all()
        )

        for inv, lot, batch in rows:
            if remaining <= 0:
                break
            qty = min(remaining, inv.quantity_on_hand)
            inv.quantity_on_hand -= qty
            db.add(OrderAllocation(order_line_id=line.id, packet_lot_id=lot.id, quantity=qty))
            db.add(InventoryMovement(
                inventory_id=inv.id,
                movement_type="ALLOCATE",
                quantity=-qty,
                reference_type="ORDER",
                reference_id=order.order_id,
            ))
            remaining -= qty

        if remaining > 0:
            db.rollback()
            raise HTTPException(409, f"Insufficient released stock for order line {line.id}")

    order.status = OrderStatus.ALLOCATED
    append_audit(db, user.id, "ORDER_ALLOCATED_FEFO", "ORDER", str(order.id), {})
    db.commit()
    # OrderAllocation rows above were added via db.add(OrderAllocation(
    # order_line_id=line.id, ...)) rather than line.allocations.append(...),
    # so each line's already-loaded `allocations` collection (read a few
    # lines up via `sum(a.quantity for a in line.allocations)`) never
    # picked up the new rows in memory. Expire it, then explicitly touch
    # it so it's reloaded into the object's __dict__ before serialization
    # — jsonable_encoder reads objects via vars(obj), which reflects
    # whatever's already in __dict__ rather than triggering a lazy load,
    # so expiring alone would make the field vanish from the response
    # entirely instead of showing what was actually just persisted.
    for line in order.lines:
        db.expire(line, ["allocations"])
        _ = line.allocations
    return order


@router.post("/{order_pk}/status")
def update_status(order_pk: int, payload: StatusUpdate, db: Session = Depends(get_db), user=Depends(require_roles(
    Role.SYSTEM_ADMIN, Role.WAREHOUSE, Role.ORDER_ENTRY
))):
    order = db.get(Order, order_pk)
    if not order:
        raise HTTPException(404, "Order not found")
    allowed = {
        OrderStatus.ALLOCATED: {OrderStatus.PICKED, OrderStatus.CANCELLED},
        OrderStatus.PICKED: {OrderStatus.PACKED, OrderStatus.CANCELLED},
        OrderStatus.PACKED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
        OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
        OrderStatus.DRAFT: {OrderStatus.CANCELLED},
    }
    if payload.status != order.status and payload.status not in allowed.get(order.status, set()):
        raise HTTPException(409, f"Invalid transition {order.status} -> {payload.status}")
    old = order.status
    order.status = payload.status
    append_audit(db, user.id, "ORDER_STATUS_CHANGED", "ORDER", str(order.id), {"from": old.value, "to": order.status.value})
    db.commit()
    return order


@router.post("/{order_pk}/pod")
def proof_of_delivery(
    order_pk: int,
    recipient_reference: str,
    notes: str = "",
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.WAREHOUSE)),
):
    order = db.get(Order, order_pk)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.SHIPPED:
        raise HTTPException(409, "Only shipped orders can receive proof of delivery")
    if db.query(ProofOfDelivery).filter(ProofOfDelivery.order_id == order.id).first():
        raise HTTPException(409, "Proof of delivery already recorded")
    pod = ProofOfDelivery(order_id=order.id, recipient_reference=recipient_reference, notes=notes)
    order.status = OrderStatus.DELIVERED
    db.add(pod)
    append_audit(db, user.id, "PROOF_OF_DELIVERY_RECORDED", "ORDER", str(order.id), {"recipient_reference": recipient_reference})
    db.commit()
    return pod


@router.get("")
def list_orders(db: Session = Depends(get_db), user=Depends(require_roles(
    Role.SYSTEM_ADMIN, Role.ORDER_ENTRY, Role.WAREHOUSE, Role.AUDITOR
))):
    return db.query(Order).order_by(Order.order_date.desc()).all()
