import os
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.database.mongodb import products_collection


router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)


# Upload folder
UPLOAD_DIR = "uploads/products"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/AddProduct")
async def create_product(
    name: str = Form(...),
    category: str = Form(...),
    quantity: int = Form(...),
    trending: bool = Form(False),
    price: float = Form(...),
    image: UploadFile = File(...)
):

    # Check image type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )

    # Get extension
    extension = os.path.splitext(image.filename)[1]

    # Unique filename
    filename = f"{uuid.uuid4()}{extension}"

    # Complete path
    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    # Save image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            image.file,
            buffer
        )

    # Path saved in MongoDB
    image_path = f"/uploads/products/{filename}"

    product_data = {
        "name": name,
        "category": category,
        "image": image_path,
        "quantity": quantity,
        "trending": trending,
        "price": price
    }

    result = products_collection.insert_one(
        product_data
    )

    return {
        "success": True,
        "message": "Product created successfully",
        "product_id": str(result.inserted_id),
        "image": image_path
    }


@router.get("/AllProducts")
def get_products():

    products = list(products_collection.find())

    for product in products:
        product["_id"] = str(product["_id"])

    return {
        "success": True,
        "products": products
    }