# Deployment Guide - Flask Grocery Shopping List

This guide covers different deployment options for the Flask Grocery Shopping List application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Production Deployment with Script](#production-deployment-with-script)
3. [Docker Deployment](#docker-deployment)
4. [Manual Production Deployment](#manual-production-deployment)
5. [Reverse Proxy Setup (Nginx)](#reverse-proxy-setup-nginx)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Monitoring & Logging](#monitoring--logging)

---

## Prerequisites

### Required Software
- Python 3.11+
- PostgreSQL 13+ (recommended) or MySQL 8+ or SQLite (development only)
- Redis 6+ (for production rate limiting)
- Nginx (optional, for reverse proxy)

### Required Environment Variables

Generate secure secret keys:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Required variables:
- `SECRET_KEY` - Flask session secret
- `JWT_SECRET_KEY` - JWT token secret
- `CORS_ORIGINS` - Comma-separated list of allowed domains
- `DATABASE_URL` - Database connection string

---

## Production Deployment with Script

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/flask-grocery-shopping-list.git
cd flask-grocery-shopping-list
```

### 2. Run Production Start Script

The `start-production.sh` script automates the entire setup process:

```bash
chmod +x start-production.sh
./start-production.sh
```

**What the script does:**
- Creates `.env` file with generated secrets
- Sets up virtual environment
- Installs dependencies
- Runs database migrations
- Initializes database with default admin user
- Starts Gunicorn with production settings

### 3. Configure Environment

Edit the generated `.env` file:

```bash
nano .env
```

**Important settings to change:**
```env
SECRET_KEY=<generated-secret>
JWT_SECRET_KEY=<generated-jwt-secret>
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
DATABASE_URL=postgresql://user:password@localhost/grocery_db
RATELIMIT_STORAGE_URL=redis://localhost:6379/0
```

### 4. Restart the Application

```bash
./start-production.sh
```

**Default Configuration:**
- Host: `0.0.0.0`
- Port: `8000`
- Workers: `4`
- Threads per worker: `2`

---

## Docker Deployment

### 1. Setup Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and set your values:

```bash
nano .env
```

### 2. Build and Start Services

Start all services (Flask app, PostgreSQL, Redis):

```bash
docker-compose up -d
```

**Services included:**
- `app` - Flask application (port 8000)
- `db` - PostgreSQL database
- `redis` - Redis for rate limiting

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
```

### 4. Stop Services

```bash
docker-compose down
```

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/flask-grocery-shopping-list/issues
