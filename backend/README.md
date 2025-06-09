# CCT Backend - README

## Overview

This is the backend system for the Cloud Connected Thermometer (CCT) application. It provides a comprehensive API for managing CCT devices, probes, temperature data, user accounts, and notifications.

## Features

- **Device Management**: Registration and management of CCT devices and probes
- **Temperature Monitoring**: Collection, storage, and analysis of temperature data
- **User Management**: User registration, authentication, and profile management
- **Notification System**: Configurable alerts for temperature thresholds and connection issues
- **Settings Synchronization**: Synchronization of settings between devices and the cloud

## Technical Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy ORM with SQLite (configurable for other databases)
- **Authentication**: JWT tokens for users, API keys for devices
- **Notifications**: Support for email, SMS, and push notifications

## Project Structure

```
cct_backend/
├── app/
│   ├── config/         # Configuration settings
│   ├── models/         # Database models and schemas
│   ├── routes/         # API routes
│   ├── services/       # Business logic
│   ├── utils/          # Utility functions
│   └── main.py         # FastAPI application
├── tests/              # Test files
├── main.py             # Entry point
├── requirements.txt    # Dependencies
├── API_DOCUMENTATION.md # API documentation
└── README.md           # This file
```

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd cct_backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables (optional):
   Create a `.env` file in the root directory with the following variables:
   ```
   DATABASE_URL=sqlite:///./cct_backend.db
   SECRET_KEY=your-secret-key
   DEBUG=False
   ```

### Running the Application

1. Start the server:
   ```
   python main.py
   ```

2. The API will be available at `http://localhost:8000`

3. Access the interactive API documentation at `http://localhost:8000/docs`

## API Documentation

For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Development

### Database Migrations

The application uses SQLAlchemy's declarative models. When changing models, you need to:

1. Update the model definitions in `app/models/models.py`
2. Restart the application to apply changes (SQLite)

For production databases, use Alembic for migrations.

### Testing

Run tests with:
```
pytest
```

## Deployment

### Docker

A Dockerfile is provided for containerized deployment:

```
docker build -t cct-backend .
docker run -p 8000:8000 cct-backend
```

### Production Considerations

For production deployment:

1. Use a production-grade database (PostgreSQL, MySQL)
2. Set up proper authentication for notification services
3. Configure CORS settings appropriately
4. Use HTTPS with a valid SSL certificate
5. Set a strong SECRET_KEY environment variable

## License

[Specify license information]

## Contact

[Specify contact information]
