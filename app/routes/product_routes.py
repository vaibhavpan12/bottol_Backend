# import os
# import uuid
# import shutil
# import json

# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from app.database.mongodb import products_collection


# router = APIRouter(
#     prefix="/api/products",
#     tags=["Products"]
# )


# # Upload folder
# UPLOAD_DIR = "uploads/products"

# os.makedirs(UPLOAD_DIR, exist_ok=True)


# @router.post("/AddProduct")
# async def create_product(
#     name: str = Form(...),
#     category: str = Form(...),
#     quantity: int = Form(...),
#     trending: bool = Form(False),
#     price: float = Form(...),

#     material: str | None = Form(None),
#     capacity: str | None = Form(None),
#     weight: str | None = Form(None),

#     use_cases: str = Form("[]"),
#     features: str = Form("[]"),

#     # Image is now OPTIONAL
#     image: UploadFile | None = File(None),
#     image_url: str | None = Form(None),
# ):

#     # --------------------------------
#     # Convert JSON strings to lists
#     # --------------------------------

#     try:
#         use_cases_list = json.loads(use_cases)
#         features_list = json.loads(features)

#     except json.JSONDecodeError:
#         raise HTTPException(
#             status_code=400,
#             detail="use_cases and features must be valid JSON arrays"
#         )

#     if not isinstance(use_cases_list, list):
#         raise HTTPException(
#             status_code=400,
#             detail="use_cases must be an array"
#         )

#     if not isinstance(features_list, list):
#         raise HTTPException(
#             status_code=400,
#             detail="features must be an array"
#         )


#     # --------------------------------
#     # Image: Upload OR URL
#     # --------------------------------

#     if image:

#         # Check image type
#         if (
#             not image.content_type
#             or not image.content_type.startswith("image/")
#         ):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Only image files are allowed"
#             )

#         # Get extension
#         extension = os.path.splitext(
#             image.filename
#         )[1]

#         # Unique filename
#         filename = f"{uuid.uuid4()}{extension}"

#         # Complete path
#         file_path = os.path.join(
#             UPLOAD_DIR,
#             filename
#         )

#         # Save image
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(
#                 image.file,
#                 buffer
#             )

#         image_path = f"/uploads/products/{filename}"

#     elif image_url:

#         # Use external image URL
#         image_path = image_url

#     else:

#         raise HTTPException(
#             status_code=400,
#             detail="Please upload an image or provide an image URL"
#         )


#     # --------------------------------
#     # Product data
#     # --------------------------------

#     product_data = {
#         "name": name,
#         "category": category,
#         "image": image_path,
#         "quantity": quantity,
#         "trending": trending,
#         "price": price,

#         "material": material,
#         "capacity": capacity,
#         "weight": weight,

#         "use_cases": use_cases_list,
#         "features": features_list
#     }


#     # --------------------------------
#     # Save to MongoDB
#     # --------------------------------

#     result = products_collection.insert_one(
#         product_data
#     )


#     return {
#         "success": True,
#         "message": "Product created successfully",
#         "product_id": str(result.inserted_id),
#         "image": image_path
#     }

# @router.get("/AllProducts")
# def get_products():

#     products = list(
#         products_collection.find()
#     )


#     for product in products:
#         product["_id"] = str(product["_id"])


#     return {
#         "success": True,
#         "products": products
#     }

import os
import uuid
import shutil
import json

from bson import ObjectId
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException
)

from app.database.mongodb import products_collection


router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)


# =========================================
# UPLOAD FOLDER
# =========================================

UPLOAD_DIR = "uploads/products"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================
# ADD PRODUCT
# =========================================

@router.post("/AddProduct")
async def create_product(
    name: str = Form(...),
    category: str = Form(...),
    quantity: int = Form(...),
    trending: bool = Form(False),
    price: float = Form(...),

    material: str | None = Form(None),
    capacity: str | None = Form(None),
    weight: str | None = Form(None),

    use_cases: str = Form("[]"),
    features: str = Form("[]"),

    image: UploadFile | None = File(None),
    image_url: str | None = Form(None),
):

    # =====================================
    # VALIDATION
    # =====================================

    if quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative"
        )

    if price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Price must be greater than 0"
        )

    # =====================================
    # JSON → LIST
    # =====================================

    try:
        use_cases_list = json.loads(use_cases)
        features_list = json.loads(features)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="use_cases and features must be valid JSON arrays"
        )

    if not isinstance(use_cases_list, list):
        raise HTTPException(
            status_code=400,
            detail="use_cases must be an array"
        )

    if not isinstance(features_list, list):
        raise HTTPException(
            status_code=400,
            detail="features must be an array"
        )

    # =====================================
    # IMAGE
    # =====================================

    if image:

        if (
            not image.content_type
            or not image.content_type.startswith("image/")
        ):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed"
            )

        extension = os.path.splitext(
            image.filename
        )[1]

        filename = f"{uuid.uuid4()}{extension}"

        file_path = os.path.join(
            UPLOAD_DIR,
            filename
        )

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                image.file,
                buffer
            )

        image_path = f"/uploads/products/{filename}"

    elif image_url:

        image_path = image_url

    else:

        raise HTTPException(
            status_code=400,
            detail="Please upload an image or provide an image URL"
        )

    # =====================================
    # PRODUCT DATA
    # =====================================

    product_data = {
        "name": name,
        "category": category,
        "image": image_path,
        "quantity": quantity,
        "trending": trending,
        "price": price,

        "material": material,
        "capacity": capacity,
        "weight": weight,

        "use_cases": use_cases_list,
        "features": features_list
    }

    # =====================================
    # SAVE
    # =====================================

    result = products_collection.insert_one(
        product_data
    )

    return {
        "success": True,
        "message": "Product created successfully",
        "product_id": str(result.inserted_id),
        "image": image_path
    }


# =========================================
# GET ALL PRODUCTS
# =========================================

@router.get("/AllProducts")
def get_products():

    products = list(
        products_collection.find()
    )

    for product in products:
        product["_id"] = str(product["_id"])

    return {
        "success": True,
        "products": products
    }


# =========================================
# GET PRODUCT STATS
# =========================================

@router.get("/Stats")
def get_product_stats():

    products = list(
        products_collection.find()
    )

    total_products = len(products)

    trending_products = sum(
        1
        for product in products
        if product.get("trending") is True
    )

    total_quantity = sum(
        int(product.get("quantity", 0))
        for product in products
    )

    inventory_value = sum(
        float(product.get("price", 0))
        * int(product.get("quantity", 0))
        for product in products
    )

    low_stock_products = sum(
        1
        for product in products
        if int(product.get("quantity", 0)) <= 5
    )

    return {
        "success": True,
        "stats": {
            "total_products": total_products,
            "trending_products": trending_products,
            "total_quantity": total_quantity,
            "inventory_value": inventory_value,
            "low_stock_products": low_stock_products
        }
    }


# =========================================
# UPDATE PRODUCT
# =========================================

@router.put("/UpdateProduct/{product_id}")
async def update_product(
    product_id: str,

    name: str = Form(...),
    category: str = Form(...),
    quantity: int = Form(...),
    trending: bool = Form(False),
    price: float = Form(...),

    material: str | None = Form(None),
    capacity: str | None = Form(None),
    weight: str | None = Form(None),

    use_cases: str = Form("[]"),
    features: str = Form("[]"),

    image: UploadFile | None = File(None),
    image_url: str | None = Form(None),
):

    # =====================================
    # OBJECT ID VALIDATION
    # =====================================

    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid product ID"
        )

    object_id = ObjectId(product_id)

    existing_product = products_collection.find_one(
        {"_id": object_id}
    )

    if not existing_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # =====================================
    # VALIDATION
    # =====================================

    if quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative"
        )

    if price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Price must be greater than 0"
        )

    # =====================================
    # JSON → LIST
    # =====================================

    try:
        use_cases_list = json.loads(use_cases)
        features_list = json.loads(features)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="use_cases and features must be valid JSON arrays"
        )

    if not isinstance(use_cases_list, list):
        raise HTTPException(
            status_code=400,
            detail="use_cases must be an array"
        )

    if not isinstance(features_list, list):
        raise HTTPException(
            status_code=400,
            detail="features must be an array"
        )

    # =====================================
    # IMAGE
    # =====================================

    image_path = existing_product.get("image")

    if image:

        if (
            not image.content_type
            or not image.content_type.startswith("image/")
        ):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed"
            )

        extension = os.path.splitext(
            image.filename
        )[1]

        filename = f"{uuid.uuid4()}{extension}"

        file_path = os.path.join(
            UPLOAD_DIR,
            filename
        )

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                image.file,
                buffer
            )

        image_path = f"/uploads/products/{filename}"

    elif image_url:

        image_path = image_url

    # =====================================
    # UPDATED DATA
    # =====================================

    updated_data = {
        "name": name,
        "category": category,
        "image": image_path,
        "quantity": quantity,
        "trending": trending,
        "price": price,

        "material": material,
        "capacity": capacity,
        "weight": weight,

        "use_cases": use_cases_list,
        "features": features_list
    }

    # =====================================
    # UPDATE MONGODB
    # =====================================

    products_collection.update_one(
        {"_id": object_id},
        {
            "$set": updated_data
        }
    )

    return {
        "success": True,
        "message": "Product updated successfully",
        "product_id": product_id
    }


# =========================================
# DELETE PRODUCT
# =========================================

@router.delete("/DeleteProduct/{product_id}")
def delete_product(product_id: str):

    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid product ID"
        )

    result = products_collection.delete_one(
        {"_id": ObjectId(product_id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return {
        "success": True,
        "message": "Product deleted successfully"
    }