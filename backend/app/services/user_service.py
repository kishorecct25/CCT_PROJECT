"""
User management service for the CCT Backend application.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import models, schemas
from app.utils.auth import get_password_hash, verify_password, create_access_token

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Create a new user in the system.
    
    Args:
        db: Database session
        user: User creation data
        
    Returns:
        Created user object
    """
    # Check if user already exists
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    
    if db_user:
        if db_user.username == user.username:
            raise ValueError(f"Username {user.username} already registered")
        else:
            raise ValueError(f"Email {user.email} already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default notification settings for the user
    db_notification_settings = models.NotificationSetting(
        user_id=db_user.id,
        email_enabled=True,
        sms_enabled=user.phone_number is not None,
        push_enabled=True,
        connection_alerts=True
    )
    db.add(db_notification_settings)
    db.commit()
    
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """
    Authenticate a user with username and password.
    
    Args:
        db: Database session
        username: Username
        password: Password
        
    Returns:
        Authenticated user object or None if authentication fails
    """
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_user_token(user: models.User) -> schemas.Token:
    """
    Create an access token for a user.
    
    Args:
        user: User object
        
    Returns:
        Token object
    """
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """
    Get a user by username.
    
    Args:
        db: Database session
        username: Username
        
    Returns:
        User object or None if not found
    """
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Get a user by email.
    
    Args:
        db: Database session
        email: Email
        
    Returns:
        User object or None if not found
    """
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User object or None if not found
    """
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> models.User:
    """
    Update a user's information.
    
    Args:
        db: Database session
        user_id: User ID
        user_update: User update data
        
    Returns:
        Updated user object
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise ValueError(f"User with ID {user_id} not found")
    
    # Check if username is being updated and is already taken
    if user_update.username and user_update.username != db_user.username:
        existing_user = get_user_by_username(db, user_update.username)
        if existing_user:
            raise ValueError(f"Username {user_update.username} already taken")
        db_user.username = user_update.username
    
    # Check if email is being updated and is already taken
    if user_update.email and user_update.email != db_user.email:
        existing_user = get_user_by_email(db, user_update.email)
        if existing_user:
            raise ValueError(f"Email {user_update.email} already registered")
        db_user.email = user_update.email
    
    # Update phone number
    if user_update.phone_number is not None:
        db_user.phone_number = user_update.phone_number
    
    # Update password if provided
    if user_update.password:
        db_user.hashed_password = get_password_hash(user_update.password)
    
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    
    return db_user

def associate_device_with_user(db: Session, user_id: int, device_id: str) -> models.CCTDevice:
    """
    Associate a device with a user.
    
    Args:
        db: Database session
        user_id: User ID
        device_id: Device ID
        
    Returns:
        Associated device object
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        raise ValueError(f"Device with ID {device_id} not found")
    
    # Check if association already exists
    association = (
        db.query(models.user_device_association)
        .filter(
            models.user_device_association.c.user_id == user_id,
            models.user_device_association.c.device_id == device.id
        )
        .first()
    )
    
    if not association:
        # Create association
        stmt = models.user_device_association.insert().values(
            user_id=user_id,
            device_id=device.id
        )
        db.execute(stmt)
        db.commit()
    
    return device

def get_user_devices(db: Session, user_id: int) -> List[models.CCTDevice]:
    """
    Get all devices associated with a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List of device objects
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return []
    
    return user.devices

def get_notification_settings(db: Session, user_id: int) -> Optional[models.NotificationSetting]:
    """
    Get notification settings for a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Notification settings object or None if not found
    """
    return (
        db.query(models.NotificationSetting)
        .filter(models.NotificationSetting.user_id == user_id)
        .first()
    )

def update_notification_settings(
    db: Session, 
    user_id: int, 
    settings_update: schemas.NotificationSettingUpdate
) -> models.NotificationSetting:
    """
    Update notification settings for a user.
    
    Args:
        db: Database session
        user_id: User ID
        settings_update: Notification settings update data
        
    Returns:
        Updated notification settings object
    """
    db_settings = get_notification_settings(db, user_id)
    if not db_settings:
        # Create settings if they don't exist
        db_settings = models.NotificationSetting(user_id=user_id)
        db.add(db_settings)
    
    # Update fields if provided
    if settings_update.email_enabled is not None:
        db_settings.email_enabled = settings_update.email_enabled
    
    if settings_update.sms_enabled is not None:
        db_settings.sms_enabled = settings_update.sms_enabled
    
    if settings_update.push_enabled is not None:
        db_settings.push_enabled = settings_update.push_enabled
    
    if settings_update.max_temp_threshold is not None:
        db_settings.max_temp_threshold = settings_update.max_temp_threshold
    
    if settings_update.min_temp_threshold is not None:
        db_settings.min_temp_threshold = settings_update.min_temp_threshold
    
    if settings_update.connection_alerts is not None:
        db_settings.connection_alerts = settings_update.connection_alerts
    
    db_settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_settings)
    
    return db_settings

def create_custom_trigger(
    db: Session, 
    user_id: int, 
    trigger: schemas.CustomTriggerCreate
) -> models.CustomTrigger:
    """
    Create a custom notification trigger for a user.
    
    Args:
        db: Database session
        user_id: User ID
        trigger: Custom trigger creation data
        
    Returns:
        Created custom trigger object
    """
    # Get notification settings
    db_settings = get_notification_settings(db, user_id)
    if not db_settings:
        raise ValueError(f"Notification settings for user with ID {user_id} not found")
    
    # Verify device exists if provided
    if trigger.device_id:
        device = db.query(models.CCTDevice).filter(models.CCTDevice.id == trigger.device_id).first()
        if not device:
            raise ValueError(f"Device with ID {trigger.device_id} not found")
        
        # Verify user is associated with device
        association = (
            db.query(models.user_device_association)
            .filter(
                models.user_device_association.c.user_id == user_id,
                models.user_device_association.c.device_id == trigger.device_id
            )
            .first()
        )
        
        if not association:
            raise ValueError(f"User with ID {user_id} is not associated with device {trigger.device_id}")
    
    # Verify probe exists if provided
    if trigger.probe_id:
        probe = db.query(models.Probe).filter(models.Probe.id == trigger.probe_id).first()
        if not probe:
            raise ValueError(f"Probe with ID {trigger.probe_id} not found")
    
    # Create custom trigger
    db_trigger = models.CustomTrigger(
        notification_setting_id=db_settings.id,
        name=trigger.name,
        condition_type=trigger.condition_type,
        threshold_value=trigger.threshold_value,
        device_id=trigger.device_id,
        probe_id=trigger.probe_id,
        is_active=trigger.is_active
    )
    
    db.add(db_trigger)
    db.commit()
    db.refresh(db_trigger)
    
    return db_trigger

def get_custom_triggers(db: Session, user_id: int) -> List[models.CustomTrigger]:
    """
    Get all custom triggers for a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List of custom trigger objects
    """
    db_settings = get_notification_settings(db, user_id)
    if not db_settings:
        return []
    
    return db_settings.custom_triggers

def update_custom_trigger(
    db: Session, 
    trigger_id: int, 
    user_id: int, 
    trigger_update: schemas.CustomTriggerUpdate
) -> Optional[models.CustomTrigger]:
    """
    Update a custom trigger.
    
    Args:
        db: Database session
        trigger_id: Trigger ID
        user_id: User ID
        trigger_update: Custom trigger update data
        
    Returns:
        Updated custom trigger object or None if not found
    """
    # Get notification settings
    db_settings = get_notification_settings(db, user_id)
    if not db_settings:
        return None
    
    # Get trigger
    db_trigger = (
        db.query(models.CustomTrigger)
        .filter(
            models.CustomTrigger.id == trigger_id,
            models.CustomTrigger.notification_setting_id == db_settings.id
        )
        .first()
    )
    
    if not db_trigger:
        return None
    
    # Update fields if provided
    if trigger_update.name:
        db_trigger.name = trigger_update.name
    
    if trigger_update.condition_type:
        db_trigger.condition_type = trigger_update.condition_type
    
    if trigger_update.threshold_value is not None:
        db_trigger.threshold_value = trigger_update.threshold_value
    
    if trigger_update.is_active is not None:
        db_trigger.is_active = trigger_update.is_active
    
    db_trigger.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_trigger)
    
    return db_trigger

def delete_custom_trigger(db, user_id, trigger_id):
    db_settings = get_notification_settings(db, user_id)
    if not db_settings:
        raise Exception("Notification settings for user not found")
    trigger = db.query(models.CustomTrigger).filter(
        models.CustomTrigger.id == trigger_id,
        models.CustomTrigger.notification_setting_id == db_settings.id
    ).first()
    if not trigger:
        raise Exception("Custom trigger not found")
    db.delete(trigger)
    db.commit()
    return trigger
