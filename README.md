# Grocery Shopping List Manager

A self-hosted grocery shopping list application built with Flask. Manage your
shopping lists from any device, share them with others via a link, and
optionally print them on an ESC/POS thermal receipt printer.

## Features

- **User accounts** with admin and regular roles
- **Private shopping lists** visible only to their creator
- **Shared lists** via unique GUID links (no login required to view)
- **Real-time editing** -- add, check off, and reorder items without page reloads
- **Soft-delete / trash** with automatic cleanup
- **Dark and light themes** (dark-blue / orange-pastel)
- **Responsive UI** for desktop and mobile
- **REST API** (`/api/v1/`) with JWT authentication
- **ESC/POS receipt printer** support (optional)
- **Docker deployment** with optional Traefik v3 reverse proxy for HTTPS

## Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/flask-grocery-shopping-list.git
cd flask-grocery-shopping-list

# 2. Create your environment file
cp .env.example .env

# 3. Generate secret keys and paste them into .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # -> SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"   # -> JWT_SECRET_KEY

# 4. Start the stack
docker compose up -d

# 5. Open http://localhost:8000
#    Default login: admin / admin123
```

## Lightweight Docker (SQLite)

If you don't need PostgreSQL or Redis, a single-container setup using SQLite is
available. This is ideal for personal use or quick evaluation.

```bash
# 1. Create your environment file
cp examples/env-sqlite.example .env

# 2. Generate secret keys and paste them into .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # -> SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"   # -> JWT_SECRET_KEY

# 3. Start the container
docker compose -f examples/compose-sqlite.yaml up -d

# 4. Open http://localhost:8000
#    Default login: admin / admin123
```

> **Note:** This variant stores data in a SQLite file and uses in-memory rate
> limiting. It is not recommended for high-traffic or multi-user deployments.
> For production use, see the full Docker stack above.

## With Traefik (HTTPS)

Set your domain and ACME email in `.env`:

```env
DOMAIN=grocery.example.com
ACME_EMAIL=you@example.com
```

Then start with the Traefik profile:

```bash
docker compose --profile with-traefik up -d
```

Traefik will automatically obtain a Let's Encrypt certificate and redirect
HTTP to HTTPS. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for details.

## Manual Setup (without Docker)

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations and create default admin
flask db upgrade
flask init-db

# Development server
python run.py

# Production server (Gunicorn)
chmod +x start-production.sh
./start-production.sh
```

## Configuration Reference

All settings are read from environment variables. The full list with defaults
is in [`.env.example`](.env.example). Key variables:

| Variable | Default | Description |
|---|---|---|
| `FLASK_CONFIG` | `config.ProductionConfig` | Config class to load |
| `SECRET_KEY` | `dev-secret` | Flask session secret (**must change**) |
| `JWT_SECRET_KEY` | (dev default) | JWT signing secret (**must change**) |
| `DATABASE_URL` | `sqlite:///app.db` | Database connection string |
| `DB_USER` / `DB_PASSWORD` / `DB_NAME` | `grocery_user` / `changeme` / `grocery_db` | PostgreSQL credentials (Docker) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `RATELIMIT_STORAGE_URL` | `memory://` | Rate-limit backend (`redis://redis:6379/0` in Docker) |
| `APP_PORT` | `8000` | Host port mapped to the container |
| `GUNICORN_WORKERS` | `4` | Gunicorn worker processes |
| `DOMAIN` | `localhost` | FQDN for Traefik routing labels |
| `ACME_EMAIL` | `you@example.com` | Let's Encrypt notification email |
| `PRINTER_ENABLED` | `false` | Enable ESC/POS receipt printing |

## CLI Commands

Run inside the container (`docker compose exec app flask <command>`) or in
your activated virtual environment.

| Command | Description |
|---|---|
| `flask init-db` | Create tables and default admin user |
| `flask create-admin <user> <email> <pw>` | Create a new admin user |
| `flask create-user <user> <email> <pw>` | Create a new regular user |
| `flask list-users` | List all users |
| `flask stats` | Show application statistics |
| `flask cleanup-trash [--days N] [--dry-run]` | Permanently delete trashed items older than N days |
| `flask trash-stats` | Show detailed trash statistics |

## API Documentation

The REST API is available at `/api/v1/`. Interactive Swagger documentation is
served at `/api/v1/docs` when the application is running.

A static reference is available in
[docs/API_DOCUMENTATION_EN.md](docs/API_DOCUMENTATION_EN.md).

## Project Structure

```
flask-grocery-shopping-list/
├── app/
│   ├── api/              # REST API (v1) with JWT auth
│   ├── main/             # Web UI blueprint, templates, forms
│   ├── services/         # Business logic (printer service, etc.)
│   ├── cli.py            # Flask CLI commands
│   ├── extensions.py     # Flask extensions (db, migrate, login)
│   ├── models.py         # SQLAlchemy models
│   └── utils.py          # Shared utilities
├── docs/                 # Deployment guide, API docs
├── examples/             # Lightweight compose variants (SQLite)
├── migrations/           # Alembic database migrations
├── tests/                # pytest test suite
├── compose.yaml          # Docker Compose (Traefik v3)
├── Dockerfile            # Multi-stage production image
├── config.py             # App configuration classes
├── requirements.txt      # Python dependencies
├── run.py                # Development entry point
└── start-production.sh   # Bare-metal Gunicorn launcher
```

## License

See [LICENSE](LICENSE) for details.
