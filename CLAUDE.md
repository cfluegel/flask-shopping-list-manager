# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask-based grocery shopping list manager with:
- User authentication (Flask-Login for web, JWT for API)
- Shopping lists private to creators, shareable via GUID links
- List items with checkbox, quantity, and name (checked items show strikethrough)
- Two user roles: administrators and regular users
- Default admin account: `admin` / `admin123`
- Admin capabilities: user management (CRUD), view/delete all users' lists
- Deleting a user cascade-deletes their lists
- REST API at `/api/v1/` with JWT authentication
- Progressive Web App (PWA) at `/pwa/` with offline support
- Soft delete with trash/restore for lists and items
- Optimistic locking (version field) for concurrent edit detection
- ESC/POS thermal receipt printer support (optional)
- Docker deployment with optional Traefik reverse proxy

## Development Commands

### Run the Application
```bash
python run.py
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FLASK_CONFIG` | `config.Config` | Config class (`config.DevelopmentConfig`, `config.ProductionConfig`, `config.TestingConfig`) |
| `SECRET_KEY` | `dev-secret` | Flask session secret (**must change in production**) |
| `JWT_SECRET_KEY` | `jwt-dev-secret-...` | JWT signing secret (**must change in production**) |
| `DATABASE_URL` | `sqlite:///app.db` | Database connection string |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `RATELIMIT_STORAGE_URL` | `memory://` | Rate-limit backend (`redis://...` in Docker) |
| `PRINTER_ENABLED` | `false` | Enable ESC/POS receipt printing |
| `PRINTER_HOST` | `192.168.1.119` | Printer IP address |
| `PRINTER_PORT` | `9100` | Printer TCP port |

### Database Management
```bash
flask db migrate -m "Description of changes"
flask db upgrade
flask db downgrade
```

### Testing
```bash
pytest
```

518 tests across 10 test files. Testing uses in-memory SQLite (`config.TestingConfig`).

## Architecture

### Application Structure

Flask application factory pattern with blueprints:

- **Application Factory** (`app/__init__.py`): `create_app(config_object)` initializes Flask, extensions (SQLAlchemy, Flask-Migrate, Flask-Login, Flask-JWT-Extended, Flask-CORS, Flask-Limiter), and registers blueprints
- **Extensions** (`app/extensions.py`): Centralized extension initialization
- **Configuration** (`config.py`): Config, DevelopmentConfig, ProductionConfig, TestingConfig

### Blueprints

1. **Main Blueprint** (`app/main/`): Server-rendered web UI with Jinja2 templates
   - Login view: `main.login` (also `login_manager.login_view`)
   - Routes in `app/main/routes.py`, forms in `app/main/forms.py`
   - Templates in `app/main/templates/`

2. **API Blueprint** (`app/api/`): REST API at `/api/v1/` with JWT authentication
   - Sub-modules: `auth.py`, `lists.py`, `items.py`, `shared.py`, `users.py`, `admin.py`
   - Marshmallow schemas for validation (`app/api/schemas.py`)
   - Custom decorators (`app/api/decorators.py`)
   - Global error handlers (`app/api/errors.py`) — catches ALL HTTP errors app-wide

3. **PWA Blueprint** (`app/pwa/`): Progressive Web App SPA shell
   - Serves SPA shell via Jinja, JS handles routing via hash-based router
   - Static assets in `app/static/pwa/` (JS modules, CSS, icons, service worker, manifest)

### Services

- **PrinterService** (`app/services/printer_service.py`): ESC/POS thermal printer integration via network/TCP

### Database Models (`app/models.py`)

**User**: `id`, `username`, `email`, `password_hash`, `is_admin`, `created_at`
- Relationship: `shopping_lists` (cascade delete)

**ShoppingList**: `id`, `guid`, `title`, `user_id`, `is_shared`, `version`, `created_at`, `updated_at`, `deleted_at`
- Soft delete: `soft_delete()`, `restore()`, class methods `active()`, `deleted()`
- Optimistic locking: `check_version()`, `increment_version()`
- Relationship: `items` (cascade delete, ordered by `order_index`)

**ShoppingListItem**: `id`, `shopping_list_id`, `name`, `quantity`, `is_checked`, `order_index`, `version`, `created_at`, `deleted_at`
- Same soft delete and optimistic locking methods as ShoppingList

**RevokedToken**: `id`, `jti`, `token_type`, `user_id`, `revoked_at`, `expires_at`
- JWT blacklist for logout support

### Authentication

- **Web UI**: Flask-Login session-based auth, `@login_required` decorator
- **API**: JWT via Flask-JWT-Extended, `@jwt_required()` decorator
  - Access tokens (30 min), refresh tokens (30 days)
  - Token blacklisting on logout

### API Response Format
```json
{"success": true, "data": { ... }}
{"success": false, "error": "...", "message": "..."}
```

## Testing

518 tests in 10 files:

| File | Tests | Focus |
|---|---|---|
| `test_auth.py` | 25 | JWT auth (register, login, refresh, logout) |
| `test_models.py` | 41 | Database models |
| `test_lists.py` | 30 | Shopping list CRUD |
| `test_items.py` | 46 | Item CRUD, toggle, reorder |
| `test_admin.py` | 44 | Admin endpoints |
| `test_permissions.py` | 29 | Authorization & access control |
| `test_sharing.py` | 24 | Shared list public access |
| `test_optimistic_locking.py` | 21 | Version control & conflicts |
| `test_soft_delete.py` | 60 | Trash & restore |
| `test_pwa.py` | 197 | PWA routes, views, service worker |

Fixtures in `tests/conftest.py` use `scope='function'`. JWT auth headers: `create_access_token(identity=str(user.id))`.

## Design

- **Light theme**: Orange and pastel tones
- **Dark theme**: Dark blue base color
- Responsive design (mobile-first)
- PWA: installable, offline-capable via service worker

## Language

Application UI is in German (messages, form labels, flash notifications).
