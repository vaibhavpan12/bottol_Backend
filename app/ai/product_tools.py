from app.database.mongodb import products_collection


def search_products(
    query: str = "",
    category: str = "",
    use_case: str = "",
    preference: str = "",
    material: str = "",
    capacity: str = "",
    max_price: float | None = None,
    limit: int = 5
):
    filters = {}

    # -------------------------------------------------
    # TEXT SEARCH
    # -------------------------------------------------
    # Search product name/category
    #
    # Example:
    # query = "bottle"
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
    # USE CASE FILTER
    # -------------------------------------------------
    # Example:
    # use_case = "gym"
    #
    # MongoDB checks:
    # use_cases = ["gym", "office", "travel"]
    # -------------------------------------------------

    if use_case:
        filters["use_cases"] = {
            "$regex": use_case,
            "$options": "i"
        }

    # -------------------------------------------------
    # PREFERENCE FILTER
    # -------------------------------------------------
    # Example:
    # preference = "lightweight"
    #
    # Searches:
    # weight
    # features
    # -------------------------------------------------

    if preference:
        filters["$or"] = [
            {
                "weight": {
                    "$regex": preference,
                    "$options": "i"
                }
            },
            {
                "features": {
                    "$regex": preference,
                    "$options": "i"
                }
            }
        ]

    # -------------------------------------------------
    # MATERIAL FILTER
    # -------------------------------------------------

    if material:
        filters["material"] = {
            "$regex": material,
            "$options": "i"
        }

    # -------------------------------------------------
    # CAPACITY FILTER
    # -------------------------------------------------

    if capacity:
        filters["capacity"] = {
            "$regex": capacity,
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
    # SEARCH DATABASE
    # -------------------------------------------------

    products = list(
        products_collection
        .find(filters)
        .limit(limit)
    )

    # -------------------------------------------------
    # FALLBACK SEARCH
    # -------------------------------------------------
    # If strict search gives no result,
    # remove requirement filters and try basic search.
    # -------------------------------------------------

    if not products:

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

            # AI recommendation information
            "material": product.get("material"),
            "capacity": product.get("capacity"),
            "weight": product.get("weight"),
            "use_cases": product.get("use_cases", []),
            "features": product.get("features", [])
        })

    return result