# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask-based grocery shopping list manager with the following key requirements:
- User authentication required for all functionality except shared lists
- Shopping lists are private to creators, shareable via GUID links
- Lists contain items with: checkbox, quantity, and item name
- Checked items display with strikethrough
- Two user roles: administrators and regular users
- Default admin account: `admin` / `admin123`
- Admin capabilities: user management (CRUD), view/delete all users' lists
- Deleting a user must cascade delete their lists
- REST API planned for future mobile app access with JWT authentication

## Development Commands

### Run the Application
```bash
python run.py
```

Environment variables:
- `FLASK_CONFIG`: Config class to use (default: `config.Config`)
  - Options: `config.DevelopmentConfig`, `config.ProductionConfig`, `config.TestingConfig`
- `FLASK_RUN_HOST`: Host to bind to (default: `127.0.0.1`)
- `FLASK_RUN_PORT`: Port to bind to (default: `5000`)
- `FLASK_DEBUG`: Debug mode (default: `False`)
- `SECRET_KEY`: Flask secret key (default: `dev-secret`)
- `DATABASE_URL`: Database connection string (default: `sqlite:///app.db`)

### Database Management
```bash
# Initialize migrations (if not already done)
flask db init

# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Testing
```bash
pytest
```

Testing configuration uses in-memory SQLite database (`config.TestingConfig`).

## Architecture

### Application Structure

The application follows the Flask application factory pattern with blueprints:

- **Application Factory** (`app/__init__.py`): `create_app(config_object)` initializes Flask app, extensions (SQLAlchemy, Flask-Migrate, Flask-Login), and registers blueprints
- **Extensions** (`app/extensions.py`): Centralized initialization of Flask extensions (db, migrate, login_manager)
- **Configuration** (`config.py`): Three config classes (Config, DevelopmentConfig, ProductionConfig, TestingConfig) with environment-based settings

### Blueprints

1. **Main Blueprint** (`app/main/`): Web interface with templates and routes
   - Login view: `main.login` (also serves as `login_manager.login_view`)
   - Routes defined in `app/main/routes.py`
   - Forms use Flask-WTF in `app/main/forms.py`
   - Templates in `app/main/templates/`

2. **API Blueprint** (`app/api/`): REST API (currently commented out in app initialization)
   - Currently has a basic `/api/status` endpoint
   - Intended for JWT-based authentication (not yet implemented)
   - Uncomment registration in `app/__init__.py` when ready

### Database Models

**User Model** (`app/models.py`):
- Fields: `id`, `username`, `email`, `password_hash`
- Password hashing via Werkzeug (methods: `set_password()`, `check_password()`)
- Flask-Login integration via `@login_manager.user_loader`

**Shopping List Models**: Not yet implemented, but requirements specify:
- Lists identified by GUID for sharing
- Items with checkbox state, quantity, and name
- User ownership relationship (one-to-many: User -> Lists)
- Cascade delete when user is deleted

### Authentication Flow

- Flask-Login manages user sessions
- Login view at `/login` using `LoginForm`
- `login_manager.login_view` redirects unauthenticated users to `main.login`
- Protected routes use `@login_required` decorator
- Logout clears session and redirects to index

## Design Requirements

**Themes**:
- Light theme: Orange and pastel tones
- Dark theme: Dark blue base color
- Responsive design for desktop and mobile

**UI Features**:
- Dynamic item addition without page refresh
- Strikethrough styling for checked items
- Input fields positioned above the list

## Language

Application is in German (UI messages, flash notifications, form labels).
