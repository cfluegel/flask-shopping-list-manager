# Frontend Design System - Grocery Shopping List

## Übersicht

Das Frontend wurde als vollständiges, modernes Design-System mit Mobile-First-Ansatz implementiert. Es verwendet CSS Custom Properties für Theme-Switching, semantisches HTML für Accessibility und JavaScript für dynamische Interaktionen ohne Seitenneuladung.

---

## Farbschema

### Light Theme (Standard)
- **Primärfarbe (Orange):** `#ff8c42`
- **Primär Dark:** `#e67837`
- **Primär Light:** `#ffb380`
- **Sekundär (Pastell):** `#ffd4a3`
- **Akzent:** `#ffecdb`
- **Hintergrund:** `#fafafa`
- **Oberflächen:** `#ffffff`
- **Text:** `#2d2d2d`

### Dark Theme
- **Primärfarbe (Hellblau):** `#4a9eff`
- **Primär Dark:** `#3d8ee6`
- **Primär Light:** `#6db3ff`
- **Sekundär (Dunkelblau):** `#2c5f8d`
- **Akzent:** `#1a3a52`
- **Hintergrund:** `#0f1419`
- **Oberflächen:** `#1a2332`
- **Text:** `#e8eaed`

---

## Implementierte Features

### 1. Design System

**CSS Custom Properties (`/app/main/static/css/main.css`)**
- Vollständiges Theme-System mit Light/Dark Varianten
- Konsistente Spacing-Skala (xs, sm, md, lg, xl, 2xl)
- Definierte Border Radius Werte (sm, md, lg, full)
- Typography-System mit Font-Größen
- Shadow-System (sm, md, lg)
- Transition-Zeiten (fast, base, slow)

**Responsive Breakpoints:**
- Mobile: < 768px (Mobile-First)
- Tablet: >= 768px
- Desktop: >= 1200px

### 2. Komponenten

**Navigation Bar**
- Sticky Navigation mit Logo
- Responsive Burger-Menu für Mobile
- Theme-Switcher Integration
- Benutzer-Status-Anzeige
- Auto-Schließen bei Click außerhalb

**Buttons**
- Varianten: Primary, Secondary, Danger, Success
- Größen: Small, Default, Large
- Icon-Only Buttons
- Block-Buttons (volle Breite)
- Touch-friendly (min. 44x44px)
- Focus States für Accessibility

**Cards**
- Basis-Card mit Shadow
- Hover-Effekte
- Header/Body/Footer Sections
- Shopping List Cards mit Grid-Layout

**Forms**
- Konsistente Form-Controls
- Inline Forms für Item-Hinzufügen
- Checkbox-Styling mit accent-color
- Error-States
- Focus-States mit Ring
- Labels und Placeholders

**Shopping List Items**
- Checkbox für Checked-State
- Durchgestrichene Darstellung bei Checked
- Quantity Badge (orange)
- Item Name
- Actions (Delete) mit Hover-States
- Optimistic Updates via JavaScript

**Tables**
- Responsive Table-Wrapper
- Hover-States für Rows
- Admin-Tabellen für Benutzer/Listen

**Flash Messages**
- Toast-Style Notifications
- Fixed Position (top-right)
- Auto-Dismiss nach 5 Sekunden
- Slide-In/Out Animationen
- Varianten: Success, Danger, Warning, Info
- Close-Button

**Badges**
- Primary, Success, Warning, Info
- Pill-Style (rounded-full)
- Icon-Integration möglich

### 3. Templates

**Erstellt:**
- `/app/main/templates/base.html` - Basis-Template mit Navigation und Theme-Switcher
- `/app/main/templates/index.html` - Landing Page mit Features und CTA
- `/app/main/templates/login.html` - Login-Formular
- `/app/main/templates/dashboard.html` - Benutzer-Dashboard mit Listen-Grid
- `/app/main/templates/create_list.html` - Neue Liste erstellen
- `/app/main/templates/edit_list.html` - Liste bearbeiten
- `/app/main/templates/view_list.html` - Listen-Detail mit Items
- `/app/main/templates/shared_list.html` - Öffentlich geteilte Liste
- `/app/main/templates/admin/dashboard.html` - Admin-Übersicht
- `/app/main/templates/admin/users.html` - Benutzerverwaltung
- `/app/main/templates/admin/create_user.html` - Benutzer erstellen
- `/app/main/templates/admin/edit_user.html` - Benutzer bearbeiten
- `/app/main/templates/admin/lists.html` - Listenverwaltung

### 4. JavaScript Features (`/app/main/static/js/main.js`)

**ThemeManager**
- **Automatische System-Theme-Erkennung** via `prefers-color-scheme`
- Theme-Switching zwischen Light/Dark
- LocalStorage-Persistenz für manuelle Auswahl
- Automatisches Laden: System-Theme oder gespeicherte Präferenz
- Button-State-Management
- Live-Update bei Änderung der Systemeinstellung (wenn keine manuelle Präferenz)

**MobileNav**
- Burger-Menu Toggle
- Auto-Close bei Click außerhalb
- Auto-Close bei Link-Click
- Aria-Labels für Accessibility

**FlashMessages**
- Auto-Dismiss nach 5 Sekunden
- Smooth Slide-Out Animation
- Manual Close via Button

**ShoppingListManager**
- Checkbox-Toggle via AJAX
- Optimistic UI Updates
- Rollback bei Fehler
- Toast-Notifications bei Fehler
- Enhanced Form Submission (optional)
- Loading States

**FormEnhancements**
- Auto-Focus erstes Input (Desktop)
- Loading States bei Submit
- Disabled während Verarbeitung
- Fallback Re-Enable nach 5s

**KeyboardShortcuts**
- Ctrl/Cmd + K: Focus Add-Item Input
- Escape: Close Mobile Menu

**AccessibilityEnhancements**
- Skip-to-Main-Content Link
- Keyboard-Accessibility für alle Clickables
- Proper ARIA-Labels
- Role-Attributes

**LazyLoad**
- Image Lazy-Loading via IntersectionObserver
- Fallback für ältere Browser

### 5. Accessibility (WCAG AA)

- Semantisches HTML (nav, main, header, footer)
- ARIA-Labels und Roles
- Keyboard-Navigation
- Focus States überall
- Skip-to-Main-Content Link
- Kontrast-Verhältnisse erfüllt
- Touch-Targets min. 44x44px
- Screen-Reader-freundlich

### 6. Performance

- CSS Custom Properties (schneller als SASS)
- Minimale JavaScript-Abhängigkeiten (Vanilla JS)
- Lazy-Loading für Bilder
- Optimistic Updates (sofortiges UI-Feedback)
- Smooth Transitions (Hardware-beschleunigt)
- Mobile-First CSS (kleinere Initial-Payload)

### 7. Responsive Design

**Mobile (< 768px):**
- Burger-Menu
- Stacked Layouts
- Full-Width Buttons
- Touch-optimierte Elemente
- Reduced Font-Sizes

**Tablet (>= 768px):**
- Horizontal Navigation
- Grid-Layouts (2 Spalten)
- Größere Spacing

**Desktop (>= 1200px):**
- Max Container Width (1200px)
- Grid-Layouts (3+ Spalten)
- Hover-States aktiv

---

## Architektur-Entscheidungen

### 1. Warum CSS Custom Properties statt SASS?
- Native Browser-Support
- Runtime Theme-Switching ohne Reload
- Kein Build-Step erforderlich
- Bessere Performance
- Einfachere Wartung

### 2. Warum Vanilla JavaScript?
- Keine externen Abhängigkeiten
- Kleinere Bundle-Größe
- Bessere Performance
- Moderne Browser-APIs ausreichend
- Einfacher zu verstehen/warten

### 3. Mobile-First Ansatz
- Progressives Enhancement
- Bessere Performance auf Mobile
- Erzwingt Fokus auf Essentials
- Einfacher zu skalieren (up statt down)

### 4. Inline SVGs statt Icon-Font
- Bessere Accessibility
- Kleinere Payload (nur genutzte Icons)
- Einfachere Styling-Kontrolle
- Keine FOUT (Flash of Unstyled Text)

### 5. Optimistic UI Updates
- Bessere User Experience
- Gefühl von Geschwindigkeit
- Rollback bei Fehler
- Standard in modernen Apps

---

## Verwendung

### Theme Switching

Das Theme wird automatisch anhand der **Systemeinstellung** erkannt (`prefers-color-scheme`). Falls der Benutzer manuell ein Theme wählt, wird diese Präferenz im LocalStorage gespeichert und hat Vorrang.

**Funktionsweise:**
1. Beim ersten Besuch: System-Theme wird automatisch verwendet (Dark/Light)
2. Bei manueller Wahl: Theme-Präferenz wird gespeichert
3. Bei Änderung der Systemeinstellung: Automatische Anpassung (nur wenn keine manuelle Präferenz gesetzt)

```html
<div class="theme-switcher">
  <button id="theme-light" class="active">☀️</button>
  <button id="theme-dark">🌙</button>
</div>
```

### Neue Komponente hinzufügen

CSS-Klassen folgen BEM-ähnlicher Konvention:

```css
.component-name {
  /* Base styles */
}

.component-name-element {
  /* Element styles */
}

.component-name--modifier {
  /* Modifier styles */
}
```

### Shopping List Items

```html
<li class="shopping-item" data-item-id="123">
  <input type="checkbox" class="shopping-item-checkbox" data-item-id="123">
  <div class="shopping-item-content">
    <span class="shopping-item-quantity">2x</span>
    <span class="shopping-item-name">Milch</span>
  </div>
  <div class="shopping-item-actions">
    <button class="btn btn-icon btn-sm btn-danger">🗑️</button>
  </div>
</li>
```

### Button-Varianten

```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-danger">Danger</button>
<button class="btn btn-success">Success</button>

<!-- Sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary">Default</button>
<button class="btn btn-primary btn-lg">Large</button>

<!-- Block -->
<button class="btn btn-primary btn-block">Full Width</button>
```

---

## Browser-Support

- Chrome/Edge: >= 90
- Firefox: >= 88
- Safari: >= 14
- Mobile Safari: >= 14
- Chrome Android: >= 90

**Features mit Fallback:**
- CSS Custom Properties (erforderlich, kein Fallback)
- IntersectionObserver (Fallback für LazyLoad)
- CSS Grid (Fallback: Flexbox)
- Fetch API (erforderlich für AJAX)

---

## Progressive Web App (PWA)

Die PWA ist unter `/pwa/` verfügbar und bietet eine native App-ähnliche Erfahrung.

### Architektur

- **SPA-Shell:** Jinja2-Template (`app/pwa/templates/pwa.html`) als Einstiegspunkt
- **Blueprint:** `app/pwa/` mit eigenem Template-Ordner
- **Statische Assets:** `app/static/pwa/`
- **Kein Build-Step:** Vanilla JavaScript mit ES6-Modulen

### Routing

Hash-basiertes Routing (`#/login`, `#/lists`, `#/lists/1`):
- `app/static/pwa/js/router.js` — Router-Klasse
- Views werden dynamisch geladen und gerendert

### JavaScript-Module

| Datei | Beschreibung |
|-------|--------------|
| `js/app.js` | App-Einstiegspunkt, initialisiert Router und Views |
| `js/auth.js` | JWT-Authentifizierung, Token-Storage |
| `js/api.js` | API-Client für `/api/v1/` Endpoints |
| `js/router.js` | Hash-basierter Router |
| `js/views/login-view.js` | Login-Screen |
| `js/views/lists-view.js` | Listen-Übersicht |
| `js/views/list-detail-view.js` | Listen-Detail mit Items |

### Offline & Caching

- **Service Worker** (`app/static/pwa/sw.js`): Caching von statischen Assets
- **Manifest** (`app/static/pwa/manifest.json`): Install-to-Homescreen
- **Icons:** 192x192 und 512x512 PNG

### Screens

1. **Login:** JWT-Authentifizierung gegen `/api/v1/auth/login`
2. **Listen-Übersicht:** Alle eigenen Listen mit Erstellen-Button
3. **Listen-Detail:** Items anzeigen, hinzufügen, abhaken, löschen

### Testing

197 PWA-Tests in `tests/test_pwa.py` (16 Test-Klassen), die Blueprint-Registrierung, Route-Handling, Template-Rendering, Service-Worker-Auslieferung und Manifest-Konfiguration abdecken.

---

## Mögliche Erweiterungen

1. **Erweiterte Animationen:**
   - Drag & Drop für Item-Reordering
   - Swipe-to-Delete auf Mobile

2. **Weitere Features:**
   - Bulk-Actions (alle abhaken/löschen)
   - Item-Kategorien mit Farben
   - Item-Suche/Filter

3. **Performance:**
   - CSS/JS Minification
   - Image Optimization

---

## Testing

### Manuell getestet:
- [x] Light/Dark Theme Switching
- [x] Mobile Navigation
- [x] Item Toggle (Checkbox)
- [x] Flash Messages
- [x] Responsive Layouts (Mobile, Tablet, Desktop)
- [x] Keyboard Navigation
- [x] Form Submissions
- [x] Loading States

### Zu testen:
- [ ] Cross-Browser (Safari, Firefox, Edge)
- [ ] Screen Reader (VoiceOver, NVDA)
- [ ] Touch-Devices
- [ ] Slow Network (3G)
- [ ] Offline-Verhalten

---

## Wartung

### CSS
- Neue Farben in `:root` und `[data-theme="dark"]` definieren
- Spacing/Typography aus Variables nutzen
- Komponenten modular halten

### JavaScript
- Klassen-basierte Architektur beibehalten
- Event Delegation wo möglich
- Error Handling nicht vergessen
- Console-Logs für Debugging

### Templates
- Jinja2-Blöcke konsequent nutzen
- Accessibility-Attribute nicht vergessen
- SVG-Icons inline für Styling
- Semantic HTML verwenden

---

## Dateien-Übersicht

```
app/main/
├── static/
│   ├── css/
│   │   └── main.css           (5.500+ Zeilen, vollständiges Design-System)
│   └── js/
│       └── main.js            (650+ Zeilen, alle Interaktionen)
└── templates/
    ├── base.html              (Basis-Template mit Nav & Footer)
    ├── index.html             (Landing Page)
    ├── login.html             (Login-Formular)
    ├── dashboard.html         (Benutzer-Dashboard)
    ├── create_list.html       (Liste erstellen)
    ├── edit_list.html         (Liste bearbeiten)
    ├── view_list.html         (Listen-Detail)
    ├── shared_list.html       (Geteilte Liste)
    └── admin/
        ├── dashboard.html     (Admin-Übersicht)
        ├── users.html         (Benutzerverwaltung)
        ├── create_user.html   (Benutzer erstellen)
        ├── edit_user.html     (Benutzer bearbeiten)
        └── lists.html         (Listenverwaltung)
```

---

## Zusammenarbeit mit Backend

### Offene Punkte für Backend-Team:

1. **API-Endpoints:**
   - `/items/<id>/toggle` - POST für Checkbox-Toggle (bereits implementiert)
   - Response-Format: `{"success": true, "is_checked": true}`

2. **Forms:**
   - Alle Forms nutzen Flask-WTF Forms mit CSRF-Protection
   - Form-Objekte werden in Templates als `form` übergeben
   - Error-Handling über `form.field.errors`

3. **Flash Messages:**
   - Kategorien: `success`, `danger`, `warning`, `info`
   - Werden automatisch gestylt und auto-dismissed

4. **Template Context:**
   - `current_user` - für User-Authentifizierung
   - `url_for()` - für URLs
   - Jinja2-Filters: `strftime()` für Datum

5. **Static Files:**
   - CSS: `{{ url_for('main.static', filename='css/main.css') }}`
   - JS: `{{ url_for('main.static', filename='js/main.js') }}`

---

## Kontakt & Support

Bei Fragen zum Frontend-Design oder für Anpassungen:
- Design-System: siehe `main.css` CSS Custom Properties
- JavaScript-Features: siehe `main.js` Klassen-Kommentare
- Template-Struktur: alle Templates nutzen `base.html`

**Wichtig:** Beim Hinzufügen neuer Features bitte das Design-System nutzen (Farben, Spacing, Components) für Konsistenz!
