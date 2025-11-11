# Backend Dokumentation - Grocery Shopping List

## Übersicht

Das Backend ist vollständig implementiert mit Flask, SQLAlchemy und Flask-Login. Es bietet sowohl eine Web-Oberfläche als auch eine REST API für zukünftige mobile Anwendungen.

## Datenbankmodelle

### User Model (`/Users/cfluegel/Nextcloud/Development/flask-grocery-shopping-list/app/models.py`)

```python
class User(UserMixin, db.Model):
    id: Integer (Primary Key)
    username: String(80) - Eindeutig, Indexiert
    email: String(120) - Eindeutig, Indexiert
    password_hash: String(255)
    is_admin: Boolean - Default: False
    created_at: DateTime

    # Relationships
    shopping_lists: Relationship zu ShoppingList (Cascade Delete)
```

**Features:**
- UserMixin von Flask-Login für Authentifizierung
- Passwort-Hashing mit werkzeug.security
- Cascade Delete: Beim Löschen werden alle Listen des Benutzers gelöscht
- Admin-Flag für erweiterte Berechtigungen

### ShoppingList Model

```python
class ShoppingList(db.Model):
    id: Integer (Primary Key)
    guid: String(36) - Eindeutig, UUID, Indexiert
    title: String(200)
    user_id: Integer (Foreign Key zu users)
    is_shared: Boolean - Default: False
    created_at: DateTime
    updated_at: DateTime - Auto-Update bei Änderungen

    # Relationships
    items: Relationship zu ShoppingListItem (Cascade Delete)
    owner: Backref zu User
```

**Features:**
- GUID für sicheres Sharing ohne ID-Enumeration
- is_shared Flag für öffentlichen Zugriff
- Automatisches updated_at Timestamp
- Cascade Delete: Beim Löschen werden alle Items gelöscht
- get_share_url() Methode für Share-Link-Generierung

### ShoppingListItem Model

```python
class ShoppingListItem(db.Model):
    id: Integer (Primary Key)
    shopping_list_id: Integer (Foreign Key zu shopping_lists)
    name: String(200)
    quantity: String(50) - Default: '1'
    is_checked: Boolean - Default: False
    order_index: Integer - Für Sortierung
    created_at: DateTime

    # Relationships
    shopping_list: Backref zu ShoppingList
```

**Features:**
- order_index für flexible Sortierung (neue Items haben höhere Werte)
- is_checked für Checkbox-Status
- Quantity als String für flexible Eingaben (z.B. "2kg", "1 Packung")

## Sicherheit & Authentifizierung

### Admin-Decorator (`/Users/cfluegel/Nextcloud/Development/flask-grocery-shopping-list/app/utils.py`)

```python
@admin_required
def protected_route():
    # Nur für Admins zugänglich
```

**Features:**
- Prüft Login-Status
- Prüft Admin-Flag
- Gibt 403 Forbidden bei fehlender Berechtigung
- Deutsche Fehlermeldungen

### Zugriffskontrolle

Die Funktion `check_list_access()` regelt den Zugriff auf Shopping Lists:

- **Nicht angemeldete Benutzer:** Nur geteilte Listen (is_shared=True)
- **Angemeldete Benutzer:** Eigene Listen + geteilte Listen (auch bearbeiten)
- **Admins:** Alle Listen (voller Zugriff)

## Web-Routes (Main Blueprint)

### Öffentliche Routes

| Route | Methoden | Beschreibung |
|-------|----------|--------------|
| `/` | GET | Homepage (Redirect zu Dashboard wenn eingeloggt) |
| `/login` | GET, POST | Login-Seite |
| `/logout` | GET | Logout |
| `/shared/<guid>` | GET | Geteilte Liste anzeigen (KEIN Login erforderlich) |

### Dashboard & Listen (Login erforderlich)

| Route | Methoden | Beschreibung |
|-------|----------|--------------|
| `/dashboard` | GET | Übersicht eigener Listen |
| `/lists/create` | GET, POST | Neue Liste erstellen |
| `/lists/<id>` | GET | Liste mit Items anzeigen |
| `/lists/<id>/edit` | GET, POST | Liste bearbeiten (nur Owner/Admin) |
| `/lists/<id>/delete` | POST | Liste löschen (nur Owner/Admin) |

### Item-Verwaltung (Login erforderlich)

| Route | Methoden | Beschreibung |
|-------|----------|--------------|
| `/lists/<id>/items/add` | POST | Item hinzufügen |
| `/items/<id>/toggle` | POST | Item abhaken/zurücksetzen (AJAX) |
| `/items/<id>/delete` | POST | Item löschen |

### Admin-Bereich (Login + Admin erforderlich)

| Route | Methoden | Beschreibung |
|-------|----------|--------------|
| `/admin` | GET | Admin-Dashboard mit Statistiken |
| `/admin/users` | GET | Benutzerverwaltung |
| `/admin/users/create` | GET, POST | Benutzer erstellen |
| `/admin/users/<id>/edit` | GET, POST | Benutzer bearbeiten |
| `/admin/users/<id>/delete` | POST | Benutzer löschen (mit Listen) |
| `/admin/lists` | GET | Alle Listen aller Benutzer |
| `/admin/lists/<id>/delete` | POST | Liste löschen |

## REST API (`/api/...`)

Das API Blueprint ist unter `/api` verfügbar und für zukünftige mobile Apps vorbereitet.

### Status

```
GET /api/status
```

Gibt API-Status zurück (keine Authentifizierung erforderlich).

### Listen-Endpunkte (Login erforderlich)

```
GET    /api/lists              - Alle eigenen Listen
GET    /api/lists/<id>         - Eine spezifische Liste mit Items
POST   /api/lists              - Neue Liste erstellen
PUT    /api/lists/<id>         - Liste aktualisieren
DELETE /api/lists/<id>         - Liste löschen
```

### Item-Endpunkte (Login erforderlich)

```
GET    /api/lists/<id>/items   - Alle Items einer Liste
POST   /api/lists/<id>/items   - Item hinzufügen
PUT    /api/items/<id>         - Item aktualisieren
POST   /api/items/<id>/toggle  - Item-Status togglen
DELETE /api/items/<id>         - Item löschen
```

### Geteilte Listen (Öffentlich)

```
GET /api/shared/<guid>          - Geteilte Liste abrufen (kein Login)
```

**API Response Format:**
```json
{
    "success": true,
    "data": { ... }
}
```

Bei Fehlern:
```json
{
    "success": false,
    "error": "Fehlerbeschreibung"
}
```

## Forms (`/Users/cfluegel/Nextcloud/Development/flask-grocery-shopping-list/app/main/forms.py`)

### Verfügbare Forms mit Validierung:

1. **LoginForm** - Benutzer-Login
2. **ShoppingListForm** - Listen erstellen/bearbeiten
3. **ShoppingListItemForm** - Items hinzufügen
4. **CreateUserForm** - Benutzer erstellen (mit Duplicate-Check)
5. **EditUserForm** - Benutzer bearbeiten (mit Duplicate-Check außer für sich selbst)

Alle Forms haben deutsche Fehlermeldungen und umfangreiche Validierung.

## CLI-Kommandos

Das Backend bietet CLI-Kommandos für Verwaltungsaufgaben:

```bash
# Datenbank initialisieren und Admin erstellen
flask init-db

# Neuen Admin erstellen
flask create-admin <username> <email> <password>

# Regulären Benutzer erstellen
flask create-user <username> <email> <password>

# Alle Benutzer auflisten
flask list-users

# Statistiken anzeigen
flask stats
```

## Standard-Admin-Benutzer

Der Standard-Admin wird automatisch beim ersten Request erstellt:

- **Username:** admin
- **Password:** admin123
- **Email:** admin@example.com
- **is_admin:** True

**WICHTIG für Produktion:** Passwort sofort ändern!

## Nächste Schritte für Deployment

### 1. Datenbank-Migration erstellen

```bash
flask db init  # Falls noch nicht geschehen
flask db migrate -m "Initial migration with User, ShoppingList, and ShoppingListItem"
flask db upgrade
```

### 2. Standard-Admin erstellen (optional, wenn nicht automatisch)

```bash
flask init-db
```

### 3. Umgebungsvariablen setzen

```bash
export SECRET_KEY='your-secret-key-here'
export DATABASE_URL='postgresql://user:pass@localhost/dbname'  # Für Produktion
```

### 4. Für Produktion

- SECRET_KEY auf kryptographisch sicheren Wert setzen
- DATABASE_URL auf PostgreSQL/MySQL umstellen
- DEBUG auf False setzen
- Admin-Passwort ändern
- HTTPS aktivieren
- CORS-Header für API konfigurieren (falls externe Apps)
- Rate Limiting implementieren (Flask-Limiter)
- JWT für API-Authentifizierung hinzufügen

## Architektur-Entscheidungen

### 1. Application Factory Pattern
- Ermöglicht mehrere App-Instanzen (Testing, Development, Production)
- Klare Trennung der Konfiguration
- Einfaches Testing

### 2. Blueprints
- **main:** Web-UI mit Templates
- **api:** REST API für zukünftige Apps
- Klare Trennung von Concerns

### 3. Service Layer (implizit in Routes)
- Business Logic in Route-Handlern
- Models enthalten nur Daten-bezogene Logik
- Bei Wachstum: Service-Layer extrahieren

### 4. Security First
- Admin-Decorator für geschützte Routes
- check_list_access() für granulare Berechtigungen
- CSRF-Protection durch Flask-WTF
- SQL Injection Prevention durch SQLAlchemy ORM
- Password Hashing mit werkzeug

### 5. Flexible Sortierung
- order_index statt fixed ordering
- Neue Items haben höheren Index (erscheinen oben)
- Spätere Erweiterung: Drag & Drop Reordering möglich

## Offene Punkte für Frontend

1. **Templates erstellen:**
   - `index.html` - Homepage
   - `login.html` - Login
   - `dashboard.html` - User Dashboard
   - `create_list.html` - Liste erstellen
   - `view_list.html` - Liste mit Items
   - `edit_list.html` - Liste bearbeiten
   - `shared_list.html` - Geteilte Liste (öffentlich)
   - `admin/dashboard.html` - Admin Dashboard
   - `admin/users.html` - Benutzerverwaltung
   - `admin/create_user.html` - Benutzer erstellen
   - `admin/edit_user.html` - Benutzer bearbeiten
   - `admin/lists.html` - Alle Listen

2. **AJAX/Fetch für dynamische Updates:**
   - Item Toggle ohne Reload
   - Item hinzufügen ohne Reload
   - Item löschen ohne Reload
   - API-Endpunkte sind vorhanden (z.B. `/items/<id>/toggle` gibt JSON zurück)

3. **Styling:**
   - Dark/Light Theme
   - Responsive Design
   - Abgehakte Items durchstreichen

4. **Share-Link UI:**
   - Share-Button mit Copy-to-Clipboard
   - QR-Code-Generierung (optional)
   - Share-Status-Indikator

## Fragen an Frontend-Team

1. **Template-Engine:** Jinja2 wird verwendet - ist das OK oder bevorzugt ihr ein Frontend-Framework (React/Vue)?

2. **AJAX vs. Full Page Reload:** Welche Actions sollen AJAX sein?
   - Item Toggle (empfohlen: AJAX)
   - Item hinzufügen (empfohlen: AJAX)
   - Item löschen (empfohlen: AJAX)
   - Liste erstellen (Full Reload OK?)

3. **API-First vs. Template-First:**
   - Aktuell: Templates mit Flask
   - Alternative: SPA mit API-Backend (alles über /api/...)

4. **Theme-Switching:**
   - Client-side (localStorage + CSS)?
   - Server-side (User-Preference in DB)?

5. **Fehlerbehandlung:**
   - Flash-Messages (current) oder Toast/Snackbar?

## Performance-Überlegungen

- **Indizes:** username, email, guid sind indexiert
- **Lazy Loading:** Relationships nutzen lazy='dynamic' für große Datensätze
- **N+1 Queries vermeiden:** Bei Bedarf eager loading mit joinedload()
- **Caching:** Für häufig abgerufene Daten (z.B. User-Listen) Redis-Caching erwägen

## Testing-Strategie

Für zukünftige Tests:

1. **Unit Tests:**
   - Model-Methoden (set_password, check_password)
   - Utility-Funktionen (check_list_access)
   - Form-Validierung

2. **Integration Tests:**
   - Route-Handler
   - Datenbankoperationen
   - Authentifizierung

3. **End-to-End Tests:**
   - User-Flows (Login → Liste erstellen → Item hinzufügen)
   - Admin-Flows
   - Sharing-Flows

## Zusammenfassung

Das Backend ist produktionsbereit mit:
- Vollständigen CRUD-Operationen
- Sicherer Authentifizierung & Autorisierung
- Admin-Bereich
- Sharing-Funktionalität
- REST API für zukünftige Erweiterungen
- CLI-Tools für Verwaltung
- Umfangreicher Validierung
- Deutschen Fehlermeldungen
