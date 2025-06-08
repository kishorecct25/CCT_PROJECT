"""
Temperature data service for the CCT Backend application.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import models, schemas

def store_temperature_reading(
    db: Session, 
    device_id: str, 
    temperature: float, 
    probe_id: Optional[str] = None, 
    is_average: bool = False
) -> models.TemperatureReading:
    """
    Store a temperature reading from a CCT device or probe.
    
    Args:
        db: Database session
        device_id: Device ID
        temperature: Temperature reading in Celsius
        probe_id: Optional probe ID
        is_average: Whether this is an average reading
        
    Returns:
        Stored temperature reading object
    """
    # Get device by ID
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        raise ValueError(f"Device with ID {device_id} not found")
    
    # Get probe by ID if provided
    probe = None
    if probe_id:
        probe = db.query(models.Probe).filter(models.Probe.probe_id == probe_id).first()
        if not probe:
            raise ValueError(f"Probe with ID {probe_id} not found")
    
    # Create temperature reading
    db_reading = models.TemperatureReading(
        temperature=temperature,
        device_id=device.id,
        probe_id=probe.id if probe else None,
        is_average=is_average,
        timestamp=datetime.utcnow()
    )
    
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    
    # Update device connection status
    device.last_connected = datetime.utcnow()
    db.commit()
    
    # Update probe connection status if applicable
    if probe:
        probe.is_connected = True
        probe.last_connected = datetime.utcnow()
        db.commit()
    
    # --- Add this block to trigger notifications ---
    # Find all active triggers for this device
    triggers = db.query(models.CustomTrigger).filter(
        models.CustomTrigger.device_id == device.id,
        models.CustomTrigger.is_active == True
    ).all()
    print(f"[store_temperature_reading] Found {len(triggers)} active triggers for device id={device.id}")

    # Ensure temperature is a float for comparison
    temperature = float(temperature)

    for trigger in triggers:
        print(f"[store_temperature_reading] Evaluating trigger id={trigger.id}, probe_id={trigger.probe_id}, threshold={trigger.threshold_value}, condition={trigger.condition_type}")
        # If the trigger is probe-specific, only fire if probe matches
        if trigger.probe_id:
            if not probe or trigger.probe_id != probe.id:
                print(f"[store_temperature_reading] Skipping trigger id={trigger.id} (probe-specific, no match)")
                continue  # Skip if no probe or probe doesn't match

        # Evaluate trigger condition
        if (
            (trigger.condition_type == "above" and temperature > trigger.threshold_value) or
            (trigger.condition_type == "below" and temperature < trigger.threshold_value) or
            (trigger.condition_type == "equal" and temperature == trigger.threshold_value)
        ):
            print(f"[store_temperature_reading] Trigger id={trigger.id} fired! Creating notification.")
            notification = models.Notification(
                user_id=trigger.notification_setting.user_id if hasattr(trigger, "notification_setting") and trigger.notification_setting else None,
                title=f"Temperature {trigger.condition_type} {trigger.threshold_value}",
                message=f"Probe {probe.probe_id if probe else 'N/A'}: {temperature}°F",
                notification_type="temperature_alert",
                channel="app",  # <-- Add this line
                device_id=device.id,
                probe_id=probe.id if probe else None,
                created_at=datetime.utcnow()
            )
            db.add(notification)
            db.commit()
            print(f"[store_temperature_reading] Notification created for trigger id={trigger.id}, notification id={notification.id}")
        else:
            print(f"[store_temperature_reading] Trigger id={trigger.id} not fired.")
    # --- End notification trigger block ---
    
    return db_reading

def process_temperature_update(
    db: Session, 
    update: schemas.TemperatureUpdateRequest
) -> schemas.TemperatureUpdateResponse:
    """
    Process a temperature update from a CCT device.
    
    Args:
        db: Database session
        update: Temperature update request
        
    Returns:
        Temperature update response
    """
    device_id = update.device_id
    
    # Store individual probe readings
    for reading in update.readings:
        probe_id = reading.get("probe_id")
        temperature = reading.get("temperature")
        
        if temperature is not None:
            store_temperature_reading(
                db=db,
                device_id=device_id,
                temperature=temperature,
                probe_id=probe_id,
                is_average=False
            )
    
    # Store average temperature if provided
    if update.average_temperature is not None:
        store_temperature_reading(
            db=db,
            device_id=device_id,
            temperature=update.average_temperature,
            is_average=True
        )
    
    # Get latest target temperature for the device
    target_temp = get_latest_target_temperature(db, device_id)
    
    return schemas.TemperatureUpdateResponse(
        message="Temperature readings received successfully",
        target_temperature=target_temp.temperature if target_temp else None
    )

def get_latest_target_temperature(db: Session, device_id: str) -> Optional[models.TargetTemperature]:
    """
    Get the latest target temperature for a device.
    
    Args:
        db: Database session
        device_id: Device ID
        
    Returns:
        Latest target temperature object or None if not found
    """
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        return None
    
    return (
        db.query(models.TargetTemperature)
        .filter(
            models.TargetTemperature.device_id == device.id,
            models.TargetTemperature.is_active == True
        )
        .order_by(models.TargetTemperature.timestamp.desc())
        .first()
    )

def get_temperature_history(
    db: Session, 
    device_id: str, 
    probe_id: Optional[str] = None,
    limit: int = 100,
    is_average: Optional[bool] = None
) -> List[models.TemperatureReading]:
    """
    Get temperature history for a device or probe.
    
    Args:
        db: Database session
        device_id: Device ID
        probe_id: Optional probe ID to filter by
        limit: Maximum number of readings to return
        is_average: Optional filter for average readings
        
    Returns:
        List of temperature reading objects
    """
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        return []
    
    query = db.query(models.TemperatureReading).filter(models.TemperatureReading.device_id == device.id)
    
    if probe_id:
        probe = db.query(models.Probe).filter(models.Probe.probe_id == probe_id).first()
        if probe:
            query = query.filter(models.TemperatureReading.probe_id == probe.id)
    
    if is_average is not None:
        query = query.filter(models.TemperatureReading.is_average == is_average)
    
    return query.order_by(models.TemperatureReading.timestamp.desc()).limit(limit).all()

def set_target_temperature(
    db: Session, 
    device_id: str, 
    temperature: float,
    set_by_user_id: Optional[int] = None
) -> models.TargetTemperature:
    """
    Set a target temperature for a device.
    
    Args:
        db: Database session
        device_id: Device ID
        temperature: Target temperature in Celsius
        set_by_user_id: Optional user ID who set the temperature
        
    Returns:
        Target temperature object
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
        set_by_user_id=set_by_user_id,
        timestamp=datetime.utcnow(),
        is_active=True
    )
    
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    
    return db_target

def calculate_average_temperature(db: Session, device_id: str) -> Optional[float]:
    """
    Calculate the average temperature from all connected probes for a device.
    
    Args:
        db: Database session
        device_id: Device ID
        
    Returns:
        Average temperature or None if no probes are connected
    """
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        return None
    
    # Get all connected probes
    probes = (
        db.query(models.Probe)
        .filter(
            models.Probe.device_id == device.id,
            models.Probe.is_connected == True
        )
        .all()
    )
    
    if not probes:
        return None
    
    # Get latest temperature reading for each probe
    temperatures = []
    for probe in probes:
        latest_reading = (
            db.query(models.TemperatureReading)
            .filter(
                models.TemperatureReading.probe_id == probe.id,
                models.TemperatureReading.is_average == False
            )
            .order_by(models.TemperatureReading.timestamp.desc())
            .first()
        )
        
        if latest_reading:
            temperatures.append(latest_reading.temperature)
    
    if not temperatures:
        return None
    
    # Calculate average
    return sum(temperatures) / len(temperatures)
