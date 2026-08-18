from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.models import Role, BatchStatus, OrderStatus

class ProductCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=200)
    packaging_type: str = "UNIT_DOSE_PACKET"
    standard_fill_weight_grams: float = Field(gt=0)

class BatchCreate(BaseModel):
    batch_id: str
    product_id: int
    production_date: datetime
    expiry_date: datetime
    bulk_quantity_tons: float = Field(gt=0)

class QCDecision(BaseModel):
    decision: BatchStatus
    qc_results: str = Field(min_length=2)

class CustomerCreate(BaseModel):
    customer_ref: str = Field(min_length=2, max_length=100)
    display_name: str = Field(min_length=1, max_length=200)

class OrderLineCreate(BaseModel):
    requested_quantity: int = Field(gt=0)

class OrderCreate(BaseModel):
    order_id: str
    customer_ref: str
    lines: list[OrderLineCreate] = Field(min_length=1)

class StatusUpdate(BaseModel):
    status: OrderStatus

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=12)
    role: Role

class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
