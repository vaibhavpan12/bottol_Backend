from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from fastapi.staticfiles import StaticFiles

from app.routes.product_routes import router as product_router
from app.routes.order_routes import router as order_router
from app.routes.user_routes import router as user_router
from app.routes.cart_routes import router as cart_router
from app.routes.ai_routes import router as ai_router

app = FastAPI(
    title="Pivora API",
    version="1.0.0"
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://bottol-steel.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Uploads
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "uploads"
)

print("UPLOAD_DIR:", UPLOAD_DIR)

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads"
)


# =========================
# Routes
# =========================

app.include_router(product_router)
app.include_router(order_router)
app.include_router(user_router)
app.include_router(cart_router)
app.include_router(ai_router)

@app.get("/")
def root():
    return {
        "success": True,
        "message": "Pivora API is running"
    }