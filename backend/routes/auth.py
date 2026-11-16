from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import func, select

from sqlalchemy.orm import Session

from database import get_db

from models.user import User

from schemas.auth import LoginRequest, LoginResponse

from core.security import (
    verify_password,
    create_access_token
)

from core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/login",
    response_model=LoginResponse
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):

    user = db.scalar(
        select(User).where(
            func.lower(User.email) == payload.email.lower()
        )
    )

    if not user or not verify_password(
        payload.password,
        user.password_hash
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user.is_active:

        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):

    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role
    }