from fastapi import HTTPException
from datetime import datetime, timezone

from app.database.mongodb import carts_collection


def get_user_cart(user_id: str):
    cart = carts_collection.find_one({"user_id": user_id})

    if not cart:
        return {
            "success": True,
            "user_id": user_id,
            "items": []
        }

    return {
        "success": True,
        "user_id": cart["user_id"],
        "items": cart.get("items", [])
    }


def update_user_cart(user_id: str, items):
    cart_items = []

    for item in items:
        if item.quantity <= 0:
            continue

        cart_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity
        })

    carts_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "items": cart_items,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

    return {
        "success": True,
        "user_id": user_id,
        "items": cart_items
    }


def clear_user_cart(user_id: str):
    carts_collection.delete_one({
        "user_id": user_id
    })

    return {
        "success": True,
        "message": "Cart cleared successfully"
    }


def merge_user_cart(user_id: str, guest_items):
    existing_cart = carts_collection.find_one({
        "user_id": user_id
    })

    existing_items = existing_cart.get("items", []) if existing_cart else []

    merged = {}

    # Existing MongoDB cart
    for item in existing_items:
        product_id = item["product_id"]
        merged[product_id] = item["quantity"]

    # Guest localStorage cart
    for item in guest_items:
        product_id = item.product_id
        quantity = item.quantity

        if quantity <= 0:
            continue

        if product_id in merged:
            merged[product_id] += quantity
        else:
            merged[product_id] = quantity

    merged_items = [
        {
            "product_id": product_id,
            "quantity": quantity
        }
        for product_id, quantity in merged.items()
        if quantity > 0
    ]

    carts_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "items": merged_items,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

    return {
        "success": True,
        "user_id": user_id,
        "items": merged_items
    }