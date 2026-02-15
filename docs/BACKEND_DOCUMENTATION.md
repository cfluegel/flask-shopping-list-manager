# Backend Dokumentation - Grocery Shopping List

## Übersicht

Das Backend ist mit Flask, SQLAlchemy, Flask-Login und Flask-JWT-Extended implementiert. Es bietet eine server-gerenderte Web-Oberfläche, eine JWT-basierte REST API und eine Progressive Web App (PWA).

## Architektur

### Application Factory Pattern

`create_app(config_object)` in `app/__init__.py` initialisiert:
- Flask-SQLAlchemy & Flask-Migrate (Datenbank)
- Flask-Login (Web-Session-Authentifizierung)
- Flask-JWT-Extended (API-Token-Authentifizierung)
- Flask-CORS (Cross-Origin-Requests)
- Flask-Limiter (Rate Limiting)
- CLI-Kommandos (`app/cli.py`)

### Blueprints

1. **Main Blueprint** (`app/main/`): Web-UI mit Jinja2-Templates
2. **API Blueprint** (`app/api/`): REST API unter `/api/v1/` mit JWT-Auth
3. **PWA Blueprint** (`app/pwa/`): Progressive Web App SPA-Shell unter `/pwa/`

### Services

- **PrinterService** (`app/services/printer_service.py`): ESC/POS Thermodrucker-Integration über Netzwerk/TCP (Port 9100). Konfigurierbar über `PRINTER_ENABLED`, `PRINTER_HOST`, `PRINTER_PORT`, `PRINTER_TIMEOUT`, `PRINTER_WIDTH`.

## Datenbankmodelle

### User Model (`app/models.py`)

```python
class User(UserMixin, db.Model):
    id: Integer (Primary Key)
    username: String(80) - Eindeutig, Indexiert
    email: String(120) - Eindeutig, Indexiert
    password_hash: String(255)
    is_admin: Boolean - Default: False
    created_at: DateTime (UTC)

    # Relationships
    shopping_lists: Relationship zu ShoppingList (Cascade Delete)
```

### ShoppingList Model

```python
class ShoppingList(db.Model):
    id: Integer (Primary Key)
    guid: String(36) - Eindeutig, UUID, Indexiert
    title: String(200)
    user_id: Integer (Foreign Key zu users, Indexiert)
    is_shared: Boolean - Default: False
    version: Integer - Default: 1 (Optimistic Locking)
    created_at: DateTime (UTC)
    updated_at: DateTime (UTC) - Auto-Update
    deleted_at: DateTime - Nullable, Indexiert (Soft Delete)

    # Relationships
    items: Relationship zu ShoppingListItem (Cascade Delete)
```

**Methoden:** `soft_delete()`, `restore()`, `check_version(v)`, `increment_version()`
**Klassenmethoden:** `active()` (nicht gelöschte), `deleted()` (gelöschte)

### ShoppingListItem Model

```python
class ShoppingListItem(db.Model):
    id: Integer (Primary Key)
    shopping_list_id: Integer (Foreign Key, Indexiert)
    name: String(200)
    quantity: String(50) - Default: '1'
    is_checked: Boolean - Default: False
    order_index: Integer - Default: 0
    version: Integer - Default: 1 (Optimistic Locking)
    created_at: DateTime (UTC)
    deleted_at: DateTime - Nullable, Indexiert (Soft Delete)
```

**Methoden & Klassenmethoden:** wie ShoppingList

### RevokedToken Model (JWT Blacklist)

```python
class RevokedToken(db.Model):
    id: Integer (Primary Key)
    jti: String - Eindeutig, Indexiert (JWT ID)
    token_type: String ('access' oder 'refresh')
    user_id: Integer (Foreign Key, Indexiert)
    revoked_at: DateTime (UTC)
    expires_at: DateTime
```

**Klassenmethoden:** `is_jti_blacklisted(jti)`, `add_to_blacklist(...)`, `cleanup_expired_tokens()`

## Soft Delete & Trash

Listen und Items werden nicht sofort gelöscht, sondern in den Papierkorb verschoben (`deleted_at` Timestamp wird gesetzt). Funktionen:
- Soft-Delete einer Liste löscht auch alle Items (Cascade)
- Restore stellt Liste und alle Items wieder her
- Permanentes Löschen nur über Trash-Endpoints
- `flask cleanup-trash [--days N]` CLI-Kommando für automatische Bereinigung

Details: [SOFT_DELETE_IMPLEMENTATION.md](SOFT_DELETE_IMPLEMENTATION.md)

## Optimistic Locking

Jede Liste und jedes Item hat ein `version`-Feld. Bei Updates kann die erwartete Version mitgesendet werden. Bei Konflikt wird HTTP 409 zurückgegeben.

Details: [OPTIMISTIC_LOCKING.md](OPTIMISTIC_LOCKING.md)

## Authentifizierung

### Web-UI: Flask-Login (Session-basiert)
- Login-View: `/login` mit `LoginForm`
- `@login_required` Decorator für geschützte Routes
- Logout löscht Session

### API: JWT (Token-basiert)
- Login: `POST /api/v1/auth/login` → Access + Refresh Token
- Access Token: 30 Minuten gültig
- Refresh Token: 30 Tage gültig
- `@jwt_required()` Decorator für geschützte Endpoints
- Token-Blacklisting bei Logout (RevokedToken Model)

### Zugriffskontrolle
- **Nicht angemeldete Benutzer:** Nur geteilte Listen (`is_shared=True`)
- **Angemeldete Benutzer:** Eigene Listen + geteilte Listen bearbeiten
- **Admins:** Voller Zugriff auf alle Ressourcen

## Web-Routes (Main Blueprint)

### Öffentliche Routes

| Route | Methoden | Beschreibung |
|-------|----------|--------------|
| `/` | GET | Homepage (Redirect zu Dashboard wenn eingeloggt) |
| `/login` | GET, POST | Login-Seite |
| `/logout` | GET | Logout |
| `/shared/<guid>` | GET | Geteilte Liste anzeigen |

### Dashboard & Listen (Login erforderlich)

| Route | Methoden | Beschreibung |
|-------|----------|--------------|
| `/dashboard` | GET | Übersicht eigener Listen |
| `/lists/create` | GET, POST | Neue Liste erstellen |
| `/lists/<id>` | GET | Liste mit Items anzeigen |
| `/lists/<id>/edit` | GET, POST | Liste bearbeiten |
| `/lists/<id>/delete` | POST | Liste löschen |

### Admin-Bereich (Login + Admin erforderlich)

| Route | Methoden | Beschreibung |
|-------|----------|--------------|
| `/admin` | GET | Admin-Dashboard |
| `/admin/users` | GET | Benutzerverwaltung |
| `/admin/users/create` | GET, POST | Benutzer erstellen |
| `/admin/users/<id>/edit` | GET, POST | Benutzer bearbeiten |
| `/admin/users/<id>/delete` | POST | Benutzer löschen |
| `/admin/lists` | GET | Alle Listen |
| `/admin/lists/<id>/delete` | POST | Liste löschen |

## REST API (`/api/v1/`)

Vollständige Endpoint-Übersicht: [API_REFERENCE.md](API_REFERENCE.md)
Detaillierte Dokumentation: [API_DOCUMENTATION.md](API_DOCUMENTATION.md) / [API_DOCUMENTATION_EN.md](API_DOCUMENTATION_EN.md)

## CLI-Kommandos

```bash
flask init-db                              # Datenbank initialisieren + Admin erstellen
flask create-admin <user> <email> <pw>     # Admin erstellen
flask create-user <user> <email> <pw>      # User erstellen
flask list-users                           # Alle User auflisten
flask stats                                # Statistiken anzeigen
flask cleanup-trash [--days N] [--dry-run] # Papierkorb bereinigen
flask trash-stats                          # Papierkorb-Statistiken
```

## Forms (`app/main/forms.py`)

1. **LoginForm** - Benutzer-Login
2. **ShoppingListForm** - Listen erstellen/bearbeiten
3. **ShoppingListItemForm** - Items hinzufügen
4. **CreateUserForm** - Benutzer erstellen (mit Duplicate-Check)
5. **EditUserForm** - Benutzer bearbeiten (mit Duplicate-Check)

Alle Forms haben deutsche Fehlermeldungen und umfangreiche Validierung.

## Sicherheit

- **Password Hashing:** werkzeug.security
- **CSRF Protection:** Flask-WTF (Web-Forms)
- **SQL Injection Prevention:** SQLAlchemy ORM
- **JWT Token Blacklisting:** Logout invalidiert Tokens
- **Rate Limiting:** Flask-Limiter (konfigurierbar mit Redis)
- **CORS:** Konfigurierbar über `CORS_ORIGINS`
- **Admin Protection:** `@admin_required` Decorator
- **Access Control:** Granulare Berechtigungen pro Endpoint
- **GUID statt ID:** Verhindert Enumeration bei Shared Lists

## Standard-Admin-Benutzer

- **Username:** admin
- **Password:** admin123
- **Email:** admin@example.com

**WICHTIG für Produktion:** Passwort sofort ändern! ProductionConfig erzwingt nicht-default SECRET_KEY und JWT_SECRET_KEY.
