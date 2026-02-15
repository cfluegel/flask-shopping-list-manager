# Progressive Web App (PWA)

## Übersicht

Die PWA ist unter `/pwa/` verfügbar und bietet eine native App-ähnliche Erfahrung für die Verwaltung von Einkaufslisten. Sie kommuniziert ausschließlich über die REST API (`/api/v1/`) mit dem Backend und verwendet JWT-Token zur Authentifizierung.

**Aufruf:** `https://<domain>/pwa/`

**Install:** Über den Browser-Menüpunkt "Zum Startbildschirm hinzufügen" / "App installieren" kann die PWA als eigenständige App installiert werden.

---

## Architektur

### Prinzipien

- **Kein Build-Step:** Vanilla JavaScript mit globalen Klassen (kein Bundler, kein Framework)
- **SPA-Shell:** Ein einziges Jinja2-Template (`pwa.html`) dient als Shell; JavaScript übernimmt das Routing und Rendering
- **API-only:** Alle Daten kommen aus der REST API; die PWA rendert kein Server-seitiges HTML
- **Offline-fähig:** Service Worker cached die App-Shell für Offline-Zugriff

### Ablauf

```
Browser → /pwa/ → Flask (pwa.html Template)
                     ↓
                  JavaScript lädt
                     ↓
                  Router prüft Auth-Status
                     ↓
              ┌──────┴──────┐
          Eingeloggt?     Nicht eingeloggt?
              ↓                  ↓
          #/lists            #/login
              ↓                  ↓
         ListsView          LoginView
              ↓                  ↓
         API-Calls        Login → API-Tokens
```

---

## Blueprint (`app/pwa/`)

### Dateien

| Datei | Beschreibung |
|-------|--------------|
| `__init__.py` | Blueprint-Definition (`pwa_bp`, `template_folder='templates'`) |
| `routes.py` | Drei Routes (siehe unten) |
| `templates/pwa.html` | SPA-Shell Template |

### Routes

| Route | Funktion | Beschreibung |
|-------|----------|--------------|
| `/` und `/<path:path>` | `index()` | Liefert das SPA-Shell Template für alle PWA-Pfade |
| `/manifest.json` | `manifest()` | PWA-Manifest (MIME: `application/manifest+json`) |
| `/sw.js` | `service_worker()` | Service Worker (MIME: `application/javascript`) |

Die Catch-all Route `/<path:path>` stellt sicher, dass bei einem Reload (z.B. auf `/pwa/lists/5`) immer die SPA-Shell ausgeliefert wird und der JavaScript-Router die richtige View lädt.

---

## JavaScript-Module

Alle Dateien liegen in `app/static/pwa/js/`. Sie werden als klassische `<script>`-Tags (nicht als ES-Module) geladen und verwenden globale Singletons.

### Lade-Reihenfolge

```html
<script src=".../auth.js"></script>     <!-- 1. authManager -->
<script src=".../api.js"></script>      <!-- 2. apiClient (nutzt authManager) -->
<script src=".../router.js"></script>   <!-- 3. router -->
<script src=".../views/login-view.js"></script>
<script src=".../views/lists-view.js"></script>
<script src=".../views/list-detail-view.js"></script>
<script src=".../app.js"></script>      <!-- 7. App (startet router) -->
```

### AuthManager (`auth.js`)

Verwaltet JWT-Tokens in `localStorage`.

| Methode | Beschreibung |
|---------|--------------|
| `getAccessToken()` | Access Token aus localStorage |
| `getRefreshToken()` | Refresh Token aus localStorage |
| `setTokens(access, refresh)` | Tokens speichern |
| `setUser(user)` | User-Objekt speichern |
| `getUser()` | User-Objekt lesen |
| `clearAll()` | Alle Auth-Daten löschen |
| `isAuthenticated()` | Prüft ob Access Token vorhanden |
| `refreshAccessToken()` | Erneuert Access Token über `/api/v1/auth/refresh` |

**LocalStorage Keys:**
- `pwa_access_token`
- `pwa_refresh_token`
- `pwa_user`

### APIClient (`api.js`)

Fetch-Wrapper mit automatischem Token-Refresh bei 401-Antworten.

| Methode | API-Endpoint | Beschreibung |
|---------|-------------|--------------|
| `login(user, pw)` | `POST /auth/login` | Login, speichert Tokens |
| `logout()` | `POST /auth/logout` | Logout, löscht Tokens |
| `getLists()` | `GET /lists` | Alle eigenen Listen |
| `getList(id)` | `GET /lists/:id` | Einzelne Liste mit Items |
| `createList(title)` | `POST /lists` | Neue Liste erstellen |
| `deleteList(id)` | `DELETE /lists/:id` | Liste löschen |
| `createItem(listId, name, qty)` | `POST /lists/:id/items` | Item hinzufügen |
| `toggleItem(itemId)` | `POST /items/:id/toggle` | Checked-Status umschalten |
| `deleteItem(itemId)` | `DELETE /items/:id` | Item löschen |
| `clearCheckedItems(listId)` | `POST /lists/:id/items/clear-checked` | Abgehakte Items löschen |

**Auto-Refresh:** Wenn ein API-Aufruf mit 401 antwortet, versucht der Client automatisch einen Token-Refresh. Bei Erfolg wird der ursprüngliche Request wiederholt. Bei Fehler wird zur Login-Seite weitergeleitet. Parallele Refresh-Requests werden dedupliziert.

### Router (`router.js`)

Hash-basierter SPA-Router mit Auth-Guard.

| Methode | Beschreibung |
|---------|--------------|
| `addRoute(pattern, viewFactory)` | Route registrieren (z.B. `/lists/:id`) |
| `start()` | Router starten, initialen Hash verarbeiten |
| `navigate(hash)` | Zu Hash navigieren (z.B. `#/lists`) |

**Registrierte Routes:**

| Pattern | View | Beschreibung |
|---------|------|--------------|
| `/login` | `LoginView` | Login-Formular |
| `/lists` | `ListsView` | Listen-Übersicht |
| `/lists/:id` | `ListDetailView` | Listen-Detail mit Items |

**Auth-Guard:**
- Nicht-eingeloggte Benutzer werden zu `#/login` weitergeleitet
- Eingeloggte Benutzer auf `#/login` werden zu `#/lists` weitergeleitet
- Unbekannte Routes leiten zu `#/lists` weiter

**View-Lifecycle:**
1. `viewFactory(params)` erstellt die View-Instanz
2. `view.render(container)` rendert in den `#pwa-content` Container
3. `view.destroy()` wird beim Routenwechsel aufgerufen (Cleanup)

### Views

#### LoginView (`views/login-view.js`)

- Zeigt Login-Formular (Benutzername + Passwort)
- Bei Erfolg: Weiterleitung zu `#/lists`
- Bei Fehler: Fehlermeldung im Formular
- Disabled-State während des Login-Vorgangs
- Versteckt Logout-Button und Back-Button

#### ListsView (`views/lists-view.js`)

- Zeigt alle eigenen Listen als Karten-Grid
- Formular zum Erstellen neuer Listen (oben)
- Klick auf Karte navigiert zu `#/lists/:id`
- Leerer Zustand mit Hinweistext
- Zeigt Item-Count pro Liste
- HTML-Escaping für alle User-Eingaben

#### ListDetailView (`views/list-detail-view.js`)

- Zeigt alle Items einer Liste
- Formular zum Hinzufügen neuer Items (Name + Menge)
- Checkbox zum Abhaken (Optimistic UI mit Rollback bei Fehler)
- Löschen-Button pro Item (mit Bestätigungsdialog)
- "Abgehakte löschen"-Button (nur sichtbar wenn abgehakte Items existieren)
- Back-Button navigiert zu `#/lists`
- HTML-Escaping für alle User-Eingaben

---

## App-Klasse (`app.js`)

Hauptcontroller der PWA. Wird beim `DOMContentLoaded`-Event instanziiert.

| Methode | Beschreibung |
|---------|--------------|
| `constructor()` | Initialisiert Theme, Routes, Header, Service Worker |
| `_initTheme()` | Lädt Theme aus `localStorage` (`pwa_theme`) |
| `_toggleTheme()` | Wechselt zwischen Light/Dark Theme |
| `_registerServiceWorker()` | Registriert `/pwa/sw.js` mit Scope `/pwa/` |

**Statische Methoden (von Views verwendet):**

| Methode | Beschreibung |
|---------|--------------|
| `App.setTitle(title)` | Setzt Header-Titel |
| `App.showBackButton(show, onClick)` | Zeigt/versteckt Back-Button |
| `App.showLogoutButton(show)` | Zeigt/versteckt Logout-Button |
| `App.showToast(message, type, duration)` | Zeigt Toast-Notification (info/success/error) |
| `App.confirm(message)` | Zeigt Bestätigungsdialog (Promise-basiert) |

---

## Service Worker (`sw.js`)

### Caching-Strategie

- **App-Shell (Cache-First):** SPA-Shell, CSS, JavaScript, Icons und Manifest werden beim Install gecached. Nachfolgende Requests werden aus dem Cache bedient.
- **API-Requests (Network-Only):** Alle Requests an `/api/` werden nicht gecached, sondern direkt ans Netzwerk weitergeleitet.

### Cache Version

```javascript
const CACHE_VERSION = 'pwa-v1';
```

Bei einem Update des Cache-Namens werden beim Activate-Event alte Caches automatisch gelöscht.

### Gecachte URLs

```
/pwa/
/pwa/manifest.json
/static/css/main.css
/static/pwa/css/pwa.css
/static/pwa/js/auth.js
/static/pwa/js/api.js
/static/pwa/js/router.js
/static/pwa/js/views/login-view.js
/static/pwa/js/views/lists-view.js
/static/pwa/js/views/list-detail-view.js
/static/pwa/js/app.js
/static/pwa/icons/icon-192.png
/static/pwa/icons/icon-512.png
```

---

## PWA Manifest (`manifest.json`)

```json
{
  "name": "Einkaufsliste",
  "short_name": "Einkaufsliste",
  "start_url": "/pwa/",
  "display": "standalone",
  "theme_color": "#ff8c42",
  "background_color": "#fafafa",
  "lang": "de",
  "orientation": "portrait-primary"
}
```

**Icons:** 192x192 und 512x512 PNG mit `purpose: "any maskable"`.

---

## Styling

Die PWA-CSS-Datei (`app/static/pwa/css/pwa.css`) baut auf den CSS Custom Properties aus `main.css` auf und definiert:

- **App-Shell Layout:** Flexbox-basiert, `100dvh` Höhe, fester Header + scrollbarer Content
- **Header:** Sticky, mit Back-Button, Titel, Theme-Toggle und Logout-Button
- **Listen-Grid:** Responsive Karten mit Hover-Effekt
- **Item-Liste:** Checkboxen mit Durchstreich-Animation, Quantity-Badge, Delete-Button
- **Login-Formular:** Zentriert, Card-Layout
- **Toast-Notifications:** Fixed-Position unten, Slide-in/out Animation
- **Bestätigungsdialog:** Modal-Overlay mit Abbrechen/Löschen-Buttons
- **Spinner:** CSS-Lade-Animation
- **Safe Area:** Unterstützt notched Devices via `env(safe-area-inset-*)`

Unterstützt Light- und Dark-Theme über `[data-theme="dark"]` aus `main.css`.

---

## SPA-Shell Template (`pwa.html`)

Das Template enthält:

1. **Meta-Tags:** Viewport, Theme-Color, Apple-Webapp-Tags
2. **Manifest-Link:** `<link rel="manifest">`
3. **Stylesheets:** `main.css` (Design-System) + `pwa.css` (PWA-spezifisch)
4. **App-Container** (`#app`):
   - Header mit Back-Button, Titel, Theme-Toggle, Logout
   - Main-Content-Bereich (`#pwa-content`) — Views rendern hierhin
   - Toast-Container (`#toast-container`)
5. **Scripts:** Alle JS-Dateien in der richtigen Reihenfolge

---

## Dateistruktur

```
app/
├── pwa/
│   ├── __init__.py              # Blueprint: pwa_bp
│   ├── routes.py                # Routes: /, /manifest.json, /sw.js
│   └── templates/
│       └── pwa.html             # SPA-Shell Template
└── static/pwa/
    ├── css/
    │   └── pwa.css              # PWA-spezifische Styles (~490 Zeilen)
    ├── icons/
    │   ├── icon-192.png         # App-Icon 192x192
    │   └── icon-512.png         # App-Icon 512x512
    ├── js/
    │   ├── app.js               # Hauptcontroller (~130 Zeilen)
    │   ├── auth.js              # JWT Token-Management (~80 Zeilen)
    │   ├── api.js               # API-Client mit Auto-Refresh (~110 Zeilen)
    │   ├── router.js            # Hash-basierter Router (~95 Zeilen)
    │   └── views/
    │       ├── login-view.js    # Login-Screen (~70 Zeilen)
    │       ├── lists-view.js    # Listen-Übersicht (~100 Zeilen)
    │       └── list-detail-view.js  # Listen-Detail (~180 Zeilen)
    ├── manifest.json            # PWA-Manifest
    └── sw.js                    # Service Worker (~60 Zeilen)
```

---

## Testing

197 Tests in `tests/test_pwa.py` über 16 Test-Klassen:

- Blueprint-Registrierung und URL-Prefix
- SPA-Shell Rendering (HTML-Struktur, Meta-Tags, Script-Tags)
- Service Worker Route und Content-Type
- Manifest Route und JSON-Inhalt
- Catch-all Routing für Deep-Links
- Statische Assets (CSS, JS, Icons)
- Template-Kontext und Jinja2-URL-Generierung

```bash
# Nur PWA-Tests ausführen
pytest tests/test_pwa.py -v
```
