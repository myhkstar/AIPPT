# Use Python 3.10 slim as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

# Copy project configuration files from root
# Note: When building from root context, these paths are correct
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN uv sync --frozen

# Copy backend code
COPY backend/ ./backend/

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=backend/app.py
ENV PORT=8080

# Expose port (Cloud Run uses $PORT)
EXPOSE 8080

# Start application using gunicorn for production
# We need to add gunicorn to dependencies if not there
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "--workers", "2", "backend.app:app"]
