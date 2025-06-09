"""
Documentation for the CCT Backend API.

This file provides an overview of the CCT Backend API endpoints, authentication mechanisms,
and data flow for the Cloud Connected Thermometer (CCT) application.
"""

# CCT Backend API Documentation

## Overview

The CCT Backend API provides a comprehensive set of endpoints for managing CCT devices, probes,
temperature data, user accounts, and notifications. The API is built using FastAPI and follows
RESTful principles.

## Authentication

The API uses two authentication mechanisms:

1. **Device Authentication**: CCT devices authenticate using API keys provided during registration.
   API keys are passed in the `X-API-Key` header.

2. **User Authentication**: Users authenticate using JWT tokens obtained through the login endpoint.
   Tokens are passed in the `Authorization` header as a Bearer token.

## API Endpoints

### Device Management

#### Register Device
- **Endpoint**: `POST /api/v1/devices/register`
- **Authentication**: None
- **Description**: Registers a new CCT device with the cloud backend
- **Request Body**:
  ```json
  {
    "device_id": "string",
    "model": "string",
    "firmware_version": "string",
    "name": "string (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "device_id": "string",
    "api_key": "string",
    "message": "string"
  }
  ```

#### Register Probe
- **Endpoint**: `POST /api/v1/devices/{device_id}/probes/register`
- **Authentication**: Device API Key
- **Description**: Registers a new probe and associates it with a CCT device
- **Request Body**:
  ```json
  {
    "probe_id": "string",
    "model": "string",
    "name": "string (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "probe_id": "string",
    "device_id": "string",
    "message": "string"
  }
  ```

#### Get Device Probes
- **Endpoint**: `GET /api/v1/devices/{device_id}/probes`
- **Authentication**: Device API Key
- **Description**: Gets all probes associated with a device
- **Response**: Array of probe objects

#### Update Device Connection
- **Endpoint**: `PUT /api/v1/devices/{device_id}/connection`
- **Authentication**: Device API Key
- **Description**: Updates the connection status of a device
- **Query Parameters**:
  - `is_connected`: boolean (default: true)
- **Response**: Device object

#### Update Probe Connection
- **Endpoint**: `PUT /api/v1/devices/{device_id}/probes/{probe_id}/connection`
- **Authentication**: Device API Key
- **Description**: Updates the connection status of a probe
- **Query Parameters**:
  - `is_connected`: boolean (default: true)
- **Response**: Probe object

### Temperature Data

#### Update Temperature
- **Endpoint**: `POST /api/v1/temperature/update`
- **Authentication**: Device API Key
- **Description**: Updates temperature readings from a CCT device
- **Request Body**:
  ```json
  {
    "device_id": "string",
    "readings": [
      {
        "probe_id": "string (optional)",
        "temperature": "number"
      }
    ],
    "average_temperature": "number (optional)",
    "timestamp": "string (optional, ISO format)"
  }
  ```
- **Response**:
  ```json
  {
    "message": "string",
    "target_temperature": "number (optional)"
  }
  ```

#### Set Target Temperature
- **Endpoint**: `POST /api/v1/temperature/target`
- **Authentication**: Device API Key
- **Description**: Sets a target temperature for a CCT device
- **Request Body**:
  ```json
  {
    "device_id": "string",
    "temperature": "number",
    "set_by_user_id": "integer (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "message": "string",
    "temperature": "number"
  }
  ```

#### Get Temperature History
- **Endpoint**: `GET /api/v1/temperature/{device_id}/history`
- **Authentication**: Device API Key
- **Description**: Gets temperature history for a CCT device or probe
- **Query Parameters**:
  - `probe_id`: string (optional)
  - `limit`: integer (default: 100)
  - `is_average`: boolean (optional)
- **Response**: Array of temperature reading objects

#### Get Target Temperature
- **Endpoint**: `GET /api/v1/temperature/{device_id}/target`
- **Authentication**: Device API Key
- **Description**: Gets the current target temperature for a CCT device
- **Response**: Target temperature object or null

#### Calculate Average Temperature
- **Endpoint**: `GET /api/v1/temperature/{device_id}/average`
- **Authentication**: Device API Key
- **Description**: Calculates the average temperature from all connected probes
- **Response**: Average temperature (number)

### Settings Synchronization

#### Sync Device Settings
- **Endpoint**: `GET /api/v1/settings/{device_id}/sync`
- **Authentication**: Device API Key
- **Description**: Synchronizes settings for a CCT device
- **Response**: Object containing device settings

#### Update Target Temperature (Device)
- **Endpoint**: `POST /api/v1/settings/{device_id}/target`
- **Authentication**: Device API Key
- **Description**: Updates target temperature from a CCT device
- **Query Parameters**:
  - `temperature`: number
- **Response**: Target temperature object

#### Update Target Temperature (User)
- **Endpoint**: `POST /api/v1/settings/user/{device_id}/target`
- **Authentication**: User JWT Token
- **Description**: Updates target temperature from the cloud (set by a user)
- **Query Parameters**:
  - `temperature`: number
- **Response**: Target temperature object

#### Get Device Settings History
- **Endpoint**: `GET /api/v1/settings/{device_id}/history`
- **Authentication**: Device API Key
- **Description**: Gets settings history for a device
- **Query Parameters**:
  - `limit`: integer (default: 100)
- **Response**: Array of target temperature objects

### User Management

#### Register User
- **Endpoint**: `POST /api/v1/users/register`
- **Authentication**: None
- **Description**: Registers a new user in the system
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "string",
    "phone_number": "string (optional)",
    "password": "string"
  }
  ```
- **Response**: User object (without password)

#### Login
- **Endpoint**: `POST /api/v1/users/token`
- **Authentication**: None
- **Description**: Authenticates a user and returns an access token
- **Request Body** (form data):
  - `username`: string
  - `password`: string
- **Response**:
  ```json
  {
    "access_token": "string",
    "token_type": "string"
  }
  ```

#### Get Current User
- **Endpoint**: `GET /api/v1/users/me`
- **Authentication**: User JWT Token
- **Description**: Gets the current user's information
- **Response**: User object

#### Update Current User
- **Endpoint**: `PUT /api/v1/users/me`
- **Authentication**: User JWT Token
- **Description**: Updates the current user's information
- **Request Body**:
  ```json
  {
    "username": "string (optional)",
    "email": "string (optional)",
    "phone_number": "string (optional)",
    "password": "string (optional)"
  }
  ```
- **Response**: Updated user object

#### Associate Device with User
- **Endpoint**: `POST /api/v1/users/me/devices/{device_id}`
- **Authentication**: User JWT Token
- **Description**: Associates a device with the current user
- **Response**: Device object

#### Get User Devices
- **Endpoint**: `GET /api/v1/users/me/devices`
- **Authentication**: User JWT Token
- **Description**: Gets all devices associated with the current user
- **Response**: Array of device objects

#### Get Notification Settings
- **Endpoint**: `GET /api/v1/users/me/notification-settings`
- **Authentication**: User JWT Token
- **Description**: Gets notification settings for the current user
- **Response**: Notification settings object

#### Update Notification Settings
- **Endpoint**: `PUT /api/v1/users/me/notification-settings`
- **Authentication**: User JWT Token
- **Description**: Updates notification settings for the current user
- **Request Body**:
  ```json
  {
    "email_enabled": "boolean (optional)",
    "sms_enabled": "boolean (optional)",
    "push_enabled": "boolean (optional)",
    "max_temp_threshold": "number (optional)",
    "min_temp_threshold": "number (optional)",
    "connection_alerts": "boolean (optional)"
  }
  ```
- **Response**: Updated notification settings object

#### Create Custom Trigger
- **Endpoint**: `POST /api/v1/users/me/triggers`
- **Authentication**: User JWT Token
- **Description**: Creates a custom notification trigger for the current user
- **Request Body**:
  ```json
  {
    "name": "string",
    "condition_type": "string",
    "threshold_value": "number",
    "device_id": "integer (optional)",
    "probe_id": "integer (optional)",
    "is_active": "boolean (optional)",
    "notification_setting_id": "integer"
  }
  ```
- **Response**: Custom trigger object

#### Get Custom Triggers
- **Endpoint**: `GET /api/v1/users/me/triggers`
- **Authentication**: User JWT Token
- **Description**: Gets all custom triggers for the current user
- **Response**: Array of custom trigger objects

#### Update Custom Trigger
- **Endpoint**: `PUT /api/v1/users/me/triggers/{trigger_id}`
- **Authentication**: User JWT Token
- **Description**: Updates a custom trigger
- **Request Body**:
  ```json
  {
    "name": "string (optional)",
    "condition_type": "string (optional)",
    "threshold_value": "number (optional)",
    "is_active": "boolean (optional)"
  }
  ```
- **Response**: Updated custom trigger object

### Notifications

#### Get User Notifications
- **Endpoint**: `GET /api/v1/notifications/`
- **Authentication**: User JWT Token
- **Description**: Gets notifications for the current user
- **Query Parameters**:
  - `limit`: integer (default: 100)
  - `unread_only`: boolean (default: false)
- **Response**: Array of notification objects

#### Mark Notification as Read
- **Endpoint**: `PUT /api/v1/notifications/{notification_id}/read`
- **Authentication**: User JWT Token
- **Description**: Marks a notification as read
- **Response**: Updated notification object

#### Mark All Notifications as Read
- **Endpoint**: `PUT /api/v1/notifications/read-all`
- **Authentication**: User JWT Token
- **Description**: Marks all notifications for the current user as read
- **Response**:
  ```json
  {
    "message": "string"
  }
  ```

#### Send Test Notification
- **Endpoint**: `POST /api/v1/notifications/test`
- **Authentication**: User JWT Token
- **Description**: Sends a test notification to the current user
- **Query Parameters**:
  - `title`: string
  - `message`: string
- **Response**:
  ```json
  {
    "message": "string",
    "results": "object"
  }
  ```

## Data Flow

### CCT Device Workflow
1. Device registers with the cloud backend
2. Device registers and associates probes
3. Device receives temperature readings from probes via Bluetooth
4. Device calculates average temperature
5. Device transmits temperature readings to the cloud
6. Device receives updated target temperature settings from the cloud

### User Workflow
1. User registers an account
2. User associates devices with their account
3. User configures notification preferences
4. User sets temperature thresholds and custom triggers
5. User receives notifications based on temperature readings and connection status

## Error Handling

All API endpoints return appropriate HTTP status codes:
- 200: Success
- 400: Bad Request (invalid input)
- 401: Unauthorized (invalid or missing authentication)
- 404: Not Found (resource not found)
- 500: Internal Server Error

Error responses include a detail message explaining the error.

## Rate Limiting

The API implements rate limiting to prevent abuse. Clients should implement appropriate retry logic with exponential backoff.

## Deployment

The API can be deployed using Docker or directly on a server with Python 3.8+ installed. See the README.md file for deployment instructions.
