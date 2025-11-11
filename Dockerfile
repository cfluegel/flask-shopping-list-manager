# Multi-stage Dockerfile for Flask Grocery Shopping List
# Optimized for production deployment

# Stage 1: Builder
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_CONFIG=config.ProductionConfig \
    FLASK_DEBUG=0 \
    PORT=8000

# Create non-root user with specific UID/GID
RUN groupadd -r -g 1000 appuser && \
    useradd -r -m -u 1000 -g appuser -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/instance /app/logs /app/migrations && \
    chown -R appuser:appuser /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Expose port (configurable via environment)
EXPOSE ${PORT}

# Health check with proper URL
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/status || exit 1

# Run database initialization and start Gunicorn with production settings
CMD ["sh", "-c", "flask db upgrade && flask init-db && gunicorn --bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS:-4} --threads ${GUNICORN_THREADS:-2} --timeout ${GUNICORN_TIMEOUT:-60} --worker-class sync --worker-tmp-dir /dev/shm --access-logfile /app/logs/access.log --error-logfile /app/logs/error.log --log-level info --capture-output 'app:create_app(\"config.ProductionConfig\")'"]
