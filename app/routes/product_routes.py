import os
import uuid
import shutil
import json

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

    material: str | None = Form(None),
    capacity: str | None = Form(None),
    weight: str | None = Form(None),

    use_cases: str = Form("[]"),
    features: str = Form("[]"),

    # Image is now OPTIONAL
    image: UploadFile | None = File(None),
    image_url: str | None = Form(None),
):

    # --------------------------------
    # Convert JSON strings to lists
    # --------------------------------

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


    # --------------------------------
    # Image: Upload OR URL
    # --------------------------------

    if image:

        # Check image type
        if (
            not image.content_type
            or not image.content_type.startswith("image/")
        ):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed"
            )

        # Get extension
        extension = os.path.splitext(
            image.filename
        )[1]

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

        image_path = f"/uploads/products/{filename}"

    elif image_url:

        # Use external image URL
        image_path = image_url

    else:

        raise HTTPException(
            status_code=400,
            detail="Please upload an image or provide an image URL"
        )


    # --------------------------------
    # Product data
    # --------------------------------

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


    # --------------------------------
    # Save to MongoDB
    # --------------------------------

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

    products = list(
        products_collection.find()
    )


    for product in products:
        product["_id"] = str(product["_id"])


    return {
        "success": True,
        "products": products
    }