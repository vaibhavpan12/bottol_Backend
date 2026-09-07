from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, HTTPException, Depends

from app.models.admin_model import AdminLogin
from app.dependencies.admin_auth import get_current_admin

from app.database.mongodb import (
    admin_collection,
    products_collection,
    orders_collection,
    users_collection,
)

from app.utils.auth import create_admin_token


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


# =====================================
# ADMIN LOGIN
# =====================================

@router.post("/login")
def admin_login(data: AdminLogin):

    # Find admin by email
    admin = admin_collection.find_one({
        "email": data.email
    })

    # Admin not found
    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin email or password"
        )

    # Check password
    password_valid = bcrypt.checkpw(
        data.password.encode("utf-8"),
        admin["password"].encode("utf-8")
    )

    # Wrong password
    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin email or password"
        )

    # Create JWT token
    token = create_admin_token(
        admin["email"]
    )

    return {
        "success": True,
        "message": "Admin login successful",
        "token": token,
        "admin": {
            "email": admin["email"],
            "role": admin["role"]
        }
    }


# =====================================
# ADMIN DASHBOARD
# =====================================

@router.get("/dashboard")
def get_dashboard(
    current_admin: dict = Depends(get_current_admin)
):

    # =====================================
    # CURRENT MONTH
    # =====================================

    now = datetime.now(timezone.utc)

    month_start = datetime(
        now.year,
        now.month,
        1,
        tzinfo=timezone.utc
    )


    # =====================================
    # PRODUCTS
    # =====================================

    # Total products
    total_products = products_collection.count_documents({})


    # Total stock
    stock_result = list(
        products_collection.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total_stock": {
                        "$sum": "$quantity"
                    }
                }
            }
        ])
    )

    total_stock = (
        stock_result[0]["total_stock"]
        if stock_result
        else 0
    )


    # =====================================
    # LOW STOCK
    # =====================================

    low_stock_products = list(
        products_collection.find(
            {
                "quantity": {
                    "$lte": 5
                }
            },
            {
                "name": 1,
                "quantity": 1,
                "price": 1,
                "image": 1
            }
        ).sort(
            "quantity",
            1
        )
    )


    # Convert ObjectId to string
    for product in low_stock_products:

        product["_id"] = str(
            product["_id"]
        )


    # =====================================
    # ORDERS
    # =====================================

    # Total orders
    total_orders = orders_collection.count_documents({})


    # Pending orders
    pending_orders = orders_collection.count_documents({
        "order_status": {
            "$in": [
                "placed",
                "processing",
                "shipped"
            ]
        }
    })


    # Completed orders
    completed_orders = orders_collection.count_documents({
        "order_status": "completed"
    })


    # Cancelled orders
    cancelled_orders = orders_collection.count_documents({
        "order_status": "cancelled"
    })


    # =====================================
    # THIS MONTH SALES
    # =====================================

    sales_result = list(
        orders_collection.aggregate([
            {
                "$match": {
                    "created_at": {
                        "$gte": month_start
                    },

                    "payment_status": "paid",

                    "order_status": {
                        "$ne": "cancelled"
                    }
                }
            },

            {
                "$group": {
                    "_id": None,

                    "sales": {
                        "$sum": "$total"
                    }
                }
            }
        ])
    )


    this_month_sales = (
        sales_result[0]["sales"]
        if sales_result
        else 0
    )


    # =====================================
    # CUSTOMERS
    # =====================================

    total_customers = users_collection.count_documents({})


    # =====================================
    # RECENT ORDERS
    # =====================================

    recent_orders = list(
        orders_collection.find(
            {},
            {
                "_id": 1,
                "order_id": 1,
                "user_id": 1,
                "total": 1,
                "order_status": 1,
                "payment_status": 1,
                "created_at": 1,
                "items": 1
            }
        )
        .sort(
            "created_at",
            -1
        )
        .limit(10)
    )


    # =====================================
    # CONVERT MONGODB VALUES
    # =====================================

    for order in recent_orders:

        order["_id"] = str(
            order["_id"]
        )

        if isinstance(
            order.get("created_at"),
            datetime
        ):
            order["created_at"] = (
                order["created_at"].isoformat()
            )


    # =====================================
    # RESPONSE
    # =====================================

    return {
        "success": True,

        "dashboard": {

            "this_month_sales":
                this_month_sales,

            "total_products":
                total_products,

            "total_stock":
                total_stock,

            "low_stock_count":
                len(low_stock_products),

            "low_stock_products":
                low_stock_products,

            "total_orders":
                total_orders,

            "pending_orders":
                pending_orders,

            "completed_orders":
                completed_orders,

            "cancelled_orders":
                cancelled_orders,

            "total_customers":
                total_customers,

            "recent_orders":
                recent_orders
        }
    }