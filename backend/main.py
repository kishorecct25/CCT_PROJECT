"""
Entry point for the CCT Backend application.
"""
import os
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port,
        reload=False
    )
