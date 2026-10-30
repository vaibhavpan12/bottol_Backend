from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from fastapi.staticfiles import StaticFiles

from app.routes.product_routes import router as product_router
from app.routes.order_routes import router as order_router
from app.routes.user_routes import router as user_router
from app.routes.cart_routes import router as cart_router
from app.routes.ai_routes import router as ai_router
from app.routes.admin_routes import router as admin_router
app = FastAPI(
    title="Pivora API",
    version="1.0.0"
)


# =========================
# CORS
# =========================

# Add your live domains in Render -> Environment -> ALLOWED_ORIGINS
# as a comma-separated list, e.g.
#   https://www.yourdomain.com,https://yourdomain.com
DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://pivoraai.vercel.app",
]

extra_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ORIGINS + extra_origins,
    # also allow every Vercel preview deployment of the frontend
    allow_origin_regex=r"https://.*\.vercel\.app",
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
app.include_router(admin_router)
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def root():
    return {
        "success": True,
        "message": "Pivora API is running"
    }
