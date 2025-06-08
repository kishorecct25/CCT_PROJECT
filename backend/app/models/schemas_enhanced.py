"""
Enhanced schemas for the CCT Backend application.
Includes support for test accounts and improved device association.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class User(UserInDB):
    pass

# CCT Device schemas
class CCTDeviceBase(BaseModel):
    device_id: str
    name: Optional[str] = None
    model: str
    firmware_version: str

class CCTDeviceCreate(CCTDeviceBase):
    pass

class CCTDeviceUpdate(BaseModel):
    name: Optional[str] = None
    firmware_version: Optional[str] = None
    is_active: Optional[bool] = None

class CCTDeviceInDB(CCTDeviceBase):
    id: int
    is_active: bool
    last_connected: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CCTDevice(CCTDeviceInDB):
    pass

# Probe schemas
class ProbeBase(BaseModel):
    probe_id: str
    name: Optional[str] = None
    model: str

class ProbeCreate(ProbeBase):
    device_id: int

class ProbeUpdate(BaseModel):
    name: Optional[str] = None
    is_connected: Optional[bool] = None

class ProbeInDB(ProbeBase):
    id: int
    is_connected: bool
    last_connected: Optional[datetime] = None
    device_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Probe(ProbeInDB):
    pass

# Temperature reading schemas
class TemperatureReadingBase(BaseModel):
    temperature: float
    is_average: bool = False

class TemperatureReadingCreate(TemperatureReadingBase):
    device_id: int
    probe_id: Optional[int] = None

class TemperatureReadingInDB(TemperatureReadingBase):
    id: int
    timestamp: datetime
    device_id: int
    probe_id: Optional[int] = None

    class Config:
        orm_mode = True

class TemperatureReading(TemperatureReadingInDB):
    pass

# Target temperature schemas
class TargetTemperatureBase(BaseModel):
    temperature: float

class TargetTemperatureCreate(TargetTemperatureBase):
    device_id: int
    set_by_user_id: Optional[int] = None

class TargetTemperatureUpdate(BaseModel):
    temperature: Optional[float] = None
    is_active: Optional[bool] = None

class TargetTemperatureInDB(TargetTemperatureBase):
    id: int
    timestamp: datetime
    device_id: int
    set_by_user_id: Optional[int] = None
    is_active: bool

    class Config:
        orm_mode = True

class TargetTemperature(TargetTemperatureInDB):
    pass

# Notification setting schemas
class NotificationSettingBase(BaseModel):
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    max_temp_threshold: Optional[float] = None
    min_temp_threshold: Optional[float] = None
    connection_alerts: bool = True

class NotificationSettingCreate(NotificationSettingBase):
    user_id: int

class NotificationSettingUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    max_temp_threshold: Optional[float] = None
    min_temp_threshold: Optional[float] = None
    connection_alerts: Optional[bool] = None

class NotificationSettingInDB(NotificationSettingBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class NotificationSetting(NotificationSettingInDB):
    pass

# Custom trigger schemas
class CustomTriggerBase(BaseModel):
    name: str
    condition_type: str
    threshold_value: float
    device_id: Optional[int] = None
    probe_id: Optional[int] = None
    is_active: bool = True

class CustomTriggerCreate(CustomTriggerBase):
    notification_setting_id: int

class CustomTriggerUpdate(BaseModel):
    name: Optional[str] = None
    condition_type: Optional[str] = None
    threshold_value: Optional[float] = None
    is_active: Optional[bool] = None

class CustomTriggerInDB(CustomTriggerBase):
    id: int
    notification_setting_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CustomTrigger(CustomTriggerInDB):
    pass

# Notification schemas
class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str
    channel: str
    device_id: Optional[int] = None
    probe_id: Optional[int] = None

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

class NotificationInDB(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True

class Notification(NotificationInDB):
    pass

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Device registration schemas
class DeviceRegistrationRequest(BaseModel):
    device_id: str
    model: str
    firmware_version: str
    name: Optional[str] = None

class DeviceRegistrationResponse(BaseModel):
    device_id: str
    api_key: str
    association_token: Optional[str] = None
    message: str = "Device registered successfully"

# Probe registration schemas
class ProbeRegistrationRequest(BaseModel):
    probe_id: str
    model: str
    name: Optional[str] = None

class ProbeRegistrationResponse(BaseModel):
    probe_id: str
    device_id: str
    message: str = "Probe registered and associated with device successfully"

# Temperature update schemas
class TemperatureUpdateRequest(BaseModel):
    device_id: str
    readings: List[dict] = Field(..., description="List of temperature readings from probes")
    average_temperature: Optional[float] = None
    timestamp: Optional[datetime] = None

class TemperatureUpdateResponse(BaseModel):
    message: str = "Temperature readings received successfully"
    target_temperature: Optional[float] = None

# Target temperature update schemas
class TargetTemperatureUpdateRequest(BaseModel):
    device_id: str
    temperature: float
    set_by_user_id: Optional[int] = None

class TargetTemperatureUpdateResponse(BaseModel):
    message: str = "Target temperature updated successfully"
    temperature: float

# Device association schemas
class DeviceAssociationRequest(BaseModel):
    device_id: str
    user_id: int
    association_token: Optional[str] = None

class DeviceAssociationResponse(BaseModel):
    device_id: str
    user_id: int
    success: bool
    message: str

# Test account schemas
class TestAccountBase(BaseModel):
    name: str
    email: EmailStr
    description: Optional[str] = None
    is_active: bool = True

class TestAccountCreate(TestAccountBase):
    pass

class TestAccountUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class TestAccountInDB(TestAccountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TestAccount(TestAccountInDB):
    pass

# Device ID generation schema
class DeviceIDGenerationRequest(BaseModel):
    pass

class DeviceIDGenerationResponse(BaseModel):
    device_id: str
    message: str = "Unique device ID generated successfully"
