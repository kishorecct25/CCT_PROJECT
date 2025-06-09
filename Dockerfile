FROM python:3.10-slim

# Install Nginx
RUN apt-get update && apt-get install -y nginx \
 && rm /etc/nginx/sites-enabled/default

# Set working directory
WORKDIR /app

# Copy apps and config
COPY backend/ ./backend
COPY webapp/ ./webapp
COPY run_combined.py .
COPY requirements.txt .
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Install Python dependencies
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Set Python path and environment variables
ENV PYTHONPATH=/app/backend
ENV BACKEND_API_URL="http://localhost:8000/api/v1"

# Expose only the Nginx-handled port
EXPOSE 8000

# Launch both apps and Nginx
CMD ["python", "run_combined.py"]