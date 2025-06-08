"""
API routes for settings synchronization in the CCT Backend application.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.config.database import get_db
from app.models import schemas
from app.services import settings_service
from app.utils.auth import verify_device_api_key, get_current_active_user

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{device_id}/sync", response_model=Dict[str, Any])
def sync_device_settings(
    device_id: str,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Synchronize settings for a CCT device.
    
    This endpoint allows a CCT device to retrieve all relevant settings that need to be
    synchronized with the cloud, including target temperature and notification thresholds.
    
    The device must provide its API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        return settings_service.sync_device_settings(db, device_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{device_id}/target", response_model=schemas.TargetTemperature)
def update_target_temperature_from_device(
    device_id: str,
    temperature: float,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Update target temperature from a CCT device.
    
    This endpoint allows a CCT device to update its target temperature setting.
    The device must provide its API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        return settings_service.update_target_temperature_from_device(db, device_id, temperature)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/user/{device_id}/target", response_model=schemas.TargetTemperature)
def update_target_temperature_from_cloud(
    device_id: str,
    temperature: float,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """
    Update target temperature from the cloud (set by a user).
    
    This endpoint allows a user to update the target temperature setting for a CCT device.
    The user must be authenticated and associated with the device.
    """
    try:
        return settings_service.update_target_temperature_from_cloud(
            db, 
            device_id, 
            temperature,
            current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{device_id}/history", response_model=List[schemas.TargetTemperature])
def get_device_settings_history(
    device_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Get settings history for a device.
    
    This endpoint allows retrieving the history of target temperature settings for a CCT device.
    The device or authorized user must provide an API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return settings_service.get_device_settings_history(db, device_id, limit)
