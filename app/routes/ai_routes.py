"""
Pivora AI shopping assistant.

Works in two modes:

1. Smart search (always available, no setup):
   understands categories, keywords and price ranges ("shoes under 3000")
   and searches MongoDB directly.

2. Online AI model (optional, better at free-form questions):
   set these environment variables on Render:
       LLM_API_KEY   = your key            (e.g. a free Groq key from console.groq.com)
       LLM_BASE_URL  = https://api.groq.com/openai/v1     (default)
       LLM_MODEL     = llama-3.3-70b-versatile            (default)
   Any OpenAI-compatible API works (Groq, OpenAI, OpenRouter, Together...).

If the AI model is missing, slow or fails, the assistant falls back to
smart search, so the chat never shows an error to the shopper.
"""

import json
import os

import requests
from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.product_tools import (
    CATEGORY_SYNONYMS,
    search_products,
    trending_products,
    understand_message,
)

router = APIRouter(prefix="/api/ai", tags=["AI"])

LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "25"))

CATEGORY_LIST = ", ".join(CATEGORY_SYNONYMS.keys())


class AgentRequest(BaseModel):
    message: str


class ChatRequest(BaseModel):
    message: str


# =========================================================
# HELPERS
# =========================================================

def price_text(min_price, max_price) -> str:
    if min_price and max_price:
        return f" between ₹{int(min_price)} and ₹{int(max_price)}"
    if max_price:
        return f" under ₹{int(max_price)}"
    if min_price:
        return f" above ₹{int(min_price)}"
    return ""


def call_llm(messages, tools=None):
    """Call an OpenAI-compatible chat API. Returns the assistant message or None."""
    if not LLM_API_KEY:
        return None

    payload = {"model": LLM_MODEL, "messages": messages, "temperature": 0.2}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        response = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json=payload,
            timeout=LLM_TIMEOUT,
        )
        if not response.ok:
            print("LLM error:", response.status_code, response.text[:300])
            return None
        return response.json()["choices"][0]["message"]
    except Exception as error:  # network error, timeout, bad JSON
        print("LLM request failed:", error)
        return None


def smart_search_reply(message: str) -> dict:
    """Rule-based assistant — no AI service needed."""
    intent = understand_message(message)

    if intent["greeting"]:
        return {
            "success": True,
            "message": (
                "Hi! I'm Pivora AI 👋 Tell me what you're looking for — for example "
                "\"phone under 20000\", \"running shoes\" or \"perfume gift above 3000\"."
            ),
            "products": trending_products(4),
        }

    has_product_words = bool(intent["query"] or intent["category"] or intent["max_price"] or intent["min_price"])
    if intent.get("faq") and not (intent["category"] or intent["max_price"]):
        return {"success": True, "message": intent["faq"], "products": []}
    if not has_product_words:
        return {
            "success": True,
            "message": "Tell me what you'd like to buy and your budget, e.g. \"headphones under 3000\". Here are some popular picks:",
            "products": trending_products(4),
        }

    search = dict(
        query=intent["query"],
        category=intent["category"],
        max_price=intent["max_price"],
        min_price=intent["min_price"],
    )
    what = intent["query"] or intent["category"] or "products"
    budget = price_text(intent["min_price"], intent["max_price"])

    products = search_products(**search, relax=False)
    if products:
        return {
            "success": True,
            "message": f"Here {'is' if len(products) == 1 else 'are'} {len(products)} {what}{budget} you might like:",
            "products": products,
        }

    similar = search_products(**search, relax=True)
    if similar:
        where = f" in {intent['category']}" if intent["category"] else ""
        return {
            "success": True,
            "message": f"I couldn't find an exact match for {what}{budget}. Here are similar products{where}:",
            "products": similar,
        }

    return {
        "success": True,
        "message": (
            f"I couldn't find {what}{budget} right now. "
            "Here are some popular picks instead — or try different words or a wider budget."
        ),
        "products": trending_products(4),
    }


# =========================================================
# AI SHOPPING AGENT
# =========================================================

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_products",
        "description": (
            "Search the real Pivora product database. Use it whenever the shopper "
            "wants product suggestions, prices or availability. Never invent products."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "1-3 product keywords, e.g. 'running shoes', 'iphone', 'perfume'.",
                },
                "category": {
                    "type": "string",
                    "enum": list(CATEGORY_SYNONYMS.keys()),
                    "description": "Store category, only if clear from the request.",
                },
                "max_price": {"type": "number", "description": "Maximum price in INR."},
                "min_price": {"type": "number", "description": "Minimum price in INR."},
            },
        },
    },
}

SYSTEM_PROMPT = (
    "You are Pivora AI, a friendly shopping assistant for Pivora, an Indian online store. "
    f"Store categories: {CATEGORY_LIST}. Prices are in Indian rupees (₹). "
    "When the shopper is looking for products, call search_products with their keywords, "
    "category and budget. Never invent product names, prices or stock. "
    "For other questions (delivery, returns, payment) answer briefly: free delivery over ₹1499, "
    "₹79 below that, 7-day returns, UPI/cards/net banking/cash on delivery accepted. "
    "Keep replies short (1-2 sentences)."
)


@router.post("/agent")
def ai_agent(request: AgentRequest):
    message = (request.message or "").strip()[:500]
    if not message:
        return {"success": True, "message": "What are you shopping for today?", "products": []}

    # --- No AI model configured: smart search only ---
    if not LLM_API_KEY:
        return smart_search_reply(message)

    # --- AI model decides what to search ---
    reply = call_llm(
        [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message}],
        tools=[SEARCH_TOOL],
    )
    if reply is None:
        return smart_search_reply(message)

    tool_calls = reply.get("tool_calls") or []

    if not tool_calls:
        text = (reply.get("content") or "").strip()
        return {
            "success": True,
            "message": text or "How can I help you shop today?",
            "products": [],
        }

    args = {}
    try:
        raw = tool_calls[0]["function"].get("arguments") or "{}"
        args = json.loads(raw) if isinstance(raw, str) else raw
    except (KeyError, ValueError, TypeError):
        return smart_search_reply(message)

    def num(value):
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    min_price, max_price = num(args.get("min_price")), num(args.get("max_price"))
    search = dict(
        query=args.get("query", "") or "",
        category=args.get("category", "") or "",
        max_price=max_price,
        min_price=min_price,
    )
    products = search_products(**search, relax=False)
    exact = bool(products)
    if not products:
        products = search_products(**search, relax=True)

    if not products:
        # let the rule-based search have a go before giving up
        fallback = smart_search_reply(message)
        if fallback["products"] and "couldn't" not in fallback["message"]:
            return fallback
        what = args.get("query") or args.get("category") or "that"
        return {
            "success": True,
            "message": (
                f"I couldn't find {what}{price_text(min_price, max_price)} right now. "
                "Here are some popular picks instead."
            ),
            "products": trending_products(4),
        }

    what = args.get("query") or args.get("category") or "products"
    if not exact:
        return {
            "success": True,
            "message": f"I couldn't find an exact match for {what}{price_text(min_price, max_price)}. Here are similar products:",
            "products": products,
        }
    return {
        "success": True,
        "message": f"Here {'is' if len(products) == 1 else 'are'} {len(products)} {what}{price_text(min_price, max_price)} you might like:",
        "products": products,
    }


# =========================================================
# PLAIN CHAT (no product search)
# =========================================================

@router.post("/chat")
def chat_with_ai(request: ChatRequest):
    reply = call_llm(
        [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": request.message}]
    )
    if reply is None:
        return smart_search_reply(request.message)
    return {"success": True, "message": reply.get("content", ""), "products": []}


# =========================================================
# STATUS / DIRECT SEARCH (handy for testing)
# =========================================================

@router.get("/status")
def ai_status():
    return {
        "success": True,
        "mode": "ai-model" if LLM_API_KEY else "smart-search",
        "model": LLM_MODEL if LLM_API_KEY else None,
    }


@router.get("/products")
def test_product_search(
    query: str = "",
    category: str = "",
    max_price: float | None = None,
    min_price: float | None = None,
):
    return {
        "success": True,
        "products": search_products(
            query=query, category=category, max_price=max_price, min_price=min_price
        ),
    }
