"""
Settings synchronization service for the CCT Backend application.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models import models, schemas

def sync_device_settings(db: Session, device_id: str) -> Dict[str, Any]:
    """
    Synchronize settings for a CCT device.
    
    This function retrieves all relevant settings for a device that need to be
    synchronized with the cloud, including target temperature and notification thresholds.
    
    Args:
        db: Database session
        device_id: Device ID
        
    Returns:
        Dictionary of settings to be synchronized
    """
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        raise ValueError(f"Device with ID {device_id} not found")
    
    # Get latest target temperature
    target_temp = (
        db.query(models.TargetTemperature)
        .filter(
            models.TargetTemperature.device_id == device.id,
            models.TargetTemperature.is_active == True
        )
        .order_by(models.TargetTemperature.timestamp.desc())
        .first()
    )
    
    # Get notification settings for all users associated with this device
    notification_settings = []
    for owner in device.owners:
        settings = (
            db.query(models.NotificationSetting)
            .filter(models.NotificationSetting.user_id == owner.id)
            .first()
        )
        if settings:
            notification_settings.append(settings)
    
    # Compile settings to sync
    sync_data = {
        "device_id": device_id,
        "target_temperature": target_temp.temperature if target_temp else None,
        "last_sync": datetime.utcnow().isoformat(),
        "thresholds": {
            "max_temperature": min([s.max_temp_threshold for s in notification_settings if s.max_temp_threshold is not None], default=None),
            "min_temperature": max([s.min_temp_threshold for s in notification_settings if s.min_temp_threshold is not None], default=None)
        },
        "custom_triggers": []
    }
    
    # Add custom triggers
    for setting in notification_settings:
        for trigger in setting.custom_triggers:
            if trigger.device_id == device.id and trigger.is_active:
                sync_data["custom_triggers"].append({
                    "name": trigger.name,
                    "condition_type": trigger.condition_type,
                    "threshold_value": trigger.threshold_value
                })
    
    # Update device last_connected timestamp
    device.last_connected = datetime.utcnow()
    db.commit()
    
    return sync_data

def update_target_temperature_from_device(
    db: Session, 
    device_id: str, 
    temperature: float
) -> models.TargetTemperature:
    """
    Update target temperature from a CCT device.
    
    Args:
        db: Database session
        device_id: Device ID
        temperature: Target temperature in Celsius
        
    Returns:
        Updated target temperature object
    """
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        raise ValueError(f"Device with ID {device_id} not found")
    
    # Deactivate previous target temperatures
    previous_targets = (
        db.query(models.TargetTemperature)
        .filter(
            models.TargetTemperature.device_id == device.id,
            models.TargetTemperature.is_active == True
        )
        .all()
    )
    
    for target in previous_targets:
        target.is_active = False
    
    db.commit()
    
    # Create new target temperature
    db_target = models.TargetTemperature(
        temperature=temperature,
        device_id=device.id,
        timestamp=datetime.utcnow(),
        is_active=True
    )
    
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    
    # Update device last_connected timestamp
    device.last_connected = datetime.utcnow()
    db.commit()
    
    return db_target

def update_target_temperature_from_cloud(
    db: Session, 
    device_id: str, 
    temperature: float,
    user_id: int
) -> models.TargetTemperature:
    """
    Update target temperature from the cloud (set by a user).
    
    Args:
        db: Database session
        device_id: Device ID
        temperature: Target temperature in Celsius
        user_id: User ID who set the temperature
        
    Returns:
        Updated target temperature object
    """
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        raise ValueError(f"Device with ID {device_id} not found")
    
    # Verify user is associated with device
    user_device = (
        db.query(models.user_device_association)
        .filter(
            models.user_device_association.c.user_id == user_id,
            models.user_device_association.c.device_id == device.id
        )
        .first()
    )
    
    if not user_device:
        raise ValueError(f"User with ID {user_id} is not associated with device {device_id}")
    
    # Deactivate previous target temperatures
    previous_targets = (
        db.query(models.TargetTemperature)
        .filter(
            models.TargetTemperature.device_id == device.id,
            models.TargetTemperature.is_active == True
        )
        .all()
    )
    
    for target in previous_targets:
        target.is_active = False
    
    db.commit()
    
    # Create new target temperature
    db_target = models.TargetTemperature(
        temperature=temperature,
        device_id=device.id,
        set_by_user_id=user_id,
        timestamp=datetime.utcnow(),
        is_active=True
    )
    
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    
    return db_target

def get_device_settings_history(
    db: Session, 
    device_id: str,
    limit: int = 100
) -> List[models.TargetTemperature]:
    """
    Get settings history for a device.
    
    Args:
        db: Database session
        device_id: Device ID
        limit: Maximum number of settings to return
        
    Returns:
        List of target temperature objects
    """
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        return []
    
    return (
        db.query(models.TargetTemperature)
        .filter(models.TargetTemperature.device_id == device.id)
        .order_by(models.TargetTemperature.timestamp.desc())
        .limit(limit)
        .all()
    )
