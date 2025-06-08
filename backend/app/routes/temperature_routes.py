"""
API routes for temperature data in the CCT Backend application.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.config.database import get_db
from app.models import schemas, models
from app.services import temperature_service
from app.utils.auth import verify_device_api_key

router = APIRouter(
    prefix="/temperature",
    tags=["temperature"],
    responses={404: {"description": "Not found"}},
)

@router.post("/update", response_model=schemas.TemperatureUpdateResponse)
def update_temperature(
    update: schemas.TemperatureUpdateRequest,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Update temperature readings from a CCT device.
    
    This endpoint allows a CCT device to send temperature readings from its connected probes
    and the calculated average temperature. It returns the latest target temperature setting
    for the device.
    
    The device must provide its API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, update.device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        return temperature_service.process_temperature_update(db, update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/target", response_model=schemas.TargetTemperatureUpdateResponse)
def set_target_temperature(
    update: schemas.TargetTemperatureUpdateRequest,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Set a target temperature for a CCT device.
    
    This endpoint allows setting a target temperature for a CCT device.
    The device or authorized user must provide an API key for authentication.
    
    If set from the CCT device UI, the device provides its own API key.
    If set from a user application, the user's API key is provided.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, update.device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        target = temperature_service.set_target_temperature(
            db, 
            update.device_id, 
            update.temperature,
            update.set_by_user_id
        )
        return schemas.TargetTemperatureUpdateResponse(
            message="Target temperature updated successfully",
            temperature=target.temperature
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{device_id}/history", response_model=List[schemas.TemperatureReading])
def get_temperature_history(
    device_id: str,
    probe_id: Optional[str] = None,
    limit: int = 100,
    is_average: Optional[bool] = True,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Get temperature history for a CCT device or probe.
    
    This endpoint allows retrieving temperature history for a CCT device or a specific probe.
    The device or authorized user must provide an API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    readings = temperature_service.get_temperature_history(
        db, 
        device_id, 
        probe_id,
        limit,
        is_average   # <-- Pass the actual query param!
    )
    return readings

@router.get("/{device_id}/probes/{probe_id}/history", response_model=List[schemas.TemperatureReading])
def get_probe_temperature_history(
    device_id: str,
    probe_id: str,
    limit: int = 100,
    is_average: Optional[bool] = None,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Get temperature history for a specific probe of a CCT device.
    The device or authorized user must provide an API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    readings = temperature_service.get_temperature_history(
        db,
        device_id,
        probe_id,
        limit,
        is_average
    )
    return readings

@router.get("/{device_id}/target", response_model=Optional[schemas.TargetTemperature])
def get_target_temperature(
    device_id: str,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Get the current target temperature for a CCT device.
    
    This endpoint allows retrieving the current target temperature setting for a CCT device.
    The device or authorized user must provide an API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    target = temperature_service.get_latest_target_temperature(db, device_id)
    if not target:
        return None
    return target

@router.get("/{device_id}/average", response_model=float)
def calculate_average_temperature(
    device_id: str,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Calculate the average temperature from all connected probes for a CCT device.
    
    This endpoint allows calculating the current average temperature from all connected
    probes for a CCT device. The device or authorized user must provide an API key for
    authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    average = temperature_service.calculate_average_temperature(db, device_id)
    if average is None:
        raise HTTPException(status_code=404, detail="No connected probes with temperature readings found")
    return average

@router.post("/temperature/batch")
def add_probe_readings_batch(batch: schemas.ProbeReadingBatch, db: Session = Depends(get_db)):
    readings = []
    for reading in batch.readings:
        db_reading = models.TemperatureReading(
            temperature=reading.temperature,
            is_average=reading.is_average,
            device_id=reading.device_id,
            probe_id=reading.probe_id,
            timestamp=reading.timestamp if hasattr(reading, "timestamp") else datetime.utcnow()
        )
        readings.append(db_reading)
    db.add_all(readings)
    db.commit()
    return {"inserted": len(readings)}
