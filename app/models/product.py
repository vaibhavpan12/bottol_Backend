from pydantic import BaseModel, Field


class Product(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    category: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    image: str

    quantity: int = Field(
        ...,
        ge=0
    )

    trending: bool = False

    price: float = Field(
        ...,
        gt=0
    )

    # =========================================
    # AI RECOMMENDATION FIELDS
    # =========================================

    material: str | None = None

    capacity: str | None = None

    weight: str | None = None

    use_cases: list[str] = Field(
        default_factory=list
    )

    features: list[str] = Field(
        default_factory=list
    )