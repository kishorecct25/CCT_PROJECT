"""
API routes for user management in the CCT Backend application.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.config.database import get_db
from app.models import schemas, models
from app.services import user_service
from app.utils.auth import get_current_active_user
from app.utils.otp_utils import generate_otp, send_otp_email, verify_otp

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# ---- New Pydantic model for OTP verification ----
class OTPVerifySchema(BaseModel):
    email: EmailStr
    otp: str

@router.post("/register", response_model=schemas.User)
async def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user in the system.

    This endpoint allows registering a new CCT owner account.
    It returns the created user object without the password.
    """
    try:
        db_user = user_service.create_user(db, user)

        # Generate OTP and send via email
        otp = generate_otp(user.email)
        print("Generated OTP:", otp)  # DEBUG
        try:
            await send_otp_email(user.email, otp,username=user.username)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"User registered, but failed to send OTP email: {str(e)}"
            )

        return db_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-otp")
async def verify_user_otp(
    payload: OTPVerifySchema,
    db: Session = Depends(get_db)
):
    """
    Verify OTP sent to user's email during registration.
    Body format: {"email": "user@example.com", "otp": "123456"}
    """
    print(f"Received OTP verification for {payload.email} with OTP: {payload.otp}")
    
    if verify_otp(payload.email, payload.otp):
        print("OTP verified successfully")
        return {"message": "OTP verified successfully"}
    else:
        print("Invalid OTP")
        raise HTTPException(status_code=401, detail="Invalid OTP")

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get an access token for authentication.

    This endpoint allows a user to authenticate and receive an access token
    that can be used for subsequent API calls.
    """
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_service.create_user_token(user)

@router.get("/me", response_model=schemas.User)
def read_users_me(
    current_user: schemas.User = Depends(get_current_active_user)
):
    """
    Get the current user's information.

    This endpoint allows a user to retrieve their own information.
    The user must be authenticated.
    """
    return current_user

@router.put("/me", response_model=schemas.User)
def update_user_me(
    user_update: schemas.UserUpdate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's information.

    This endpoint allows a user to update their own information.
    The user must be authenticated.
    """
    try:
        return user_service.update_user(db, current_user.id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
