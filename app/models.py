from enum import StrEnum

from pydantic import BaseModel, Field


class OrderStatus(StrEnum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"


class Product(BaseModel):
    sku: str
    name: str
    price: float = Field(gt=0)
    in_stock: int = Field(ge=0)


class OrderCreate(BaseModel):
    sku: str
    quantity: int = Field(gt=0, le=20)


class Order(BaseModel):
    id: str
    sku: str
    quantity: int
    total: float
    status: OrderStatus


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str

