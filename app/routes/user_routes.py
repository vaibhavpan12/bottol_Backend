from fastapi import APIRouter

from app.controllers.user_controller import (
    create_user,
    login_user
)

from app.models.user_model import UserCreate, UserLogin


router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)


@router.post("/signup")
def signup(user: UserCreate):
    return create_user(user)


@router.post("/login")
def login(user: UserLogin):
    return login_user(user)