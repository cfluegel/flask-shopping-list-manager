# Deployment Guide

This document covers every supported way to run the Grocery Shopping List
application in production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Lightweight Docker (SQLite)](#lightweight-docker-sqlite)
4. [Docker with Traefik (HTTPS)](#docker-with-traefik-https)
5. [Manual Deployment](#manual-deployment)
6. [Database Setup](#database-setup)
7. [Security Checklist](#security-checklist)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Backup and Restore](#backup-and-restore)
10. [Upgrading](#upgrading)

---

## Prerequisites

| Software | Minimum Version | Notes |
|---|---|---|
| Docker + Compose | 24.0 / v2 | `docker compose version` |
| Python | 3.11 | Only needed for manual deployment |
| PostgreSQL | 13 | Provided by the Docker stack |
| Redis | 6 | Provided by the Docker stack |

---

## Docker Deployment

This is the recommended approach. The stack includes PostgreSQL, Redis, and the
Flask application.

### 1. Clone and Configure

```bash
git clone https://github.com/yourusername/flask-grocery-shopping-list.git
cd flask-grocery-shopping-list
cp .env.example .env
```

Edit `.env` and set **at least** these values:

```bash
# Generate two different keys
python3 -c "import secrets; print(secrets.token_hex(32))"
```

```env
SECRET_KEY=<paste first key>
JWT_SECRET_KEY=<paste second key>
DB_PASSWORD=<strong database password>
```

### 2. Start Services

```bash
docker compose up -d
```

### 3. Verify

```bash
# Check all containers are running
docker compose ps

# Follow application logs
docker compose logs -f app

# Test the health endpoint
curl http://localhost:8000/api/status
```

The application is now available at `http://localhost:8000`.
Default login: **admin** / **admin123**.

### 4. Stop Services

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop containers AND delete volumes (data loss!)
```

---

## Lightweight Docker (SQLite)

A single-container alternative that uses SQLite instead of PostgreSQL and
in-memory rate limiting instead of Redis. Choose this when:

- You are the only user (or have very few users)
- You want a quick evaluation without setting up a database server
- You are running on a resource-constrained device (e.g. Raspberry Pi)

### 1. Configure

```bash
cp examples/env-sqlite.example .env
```

Edit `.env` and set **at least** `SECRET_KEY` and `JWT_SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Start

```bash
docker compose -f examples/compose-sqlite.yaml up -d
```

The application is available at `http://localhost:8000`.
Default login: **admin** / **admin123**.

### 3. Limitations

- **SQLite** does not handle concurrent writes well. Under heavy load, requests
  may fail with `database is locked` errors.
- **Rate limiting** uses in-memory storage (`memory://`), which resets on every
  container restart and does not share state across workers. The env example
  sets `GUNICORN_WORKERS=2` and `GUNICORN_THREADS=1` to reduce concurrency
  issues.
- **No Traefik** labels are included. Place your own reverse proxy in front of
  the container if you need HTTPS.

### 4. Backup

The SQLite database is stored in the `app_instance` Docker volume. Back it up
with:

```bash
docker compose -f examples/compose-sqlite.yaml exec app \
    cp /app/instance/app.db /app/instance/app.db.bak
# Or copy the file from the volume to the host:
docker cp grocery-app:/app/instance/app.db ./backup_$(date +%F).db
```

### 5. Migrating to PostgreSQL

When you outgrow SQLite, switch to the full stack:

1. Export your data (or start fresh).
2. Copy `.env.example` to `.env` and configure PostgreSQL credentials.
3. Run `docker compose up -d` (uses `compose.yaml` with PostgreSQL + Redis).

---

## Docker with Traefik (HTTPS)

Traefik v3 is included as an optional Compose profile. It provides automatic
Let's Encrypt HTTPS certificates and HTTP-to-HTTPS redirect.

### 1. Configure

Set the following in `.env`:

```env
DOMAIN=grocery.example.com
ACME_EMAIL=you@example.com
```

Ensure DNS for `grocery.example.com` points to your server and ports 80/443 are
open.

### 2. Start with Traefik Profile

```bash
docker compose --profile with-traefik up -d
```

### 3. How It Works

- Traefik reads Docker labels from the `app` service to create routing rules.
- All HTTP traffic on port 80 is redirected to HTTPS on port 443.
- Certificates are obtained via HTTP-01 challenge and stored in the
  `letsencrypt_data` volume.
- The Traefik dashboard is disabled by default. Enable it with
  `TRAEFIK_DASHBOARD=true` in `.env` (accessible on port 8080).

### 4. Remove Direct Port Exposure

When Traefik handles all traffic you may want to stop exposing port 8000
directly. Comment out or remove the `ports` section from the `app` service in
`compose.yaml`:

```yaml
    # ports:
    #   - "${APP_PORT:-8000}:8000"
```

The app is still reachable by Traefik through the Docker network.

---

## Manual Deployment

Use this when you cannot or do not want to run Docker.

### 1. Install System Dependencies

```bash
# Debian / Ubuntu
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv libpq-dev
```

### 2. Set Up the Application

```bash
cd flask-grocery-shopping-list
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env - set SECRET_KEY, JWT_SECRET_KEY, DATABASE_URL, etc.
```

For a manually-managed PostgreSQL instance:

```env
DATABASE_URL=postgresql://grocery_user:strongpassword@localhost:5432/grocery_db
RATELIMIT_STORAGE_URL=redis://localhost:6379/0
```

### 4. Run Migrations and Initialize

```bash
export $(grep -v '^#' .env | xargs)
flask db upgrade
flask init-db
```

### 5. Start the Server

The included `start-production.sh` script automates virtual-environment setup,
migrations, and Gunicorn launch:

```bash
chmod +x start-production.sh
./start-production.sh
```

### 6. systemd Service (optional)

Create `/etc/systemd/system/grocery-list.service`:

```ini
[Unit]
Description=Grocery Shopping List (Gunicorn)
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/flask-grocery-shopping-list
EnvironmentFile=/opt/flask-grocery-shopping-list/.env
ExecStart=/opt/flask-grocery-shopping-list/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 --threads 2 --timeout 60 \
    --access-logfile /opt/flask-grocery-shopping-list/logs/access.log \
    --error-logfile /opt/flask-grocery-shopping-list/logs/error.log \
    "app:create_app('config.ProductionConfig')"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now grocery-list
```

---

## Database Setup

### Using Docker (default)

PostgreSQL is configured automatically by Compose. Credentials come from
`DB_USER`, `DB_PASSWORD`, and `DB_NAME` in `.env`.

### External PostgreSQL

```sql
CREATE USER grocery_user WITH PASSWORD 'strongpassword';
CREATE DATABASE grocery_db OWNER grocery_user;
```

Set in `.env`:

```env
DATABASE_URL=postgresql://grocery_user:strongpassword@db-host:5432/grocery_db
```

### Migrations

Migrations are applied automatically when the Docker container starts
(`flask db upgrade` in the Dockerfile CMD). For manual deployments:

```bash
flask db upgrade        # apply pending migrations
flask db downgrade      # roll back one migration
flask db current        # show current migration revision
```

---

## Security Checklist

Before exposing the application to the internet, verify:

- [ ] `SECRET_KEY` is a unique, random hex string (not `dev-secret`)
- [ ] `JWT_SECRET_KEY` is a unique, random hex string
- [ ] `DB_PASSWORD` has been changed from the default
- [ ] `CORS_ORIGINS` is set to your actual domain(s)
- [ ] Default admin password (`admin123`) has been changed in the UI
- [ ] HTTPS is enabled (Traefik or external reverse proxy)
- [ ] Docker socket is mounted read-only (`:ro`) for Traefik
- [ ] Traefik dashboard is disabled or protected in production
- [ ] Database port (5432) is **not** published to the host

---

## Monitoring and Logging

### Log Locations

| Log | Docker path | Host volume |
|---|---|---|
| Application (Gunicorn access) | `/app/logs/access.log` | `app_logs` volume |
| Application (Gunicorn error) | `/app/logs/error.log` | `app_logs` volume |
| PostgreSQL | Docker stdout | `docker compose logs db` |
| Redis | Docker stdout | `docker compose logs redis` |

### Health Endpoint

```bash
curl http://localhost:8000/api/status
```

Returns `200 OK` with JSON status when the application is healthy.
This endpoint is exempt from rate limiting to support Docker healthchecks.

### Sentry Integration (optional)

Set `SENTRY_DSN` in `.env` to send errors to Sentry. The application already
includes Sentry support when the DSN is configured.

---

## Backup and Restore

### Database Backup

```bash
# From the host
docker compose exec db pg_dump -U grocery_user grocery_db > backup_$(date +%F).sql

# Or from an external machine
pg_dump -h db-host -U grocery_user grocery_db > backup.sql
```

### Database Restore

```bash
# Drop and recreate the database, then restore
docker compose exec -T db psql -U grocery_user -d grocery_db < backup.sql
```

### Volume Backup

```bash
# Stop services first to guarantee consistency
docker compose down
docker run --rm -v flask-grocery-shopping-list_postgres_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/postgres_data.tar.gz -C /data .
docker compose up -d
```

---

## Upgrading

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild the image
docker compose build

# 3. Apply database migrations and restart
docker compose up -d
```

The container entrypoint runs `flask db upgrade` automatically on start, so
migrations are applied each time the container boots.

For manual deployments:

```bash
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart grocery-list
```
