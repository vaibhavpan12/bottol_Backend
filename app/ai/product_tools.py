from app.database.mongodb import products_collection


def search_products(
    query: str = "",
    category: str = "",
    max_price: float | None = None,
    limit: int = 5
):
    filters = {}

    # -------------------------------------------------
    # PRODUCT SEARCH
    # -------------------------------------------------
    # Search query in BOTH:
    # 1. product name
    # 2. product category
    #
    # Example:
    # query = "bottle"
    #
    # It can match:
    # name = "Water Bottle"
    # OR
    # category = "Daily Bottles"
    # -------------------------------------------------

    if query:
        filters["$or"] = [
            {
                "name": {
                    "$regex": query,
                    "$options": "i"
                }
            },
            {
                "category": {
                    "$regex": query,
                    "$options": "i"
                }
            }
        ]

    # -------------------------------------------------
    # CATEGORY FILTER
    # -------------------------------------------------

    if category:
        filters["category"] = {
            "$regex": category,
            "$options": "i"
        }

    # -------------------------------------------------
    # PRICE FILTER
    # -------------------------------------------------

    if max_price is not None:
        filters["price"] = {
            "$lte": max_price
        }

    # -------------------------------------------------
    # FIRST SEARCH
    # -------------------------------------------------

    products = list(
        products_collection
        .find(filters)
        .limit(limit)
    )

    # -------------------------------------------------
    # FALLBACK SEARCH
    # -------------------------------------------------
    # If AI gives an incorrect category such as
    # "office", remove the category filter and
    # search using the actual product information.
    # -------------------------------------------------

    if not products and category:

        fallback_filters = {}

        if query:
            fallback_filters["$or"] = [
                {
                    "name": {
                        "$regex": query,
                        "$options": "i"
                    }
                },
                {
                    "category": {
                        "$regex": query,
                        "$options": "i"
                    }
                }
            ]

        if max_price is not None:
            fallback_filters["price"] = {
                "$lte": max_price
            }

        products = list(
            products_collection
            .find(fallback_filters)
            .limit(limit)
        )

    # -------------------------------------------------
    # FORMAT RESULT
    # -------------------------------------------------

    result = []

    for product in products:

        result.append({
            "id": str(product["_id"]),
            "name": product.get("name"),
            "category": product.get("category"),
            "price": product.get("price"),
            "quantity": product.get("quantity"),
            "trending": product.get("trending"),
            "image": product.get("image"),
        })

    return result