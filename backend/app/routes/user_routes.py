"""
API routes for user management in the CCT Backend application.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
from app.models import schemas, models
from app.services import user_service
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=schemas.User)
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user in the system.
    
    This endpoint allows registering a new CCT owner account.
    It returns the created user object without the password.
    """
    try:
        return user_service.create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@router.post("/me/devices/{device_id}", response_model=schemas.CCTDevice)
def associate_device(
    device_id: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Associate a device with the current user.
    
    This endpoint allows a user to associate a CCT device with their account.
    The user must be authenticated.
    """
    try:
        return user_service.associate_device_with_user(db, current_user.id, device_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me/devices")
def get_user_devices(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all devices associated with the current user.
    
    This endpoint allows a user to retrieve all CCT devices associated with their account.
    The user must be authenticated.
    """
    devices = user_service.get_user_devices(db, current_user.id)
    device_list = []
    for device in devices:
        # Query the API key for this device (using device.id)
        api_key_obj = db.query(models.APIKey).filter(
            models.APIKey.device_id == device.id,
            models.APIKey.is_active == True
        ).first()
        api_key = api_key_obj.key if api_key_obj else None
        # Get all column attributes dynamically
        device_data = {col.name: getattr(device, col.name) for col in device.__table__.columns}
        device_data["api_key"] = api_key

        device_list.append(device_data)
    return device_list

@router.get("/me/notification-settings", response_model=schemas.NotificationSetting)
def get_notification_settings(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get notification settings for the current user.
    
    This endpoint allows a user to retrieve their notification settings.
    The user must be authenticated.
    """
    settings = user_service.get_notification_settings(db, current_user.id)
    if not settings:
        raise HTTPException(status_code=404, detail="Notification settings not found")
    return settings

@router.put("/me/notification-settings", response_model=schemas.NotificationSetting)
def update_notification_settings(
    settings_update: schemas.NotificationSettingUpdate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update notification settings for the current user.
    
    This endpoint allows a user to update their notification settings.
    The user must be authenticated.
    """
    return user_service.update_notification_settings(db, current_user.id, settings_update)

@router.post("/me/triggers", response_model=schemas.CustomTrigger)
def create_custom_trigger(
    trigger: schemas.CustomTriggerCreate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a custom notification trigger for the current user.
    
    This endpoint allows a user to create a custom temperature-based trigger.
    The user must be authenticated.
    """
    try:
        return user_service.create_custom_trigger(db, current_user.id, trigger)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me/triggers", response_model=List[schemas.CustomTrigger])
def get_custom_triggers(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all custom triggers for the current user.
    
    This endpoint allows a user to retrieve all their custom triggers.
    The user must be authenticated.
    """
    return user_service.get_custom_triggers(db, current_user.id)

@router.put("/me/triggers/{trigger_id}", response_model=schemas.CustomTrigger)
def update_custom_trigger(
    trigger_id: int,
    trigger_update: schemas.CustomTriggerUpdate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a custom trigger.
    
    This endpoint allows a user to update one of their custom triggers.
    The user must be authenticated.
    """
    trigger = user_service.update_custom_trigger(db, trigger_id, current_user.id, trigger_update)
    if not trigger:
        raise HTTPException(status_code=404, detail="Custom trigger not found")
    return trigger

@router.delete("/me/triggers/{trigger_id}", response_model=schemas.CustomTrigger)
def delete_custom_trigger(
    trigger_id: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a custom trigger for the current user.
    """
    return user_service.delete_custom_trigger(db, current_user.id, trigger_id)

@router.patch("/me/devices/{device_id}", response_model=schemas.CCTDevice)
def update_user_device(
    device_id: str,
    update: dict = Body(...),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a device's name and status for the current user.
    """
    device = (
        db.query(models.CCTDevice)
        .join(models.user_device_association, models.CCTDevice.id == models.user_device_association.c.device_id)
        .filter(models.CCTDevice.device_id == device_id)
        .filter(models.user_device_association.c.user_id == current_user.id)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or not owned by user")

    if "name" in update:
        device.name = update["name"]
    if "is_active" in update:
        device.is_active = update["is_active"]

    db.commit()
    db.refresh(device)
    return device

@router.delete("/{user_id}/deregister", response_model=dict)
def deregister_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Deregister (delete) a user and all associated data.
    """
    try:
        user_service.deregister_user(db, user_id)
        return {"success": True, "message": "User and associated data deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))