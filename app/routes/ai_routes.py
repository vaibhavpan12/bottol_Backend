from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import re

from app.ai.product_tools import search_products


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"]
)


# =========================================================
# REQUEST MODELS
# =========================================================

class AgentRequest(BaseModel):
    message: str


class ChatRequest(BaseModel):
    message: str


# =========================================================
# SIMPLE PRODUCT QUERY DETECTOR
# =========================================================

def detect_simple_product_query(message: str):
    """
    Detect simple shopping queries without using Llama.

    Examples:

    bottle under 1500
    bottles below 1000
    tumbler under 2000
    flask under 1200
    """

    text = message.lower().strip()

    # -----------------------------------------------------
    # PRICE DETECTION
    # -----------------------------------------------------

    price_match = re.search(
        r"(?:under|below|less than|upto|up to|within)"
        r"\s*(?:₹|rs\.?|inr)?"
        r"\s*(\d+(?:\.\d+)?)",
        text
    )

    max_price = None

    if price_match:
        max_price = float(
            price_match.group(1)
        )


    # -----------------------------------------------------
    # PRODUCT KEYWORD DETECTION
    # -----------------------------------------------------

    product_keywords = [
        "bottle",
        "bottles",
        "tumbler",
        "tumblers",
        "flask",
        "flasks"
    ]

    query = ""

    for keyword in product_keywords:

        if keyword in text:

            query = keyword.rstrip("s")

            break


    # Product keyword nahi mila
    if not query:
        return None


    # -----------------------------------------------------
    # Return detected information
    # -----------------------------------------------------

    return {
        "query": query,
        "max_price": max_price
    }


# =========================================================
# NORMAL AI CHAT
# =========================================================

@router.post("/chat")
def chat_with_ai(request: ChatRequest):

    try:

        response = requests.post(

            "http://localhost:11434/api/chat",

            json={

                "model": "llama3.2:3b",

                "messages": [

                    {
                        "role": "system",

                        "content": (
                            "You are Pivora AI, a helpful shopping "
                            "assistant for a bottle e-commerce store. "

                            "Be concise and helpful. "

                            "Do not invent product names, prices, "
                            "stock, or product details."
                        )
                    },

                    {
                        "role": "user",
                        "content": request.message
                    }
                ],

                "stream": False
            },

            timeout=120
        )


        if not response.ok:

            raise HTTPException(
                status_code=500,
                detail="Ollama request failed"
            )


        data = response.json()


        return {

            "success": True,

            "message": data["message"]["content"]

        }


    except requests.exceptions.RequestException as error:

        print("Ollama Error:", error)

        raise HTTPException(
            status_code=500,
            detail="Could not connect to Ollama"
        )


# =========================================================
# AI SHOPPING AGENT
# =========================================================

@router.post("/agent")
def ai_agent(request: AgentRequest):

    # =====================================================
    # FAST PATH
    # =====================================================

    simple_query = detect_simple_product_query(
        request.message
    )


    if simple_query:

        print("================================")
        print("FAST PATH")
        print("DIRECT MONGODB SEARCH")
        print("QUERY:", simple_query)
        print("================================")


        products = search_products(

            query=simple_query["query"],

            max_price=simple_query["max_price"]

        )


        if not products:

            return {

                "success": True,

                "message": (
                    "Sorry, I couldn't find any products "
                    "matching your requirements."
                ),

                "products": []

            }


        return {

            "success": True,

            "message": (
                f"I found {len(products)} "
                "products matching your requirements."
            ),

            "products": products

        }


    # =====================================================
    # NORMAL AI AGENT
    # =====================================================

    tools = [

        {

            "type": "function",

            "function": {

                "name": "search_products",

                "description": (
                    "Search real Pivora products from the "
                    "MongoDB product database. "

                    "Use this tool whenever the user is looking "
                    "for products or gives product requirements. "

                    "You can search by product type, category, "
                    "use case, preference, material, capacity "
                    "and maximum price. "

                    "Never invent product information. "

                    "Office, gym, travel, school and home are "
                    "use cases, NOT product categories."
                ),

                "parameters": {

                    "type": "object",

                    "properties": {

                        # ---------------------------------
                        # PRODUCT
                        # ---------------------------------

                        "query": {

                            "type": "string",

                            "description": (
                                "Product type or keyword. "
                                "Examples: bottle, tumbler, flask."
                            )
                        },


                        # ---------------------------------
                        # CATEGORY
                        # ---------------------------------

                        "category": {

                            "type": "string",

                            "description": (
                                "Product category only when "
                                "explicitly mentioned by the user."
                            )
                        },


                        # ---------------------------------
                        # USE CASE
                        # ---------------------------------

                        "use_case": {

                            "type": "string",

                            "description": (
                                "How the user intends to use "
                                "the product. Examples: gym, "
                                "office, travel, school."
                            )
                        },


                        # ---------------------------------
                        # PREFERENCE
                        # ---------------------------------

                        "preference": {

                            "type": "string",

                            "description": (
                                "Product preference such as "
                                "lightweight, leak proof, "
                                "insulated or BPA free."
                            )
                        },


                        # ---------------------------------
                        # MATERIAL
                        # ---------------------------------

                        "material": {

                            "type": "string",

                            "description": (
                                "Preferred product material. "
                                "Example: stainless steel."
                            )
                        },


                        # ---------------------------------
                        # CAPACITY
                        # ---------------------------------

                        "capacity": {

                            "type": "string",

                            "description": (
                                "Preferred product capacity. "
                                "Examples: 500ml, 750ml, 1 litre."
                            )
                        },


                        # ---------------------------------
                        # MAX PRICE
                        # ---------------------------------

                        "max_price": {

                            "type": "number",

                            "description": (
                                "Maximum amount the user "
                                "wants to spend."
                            )
                        }
                    }
                }
            }
        }
    ]


    # =====================================================
    # INITIAL CONVERSATION
    # =====================================================

    messages = [

        {

            "role": "system",

            "content": (

                "You are Pivora AI, an e-commerce shopping "
                "assistant. "

                "You have access to a search_products tool "
                "that searches the real Pivora MongoDB database. "

                "Always use the tool when the user asks about "
                "real products, prices, stock, availability "
                "or product recommendations. "

                "Never invent product names, prices, stock "
                "or product details. "

                "Extract the user's requirements and provide "
                "them to the search_products tool. "

                "For example, if the user says "
                "'I need a lightweight bottle for gym under "
                "1500', use: "

                "query=bottle, "
                "use_case=gym, "
                "preference=lightweight, "
                "max_price=1500. "

                "Only provide a category when the user "
                "explicitly mentions a product category. "

                "Office, gym, travel, school and home are "
                "use cases, NOT categories."
            )
        },

        {

            "role": "user",

            "content": request.message

        }
    ]


    # =====================================================
    # CALL OLLAMA
    # =====================================================

    try:

        response = requests.post(

            "http://localhost:11434/api/chat",

            json={

                "model": "llama3.2:3b",

                "messages": messages,

                "tools": tools,

                "stream": False
            },

            timeout=120
        )


    except requests.exceptions.RequestException as error:

        print("Ollama Error:", error)

        raise HTTPException(
            status_code=500,
            detail="Could not connect to Ollama"
        )


    # =====================================================
    # VALIDATE RESPONSE
    # =====================================================

    if not response.ok:

        print(
            "Ollama Response:",
            response.text
        )

        raise HTTPException(
            status_code=500,
            detail="Ollama request failed"
        )


    data = response.json()


    assistant_message = data.get(
        "message",
        {}
    )


    tool_calls = assistant_message.get(
        "tool_calls",
        []
    )


    # =====================================================
    # NO TOOL CALL
    # =====================================================

    if not tool_calls:

        return {

            "success": True,

            "message": assistant_message.get(
                "content",
                ""
            ),

            "products": []

        }


    # =====================================================
    # EXECUTE TOOL
    # =====================================================

    products = []


    for tool_call in tool_calls:

        function_name = tool_call["function"]["name"]

        arguments = tool_call["function"]["arguments"]


        print("================================")
        print("AI TOOL ARGUMENTS:")
        print(arguments)
        print("================================")


        # -------------------------------------------------
        # SEARCH PRODUCTS
        # -------------------------------------------------

        if function_name == "search_products":

            products = search_products(

                query=arguments.get(
                    "query",
                    ""
                ),

                category=arguments.get(
                    "category",
                    ""
                ),

                use_case=arguments.get(
                    "use_case",
                    ""
                ),

                preference=arguments.get(
                    "preference",
                    ""
                ),

                material=arguments.get(
                    "material",
                    ""
                ),

                capacity=arguments.get(
                    "capacity",
                    ""
                ),

                max_price=(

                    float(
                        arguments["max_price"]
                    )

                    if arguments.get(
                        "max_price"
                    ) is not None

                    else None
                )
            )


    # =====================================================
    # DEBUG
    # =====================================================

    print(
        "PRODUCTS FOUND:",
        len(products)
    )


    # =====================================================
    # NO PRODUCTS
    # =====================================================

    if not products:

        return {

            "success": True,

            "message": (
                "Sorry, I couldn't find any products "
                "matching your requirements."
            ),

            "products": []

        }


    # =====================================================
    # RETURN REAL PRODUCTS
    # =====================================================

    return {

        "success": True,

        "message": (
            f"I found {len(products)} "
            "products matching your requirements."
        ),

        "products": products

    }


# =========================================================
# DIRECT PRODUCT TOOL TEST
# =========================================================

@router.get("/products")
def test_product_search(

    query: str = "",

    category: str = "",

    use_case: str = "",

    preference: str = "",

    material: str = "",

    capacity: str = "",

    max_price: float | None = None

):

    products = search_products(

        query=query,

        category=category,

        use_case=use_case,

        preference=preference,

        material=material,

        capacity=capacity,

        max_price=max_price

    )


    return {

        "success": True,

        "products": products

    }