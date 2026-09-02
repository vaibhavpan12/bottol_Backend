from pydantic import BaseModel, Field


class Product(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., min_length=2, max_length=50)
    image: str
    quantity: int = Field(..., ge=0)
    trending: bool = False
    price: float = Field(..., gt=0)