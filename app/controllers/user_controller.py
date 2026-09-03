from fastapi import HTTPException
from datetime import datetime, timezone
import bcrypt

from app.database.mongodb import users_collection
from app.models.user_model import UserCreate, UserLogin
from app.utils.auth import create_access_token

def create_user(user: UserCreate):
    existing_user = users_collection.find_one({
        "email": user.email.lower()
    })

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    user_data = {
        "name": user.name,
        "email": user.email.lower(),
        "password": hashed_password,
        "phone": user.phone,
        "address": user.address,
        "city": user.city,
        "pin": user.pin,
        "created_at": datetime.now(timezone.utc),
    }

    result = users_collection.insert_one(user_data)

    user_id = str(result.inserted_id)

    # Automatically login after signup
    token = create_access_token(user_id)

    return {
        "success": True,
        "message": "Account created successfully",
        "token": token,
        "user": {
            "id": user_id,
            "name": user.name,
            "email": user.email.lower(),
            "phone": user.phone,
            "address": user.address,
            "city": user.city,
            "pin": user.pin,
        }
    }

def login_user(user: UserLogin):
    existing_user = users_collection.find_one({
        "email": user.email.lower()
    })

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = bcrypt.checkpw(
        user.password.encode("utf-8"),
        existing_user["password"].encode("utf-8")
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    user_id = str(existing_user["_id"])

    token = create_access_token(user_id)

    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user_id,
            "name": existing_user["name"],
            "email": existing_user["email"],
            "phone": existing_user.get("phone"),
        }
    }