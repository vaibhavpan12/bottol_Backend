from pydantic import BaseModel, Field
from typing import List


class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class CartCreate(BaseModel):
    items: List[CartItem] = []


class CartResponse(BaseModel):
    user_id: str
    items: List[CartItem] = []