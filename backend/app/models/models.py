"""
Database models for the CCT Backend application.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel

Base = declarative_base()

# Association table for user-device relationship
user_device_association = Table(
    'user_device_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('device_id', Integer, ForeignKey('cct_devices.id'))
)

class User(Base):
    """User model representing CCT device owners."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    devices = relationship("CCTDevice", secondary=user_device_association, back_populates="owners")
    notifications = relationship("Notification", back_populates="user")
    notification_settings = relationship("NotificationSetting", back_populates="user")

class CCTDevice(Base):
    """CCT Device model representing physical cooking thermometer devices."""
    __tablename__ = "cct_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)  # Unique identifier for the device
    name = Column(String, nullable=True)  # User-friendly name
    model = Column(String)
    firmware_version = Column(String)
    is_active = Column(Boolean, default=True)
    last_connected = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owners = relationship("User", secondary=user_device_association, back_populates="devices")
    probes = relationship("Probe", back_populates="device")
    temperature_readings = relationship("TemperatureReading", back_populates="device")
    target_temperatures = relationship("TargetTemperature", back_populates="device")

class APIKey(Base):
    """API Key model for device authentication."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    device_id = Column(Integer, ForeignKey("cct_devices.id"), nullable=False)  # <-- updated line
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)

    # Relationship (optional, for ORM convenience)
    device = relationship("CCTDevice")

class Probe(Base):
    """Probe model representing temperature probes connected to CCT devices."""
    __tablename__ = "probes"
    
    id = Column(Integer, primary_key=True, index=True)
    probe_id = Column(String, unique=True, index=True)  # Unique identifier for the probe
    name = Column(String, nullable=True)  # User-friendly name
    model = Column(String)
    is_connected = Column(Boolean, default=False)
    last_connected = Column(DateTime, nullable=True)
    device_id = Column(Integer, ForeignKey("cct_devices.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    device = relationship("CCTDevice", back_populates="probes")
    temperature_readings = relationship("TemperatureReading", back_populates="probe")

class TemperatureReading(Base):
    """Temperature reading model for storing temperature data from probes."""
    __tablename__ = "temperature_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float)  # Temperature in Celsius
    timestamp = Column(DateTime, default=datetime.utcnow)
    device_id = Column(Integer, ForeignKey("cct_devices.id"))
    probe_id = Column(Integer, ForeignKey("probes.id"))
    is_average = Column(Boolean, default=False)  # Flag for average readings
    
    # Relationships
    device = relationship("CCTDevice", back_populates="temperature_readings")
    probe = relationship("Probe", back_populates="temperature_readings")

class TargetTemperature(Base):
    """Target temperature model for storing temperature settings."""
    __tablename__ = "target_temperatures"
    
    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float)  # Target temperature in Celsius
    timestamp = Column(DateTime, default=datetime.utcnow)
    device_id = Column(Integer, ForeignKey("cct_devices.id"))
    set_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    device = relationship("CCTDevice", back_populates="target_temperatures")
    set_by_user = relationship("User")

class NotificationSetting(Base):
    """Notification settings model for user preferences."""
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    max_temp_threshold = Column(Float, nullable=True)  # Maximum temperature threshold
    min_temp_threshold = Column(Float, nullable=True)  # Minimum temperature threshold
    connection_alerts = Column(Boolean, default=True)  # Alert on connection issues
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notification_settings")
    custom_triggers = relationship("CustomTrigger", back_populates="notification_setting")

class CustomTrigger(Base):
    """Custom trigger model for user-defined notification triggers."""
    __tablename__ = "custom_triggers"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_setting_id = Column(Integer, ForeignKey("notification_settings.id"))
    name = Column(String)
    condition_type = Column(String)  # e.g., "above", "below", "equal"
    threshold_value = Column(Float)
    device_id = Column(Integer, ForeignKey("cct_devices.id"), nullable=True)
    probe_id = Column(Integer, ForeignKey("probes.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notification_setting = relationship("NotificationSetting", back_populates="custom_triggers")

class Notification(Base):
    """Notification model for storing sent notifications."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(String)
    notification_type = Column(String)  # e.g., "temperature_alert", "connection_lost"
    channel = Column(String)  # e.g., "email", "sms", "push"
    is_read = Column(Boolean, default=False)
    device_id = Column(Integer, ForeignKey("cct_devices.id"), nullable=True)
    probe_id = Column(Integer, ForeignKey("probes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
