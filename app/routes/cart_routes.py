from fastapi import APIRouter, Depends

from app.controllers.cart_controller import (
    get_user_cart,
    update_user_cart,
    clear_user_cart,
    merge_user_cart,
)
from app.models.cart_model import CartCreate
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/api/cart",
    tags=["Cart"]
)


@router.get("/me")
def get_my_cart(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["_id"]

    return get_user_cart(user_id)


@router.put("/me")
def update_my_cart(
    cart: CartCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["_id"]

    return update_user_cart(
        user_id,
        cart.items
    )


@router.delete("/me")
def delete_my_cart(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["_id"]

    return clear_user_cart(user_id)


@router.post("/merge")
def merge_my_cart(
    cart: CartCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["_id"]

    return merge_user_cart(
        user_id,
        cart.items
    )