# REST API Reference

## Base URL

```
http://localhost:5000/api
```

## Authentication

Aktuell nutzt die API Flask-Login Session-basierte Authentifizierung. Für zukünftige mobile Apps ist JWT-Authentifizierung geplant.

### Session-basiert (aktuell)

Authentifizierung erfolgt über Cookie-Sessions nach Login über die Web-UI (`POST /login`).

### JWT (geplant für v2.0)

```http
Authorization: Bearer <jwt_token>
```

## Response Format

### Success Response

```json
{
    "success": true,
    "data": { ... }
}
```

### Error Response

```json
{
    "success": false,
    "error": "Error message"
}
```

### HTTP Status Codes

- `200 OK` - Erfolgreiche GET, PUT, DELETE Requests
- `201 Created` - Erfolgreiche POST Requests (Ressource erstellt)
- `400 Bad Request` - Ungültige Request-Daten
- `401 Unauthorized` - Nicht authentifiziert
- `403 Forbidden` - Keine Berechtigung
- `404 Not Found` - Ressource nicht gefunden
- `500 Internal Server Error` - Server-Fehler

---

## Endpoints

### Health Check

#### GET /status

Überprüft, ob die API läuft.

**Authentifizierung:** Nicht erforderlich

**Response:**
```json
{
    "status": "ok",
    "version": "1.0.0",
    "message": "Grocery Shopping List API is running"
}
```

---

## Shopping Lists

### GET /lists

Ruft alle Shopping Lists des aktuellen Benutzers ab.

**Authentifizierung:** Erforderlich

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "guid": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Wocheneinkauf",
            "is_shared": false,
            "created_at": "2025-11-09T10:30:00",
            "updated_at": "2025-11-09T14:20:00",
            "item_count": 5
        }
    ]
}
```

---

### GET /lists/:id

Ruft eine spezifische Shopping List mit allen Items ab.

**Authentifizierung:** Erforderlich

**Parameter:**
- `id` (path, integer) - Shopping List ID

**Zugriffskontrolle:**
- Owner kann zugreifen
- Admin kann zugreifen
- Authentifizierte Benutzer können auf geteilte Listen zugreifen

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "guid": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Wocheneinkauf",
        "is_shared": false,
        "owner": "testuser",
        "created_at": "2025-11-09T10:30:00",
        "updated_at": "2025-11-09T14:20:00",
        "items": [
            {
                "id": 1,
                "name": "Milch",
                "quantity": "2",
                "is_checked": false,
                "order_index": 3
            },
            {
                "id": 2,
                "name": "Brot",
                "quantity": "1",
                "is_checked": true,
                "order_index": 2
            }
        ]
    }
}
```

---

### POST /lists

Erstellt eine neue Shopping List.

**Authentifizierung:** Erforderlich

**Request Body:**
```json
{
    "title": "Wocheneinkauf",
    "is_shared": false
}
```

**Erforderliche Felder:**
- `title` (string) - Titel der Liste

**Optionale Felder:**
- `is_shared` (boolean) - Standard: false

**Response (201 Created):**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "guid": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Wocheneinkauf",
        "is_shared": false
    }
}
```

**Error Response (400 Bad Request):**
```json
{
    "success": false,
    "error": "Title is required"
}
```

---

### PUT /lists/:id

Aktualisiert eine Shopping List.

**Authentifizierung:** Erforderlich

**Zugriffskontrolle:** Nur Owner oder Admin

**Parameter:**
- `id` (path, integer) - Shopping List ID

**Request Body:**
```json
{
    "title": "Neuer Titel",
    "is_shared": true
}
```

**Alle Felder optional:**
- `title` (string)
- `is_shared` (boolean)

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "title": "Neuer Titel",
        "is_shared": true
    }
}
```

---

### DELETE /lists/:id

Löscht eine Shopping List und alle zugehörigen Items.

**Authentifizierung:** Erforderlich

**Zugriffskontrolle:** Nur Owner oder Admin

**Parameter:**
- `id` (path, integer) - Shopping List ID

**Response:**
```json
{
    "success": true,
    "message": "List deleted"
}
```

---

## Shopping List Items

### GET /lists/:id/items

Ruft alle Items einer Shopping List ab.

**Authentifizierung:** Erforderlich

**Parameter:**
- `id` (path, integer) - Shopping List ID

**Zugriffskontrolle:**
- Owner kann zugreifen
- Admin kann zugreifen
- Authentifizierte Benutzer können Items geteilter Listen abrufen

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "Milch",
            "quantity": "2",
            "is_checked": false,
            "order_index": 3
        },
        {
            "id": 2,
            "name": "Brot",
            "quantity": "1",
            "is_checked": true,
            "order_index": 2
        }
    ]
}
```

---

### POST /lists/:id/items

Fügt ein neues Item zu einer Shopping List hinzu.

**Authentifizierung:** Erforderlich

**Zugriffskontrolle:**
- Owner kann Items hinzufügen
- Admin kann Items hinzufügen
- Authentifizierte Benutzer können Items zu geteilten Listen hinzufügen

**Parameter:**
- `id` (path, integer) - Shopping List ID

**Request Body:**
```json
{
    "name": "Milch",
    "quantity": "2"
}
```

**Erforderliche Felder:**
- `name` (string) - Artikelbezeichnung

**Optionale Felder:**
- `quantity` (string) - Standard: "1"

**Response (201 Created):**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "Milch",
        "quantity": "2",
        "is_checked": false,
        "order_index": 3
    }
}
```

**Hinweis:** Der `order_index` wird automatisch gesetzt (max_existing + 1), sodass neue Items zuerst erscheinen.

---

### PUT /items/:id

Aktualisiert ein Shopping List Item.

**Authentifizierung:** Erforderlich

**Zugriffskontrolle:**
- Owner der Liste kann Items bearbeiten
- Admin kann Items bearbeiten
- Authentifizierte Benutzer können Items geteilter Listen bearbeiten

**Parameter:**
- `id` (path, integer) - Item ID

**Request Body:**
```json
{
    "name": "Vollmilch",
    "quantity": "2 Liter",
    "is_checked": true
}
```

**Alle Felder optional:**
- `name` (string)
- `quantity` (string)
- `is_checked` (boolean)

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "Vollmilch",
        "quantity": "2 Liter",
        "is_checked": true
    }
}
```

---

### POST /items/:id/toggle

Wechselt den Checked-Status eines Items (checked ↔ unchecked).

**Authentifizierung:** Erforderlich

**Zugriffskontrolle:**
- Owner der Liste kann Items togglen
- Admin kann Items togglen
- Authentifizierte Benutzer können Items geteilter Listen togglen

**Parameter:**
- `id` (path, integer) - Item ID

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "is_checked": true
    }
}
```

**Verwendung:**
Dieser Endpunkt ist optimal für AJAX/Fetch-Requests beim Klick auf eine Checkbox.

**Beispiel JavaScript:**
```javascript
async function toggleItem(itemId) {
    const response = await fetch(`/api/items/${itemId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    const data = await response.json();
    if (data.success) {
        // Update UI based on data.data.is_checked
    }
}
```

---

### DELETE /items/:id

Löscht ein Shopping List Item.

**Authentifizierung:** Erforderlich

**Zugriffskontrolle:**
- Owner der Liste kann Items löschen
- Admin kann Items löschen
- Authentifizierte Benutzer können Items geteilter Listen löschen

**Parameter:**
- `id` (path, integer) - Item ID

**Response:**
```json
{
    "success": true,
    "message": "Item deleted"
}
```

---

## Shared Lists (Public)

### GET /shared/:guid

Ruft eine geteilte Shopping List ab (KEIN Login erforderlich).

**Authentifizierung:** Nicht erforderlich

**Parameter:**
- `guid` (path, string) - GUID der geteilten Liste

**Zugriffskontrolle:**
- Liste muss `is_shared = true` sein
- Andernfalls: 404 Not Found

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "guid": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Party-Einkaufsliste",
        "owner": "johndoe",
        "created_at": "2025-11-09T10:30:00",
        "updated_at": "2025-11-09T14:20:00",
        "items": [
            {
                "id": 1,
                "name": "Chips",
                "quantity": "3 Packungen",
                "is_checked": false,
                "order_index": 5
            },
            {
                "id": 2,
                "name": "Cola",
                "quantity": "2 Liter",
                "is_checked": true,
                "order_index": 4
            }
        ]
    }
}
```

**Verwendung:**
- Nicht-authentifizierte Benutzer können die Liste sehen
- Authentifizierte Benutzer können die Liste bearbeiten (über andere Endpunkte)

---

## Examples

### Complete Shopping List Workflow

#### 1. Login (Web UI)
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=testuser&password=password123
```

#### 2. Create Shopping List
```http
POST /api/lists
Content-Type: application/json

{
    "title": "Wocheneinkauf",
    "is_shared": false
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "guid": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Wocheneinkauf",
        "is_shared": false
    }
}
```

#### 3. Add Items
```http
POST /api/lists/1/items
Content-Type: application/json

{
    "name": "Milch",
    "quantity": "2 Liter"
}
```

```http
POST /api/lists/1/items
Content-Type: application/json

{
    "name": "Brot",
    "quantity": "1"
}
```

#### 4. Get Complete List
```http
GET /api/lists/1
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "guid": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Wocheneinkauf",
        "is_shared": false,
        "owner": "testuser",
        "created_at": "2025-11-09T10:30:00",
        "updated_at": "2025-11-09T10:35:00",
        "items": [
            {
                "id": 2,
                "name": "Brot",
                "quantity": "1",
                "is_checked": false,
                "order_index": 2
            },
            {
                "id": 1,
                "name": "Milch",
                "quantity": "2 Liter",
                "is_checked": false,
                "order_index": 1
            }
        ]
    }
}
```

#### 5. Toggle Item
```http
POST /api/items/1/toggle
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "is_checked": true
    }
}
```

#### 6. Share List
```http
PUT /api/lists/1
Content-Type: application/json

{
    "is_shared": true
}
```

#### 7. Access Shared List (No Login)
```http
GET /api/shared/550e8400-e29b-41d4-a716-446655440000
```

**Response:** Vollständige Liste mit allen Items (siehe oben)

---

## Error Codes

### 400 Bad Request

**Ursachen:**
- Fehlende erforderliche Felder
- Ungültige Datentypen
- Validierungsfehler

**Beispiel:**
```json
{
    "success": false,
    "error": "Title is required"
}
```

### 401 Unauthorized

**Ursachen:**
- Nicht authentifiziert
- Session abgelaufen

**Beispiel:**
Redirect zu `/login` mit Flash-Message

### 403 Forbidden

**Ursachen:**
- Fehlende Berechtigung (nicht Owner, nicht Admin)
- Versuch, nicht-geteilte Liste zu bearbeiten

**Beispiel:**
HTTP 403 Status ohne JSON-Body (Standard Flask abort)

### 404 Not Found

**Ursachen:**
- Ressource existiert nicht
- Liste nicht geteilt (bei /shared/:guid)
- Ungültige ID

**Beispiel:**
HTTP 404 Status

---

## Rate Limiting (Future)

Für Produktion wird Rate Limiting empfohlen:

```
100 requests per hour per user (authenticated)
20 requests per hour per IP (unauthenticated)
```

Implementation with Flask-Limiter:

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@api_bp.route('/lists')
@limiter.limit("100 per hour")
def get_lists():
    # ...
```

---

## Pagination (Future)

Für große Datensätze wird Pagination empfohlen:

**Request:**
```http
GET /api/lists?page=2&per_page=20
```

**Response:**
```json
{
    "success": true,
    "data": [...],
    "pagination": {
        "page": 2,
        "per_page": 20,
        "total": 150,
        "pages": 8
    }
}
```

---

## CORS

Für Cross-Origin Requests (z.B. separate Frontend-App):

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

## Versioning

Aktuelle Version: **v1.0.0**

Für zukünftige API-Versionen:

```
/api/v1/lists
/api/v2/lists
```

---

## Testing with curl

### Get Status
```bash
curl http://localhost:5000/api/status
```

### Create List (with session)
```bash
# 1. Login to get session cookie
curl -c cookies.txt -X POST http://localhost:5000/login \
  -d "username=admin&password=admin123"

# 2. Create list using session
curl -b cookies.txt -X POST http://localhost:5000/api/lists \
  -H "Content-Type: application/json" \
  -d '{"title": "Test List", "is_shared": false}'

# 3. Get lists
curl -b cookies.txt http://localhost:5000/api/lists
```

### Get Shared List (no auth)
```bash
curl http://localhost:5000/api/shared/<guid>
```

---

## Support

Für Fragen zur API-Nutzung siehe `BACKEND_DOCUMENTATION.md` oder kontaktiere das Backend-Team.
