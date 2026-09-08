from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, HTTPException, Depends

from app.models.admin_model import AdminLogin
from app.dependencies.admin_auth import get_current_admin
from bson import ObjectId
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
    
    
    # Get all orders for admin
@router.get("/orders")
def get_all_orders(current_admin: dict = Depends(get_current_admin)):

    pipeline = [
        {
            "$addFields": {
                "user_object_id": {
                    "$convert": {
                        "input": "$user_id",
                        "to": "objectId",
                        "onError": None,
                        "onNull": None
                    }
                }
            }
        },

        {
            "$lookup": {
                "from": "users",
                "localField": "user_object_id",
                "foreignField": "_id",
                "as": "customer"
            }
        },

        {
            "$unwind": {
                "path": "$customer",
                "preserveNullAndEmptyArrays": True
            }
        },

        {
            "$sort": {
                "created_at": -1
            }
        }
    ]

    orders = list(
        orders_collection.aggregate(pipeline)
    )

    admin_orders = []

    for order in orders:

        customer = order.get("customer", {})

        admin_orders.append({
            "order_id": order.get("order_id"),

            "customer": {
                "user_id": order.get("user_id"),
                "name": customer.get("name"),
                "email": customer.get("email"),
                "phone": customer.get("phone"),
                "address": customer.get("address"),
                "city": customer.get("city"),
                "pin": customer.get("pin"),
            },

            "items": [
                {
                    "product_id": item.get("product_id"),
                    "name": item.get("name"),
                    "image": item.get("image"),
                    "quantity": item.get("quantity"),
                    "price": item.get("price"),
                }
                for item in order.get("items", [])
            ],

            "subtotal": order.get("subtotal", 0),
            "shipping": order.get("shipping", 0),
            "total": order.get("total", 0),

            "payment_status": order.get("payment_status"),
            "order_status": order.get("order_status"),

            "created_at": order.get("created_at"),
        })

    return {
        "success": True,
        "orders": admin_orders
    }
    
    
    # =====================================
# ADMIN CUSTOMERS
# =====================================

@router.get("/customers")
def get_all_customers(
    current_admin: dict = Depends(get_current_admin)
):

    pipeline = [
        {
            "$lookup": {
                "from": "orders",
                "let": {
                    "customer_id": {
                        "$toString": "$_id"
                    }
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$eq": [
                                    "$user_id",
                                    "$$customer_id"
                                ]
                            }
                        }
                    }
                ],
                "as": "orders"
            }
        },

        {
            "$addFields": {
                "total_orders": {
                    "$size": "$orders"
                },

                "total_spent": {
                    "$sum": {
                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$orders",
                                    "as": "order",
                                    "cond": {
                                        "$and": [
                                            {
                                                "$eq": [
                                                    "$$order.payment_status",
                                                    "paid"
                                                ]
                                            },
                                            {
                                                "$ne": [
                                                    "$$order.order_status",
                                                    "cancelled"
                                                ]
                                            }
                                        ]
                                    }
                                }
                            },
                            "as": "order",
                            "in": {
                                "$ifNull": [
                                    "$$order.total",
                                    0
                                ]
                            }
                        }
                    }
                },

                "last_order": {
                    "$max": "$orders.created_at"
                }
            }
        },

        {
            "$sort": {
                "created_at": -1
            }
        }
    ]

    customers = list(
        users_collection.aggregate(pipeline)
    )

    customer_list = []

    for customer in customers:

        customer_list.append({
            "user_id": str(customer["_id"]),

            "name": customer.get("name"),
            "email": customer.get("email"),
            "phone": customer.get("phone"),

            "address": customer.get("address"),
            "city": customer.get("city"),
            "pin": customer.get("pin"),

            "total_orders": customer.get(
                "total_orders",
                0
            ),

            "total_spent": customer.get(
                "total_spent",
                0
            ),

            "last_order": (
                customer["last_order"].isoformat()
                if isinstance(
                    customer.get("last_order"),
                    datetime
                )
                else None
            ),

            "created_at": (
                customer["created_at"].isoformat()
                if isinstance(
                    customer.get("created_at"),
                    datetime
                )
                else None
            )
        })

    return {
        "success": True,
        "customers": customer_list
    }


# =====================================
# CUSTOMER DETAILS + ORDERS
# =====================================

@router.get("/customers/{user_id}")
def get_customer_details(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):

    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid customer ID"
        )

    customer = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    orders = list(
        orders_collection.find({
            "user_id": user_id
        }).sort(
            "created_at",
            -1
        )
    )

    total_spent = 0

    for order in orders:

        if (
            order.get("payment_status") == "paid"
            and order.get("order_status") != "cancelled"
        ):
            total_spent += float(
                order.get("total", 0)
            )

    customer_orders = []

    for order in orders:

        customer_orders.append({
            "order_id": order.get("order_id"),

            "items": [
                {
                    "product_id": item.get("product_id"),
                    "name": item.get("name"),
                    "image": item.get("image"),
                    "price": item.get("price"),
                    "quantity": item.get("quantity")
                }
                for item in order.get("items", [])
            ],

            "subtotal": order.get(
                "subtotal",
                0
            ),

            "shipping": order.get(
                "shipping",
                0
            ),

            "total": order.get(
                "total",
                0
            ),

            "payment_status": order.get(
                "payment_status"
            ),

            "order_status": order.get(
                "order_status"
            ),

            "created_at": (
                order["created_at"].isoformat()
                if isinstance(
                    order.get("created_at"),
                    datetime
                )
                else None
            )
        })

    return {
        "success": True,

        "customer": {
            "user_id": str(customer["_id"]),

            "name": customer.get("name"),
            "email": customer.get("email"),
            "phone": customer.get("phone"),

            "address": customer.get("address"),
            "city": customer.get("city"),
            "pin": customer.get("pin"),

            "created_at": (
                customer["created_at"].isoformat()
                if isinstance(
                    customer.get("created_at"),
                    datetime
                )
                else None
            ),

            "total_orders": len(orders),
            "total_spent": total_spent
        },

        "orders": customer_orders
    }