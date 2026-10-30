"""
Product search used by the AI shopping assistant.

Works for any kind of product (electronics, fashion, home, beauty, sports,
accessories...). Searches name, category, brand, description and features.
"""

import re

from app.database.mongodb import products_collection


# Words people use -> the store category they mean.
CATEGORY_SYNONYMS = {
    "Electronics": [
        "electronic", "electronics", "phone", "phones", "mobile", "smartphone",
        "iphone", "android", "laptop", "laptops", "macbook", "computer", "tablet",
        "ipad", "gadget", "gadgets", "headphone", "earbuds", "earphone", "speaker",
        "charger", "echo", "tech",
    ],
    "Fashion": [
        "fashion", "clothes", "clothing", "shirt", "shirts", "tshirt", "t-shirt",
        "top", "tops", "dress", "dresses", "gown", "frock", "jeans", "shoe", "shoes",
        "sneaker", "sneakers", "footwear", "slipper", "slippers", "sandal", "jacket",
        "wear", "outfit",
    ],
    "Home & Kitchen": [
        "home", "kitchen", "furniture", "sofa", "bed", "table", "chair", "decor",
        "decoration", "frame", "spatula", "cookware", "utensil", "utensils", "pan",
        "knife", "plate", "mug", "bottle", "bottles", "tumbler", "flask",
    ],
    "Beauty & Personal Care": [
        "beauty", "makeup", "make-up", "mascara", "eyeshadow", "lipstick", "cosmetic",
        "cosmetics", "perfume", "perfumes", "fragrance", "fragrances", "scent",
        "skincare", "skin", "soap", "lotion", "cream", "serum", "personal care",
    ],
    "Sports & Fitness": [
        "sport", "sports", "fitness", "gym", "workout", "exercise", "ball", "football",
        "basketball", "baseball", "cricket", "glove", "racket", "yoga", "running",
    ],
    "Watches & Accessories": [
        "watch", "watches", "accessory", "accessories", "sunglass", "sunglasses",
        "glasses", "bag", "bags", "handbag", "purse", "wallet", "jewellery",
        "jewelry", "earring", "earrings", "necklace", "ring", "bracelet", "belt",
    ],
}

STOP_WORDS = {
    "i", "me", "my", "a", "an", "the", "and", "or", "for", "to", "of", "in", "on",
    "with", "want", "need", "looking", "look", "find", "show", "get", "buy", "some",
    "any", "please", "can", "you", "is", "are", "do", "have", "good", "best", "nice",
    "under", "below", "less", "than", "upto", "up", "within", "above", "over", "more",
    "between", "rs", "inr", "price", "cheap", "budget", "something", "items", "item",
    "product", "products", "gift", "suggest", "recommend", "which", "what", "there",
    "under", "around", "about", "like", "that", "this", "it", "new", "latest", "₹",
}

# Store questions the assistant can answer without searching.
FAQ_ANSWERS = [
    (("deliver", "delivery", "shipping", "ship", "courier", "dispatch"),
     "We deliver across India. Delivery is free on orders over ₹1499 (₹79 below that). "
     "Most orders ship within 48 hours and arrive in 3–7 working days."),
    (("return", "refund", "exchange", "replace"),
     "You can return eligible items within 7 days of delivery. Refunds go back to your "
     "original payment method within 5–7 working days."),
    (("payment", "pay", "cod", "cash on delivery", "upi", "card", "emi"),
     "You can pay with UPI, cards, net banking or cash on delivery."),
    (("track", "where is my order", "order status", "my order"),
     "Sign in and open My Orders to see the status of every order."),
    (("contact", "support", "customer care", "help desk", "phone number", "email"),
     "You can reach our support team from the Contact page — include your order ID for faster help."),
]

GREETINGS = {"hi", "hello", "hey", "hii", "namaste", "yo", "hola", "good morning", "good evening"}


def _regex(text: str) -> dict:
    return {"$regex": re.escape(text), "$options": "i"}


def _text_match(term: str, include_category: bool = True) -> dict:
    """Match a word anywhere in the main text fields."""
    rx = _regex(term)
    fields = ["name", "brand", "description", "features"]
    if include_category:
        fields.append("category")
    return {"$or": [{f: rx} for f in fields]}


def format_product(product: dict) -> dict:
    return {
        "id": str(product["_id"]),
        "_id": str(product["_id"]),
        "name": product.get("name"),
        "category": product.get("category"),
        "brand": product.get("brand"),
        "description": product.get("description"),
        "price": product.get("price"),
        "quantity": product.get("quantity"),
        "trending": product.get("trending"),
        "image": product.get("image"),
        "material": product.get("material"),
        "capacity": product.get("capacity"),
        "weight": product.get("weight"),
        "use_cases": product.get("use_cases", []),
        "features": product.get("features", []),
    }


def search_products(
    query: str = "",
    category: str = "",
    use_case: str = "",
    preference: str = "",
    material: str = "",
    capacity: str = "",
    max_price: float | None = None,
    min_price: float | None = None,
    limit: int = 6,
    relax: bool = True,
):
    """
    Search real products. All filters are optional and combined with AND.
    With relax=True, loosens the search step by step if nothing matches
    (the price limit is always kept).
    """
    conditions = []

    if category:
        conditions.append({"category": _regex(category)})

    words = [w for w in re.split(r"\s+", (query or "").strip()) if w]
    if words:
        # every keyword must match somewhere (name, brand, description...)
        conditions.extend(
            _text_match(w.rstrip("s") if len(w) > 3 else w, include_category=not category)
            for w in words
        )

    if use_case:
        conditions.append({"$or": [{"use_cases": _regex(use_case)}, _text_match(use_case)]})
    if preference:
        conditions.append({"$or": [{"weight": _regex(preference)}, _text_match(preference)]})
    if material:
        conditions.append({"material": _regex(material)})
    if capacity:
        conditions.append({"capacity": _regex(capacity)})

    price = {}
    if max_price is not None:
        price["$lte"] = float(max_price)
    if min_price is not None:
        price["$gte"] = float(min_price)
    if price:
        conditions.append({"price": price})

    in_stock = {"quantity": {"$gt": 0}}
    filters = {"$and": conditions + [in_stock]} if conditions else in_stock

    products = list(products_collection.find(filters).sort("trending", -1).limit(limit))
    if products or not relax:
        return [format_product(p) for p in products]

    # Relax: keep category + price, drop the keyword/requirement filters.
    if category:
        relaxed = [in_stock]
        if category:
            relaxed.append({"category": _regex(category)})
        if price:
            relaxed.append({"price": price})
        products = list(products_collection.find({"$and": relaxed}).sort("trending", -1).limit(limit))

    # Relax more: any single keyword, still within budget.
    if not products and words:
        loose = [in_stock, {"$or": [_text_match(w) for w in words]}]
        if price:
            loose.append({"price": price})
        products = list(products_collection.find({"$and": loose}).limit(limit))

    return [format_product(p) for p in products]


def trending_products(limit: int = 6):
    products = list(
        products_collection.find({"quantity": {"$gt": 0}}).sort("trending", -1).limit(limit)
    )
    return [format_product(p) for p in products]


def understand_message(message: str) -> dict:
    """
    Rule-based understanding of a shopping message — no AI service needed.

    "phone under 20000"            -> category Electronics, max_price 20000
    "nike shoes between 2000 and 5000"
    "perfume for women above 3000"
    """
    text = message.lower().strip()
    result = {"faq": None, "greeting": False, "category": "", "query": "", "max_price": None, "min_price": None}

    if text.strip(" !.?") in GREETINGS:
        result["greeting"] = True
        return result

    result["faq"] = None
    for keys, answer in FAQ_ANSWERS:
        if any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in keys):
            result["faq"] = answer
            break

    num = r"(?:₹|rs\.?|inr)?\s*(\d[\d,]*(?:\.\d+)?)\s*(k)?"

    def to_number(value, k):
        n = float(value.replace(",", ""))
        return n * 1000 if k else n

    between = re.search(r"between\s*" + num + r"\s*(?:and|to|-)\s*" + num, text)
    if between:
        result["min_price"] = to_number(between.group(1), between.group(2))
        result["max_price"] = to_number(between.group(3), between.group(4))
    else:
        under = re.search(r"(?:under|below|less than|upto|up to|within|max|maximum|budget)\s*" + num, text)
        if under:
            result["max_price"] = to_number(under.group(1), under.group(2))
        over = re.search(r"(?:above|over|more than|minimum|min|starting)\s*" + num, text)
        if over:
            result["min_price"] = to_number(over.group(1), over.group(2))

    # strip numbers / currency so they aren't used as keywords
    cleaned = re.sub(r"(?:₹|rs\.?|inr)?\s*\d[\d,]*(?:\.\d+)?\s*k?", " ", text)
    tokens = [t for t in re.findall(r"[a-z][a-z\-]+", cleaned) if t not in STOP_WORDS]

    keywords = []
    for token in tokens:
        matched = False
        for category, synonyms in CATEGORY_SYNONYMS.items():
            if token in synonyms:
                matched = True
                if not result["category"]:
                    result["category"] = category
                # generic category words (e.g. "electronics") aren't useful keywords
                if token.rstrip("s") not in {"electronic", "fashion", "beauty", "sport", "accessorie", "home", "kitchen", "fitnes"}:
                    keywords.append(token)
                break
        if not matched:
            keywords.append(token)

    result["query"] = " ".join(keywords[:3])
    return result
