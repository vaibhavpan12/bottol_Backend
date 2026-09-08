from fastapi import APIRouter, HTTPException

from app.controllers.order_controller import create_order
from app.database.mongodb import orders_collection
from app.models.order_model import OrderCreate


router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"]
)


# Create Order
@router.post("/createUserOrder")
def create_new_order(order: OrderCreate):

    return create_order(order)


# Get user's order history
@router.get("/AllOrder/user/{user_id}")
def get_user_orders(user_id: str):

    orders = list(
        orders_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1)
    )

    for order in orders:
        order["_id"] = str(order["_id"])

    return {
        "success": True,
        "orders": orders
    }


# Get single order
@router.get("/SingleOrder/{order_id}")
def get_order(order_id: str):

    order = orders_collection.find_one(
        {"order_id": order_id}
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    order["_id"] = str(order["_id"])

    return {
        "success": True,
        "order": order
    }
    
    