# Grocery Shopping List API v1 Documentation

Vollständige REST API-Dokumentation für mobile Apps (Expo/Flutter).

## Inhaltsverzeichnis

- [Übersicht](#übersicht)
- [Basis-URL](#basis-url)
- [Authentifizierung](#authentifizierung)
- [Response-Format](#response-format)
- [Error-Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Authentication](#authentication)
  - [Users](#users)
  - [Shopping Lists](#shopping-lists)
  - [Shopping Items](#shopping-items)
  - [Shared Lists](#shared-lists-public)
  - [Admin](#admin)

---

## Übersicht

Die Grocery Shopping List API ist eine RESTful API, die JWT-basierte Authentifizierung verwendet. Sie ermöglicht die Verwaltung von Einkaufslisten und deren Items über mobile Apps.

**Version:** 1.0
**Authentifizierung:** JWT (JSON Web Tokens)
**Content-Type:** `application/json`

---

## Basis-URL

```
https://your-domain.com/api/v1
```

Lokale Entwicklung:
```
http://localhost:5000/api/v1
```

---

## Authentifizierung

Die API verwendet **JWT (JSON Web Tokens)** für die Authentifizierung.

### Token-Typen

1. **Access Token**
   - Kurze Lebensdauer: 30 Minuten
   - Für alle authentifizierten API-Requests
   - Header: `Authorization: Bearer <access_token>`

2. **Refresh Token**
   - Längere Lebensdauer: 30 Tage
   - Nur für Token-Refresh
   - Header: `Authorization: Bearer <refresh_token>`

### Authentifizierungs-Flow

```
1. Login/Register → Access Token + Refresh Token
2. API Request → Access Token im Header
3. Access Token abgelaufen → Refresh Token verwenden
4. Refresh → Neuer Access Token
5. Logout → Token blacklisten
```

### Header-Format

Für alle authentifizierten Requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

---

## Response-Format

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation successful"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Optional additional error details
    }
  }
}
```

### Paginated Response

```json
{
  "success": true,
  "data": [
    // Array of items
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Error-Codes

| Code | HTTP Status | Beschreibung |
|------|-------------|--------------|
| `UNAUTHORIZED` | 401 | Authentifizierung erforderlich |
| `FORBIDDEN` | 403 | Zugriff verweigert |
| `INVALID_CREDENTIALS` | 401 | Ungültige Anmeldedaten |
| `TOKEN_EXPIRED` | 401 | Token abgelaufen |
| `TOKEN_INVALID` | 401 | Ungültiger Token |
| `TOKEN_REVOKED` | 401 | Token wurde widerrufen |
| `VALIDATION_ERROR` | 400 | Validierungsfehler |
| `MISSING_FIELD` | 400 | Pflichtfeld fehlt |
| `INVALID_INPUT` | 400 | Ungültige Eingabe |
| `NOT_FOUND` | 404 | Ressource nicht gefunden |
| `ALREADY_EXISTS` | 409 | Ressource existiert bereits |
| `CONFLICT` | 409 | Konflikt mit bestehenden Daten |
| `INTERNAL_ERROR` | 500 | Interner Serverfehler |
| `DATABASE_ERROR` | 500 | Datenbankfehler |
| `LIST_NOT_SHARED` | 404 | Liste ist nicht geteilt |
| `INSUFFICIENT_PERMISSIONS` | 403 | Unzureichende Berechtigungen |

---

## Rate Limiting (Ratenbegrenzung)

Die API implementiert Ratenbegrenzung zum Schutz vor Missbrauch:

| Endpoint-Kategorie | Ratenlimit |
|-------------------|------------|
| Registrierung | 5 Anfragen pro Stunde |
| Login | 5 Anfragen pro Minute |
| Passwort-Änderungen | 5 Anfragen pro Stunde |
| Allgemeine Operationen | 30 Anfragen pro Minute |
| Admin-Operationen | 20 Anfragen pro Stunde |

### Rate Limit Response Headers

Jede API-Antwort enthält Ratenbegrenzungs-Informationen in den Headers:

| Header | Beschreibung | Beispiel |
|--------|--------------|----------|
| `X-RateLimit-Limit` | Maximale Anzahl erlaubter Anfragen im Zeitfenster | `5` |
| `X-RateLimit-Remaining` | Verbleibende Anfragen im aktuellen Zeitfenster | `4` |
| `X-RateLimit-Reset` | Unix-Timestamp, wann das Ratenlimit zurückgesetzt wird | `1762844996` |
| `Retry-After` | Anzahl Sekunden, die gewartet werden soll vor erneutem Versuch | `60` |

**Beispiel Response Headers:**
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1762844996
Retry-After: 60
```

### Umgang mit Ratenlimits

**Best Practices:**
1. **Headers überwachen**: Prüfe `X-RateLimit-Remaining` vor Anfragen
2. **Limits respektieren**: Stoppe Anfragen wenn `X-RateLimit-Remaining` 0 erreicht
3. **Angemessen warten**: Verwende `Retry-After` Header-Wert für Wartezeit
4. **Backoff implementieren**: Nutze exponentielles Backoff für Wiederholungen
5. **Responses cachen**: Cache GET-Antworten um API-Aufrufe zu reduzieren

**Beispiel-Implementierung (JavaScript):**
```javascript
async function apiAnfrage(url, optionen) {
  const response = await fetch(url, optionen);

  // Rate Limit Headers prüfen
  const verbleibend = parseInt(response.headers.get('X-RateLimit-Remaining'));
  const reset = parseInt(response.headers.get('X-RateLimit-Reset'));

  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After'));
    console.log(`Ratenlimit überschritten. Erneuter Versuch in ${retryAfter} Sekunden.`);

    // Warten und wiederholen
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    return apiAnfrage(url, optionen);
  }

  // Warnung bei Annäherung an Limit
  if (verbleibend < 2) {
    console.warn(`Ratenlimit wird erreicht. ${verbleibend} Anfragen verbleibend.`);
  }

  return response;
}
```

**Beispiel-Implementierung (Python):**
```python
import time
import requests

def api_anfrage(url, headers=None):
    response = requests.get(url, headers=headers)

    # Rate Limit Headers prüfen
    verbleibend = int(response.headers.get('X-RateLimit-Remaining', 0))
    reset = int(response.headers.get('X-RateLimit-Reset', 0))

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Ratenlimit überschritten. Warte {retry_after} Sekunden...")
        time.sleep(retry_after)
        return api_anfrage(url, headers)

    # Warnung bei Annäherung an Limit
    if verbleibend < 2:
        print(f"Warnung: Nur noch {verbleibend} Anfragen verbleibend")

    return response
```

### Rate Limit Fehler-Antwort

Wenn das Ratenlimit überschritten wird, gibt die API zurück:
```json
{
  "error": "Ratenbegrenzung überschritten",
  "message": "Sie haben zu viele Anfragen gesendet. Bitte versuchen Sie es später erneut."
}
```
**Status Code**: 429 Too Many Requests

---

## Optimistic Locking (Versionskontrolle)

Die API verwendet **Optimistic Locking** um Race Conditions bei gleichzeitigen Updates zu verhindern. Dies schützt vor dem "Lost Update Problem", wenn mehrere Clients dieselbe Ressource gleichzeitig bearbeiten.

### Wie funktioniert es?

Jede `ShoppingList` und jedes `ShoppingListItem` hat ein `version` Feld:

```json
{
  "id": 1,
  "title": "Wocheneinkauf",
  "version": 3,
  ...
}
```

Die Version wird bei jedem Update automatisch inkrementiert.

### Verwendung

**Optional:** Sie können die `version` bei Updates mitschicken, um zu garantieren, dass die Ressource zwischenzeitlich nicht geändert wurde:

```json
PUT /api/v1/lists/1
{
  "title": "Neuer Titel",
  "version": 3
}
```

**Erfolg (200):** Update wird durchgeführt, Version wird inkrementiert:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Neuer Titel",
    "version": 4,
    ...
  }
}
```

**Konflikt (409):** Jemand anderes hat die Ressource zwischenzeitlich geändert:
```json
{
  "success": false,
  "error": {
    "message": "Die Ressource wurde zwischenzeitlich geändert. Bitte aktualisieren Sie und versuchen es erneut.",
    "code": "CONFLICT",
    "details": {
      "current_version": 5,
      "expected_version": 3
    }
  }
}
```

### Retry-Strategie

Bei einem 409 Konflikt:

1. Holen Sie die aktuelle Version der Ressource (GET Request)
2. Mergen Sie Ihre Änderungen mit den aktuellen Daten
3. Senden Sie das Update mit der neuen Version erneut

**Beispiel-Implementierung (JavaScript):**
```javascript
async function updateListWithRetry(listId, updates, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      // Aktuelle Daten abrufen
      const current = await fetch(`/api/v1/lists/${listId}`).then(r => r.json());

      // Update mit aktueller Version senden
      const response = await fetch(`/api/v1/lists/${listId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...updates,
          version: current.data.version
        })
      });

      if (response.status === 409) {
        // Konflikt - erneut versuchen
        console.log('Konflikt erkannt, versuche erneut...');
        continue;
      }

      if (response.ok) {
        return await response.json();
      }

      throw new Error(`Update fehlgeschlagen: ${response.status}`);
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
    }
  }

  throw new Error('Max Retries erreicht');
}
```

### Backwards Compatibility

**Wichtig:** Das `version` Feld ist **optional** bei Updates. Wenn Sie es weglassen, wird das Update ohne Version-Check durchgeführt (wie bisher). Dies gewährleistet Kompatibilität mit bestehenden Clients.

```json
PUT /api/v1/lists/1
{
  "title": "Neuer Titel"
}
```
→ Wird immer erfolgreich sein (solange andere Validierungen passen)

### Betroffene Endpoints

- `PUT /lists/{list_id}` - Shopping List Updates
- `PUT /items/{item_id}` - Shopping Item Updates

---

## Endpoints

---

## Authentication

### POST `/auth/register`

Registriere einen neuen Benutzer.

**Request Body:**
```json
{
  "username": "string (3-80 chars)",
  "email": "string (valid email)",
  "password": "string (min 6 chars)",
  "password_confirm": "string (must match password)"
}
```

**Response: 201 Created**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "is_admin": false,
      "created_at": "2025-11-09T12:00:00Z"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  },
  "message": "Registrierung erfolgreich"
}
```

**Errors:**
- `400` - Validierungsfehler
- `409` - Benutzername oder E-Mail bereits vergeben

---

### POST `/auth/login`

Anmeldung mit Benutzername und Passwort.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "mypassword123"
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "is_admin": false,
      "created_at": "2025-11-09T12:00:00Z"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  },
  "message": "Login erfolgreich"
}
```

**Errors:**
- `400` - Validierungsfehler
- `401` - Ungültige Anmeldedaten

---

### POST `/auth/refresh`

Erneuere Access Token mit Refresh Token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "Token erfolgreich erneuert"
}
```

**Errors:**
- `401` - Ungültiger oder abgelaufener Refresh Token

---

### POST `/auth/logout`

Logout (Access Token widerrufen).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Logout erfolgreich"
}
```

---

### POST `/auth/logout-all`

Logout von allen Geräten (beide Tokens widerrufen).

**Hinweis:** Muss zweimal aufgerufen werden:
1. Mit Access Token
2. Mit Refresh Token

**Headers:**
```
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Access-Token erfolgreich widerrufen"
}
```

---

### GET `/auth/me`

Hole Informationen über aktuellen Benutzer.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "is_admin": false,
    "created_at": "2025-11-09T12:00:00Z"
  }
}
```

---

### PUT `/auth/me`

Aktualisiere eigenes Profil.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "username": "new_username (optional)",
  "email": "new_email@example.com (optional)"
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "new_username",
    "email": "new_email@example.com",
    "is_admin": false,
    "created_at": "2025-11-09T12:00:00Z"
  },
  "message": "Profil erfolgreich aktualisiert"
}
```

**Errors:**
- `400` - Validierungsfehler
- `409` - Benutzername oder E-Mail bereits vergeben

---

### POST `/auth/change-password`

Passwort ändern.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "old_password": "oldpassword123",
  "new_password": "newpassword123",
  "new_password_confirm": "newpassword123"
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Passwort erfolgreich geändert"
}
```

**Errors:**
- `400` - Validierungsfehler
- `401` - Altes Passwort falsch

---

## Users

### GET `/users`

Alle Benutzer abrufen (Admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (int, default: 1) - Seitennummer
- `per_page` (int, default: 20, max: 100) - Items pro Seite

**Response: 200 OK**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "is_admin": false,
      "created_at": "2025-11-09T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

**Errors:**
- `401` - Nicht authentifiziert
- `403` - Nicht Admin

---

### GET `/users/{user_id}`

Benutzer-Details abrufen.

**Zugriff:** Nur auf eigene Daten oder als Admin.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "is_admin": false,
    "created_at": "2025-11-09T12:00:00Z"
  }
}
```

**Errors:**
- `401` - Nicht authentifiziert
- `403` - Zugriff verweigert
- `404` - Benutzer nicht gefunden

---

### POST `/users`

Neuen Benutzer erstellen (Admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "username": "new_user",
  "email": "newuser@example.com",
  "password": "password123",
  "is_admin": false
}
```

**Response: 201 Created**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "username": "new_user",
    "email": "newuser@example.com",
    "is_admin": false,
    "created_at": "2025-11-09T12:00:00Z"
  },
  "message": "Benutzer erfolgreich erstellt"
}
```

**Errors:**
- `400` - Validierungsfehler
- `401` - Nicht authentifiziert
- `403` - Nicht Admin
- `409` - Benutzername oder E-Mail bereits vergeben

---

### PUT `/users/{user_id}`

Benutzer aktualisieren.

**Zugriff:** Nur eigene Daten (außer is_admin) oder als Admin.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "username": "updated_name (optional)",
  "email": "updated@email.com (optional)",
  "is_admin": true (optional, nur Admin)
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "updated_name",
    "email": "updated@email.com",
    "is_admin": true,
    "created_at": "2025-11-09T12:00:00Z"
  },
  "message": "Benutzer erfolgreich aktualisiert"
}
```

**Errors:**
- `400` - Validierungsfehler
- `401` - Nicht authentifiziert
- `403` - Zugriff verweigert
- `404` - Benutzer nicht gefunden
- `409` - Benutzername oder E-Mail bereits vergeben

---

### DELETE `/users/{user_id}`

Benutzer löschen (Admin only).

**Hinweis:** Löscht auch alle Einkaufslisten des Benutzers.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Benutzer \"john_doe\" erfolgreich gelöscht"
}
```

**Errors:**
- `400` - Kann eigenen Account nicht löschen
- `401` - Nicht authentifiziert
- `403` - Nicht Admin
- `404` - Benutzer nicht gefunden

---

### GET `/users/{user_id}/lists`

Einkaufslisten eines Benutzers abrufen.

**Zugriff:** Nur eigene Listen oder als Admin.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)

**Response: 200 OK**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "guid": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Wocheneinkauf",
      "is_shared": true,
      "created_at": "2025-11-09T12:00:00Z",
      "updated_at": "2025-11-09T14:30:00Z",
      "item_count": 5
    }
  ],
  "pagination": { /* ... */ }
}
```

---

## Shopping Lists

### GET `/lists`

Alle eigenen Einkaufslisten abrufen.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)

**Response: 200 OK**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "guid": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Wocheneinkauf",
      "is_shared": true,
      "owner_id": 1,
      "owner_username": "john_doe",
      "created_at": "2025-11-09T12:00:00Z",
      "updated_at": "2025-11-09T14:30:00Z",
      "item_count": 5
    }
  ],
  "pagination": { /* ... */ }
}
```

---

### GET `/lists/{list_id}`

Einkaufsliste mit allen Items abrufen.

**Zugriff:** Besitzer, Admin oder wenn geteilt.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "guid": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Wocheneinkauf",
    "is_shared": true,
    "owner_id": 1,
    "owner_username": "john_doe",
    "created_at": "2025-11-09T12:00:00Z",
    "updated_at": "2025-11-09T14:30:00Z",
    "items": [
      {
        "id": 1,
        "name": "Milch",
        "quantity": "2L",
        "is_checked": false,
        "order_index": 1,
        "created_at": "2025-11-09T12:00:00Z"
      }
    ]
  }
}
```

**Errors:**
- `401` - Nicht authentifiziert
- `403` - Zugriff verweigert
- `404` - Liste nicht gefunden

---

### POST `/lists`

Neue Einkaufsliste erstellen.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "title": "Meine neue Liste",
  "is_shared": false
}
```

**Response: 201 Created**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "guid": "660e8400-e29b-41d4-a716-446655440001",
    "title": "Meine neue Liste",
    "is_shared": false,
    "owner_id": 1,
    "owner_username": "john_doe",
    "created_at": "2025-11-09T15:00:00Z",
    "updated_at": "2025-11-09T15:00:00Z",
    "item_count": 0
  },
  "message": "Einkaufsliste erfolgreich erstellt"
}
```

**Errors:**
- `400` - Validierungsfehler
- `401` - Nicht authentifiziert

---

### PUT `/lists/{list_id}`

Einkaufsliste aktualisieren.

**Zugriff:** Nur Besitzer oder Admin.

**Hinweis:** Unterstützt Optimistic Locking (siehe [Versionskontrolle](#optimistic-locking-versionskontrolle))

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "title": "Aktualisierter Titel (optional)",
  "is_shared": true,
  "version": 3
}
```

**Felder:**
- `title` (string, optional): Neuer Titel der Liste
- `is_shared` (boolean, optional): Sharing-Status ändern
- `version` (integer, optional): Aktuelle Version für Optimistic Locking

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "guid": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Aktualisierter Titel",
    "is_shared": true,
    "owner_id": 1,
    "owner_username": "john_doe",
    "created_at": "2025-11-09T12:00:00Z",
    "updated_at": "2025-11-09T15:30:00Z",
    "item_count": 5
  },
  "message": "Einkaufsliste erfolgreich aktualisiert"
}
```

**Errors:**
- `400` - Validierungsfehler
- `401` - Nicht authentifiziert
- `403` - Zugriff verweigert
- `404` - Liste nicht gefunden

---

### DELETE `/lists/{list_id}`

Einkaufsliste löschen.

**Hinweis:** Löscht auch alle Items der Liste.

**Zugriff:** Nur Besitzer oder Admin.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Einkaufsliste \"Wocheneinkauf\" erfolgreich gelöscht"
}
```

**Errors:**
- `401` - Nicht authentifiziert
- `403` - Zugriff verweigert
- `404` - Liste nicht gefunden

---

### POST `/lists/{list_id}/share`

Sharing-Status einer Liste ändern.

**Zugriff:** Nur Besitzer oder Admin.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "is_shared": true
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "is_shared": true
  },
  "message": "Liste ist jetzt geteilt"
}
```

**Errors:**
- `400` - Validierungsfehler
- `401` - Nicht authentifiziert
- `403` - Zugriff verweigert
- `404` - Liste nicht gefunden

---

### GET `/lists/{list_id}/share-url`

Share-URL für eine Liste abrufen.

**Zugriff:** Nur Besitzer oder Admin.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "guid": "550e8400-e29b-41d4-a716-446655440000",
    "is_shared": true,
    "api_url": "/api/v1/shared/550e8400-e29b-41d4-a716-446655440000",
    "web_url": "/shared/550e8400-e29b-41d4-a716-446655440000",
    "full_api_url": "https://your-domain.com/api/v1/shared/550e8400-e29b-41d4-a716-446655440000",
    "full_web_url": "https://your-domain.com/shared/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## Shopping Items

### GET `/lists/{list_id}/items`

Alle Items einer Liste abrufen.

**Zugriff:** Besitzer, Admin oder wenn geteilt.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Milch",
      "quantity": "2L",
      "is_checked": false,
      "order_index": 2,
      "created_at": "2025-11-09T12:00:00Z"
    },
    {
      "id": 2,
      "name": "Brot",
      "quantity": "1",
      "is_checked": true,
      "order_index": 1,
      "created_at": "2025-11-09T12:05:00Z"
    }
  ]
}
```

---

### POST `/lists/{list_id}/items`

Item zu Liste hinzufügen.

**Zugriff:** Besitzer, Admin oder wenn geteilt.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "Eier",
  "quantity": "10 Stück"
}
```

**Response: 201 Created**
```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "Eier",
    "quantity": "10 Stück",
    "is_checked": false,
    "order_index": 3,
    "created_at": "2025-11-09T16:00:00Z"
  },
  "message": "Artikel erfolgreich hinzugefügt"
}
```

**Errors:**
- `400` - Validierungsfehler
- `401` - Nicht authentifiziert
- `403` - Zugriff verweigert
- `404` - Liste nicht gefunden

---

### GET `/items/{item_id}`

Item-Details abrufen.

**Zugriff:** Besitzer, Admin oder wenn Liste geteilt.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Milch",
    "quantity": "2L",
    "is_checked": false,
    "order_index": 1,
    "created_at": "2025-11-09T12:00:00Z",
    "list_id": 1,
    "list_title": "Wocheneinkauf"
  }
}
```

---

### PUT `/items/{item_id}`

Item aktualisieren.

**Zugriff:** Besitzer, Admin oder wenn Liste geteilt.

**Hinweis:** Unterstützt Optimistic Locking (siehe [Versionskontrolle](#optimistic-locking-versionskontrolle))

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "Vollmilch (optional)",
  "quantity": "3L (optional)",
  "is_checked": true,
  "version": 2
}
```

**Felder:**
- `name` (string, optional): Neuer Name des Artikels
- `quantity` (string, optional): Neue Menge
- `is_checked` (boolean, optional): Checkbox-Status
- `version` (integer, optional): Aktuelle Version für Optimistic Locking

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Vollmilch",
    "quantity": "3L",
    "is_checked": true,
    "order_index": 1,
    "created_at": "2025-11-09T12:00:00Z"
  },
  "message": "Artikel erfolgreich aktualisiert"
}
```

---

### DELETE `/items/{item_id}`

Item löschen.

**Zugriff:** Besitzer, Admin oder wenn Liste geteilt.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Artikel \"Milch\" erfolgreich gelöscht"
}
```

---

### POST `/items/{item_id}/toggle`

Item abhaken/abhaken rückgängig.

**Zugriff:** Besitzer, Admin oder wenn Liste geteilt.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "is_checked": true
  },
  "message": "Artikel \"Milch\" abgehakt"
}
```

---

### PUT `/items/{item_id}/reorder`

Reihenfolge eines Items ändern.

**Zugriff:** Nur Besitzer oder Admin.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "order_index": 5
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "order_index": 5
  },
  "message": "Reihenfolge erfolgreich geändert"
}
```

---

### POST `/lists/{list_id}/items/clear-checked`

Alle abgehakten Items löschen.

**Zugriff:** Nur Besitzer oder Admin.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "deleted_count": 3
  },
  "message": "3 abgehakte Artikel wurden entfernt"
}
```

---

## Shared Lists (Public)

Diese Endpoints benötigen **keine Authentifizierung**.

### GET `/shared/{guid}`

Geteilte Liste mit Items abrufen.

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "guid": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Wocheneinkauf",
    "owner": "john_doe",
    "created_at": "2025-11-09T12:00:00Z",
    "updated_at": "2025-11-09T14:30:00Z",
    "items": [
      {
        "id": 1,
        "name": "Milch",
        "quantity": "2L",
        "is_checked": false,
        "order_index": 1,
        "created_at": "2025-11-09T12:00:00Z"
      }
    ]
  }
}
```

**Errors:**
- `404` - Liste nicht gefunden oder nicht geteilt

---

### GET `/shared/{guid}/items`

Nur Items einer geteilten Liste abrufen.

**Response: 200 OK**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Milch",
      "quantity": "2L",
      "is_checked": false,
      "order_index": 1,
      "created_at": "2025-11-09T12:00:00Z"
    }
  ]
}
```

---

### GET `/shared/{guid}/info`

Basis-Informationen einer geteilten Liste.

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "guid": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Wocheneinkauf",
    "owner": "john_doe",
    "is_shared": true,
    "created_at": "2025-11-09T12:00:00Z",
    "updated_at": "2025-11-09T14:30:00Z",
    "item_count": 5,
    "checked_count": 2
  }
}
```

---

## Admin

Alle Admin-Endpoints benötigen Admin-Rechte.

### GET `/admin/stats`

System-Statistiken abrufen.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "users": {
      "total": 50,
      "admins": 2,
      "regular": 48
    },
    "lists": {
      "total": 120,
      "shared": 30,
      "private": 90
    },
    "items": {
      "total": 450,
      "checked": 200,
      "unchecked": 250
    },
    "tokens": {
      "revoked": 15
    },
    "top_users": [
      {
        "user_id": 1,
        "username": "john_doe",
        "list_count": 10
      }
    ],
    "largest_lists": [
      {
        "list_id": 5,
        "title": "Mega Einkauf",
        "owner_id": 1,
        "owner": "john_doe",
        "item_count": 50
      }
    ]
  }
}
```

---

### GET `/admin/lists`

Alle Listen aller Benutzer abrufen.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `shared_only` (bool, default: false)

**Response: 200 OK**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "guid": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Wocheneinkauf",
      "is_shared": true,
      "owner_id": 1,
      "owner_username": "john_doe",
      "created_at": "2025-11-09T12:00:00Z",
      "updated_at": "2025-11-09T14:30:00Z",
      "item_count": 5
    }
  ],
  "pagination": { /* ... */ }
}
```

---

### DELETE `/admin/lists/{list_id}`

Beliebige Liste löschen.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Einkaufsliste \"Wocheneinkauf\" von Benutzer \"john_doe\" erfolgreich gelöscht"
}
```

---

### POST `/admin/tokens/cleanup`

Abgelaufene Tokens aus Blacklist entfernen.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "deleted_count": 10
  },
  "message": "10 abgelaufene Tokens wurden entfernt"
}
```

---

### GET `/admin/tokens/stats`

Token-Statistiken abrufen.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "total_revoked": 15,
    "by_type": {
      "access": 10,
      "refresh": 5
    },
    "recent_revocations": [
      {
        "jti": "abc123...",
        "type": "access",
        "user_id": 1,
        "revoked_at": "2025-11-09T15:00:00Z",
        "expires_at": "2025-11-09T15:30:00Z"
      }
    ]
  }
}
```

---

### GET `/admin/users/{user_id}/activity`

Aktivitäts-Statistiken für einen Benutzer.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "is_admin": false,
      "created_at": "2025-11-09T12:00:00Z"
    },
    "lists": {
      "total": 10,
      "shared": 3,
      "private": 7
    },
    "items": {
      "total": 50
    },
    "recent_lists": [
      {
        "id": 1,
        "title": "Wocheneinkauf",
        "is_shared": true,
        "updated_at": "2025-11-09T14:30:00Z",
        "item_count": 5
      }
    ]
  }
}
```

---

## HTTP Status Codes

| Code | Bedeutung |
|------|-----------|
| 200 | OK - Request erfolgreich |
| 201 | Created - Ressource erstellt |
| 400 | Bad Request - Validierungsfehler |
| 401 | Unauthorized - Authentifizierung erforderlich |
| 403 | Forbidden - Zugriff verweigert |
| 404 | Not Found - Ressource nicht gefunden |
| 409 | Conflict - Konflikt mit bestehenden Daten |
| 500 | Internal Server Error - Serverfehler |

---

## Best Practices für Mobile Apps

### 1. Token-Management

```javascript
// Token speichern
await SecureStore.setItemAsync('access_token', tokens.access_token);
await SecureStore.setItemAsync('refresh_token', tokens.refresh_token);

// Token abrufen
const accessToken = await SecureStore.getItemAsync('access_token');

// Bei 401 Error: Token refresh
if (error.status === 401) {
  const newToken = await refreshAccessToken();
  // Request wiederholen
}
```

### 2. Error Handling

```javascript
try {
  const response = await api.get('/lists');
  return response.data;
} catch (error) {
  if (error.response) {
    // API Error
    const errorCode = error.response.data.error.code;
    const errorMessage = error.response.data.error.message;

    switch(errorCode) {
      case 'TOKEN_EXPIRED':
        // Refresh token
        break;
      case 'NOT_FOUND':
        // Show not found UI
        break;
      default:
        // Show error message
    }
  }
}
```

### 3. Optimistic Updates

```javascript
// Item abhaken (optimistisch)
const toggleItem = async (itemId) => {
  // UI sofort aktualisieren
  setItems(prev => prev.map(item =>
    item.id === itemId
      ? {...item, is_checked: !item.is_checked}
      : item
  ));

  try {
    // API Request
    await api.post(`/items/${itemId}/toggle`);
  } catch (error) {
    // Bei Fehler: Zurücksetzen
    setItems(prev => prev.map(item =>
      item.id === itemId
        ? {...item, is_checked: !item.is_checked}
        : item
    ));
  }
};
```

### 4. Pagination

```javascript
const loadMore = async () => {
  const nextPage = currentPage + 1;
  const response = await api.get(`/lists?page=${nextPage}&per_page=20`);

  if (response.data.pagination.has_next) {
    setLists([...lists, ...response.data.data]);
    setCurrentPage(nextPage);
  }
};
```

---

## Changelog

### Version 1.0 (2025-11-09)

- Initiales Release
- JWT-Authentifizierung
- User Management
- Shopping Lists CRUD
- Shopping Items CRUD
- Shared Lists (public)
- Admin-Funktionen

---

## Support

Bei Fragen oder Problemen:
- GitHub Issues: [your-repo/issues]
- E-Mail: support@your-domain.com

---

**Ende der Dokumentation**
