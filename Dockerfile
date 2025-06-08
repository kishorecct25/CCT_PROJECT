FROM python:3.10-slim

WORKDIR /app

COPY backend/ ./backend
COPY webapp/ ./webapp
COPY run_combined.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Set PYTHONPATH for FastAPI to find app module
ENV PYTHONPATH=/app/backend

# ✅ Set environment variable for your Flask webapp
ENV BACKEND_API_URL="http://localhost:8000/api/v1"

# Expose both services
EXPOSE 8000
EXPOSE 3000

CMD ["python", "run_combined.py"]
