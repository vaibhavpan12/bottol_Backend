from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class OrderItem(BaseModel):
    product_id: str
    name: str
    image: Optional[str] = None
    price: float
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    user_id: str

    items: List[OrderItem]

    subtotal: float
    shipping: float
    total: float

    payment_status: str = "paid"
    order_status: str = "placed"


class OrderResponse(OrderCreate):
    order_id: str
    created_at: datetime