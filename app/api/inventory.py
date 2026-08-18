from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.core.audit import append_audit
from app.models.models import Batch, BatchStatus, Inventory, InventoryMovement, PacketProduction, Role

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/packaging")
def record_packaging(
    packet_lot_id: str,
    batch_id: int,
    number_of_packets: int,
    fill_weight_grams: float,
    packaging_date: str,
    rejected_packets: int = 0,
    location_id: str = "FINISHED_GOODS",
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.PRODUCTION)),
):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    if batch.status != BatchStatus.RELEASED:
        raise HTTPException(409, "Only released batches can enter finished inventory")
    if number_of_packets <= 0 or fill_weight_grams <= 0 or rejected_packets < 0:
        raise HTTPException(400, "Invalid packaging quantities")
    if rejected_packets > number_of_packets:
        raise HTTPException(400, "Rejected packets cannot exceed produced packets")
    if db.query(PacketProduction).filter(PacketProduction.packet_lot_id == packet_lot_id).first():
        raise HTTPException(409, "Packet lot already exists")

    lot = PacketProduction(
        packet_lot_id=packet_lot_id,
        batch_id=batch_id,
        number_of_packets=number_of_packets,
        fill_weight_grams=fill_weight_grams,
        packaging_date=datetime.fromisoformat(packaging_date),
        rejected_packets=rejected_packets,
    )
    db.add(lot)
    db.flush()

    available = number_of_packets - rejected_packets
    inv = Inventory(packet_lot_id=lot.id, location_id=location_id, quantity_on_hand=available, status="AVAILABLE")
    db.add(inv)
    db.flush()
    db.add(InventoryMovement(
        inventory_id=inv.id,
        movement_type="RECEIPT",
        quantity=available,
        reference_type="PACKET_LOT",
        reference_id=packet_lot_id,
    ))
    append_audit(db, user.id, "PACKAGING_RECORDED", "PACKET_LOT", str(lot.id), {
        "packet_lot_id": packet_lot_id,
        "produced": number_of_packets,
        "rejected": rejected_packets,
        "available": available,
        "location": location_id,
    })
    db.commit()
    return {"lot": lot, "inventory": inv}


@router.post("/{inventory_id}/adjust")
def adjust_inventory(
    inventory_id: int,
    quantity_delta: int,
    reason: str,
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.SYSTEM_ADMIN, Role.WAREHOUSE)),
):
    if quantity_delta == 0 or not reason.strip():
        raise HTTPException(400, "A non-zero adjustment and reason are required")
    inv = db.get(Inventory, inventory_id)
    if not inv:
        raise HTTPException(404, "Inventory record not found")
    if inv.quantity_on_hand + quantity_delta < 0:
        raise HTTPException(409, "Adjustment would make stock negative")
    inv.quantity_on_hand += quantity_delta
    db.add(InventoryMovement(
        inventory_id=inv.id,
        movement_type="ADJUSTMENT",
        quantity=quantity_delta,
        reference_type="MANUAL",
        reference_id=reason[:100],
    ))
    append_audit(db, user.id, "INVENTORY_ADJUSTED", "INVENTORY", str(inv.id), {
        "delta": quantity_delta, "reason": reason
    })
    db.commit()
    return inv


@router.get("")
def list_inventory(db: Session = Depends(get_db), user=Depends(require_roles(
    Role.SYSTEM_ADMIN, Role.WAREHOUSE, Role.ORDER_ENTRY, Role.AUDITOR, Role.GUEST
))):
    return db.query(Inventory).all()
