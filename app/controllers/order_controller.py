import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.database.mongodb import orders_collection
from app.models.order_model import OrderCreate


def create_order(order: OrderCreate):

    if not order.items:
        raise HTTPException(
            status_code=400,
            detail="Order must contain at least one product"
        )

    order_id = f"PIV-{uuid.uuid4().hex[:8].upper()}"

    order_data = {
        "order_id": order_id,
        "user_id": order.user_id,

        "items": [
            {
                "product_id": item.product_id,
                "name": item.name,
                "image": item.image,
                "price": item.price,
                "quantity": item.quantity,
            }
            for item in order.items
        ],

        "subtotal": order.subtotal,
        "shipping": order.shipping,
        "total": order.total,

        "payment_status": order.payment_status,
        "order_status": order.order_status,

        "created_at": datetime.now(timezone.utc),
    }

    result = orders_collection.insert_one(order_data)

    return {
        "success": True,
        "message": "Order created successfully",
        "order_id": order_id,
        "database_id": str(result.inserted_id),
    }