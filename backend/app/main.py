"""
Main application file for the CCT Backend.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import settings
from app.config.database import engine, Base
from app.routes import device_routes, temperature_routes, settings_routes, user_routes, notification_routes

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="Backend API for Connected Cooking Thermometer (CCT) devices"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    device_routes.router,
    prefix=f"/api/{settings.API_VERSION}",
)
app.include_router(
    temperature_routes.router,
    prefix=f"/api/{settings.API_VERSION}",
)
app.include_router(
    settings_routes.router,
    prefix=f"/api/{settings.API_VERSION}",
)
app.include_router(
    user_routes.router,
    prefix=f"/api/{settings.API_VERSION}",
)
app.include_router(
    notification_routes.router,
    prefix=f"/api/{settings.API_VERSION}",
)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.API_VERSION,
        "status": "running"
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
