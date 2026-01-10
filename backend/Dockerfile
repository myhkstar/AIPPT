# Use Python 3.10 slim as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project configuration files from root
COPY pyproject.toml ./

# Install dependencies using a mirror for speed
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ \
    gunicorn \
    flask \
    flask-cors \
    google-genai \
    pydantic \
    pillow \
    python-pptx \
    python-dotenv \
    reportlab \
    werkzeug \
    markitdown \
    openai \
    firebase-admin \
    PyJWT

# Copy backend code
COPY backend/ ./backend/

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV FLASK_APP=app.py
ENV PORT=8080

# Expose port (Cloud Run uses $PORT)
EXPOSE 8080

# Start application using gunicorn for production
CMD ["gunicorn", "--chdir", "/app/backend", "--bind", "0.0.0.0:8080", "--timeout", "120", "--workers", "2", "app:app"]
