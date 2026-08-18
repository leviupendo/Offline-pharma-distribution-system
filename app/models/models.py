from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Role(str, Enum):
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    QC_MANAGER = "QC_MANAGER"
    PRODUCTION = "PRODUCTION"
    WAREHOUSE = "WAREHOUSE"
    ORDER_ENTRY = "ORDER_ENTRY"
    AUDITOR = "AUDITOR"
    GUEST = "GUEST"


class BatchStatus(str, Enum):
    QUARANTINE = "QUARANTINE"
    RELEASED = "RELEASED"
    REJECTED = "REJECTED"
    RECALLED = "RECALLED"


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    ALLOCATED = "ALLOCATED"
    PICKED = "PICKED"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[Role] = mapped_column(default=Role.GUEST)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    packaging_type: Mapped[str] = mapped_column(String(100), default="UNIT_DOSE_PACKET")
    standard_fill_weight_grams: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    production_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    bulk_quantity_tons: Mapped[float] = mapped_column(Float)
    status: Mapped[BatchStatus] = mapped_column(default=BatchStatus.QUARANTINE)
    qc_results: Mapped[str] = mapped_column(Text, default="")
    product: Mapped[Product] = relationship()


class PacketProduction(Base):
    __tablename__ = "packet_production"
    id: Mapped[int] = mapped_column(primary_key=True)
    packet_lot_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    number_of_packets: Mapped[int] = mapped_column(Integer)
    fill_weight_grams: Mapped[float] = mapped_column(Float)
    packaging_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rejected_packets: Mapped[int] = mapped_column(Integer, default=0)
    batch: Mapped[Batch] = relationship()


class Inventory(Base):
    __tablename__ = "inventory"
    id: Mapped[int] = mapped_column(primary_key=True)
    packet_lot_id: Mapped[int] = mapped_column(ForeignKey("packet_production.id"))
    location_id: Mapped[str] = mapped_column(String(100))
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="AVAILABLE")
    packet_lot: Mapped[PacketProduction] = relationship()
    __table_args__ = (UniqueConstraint("packet_lot_id", "location_id", name="uq_inventory_lot_location"),)


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id"))
    movement_type: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_ref: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.DRAFT)
    customer: Mapped[Customer] = relationship()
    lines: Mapped[list["OrderLine"]] = relationship(cascade="all, delete-orphan")


class OrderLine(Base):
    __tablename__ = "order_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    requested_quantity: Mapped[int] = mapped_column(Integer)
    allocations: Mapped[list["OrderAllocation"]] = relationship(cascade="all, delete-orphan")


class OrderAllocation(Base):
    __tablename__ = "order_allocations"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_line_id: Mapped[int] = mapped_column(ForeignKey("order_lines.id"))
    packet_lot_id: Mapped[int] = mapped_column(ForeignKey("packet_production.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    packet_lot: Mapped[PacketProduction] = relationship()


class ProofOfDelivery(Base):
    __tablename__ = "proof_of_delivery"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    recipient_reference: Mapped[str] = mapped_column(String(200))
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    notes: Mapped[str] = mapped_column(Text, default="")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    previous_hash: Mapped[str] = mapped_column(String(64))
    entry_hash: Mapped[str] = mapped_column(String(64), unique=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[str] = mapped_column(Text)
