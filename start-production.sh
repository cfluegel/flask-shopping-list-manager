#!/bin/bash

# Production Start Script for Flask Grocery Shopping List Application
# This script starts the application in production mode with proper configuration

set -e  # Exit on error

echo "=========================================="
echo "Flask Grocery Shopping List - Production"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to generate random secret
generate_secret() {
    python3 -c "import secrets; print(secrets.token_hex(32))"
}

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"

    # Generate secrets
    SECRET_KEY=$(generate_secret)
    JWT_SECRET_KEY=$(generate_secret)

    # Create .env file
    cat > .env << EOF
# Flask Configuration
FLASK_CONFIG=config.ProductionConfig
FLASK_DEBUG=0

# Security - CHANGE THESE IN PRODUCTION!
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# Database Configuration
# For SQLite (development/testing):
DATABASE_URL=sqlite:///app.db
# For PostgreSQL (production):
# DATABASE_URL=postgresql://username:password@localhost:5432/grocery_db
# For MySQL (production):
# DATABASE_URL=mysql://username:password@localhost:3306/grocery_db

# CORS Configuration - Comma-separated list of allowed origins
# Example: CORS_ORIGINS=https://example.com,https://www.example.com
CORS_ORIGINS=https://your-domain.com

# Rate Limiting Storage
# For development/testing (in-memory):
RATELIMIT_STORAGE_URL=memory://
# For production (Redis):
# RATELIMIT_STORAGE_URL=redis://localhost:6379/0

# Server Configuration
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=8000

# Gunicorn Workers
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=60

# Optional: Sentry for Error Tracking
# SENTRY_DSN=https://xxxxx@sentry.io/123456
EOF

    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file and configure production settings!${NC}"
    echo -e "${YELLOW}   Especially: CORS_ORIGINS, DATABASE_URL, and RATELIMIT_STORAGE_URL${NC}"
    echo ""
fi

# Load environment variables
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
    echo ""
fi

# Validate required environment variables
echo "🔍 Validating configuration..."

if [ "${SECRET_KEY}" = "dev-secret" ]; then
    echo -e "${RED}✗ ERROR: SECRET_KEY must be changed from default!${NC}"
    echo "  Generate new secret: python3 -c 'import secrets; print(secrets.token_hex(32))'"
    exit 1
fi

if [ "${JWT_SECRET_KEY}" = "jwt-dev-secret-change-in-production" ]; then
    echo -e "${RED}✗ ERROR: JWT_SECRET_KEY must be changed from default!${NC}"
    echo "  Generate new secret: python3 -c 'import secrets; print(secrets.token_hex(32))'"
    exit 1
fi

if [ -z "${CORS_ORIGINS}" ]; then
    echo -e "${YELLOW}⚠️  WARNING: CORS_ORIGINS is not set. All origins will be blocked.${NC}"
fi

echo -e "${GREEN}✓ Configuration valid${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install/update dependencies
echo "📦 Installing/updating dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p instance
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Run database migrations
echo "🗄️  Running database migrations..."
flask db upgrade
echo -e "${GREEN}✓ Database migrations completed${NC}"
echo ""

# Initialize database with default admin user
echo "👤 Initializing database (if needed)..."
flask init-db || true
echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

# Check Gunicorn configuration
WORKERS=${GUNICORN_WORKERS:-4}
THREADS=${GUNICORN_THREADS:-2}
TIMEOUT=${GUNICORN_TIMEOUT:-60}
PORT=${FLASK_RUN_PORT:-8000}

echo "=========================================="
echo "🚀 Starting Production Server"
echo "=========================================="
echo "  Config:     ${FLASK_CONFIG}"
echo "  Host:       ${FLASK_RUN_HOST:-0.0.0.0}"
echo "  Port:       ${PORT}"
echo "  Workers:    ${WORKERS}"
echo "  Threads:    ${THREADS}"
echo "  Timeout:    ${TIMEOUT}s"
echo "=========================================="
echo ""

# Start Gunicorn
gunicorn \
    --bind ${FLASK_RUN_HOST:-0.0.0.0}:${PORT} \
    --workers ${WORKERS} \
    --threads ${THREADS} \
    --timeout ${TIMEOUT} \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    --capture-output \
    "app:create_app('${FLASK_CONFIG}')"
