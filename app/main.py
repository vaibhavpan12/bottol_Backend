from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.routes.product_routes import router as product_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Pivora API",
    version="1.0.0"
)

# backend folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
# backend/uploads
UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "uploads"
)

print("UPLOAD_DIR:", UPLOAD_DIR)
# Serve uploaded images
app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(product_router)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "Pivora API is running"
    }