# Multi-stage Dockerfile for Flask Grocery Shopping List

# Stage 1: Builder
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_CONFIG=config.ProductionConfig \
    FLASK_DEBUG=0

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app/instance && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Create instance directory for SQLite database
RUN mkdir -p /app/instance

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/status', timeout=5)"

# Run database initialization and start Gunicorn
CMD ["sh", "-c", "flask db upgrade && flask init-db && gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 60 --access-logfile - --error-logfile - 'app:create_app()'"]
