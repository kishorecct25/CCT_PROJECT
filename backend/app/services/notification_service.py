"""
Notification service for the CCT Backend application.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models import models, schemas
from app.config.config import settings

class NotificationChannel:
    """Base class for notification channels."""
    
    def send_notification(self, user: models.User, title: str, message: str, **kwargs) -> bool:
        """
        Send a notification to a user.
        
        Args:
            user: User to send notification to
            title: Notification title
            message: Notification message
            **kwargs: Additional channel-specific parameters
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement send_notification")

class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""
    
    def send_notification(self, user: models.User, title: str, message: str, **kwargs) -> bool:
        """
        Send an email notification to a user.
        
        Args:
            user: User to send notification to
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not settings.EMAIL_ENABLED or not user.email:
            return False
        
        # In a real implementation, this would use an email service like SMTP or a third-party API
        # For this example, we'll just log the notification
        print(f"[EMAIL] To: {user.email}, Subject: {title}, Message: {message}")
        
        return True

class SMSNotificationChannel(NotificationChannel):
    """SMS notification channel."""
    
    def send_notification(self, user: models.User, title: str, message: str, **kwargs) -> bool:
        """
        Send an SMS notification to a user.
        
        Args:
            user: User to send notification to
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not settings.SMS_ENABLED or not user.phone_number:
            return False
        
        # In a real implementation, this would use an SMS service like Twilio
        # For this example, we'll just log the notification
        print(f"[SMS] To: {user.phone_number}, Message: {title}: {message}")
        
        return True

class PushNotificationChannel(NotificationChannel):
    """Push notification channel."""
    
    def send_notification(self, user: models.User, title: str, message: str, **kwargs) -> bool:
        """
        Send a push notification to a user.
        
        Args:
            user: User to send notification to
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not settings.PUSH_ENABLED:
            return False
        
        # In a real implementation, this would use a push notification service like Firebase
        # For this example, we'll just log the notification
        print(f"[PUSH] To: User {user.id}, Title: {title}, Message: {message}")
        
        return True

def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    channel: str,
    device_id: Optional[int] = None,
    probe_id: Optional[int] = None
) -> models.Notification:
    """
    Create a notification record in the database.
    
    Args:
        db: Database session
        user_id: User ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        channel: Channel used for notification
        device_id: Optional device ID
        probe_id: Optional probe ID
        
    Returns:
        Created notification object
    """
    db_notification = models.Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        channel=channel,
        device_id=device_id,
        probe_id=probe_id
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    return db_notification

def send_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    device_id: Optional[int] = None,
    probe_id: Optional[int] = None
) -> Dict[str, bool]:
    """
    Send a notification to a user through all enabled channels.
    
    Args:
        db: Database session
        user_id: User ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        device_id: Optional device ID
        probe_id: Optional probe ID
        
    Returns:
        Dictionary of channel results
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    # Get notification settings
    settings = (
        db.query(models.NotificationSetting)
        .filter(models.NotificationSetting.user_id == user_id)
        .first()
    )
    
    if not settings:
        # Create default settings
        settings = models.NotificationSetting(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Initialize channels
    channels = {
        "email": EmailNotificationChannel() if settings.email_enabled else None,
        "sms": SMSNotificationChannel() if settings.sms_enabled else None,
        "push": PushNotificationChannel() if settings.push_enabled else None
    }
    
    # Send notifications through enabled channels
    results = {}
    for channel_name, channel in channels.items():
        if channel:
            success = channel.send_notification(user, title, message)
            results[channel_name] = success
            
            if success:
                # Create notification record
                create_notification(
                    db,
                    user_id,
                    title,
                    message,
                    notification_type,
                    channel_name,
                    device_id,
                    probe_id
                )
    
    return results

def check_temperature_triggers(
    db: Session,
    device_id: str,
    temperature: float,
    probe_id: Optional[str] = None,
    is_average: bool = False
) -> None:
    """
    Check if a temperature reading triggers any notifications.
    
    Args:
        db: Database session
        device_id: Device ID
        temperature: Temperature reading
        probe_id: Optional probe ID
        is_average: Whether this is an average reading
    """
    # Get device
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        return
    
    # Get probe if provided
    probe = None
    if probe_id:
        probe = db.query(models.Probe).filter(models.Probe.probe_id == probe_id).first()
    
    # Get all users associated with this device
    for owner in device.owners:
        # Get notification settings
        settings = (
            db.query(models.NotificationSetting)
            .filter(models.NotificationSetting.user_id == owner.id)
            .first()
        )
        
        if not settings:
            continue
        
        # Check max temperature threshold
        if settings.max_temp_threshold is not None and temperature > settings.max_temp_threshold:
            probe_name = f" ({probe.name})" if probe and probe.name else ""
            device_name = device.name or device.device_id
            
            title = f"High Temperature Alert"
            message = f"Temperature for {device_name}{probe_name} has exceeded the maximum threshold. Current temperature: {temperature}°F (Threshold: {settings.max_temp_threshold}°F)"
            
            send_notification(
                db,
                owner.id,
                title,
                message,
                "temperature_alert",
                device.id,
                probe.id if probe else None
            )
        
        # Check min temperature threshold
        if settings.min_temp_threshold is not None and temperature < settings.min_temp_threshold:
            probe_name = f" ({probe.name})" if probe and probe.name else ""
            device_name = device.name or device.device_id
            
            title = f"Low Temperature Alert"
            message = f"Temperature for {device_name}{probe_name} has fallen below the minimum threshold. Current temperature: {temperature}°F (Threshold: {settings.min_temp_threshold}°F)"
            
            send_notification(
                db,
                owner.id,
                title,
                message,
                "temperature_alert",
                device.id,
                probe.id if probe else None
            )
        
        # Check custom triggers
        for trigger in settings.custom_triggers:
            # Skip inactive triggers
            if not trigger.is_active:
                continue
            
            # Skip triggers for other devices
            if trigger.device_id and trigger.device_id != device.id:
                continue
            
            # Skip triggers for other probes
            if trigger.probe_id and (not probe or trigger.probe_id != probe.id):
                continue
            
            # Check condition
            triggered = False
            if trigger.condition_type == "above" and temperature > trigger.threshold_value:
                triggered = True
            elif trigger.condition_type == "below" and temperature < trigger.threshold_value:
                triggered = True
            elif trigger.condition_type == "equal" and abs(temperature - trigger.threshold_value) < 0.5:
                triggered = True
            
            if triggered:
                probe_name = f" ({probe.name})" if probe and probe.name else ""
                device_name = device.name or device.device_id
                
                title = f"Custom Temperature Alert: {trigger.name}"
                message = f"Temperature for {device_name}{probe_name} has triggered a custom alert. Current temperature: {temperature}°F (Trigger: {trigger.condition_type} {trigger.threshold_value}°F)"
                
                send_notification(
                    db,
                    owner.id,
                    title,
                    message,
                    "custom_trigger",
                    device.id,
                    probe.id if probe else None
                )

def notify_connection_lost(
    db: Session,
    device_id: str,
    probe_id: Optional[str] = None
) -> None:
    """
    Notify users that a device or probe connection has been lost.
    
    Args:
        db: Database session
        device_id: Device ID
        probe_id: Optional probe ID
    """
    # Get device
    device = db.query(models.CCTDevice).filter(models.CCTDevice.device_id == device_id).first()
    if not device:
        return
    
    # Get probe if provided
    probe = None
    if probe_id:
        probe = db.query(models.Probe).filter(models.Probe.probe_id == probe_id).first()
    
    # Get all users associated with this device
    for owner in device.owners:
        # Get notification settings
        settings = (
            db.query(models.NotificationSetting)
            .filter(models.NotificationSetting.user_id == owner.id)
            .first()
        )
        
        if not settings or not settings.connection_alerts:
            continue
        
        if probe:
            # Probe connection lost
            probe_name = probe.name or probe.probe_id
            device_name = device.name or device.device_id
            
            title = f"Probe Connection Lost"
            message = f"Connection to probe {probe_name} on device {device_name} has been lost."
            
            send_notification(
                db,
                owner.id,
                title,
                message,
                "connection_lost",
                device.id,
                probe.id
            )
        else:
            # Device connection lost
            device_name = device.name or device.device_id
            
            title = f"Device Connection Lost"
            message = f"Connection to device {device_name} has been lost."
            
            send_notification(
                db,
                owner.id,
                title,
                message,
                "connection_lost",
                device.id
            )

def check_connection_status(db: Session) -> None:
    """
    Check connection status of all devices and probes.
    
    This function should be called periodically to check if any devices or probes
    have lost connection.
    
    Args:
        db: Database session
    """
    # Get current time
    now = datetime.utcnow()
    
    # Check device connections
    devices = db.query(models.CCTDevice).filter(models.CCTDevice.is_active == True).all()
    for device in devices:
        if device.last_connected:
            time_diff = (now - device.last_connected).total_seconds()
            if time_diff > settings.CONNECTION_TIMEOUT_SECONDS:
                # Device connection lost
                notify_connection_lost(db, device.device_id)
                
                # Mark device as inactive
                device.is_active = False
                db.commit()
    
    # Check probe connections
    probes = db.query(models.Probe).filter(models.Probe.is_connected == True).all()
    for probe in probes:
        if probe.last_connected:
            time_diff = (now - probe.last_connected).total_seconds()
            if time_diff > settings.CONNECTION_TIMEOUT_SECONDS:
                # Get device
                device = db.query(models.CCTDevice).filter(models.CCTDevice.id == probe.device_id).first()
                if device:
                    # Probe connection lost
                    notify_connection_lost(db, device.device_id, probe.probe_id)
                
                # Mark probe as disconnected
                probe.is_connected = False
                db.commit()

def get_user_notifications(
    db: Session,
    user_id: int,
    limit: int = 100,
    unread_only: bool = False
) -> List[models.Notification]:
    """
    Get notifications for a user.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of notifications to return
        unread_only: Whether to return only unread notifications
        
    Returns:
        List of notification objects
    """
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(models.Notification.is_read == False)
    
    return query.order_by(models.Notification.created_at.desc()).limit(limit).all()

def mark_notification_as_read(
    db: Session,
    notification_id: int,
    user_id: int
) -> Optional[models.Notification]:
    """
    Mark a notification as read.
    
    Args:
        db: Database session
        notification_id: Notification ID
        user_id: User ID
        
    Returns:
        Updated notification object or None if not found
    """
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.user_id == user_id
        )
        .first()
    )
    
    if not notification:
        return None
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    
    return notification

def mark_all_notifications_as_read(
    db: Session,
    user_id: int
) -> int:
    """
    Mark all notifications for a user as read.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Number of notifications marked as read
    """
    result = (
        db.query(models.Notification)
        .filter(
            models.Notification.user_id == user_id,
            models.Notification.is_read == False
        )
        .update({"is_read": True})
    )
    
    db.commit()
    
    return result
