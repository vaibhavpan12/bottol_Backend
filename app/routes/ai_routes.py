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

def detect_simple_product_query(message: str):
    """
    Detect simple shopping queries without using Llama.

    Examples:
    - bottle under 1500
    - bottles below 1000
    - tumbler under 2000
    """

    text = message.lower().strip()

    # Price detect
    price_match = re.search(
        r"(?:under|below|less than|upto|up to|within)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)",
        text
    )

    max_price = None

    if price_match:
        max_price = float(price_match.group(1))

    # Product keyword detect
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

    # Simple query tabhi maanenge jab product keyword mile
    if not query:
        return None

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
    # Simple product query -> Llama ko call nahi karna
    # Direct MongoDB search
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

    # ... existing code continues here
    # -----------------------------------------------------
    # TOOL DEFINITION
    # -----------------------------------------------------

    tools = [
        {
            "type": "function",

            "function": {
                "name": "search_products",

                "description": (
                    "Search real Pivora products from the database "
                    "using product name, category and maximum price. "

                    "Only use category when the user explicitly "
                    "mentions a product category. "

                    "Do NOT treat use cases such as office, gym, "
                    "travel, school or home as product categories."
                ),

                "parameters": {
                    "type": "object",

                    "properties": {

                        "query": {
                            "type": "string",
                            "description": (
                                "Product name or keyword, "
                                "for example bottle or tumbler."
                            )
                        },

                        "category": {
                            "type": "string",
                            "description": (
                                "Product category only when explicitly "
                                "mentioned by the user."
                            )
                        },

                        "max_price": {
                            "type": "number",
                            "description": (
                                "Maximum price the user wants to spend."
                            )
                        }
                    }
                }
            }
        }
    ]


    # -----------------------------------------------------
    # INITIAL CONVERSATION
    # -----------------------------------------------------

    messages = [

        {
            "role": "system",

            "content": (
                "You are Pivora AI, an e-commerce shopping assistant. "

                "You have access to a search_products tool that "
                "searches the real Pivora MongoDB database. "

                "Always use the tool when the user asks about "
                "real products, prices, stock or availability. "

                "Never invent product names, prices, stock or "
                "product details. "

                "Only provide a category to the tool when the user "
                "explicitly mentions a product category. "

                "Words such as office, gym, travel, school and home "
                "describe the user's use case and are NOT categories."
            )
        },

        {
            "role": "user",
            "content": request.message
        }
    ]


    # -----------------------------------------------------
    # STEP 1
    # Ask Llama what action is required
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # STEP 2
    # Validate Ollama response
    # -----------------------------------------------------

    if not response.ok:

        raise HTTPException(
            status_code=500,
            detail="Ollama request failed"
        )


    data = response.json()

    assistant_message = data["message"]

    tool_calls = assistant_message.get(
        "tool_calls",
        []
    )


    # -----------------------------------------------------
    # STEP 3
    # If no tool is required
    # -----------------------------------------------------

    if not tool_calls:

        return {
            "success": True,
            "message": assistant_message.get(
                "content",
                ""
            ),
            "products": []
        }


    # -----------------------------------------------------
    # STEP 4
    # Execute tool
    # -----------------------------------------------------

    products = []

    for tool_call in tool_calls:

        function_name = tool_call["function"]["name"]

        arguments = tool_call["function"]["arguments"]

        print("================================")
        print("AI TOOL ARGUMENTS:")
        print(arguments)
        print("================================")


        # -------------------------------------------------
        # search_products
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

                max_price=(
                    float(arguments["max_price"])
                    if arguments.get("max_price") is not None
                    else None
                )
            )


    print(
        "PRODUCTS FOUND:",
        len(products)
    )


    # -----------------------------------------------------
    # STEP 5
    # No products found
    # -----------------------------------------------------

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
    # OPTIMIZATION
    # =====================================================
    #
    # Previously we made another Ollama request here:
    #
    # MongoDB products
    #       ↓
    #      Llama
    #       ↓
    # final response
    #
    # That second Llama request was unnecessary and
    # increased the "Thinking..." time.
    #
    # Now we directly return the real MongoDB products.
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

    max_price: float | None = None

):

    products = search_products(

        query=query,

        category=category,

        max_price=max_price

    )

    return {

        "success": True,

        "products": products

    }