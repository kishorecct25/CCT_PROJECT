"""
Enhanced device service for the CCT Backend application.
Includes support for test accounts and improved device association.
"""
from datetime import datetime
import secrets
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import models, schemas
from app.utils.auth import create_device_api_key

def register_device(db: Session, device: schemas.DeviceRegistrationRequest) -> schemas.DeviceRegistrationResponse:
    """
    Register a new CCT device in the system.
    
    Args:
        db: Database session
        device: Device registration data
        
    Returns:
        Device registration response with API key
    """
    # Validate device_id format (should be CCT-XXXX-XXXX)
    if not device.device_id.startswith("CCT-") or len(device.device_id.split('-')) != 3:
        raise ValueError("Invalid device ID format. Expected format: CCT-XXXX-XXXX")
    
    # Check if device already exists
    db_device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device.device_id).first()
    
    if db_device:
        # Update existing device information
        db_device.name = device.name if device.name else db_device.name
        db_device.firmware_version = device.firmware_version
        db_device.last_connected = datetime.utcnow()
        db_device.is_active = True
        db.commit()
        db.refresh(db_device)
    else:
        # Create new device
        db_device = models.CCTDevice(
            device_id=device.device_id,
            name=device.name,
            model=device.model,
            firmware_version=device.firmware_version,
            last_connected=datetime.utcnow()
        )
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
    
    # Generate API key for device
    api_key = create_device_api_key(device.device_id)
    expires_at = db.execute(text("SELECT NOW() + INTERVAL '30 days'")).scalar()

    # Insert API key
    insert_statement = text("""
        INSERT INTO api_keys (key, device_id, expires_at, is_active)
        VALUES (:key, :device_id, :expires_at, :is_active)
    """)

    db.execute(
        insert_statement,
        {
            "key": api_key,
            "device_id": db_device.id,
            "expires_at": expires_at,
            "is_active": True
        }
    )
    db.commit()

    # Generate association token for secure device-user association
    association_token = generate_association_token(device.device_id)
    
    return schemas.DeviceRegistrationResponse(
        device_id=db_device.device_id,
        api_key=api_key,
        association_token=association_token
    )

def register_probe(db: Session, probe: schemas.ProbeRegistrationRequest, device_id: str) -> schemas.ProbeRegistrationResponse:
    """
    Register a new probe and associate it with a CCT device.
    
    Args:
        db: Database session
        probe: Probe registration data
        device_id: Device ID to associate the probe with
        
    Returns:
        Probe registration response
    """
    # Get the device
    db_device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not db_device:
        raise ValueError(f"Device with ID {device_id} not found")
    
    # Check if probe already exists
    db_probe = db.query(models.Probe).filter(models.Probe.probe_id == probe.probe_id).first()
    
    if db_probe:
        # Update existing probe information
        db_probe.name = probe.name if probe.name else db_probe.name
        db_probe.device_id = db_device.id
        db_probe.is_connected = True
        db_probe.last_connected = datetime.utcnow()
        db.commit()
        db.refresh(db_probe)
    else:
        # Check if device already has maximum number of probes
        probe_count = db.query(models.Probe).filter(models.Probe.device_id == db_device.id).count()
        from app.config.config import settings
        if probe_count >= settings.MAX_PROBES_PER_CCT:
            raise ValueError(f"Device already has maximum number of probes ({settings.MAX_PROBES_PER_CCT})")
        
        # Create new probe
        db_probe = models.Probe(
            probe_id=probe.probe_id,
            name=probe.name,
            model=probe.model,
            device_id=db_device.id,
            is_connected=True,
            last_connected=datetime.utcnow()
        )
        db.add(db_probe)
        db.commit()
        db.refresh(db_probe)
    
    return schemas.ProbeRegistrationResponse(
        probe_id=db_probe.probe_id,
        device_id=device_id
    )

def get_device_by_id(db: Session, device_id: str):
    """
    Get a device by its ID.
    
    Args:
        db: Database session
        device_id: Device ID
        
    Returns:
        Device object or None if not found
    """
    return db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()

def get_probe_by_id(db: Session, probe_id: str):
    """
    Get a probe by its ID.
    
    Args:
        db: Database session
        probe_id: Probe ID
        
    Returns:
        Probe object or None if not found
    """
    return db.query(models.Probe).filter(models.Probe.probe_id == probe_id).first()

def get_probes_by_device_id(db: Session, device_id: str):
    """
    Get all probes associated with a device.
    
    Args:
        db: Database session
        device_id: Device ID
        
    Returns:
        List of probe objects
    """
    device = get_device_by_id(db, device_id)
    if not device:
        return []
    return db.query(models.Probe).filter(models.Probe.device_id == device.id).all()

def update_device_connection_status(db: Session, device_id: str, is_connected: bool = True):
    """
    Update the connection status of a device.
    
    Args:
        db: Database session
        device_id: Device ID
        is_connected: Connection status
        
    Returns:
        Updated device object or None if not found
    """
    device = get_device_by_id(db, device_id)
    if not device:
        return None
    
    device.last_connected = datetime.utcnow() if is_connected else device.last_connected
    db.commit()
    db.refresh(device)
    return device

def update_probe_connection_status(db: Session, probe_id: str, is_connected: bool = True):
    """
    Update the connection status of a probe.
    
    Args:
        db: Database session
        probe_id: Probe ID
        is_connected: Connection status
        
    Returns:
        Updated probe object or None if not found
    """
    probe = get_probe_by_id(db, probe_id)
    if not probe:
        return None
    
    probe.is_connected = is_connected
    probe.last_connected = datetime.utcnow() if is_connected else probe.last_connected
    db.commit()
    db.refresh(probe)
    return probe

def generate_association_token(device_id: str) -> str:
    """
    Generate a secure token for device-user association.
    
    Args:
        device_id: Device ID
        
    Returns:
        Secure association token
    """
    # Generate a random token
    random_bytes = secrets.token_bytes(32)
    
    # Combine with device_id and hash
    combined = device_id.encode() + random_bytes
    token = hashlib.sha256(combined).hexdigest()
    
    return token

def associate_device_with_user(db: Session, device_id: str, user_id: int, token: str = None) -> bool:
    """
    Associate a device with a user.
    
    Args:
        db: Database session
        device_id: Device ID
        user_id: User ID
        token: Optional association token for verification
        
    Returns:
        True if association was successful, False otherwise
    """
    # Get the device
    device = get_device_by_id(db, device_id)
    if not device:
        return False
    
    get_all_users(db)
    
    # Get the user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return False
    
    # Check if device is already associated with this user
    if user in device.owners:
        return True
    
    # Associate device with user
    device.owners.append(user)
    db.commit()
    
    return True

def get_all_users(db: Session):
    users = db.query(models.User).all()  # Retrieve all users
    if not users:
        return []  # Return an empty list if no users are found

    for user in users:
        print(f"User ID: {user.id}, Username: {user.username}, Email: {user.email}") # Adjust attributes as per your User model

    return users

def get_user_devices(db: Session, user_id: int):
    """
    Get all devices associated with a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List of device objects
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return []
    
    return user.devices

def generate_unique_device_id(db: Session) -> str:
    """
    Generate a unique device ID in the format CCT-XXXX-XXXX.
    
    Args:
        db: Database session
        
    Returns:
        Unique device ID
    """
    while True:
        # Generate random alphanumeric string for the device ID
        random_part1 = ''.join(secrets.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(4))
        random_part2 = ''.join(secrets.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(4))
        
        device_id = f"CCT-{random_part1}-{random_part2}"
        
        # Check if device ID already exists
        if not get_device_by_id(db, device_id):
            return device_id
