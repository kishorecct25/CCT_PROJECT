"""
Entry point for the CCT Backend application.
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))  # Match your Docker port

    uvicorn.run(
        "app.main:app",  # Correct import path for FastAPI app instance
        host="0.0.0.0",
        port=port,
        reload=False
    )
