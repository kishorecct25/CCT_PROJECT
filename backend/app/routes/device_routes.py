"""
Enhanced device routes for the CCT Backend application.
Includes support for test accounts and improved device association.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
from app.models import schemas_enhanced as schemas
from app.services import device_service
from app.utils.auth import verify_device_api_key

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=schemas.DeviceRegistrationResponse)
def register_device(
    device: schemas.DeviceRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new CCT device in the system.
    
    This endpoint allows a CCT device to register itself with the cloud backend.
    It returns an API key that the device must use for subsequent API calls.
    
    If the device is already registered, it updates the device information and
    returns a new API key.
    """
    try:
        return device_service.register_device(db, device)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{device_id}/probes/register", response_model=schemas.ProbeRegistrationResponse)
def register_probe(
    device_id: str,
    probe: schemas.ProbeRegistrationRequest,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Register a new probe and associate it with a CCT device.
    
    This endpoint allows a CCT device to register a probe and associate it with itself.
    The device must provide its API key for authentication.
    
    If the probe is already registered, it updates the probe information and
    associates it with the specified device.
    
    A device can have a maximum of 4 probes associated with it.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        return device_service.register_probe(db, probe, device_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{device_id}/probes", response_model=List[schemas.Probe])
def get_device_probes(
    device_id: str,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Get all probes associated with a device.
    
    This endpoint allows a CCT device to retrieve all probes associated with it.
    The device must provide its API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    probes = device_service.get_probes_by_device_id(db, device_id)
    return probes

@router.put("/{device_id}/connection", response_model=schemas.CCTDevice)
def update_device_connection(
    device_id: str,
    is_connected: bool = True,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Update the connection status of a device.
    
    This endpoint allows updating the connection status of a CCT device.
    The device must provide its API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    device = device_service.update_device_connection_status(db, device_id, is_connected)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.put("/{device_id}/probes/{probe_id}/connection", response_model=schemas.Probe)
def update_probe_connection(
    device_id: str,
    probe_id: str,
    is_connected: bool = True,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None)
):
    """
    Update the connection status of a probe.
    
    This endpoint allows updating the connection status of a probe.
    The device must provide its API key for authentication.
    """
    if not x_api_key or not verify_device_api_key(db, x_api_key, device_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    probe = device_service.update_probe_connection_status(db, probe_id, is_connected)
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found")
    return probe

@router.post("/generate-id", response_model=schemas.DeviceIDGenerationResponse)
def generate_device_id(
    db: Session = Depends(get_db)
):
    """
    Generate a unique device ID.
    
    This endpoint generates a unique device ID in the format CCT-XXXX-XXXX.
    """
    try:
        device_id = device_service.generate_unique_device_id(db)
        return schemas.DeviceIDGenerationResponse(device_id=device_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/associate", response_model=schemas.DeviceAssociationResponse)
def associate_device_with_user(
    association: schemas.DeviceAssociationRequest,
    db: Session = Depends(get_db)
):
    """
    Associate a device with a user.
    
    This endpoint allows associating a device with a user account.
    An optional association token can be provided for secure association.
    """
    try:
        success = device_service.associate_device_with_user(
            db, 
            association.device_id, 
            association.user_id, 
            association.association_token
        )
        
        if success:
            return schemas.DeviceAssociationResponse(
                device_id=association.device_id,
                user_id=association.user_id,
                success=True,
                message="Device successfully associated with user"
            )
        else:
            return schemas.DeviceAssociationResponse(
                device_id=association.device_id,
                user_id=association.user_id,
                success=False,
                message="Failed to associate device with user"
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
