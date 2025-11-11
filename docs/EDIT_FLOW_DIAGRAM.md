# Edit-Item Flow Diagram

## Vollständiger Ablauf der Edit-Funktionalität

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                 │
└─────────────────────────────────────────────────────────────────────────┘

1. Display Mode (Initial State)
┌──────────────────────────────────────────────────────────┐
│  [ ] 2x Milch                          [Edit] [Delete]   │  <-- Item Row
└──────────────────────────────────────────────────────────┘
      │
      │ User clicks [Edit] button
      ▼

2. Edit Mode (After clicking Edit)
┌──────────────────────────────────────────────────────────┐
│  [ ] [2x   ] [Milch      ]     [Save] [Cancel] [Delete]  │
└──────────────────────────────────────────────────────────┘
      │                                    │
      │ User edits values                  │ User clicks [Cancel]
      │ User clicks [Save]                 │
      ▼                                    ▼

3a. Save Flow                         3b. Cancel Flow
     │                                     │
     ▼                                     ▼
┌─────────────────────────────────┐  ┌──────────────────────────┐
│ JavaScript: ShoppingItemEditor  │  │ Restore original values  │
│ - Collect form values           │  │ Exit edit mode           │
│ - Get CSRF token                │  │ Show display mode        │
│ - Build FormData                │  └──────────────────────────┘
│ - Send AJAX request             │
└─────────────────────────────────┘
     │
     │ fetch('/items/{id}/edit', {method: 'POST', body: FormData})
     ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (Flask)                                 │
└─────────────────────────────────────────────────────────────────────────┘

4. Route Handler: /items/<int:item_id>/edit
┌────────────────────────────────────────────────────────┐
│  @main_bp.route('/items/<int:item_id>/edit', ...)     │
│  @login_required                                       │
│  def edit_item(item_id: int):                          │
└────────────────────────────────────────────────────────┘
     │
     ▼
5. Authentication Check (Flask-Login)
┌────────────────────────────────────────────────────────┐
│  Is user logged in?                                    │
│  ├─ No  → Redirect to login (302)                      │
│  └─ Yes → Continue                                     │
└────────────────────────────────────────────────────────┘
     │
     ▼
6. Load Item from Database
┌────────────────────────────────────────────────────────┐
│  item = ShoppingListItem.query.get_or_404(item_id)     │
│  ├─ Not found → HTTP 404                               │
│  └─ Found → Continue                                   │
└────────────────────────────────────────────────────────┘
     │
     ▼
7. Authorization Check
┌────────────────────────────────────────────────────────┐
│  check_list_access(shopping_list, allow_shared=True)   │
│  ├─ Is owner?     → Yes, allowed                       │
│  ├─ Is admin?     → Yes, allowed                       │
│  ├─ Is shared?    → Yes, allowed                       │
│  └─ Otherwise     → HTTP 403 {"error": "No access"}    │
└────────────────────────────────────────────────────────┘
     │
     ▼
8. CSRF Token Validation (Flask-WTF)
┌────────────────────────────────────────────────────────┐
│  form = ShoppingListItemForm()                         │
│  CSRF token in request?                                │
│  ├─ Missing/Invalid → HTTP 400 {"errors": {...}}       │
│  └─ Valid → Continue                                   │
└────────────────────────────────────────────────────────┘
     │
     ▼
9. Form Validation
┌────────────────────────────────────────────────────────┐
│  if form.validate_on_submit():                         │
│    - name: DataRequired, Length(1-200)                 │
│    - quantity: DataRequired, Length(1-50)              │
│                                                         │
│  ├─ Invalid → HTTP 400                                 │
│  │   {"success": false, "errors": {                    │
│  │     "name": "Artikelbezeichnung ist erforderlich."  │
│  │   }}                                                │
│  │                                                      │
│  └─ Valid → Continue                                   │
└────────────────────────────────────────────────────────┘
     │
     ▼
10. Update Database
┌────────────────────────────────────────────────────────┐
│  item.name = form.name.data.strip()                    │
│  item.quantity = form.quantity.data.strip()            │
│  shopping_list.updated_at = datetime.now(timezone.utc) │
│                                                         │
│  try:                                                  │
│    db.session.commit()                                 │
│  except Exception as e:                                │
│    db.session.rollback()                               │
│    return HTTP 500 {"error": "Fehler beim Speichern"}  │
└────────────────────────────────────────────────────────┘
     │
     ▼
11. Success Response
┌────────────────────────────────────────────────────────┐
│  HTTP 200                                              │
│  {                                                     │
│    "success": true,                                    │
│    "item": {                                           │
│      "id": 1,                                          │
│      "name": "Milch",                                  │
│      "quantity": "2x",                                 │
│      "is_checked": false                               │
│    }                                                   │
│  }                                                     │
└────────────────────────────────────────────────────────┘
     │
     │ Response sent to Frontend
     ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND (JavaScript)                              │
└─────────────────────────────────────────────────────────────────────────┘

12. Handle Response
┌────────────────────────────────────────────────────────┐
│  const data = await response.json();                   │
│                                                         │
│  if (data.success) {                                   │
│    ├─ Update DOM with new values                       │
│    ├─ Exit edit mode                                   │
│    └─ Show success toast                               │
│  } else {                                              │
│    ├─ Show error toast                                 │
│    └─ Keep edit mode active                            │
│  }                                                     │
└────────────────────────────────────────────────────────┘
     │
     ▼
13. Update UI
┌────────────────────────────────────────────────────────┐
│  listItem.querySelector('.shopping-item-name')         │
│    .textContent = data.item.name;                      │
│                                                         │
│  listItem.querySelector('.shopping-item-quantity')     │
│    .textContent = data.item.quantity;                  │
└────────────────────────────────────────────────────────┘
     │
     ▼
14. Exit Edit Mode
┌────────────────────────────────────────────────────────┐
│  - Hide: .shopping-item-edit-form                      │
│  - Hide: .item-save-btn                                │
│  - Hide: .item-cancel-btn                              │
│  - Show: .shopping-item-content                        │
│  - Show: .item-edit-btn                                │
└────────────────────────────────────────────────────────┘
     │
     ▼
15. Display Mode (Final State)
┌──────────────────────────────────────────────────────────┐
│  [ ] 2x Milch                          [Edit] [Delete]   │  <-- Updated
└──────────────────────────────────────────────────────────┘
```

---

## Request/Response Details

### HTTP Request
```
POST /items/1/edit HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
Cookie: session=eyJ...
X-Requested-With: XMLHttpRequest

------WebKitFormBoundary...
Content-Disposition: form-data; name="name"

Milch
------WebKitFormBoundary...
Content-Disposition: form-data; name="quantity"

2x
------WebKitFormBoundary...
Content-Disposition: form-data; name="csrf_token"

ImQ5YzE3OWY2ZjE3MjQwNmI5N2U3MDg4ZGE5OWI2YTY1ZmQ3MjI1ZGYi...
------WebKitFormBoundary...--
```

### HTTP Response (Success)
```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "item": {
    "id": 1,
    "name": "Milch",
    "quantity": "2x",
    "is_checked": false
  }
}
```

### HTTP Response (Validation Error)
```
HTTP/1.1 400 BAD REQUEST
Content-Type: application/json

{
  "success": false,
  "errors": {
    "name": "Artikelbezeichnung ist erforderlich.",
    "quantity": "Anzahl ist erforderlich."
  }
}
```

### HTTP Response (Authorization Error)
```
HTTP/1.1 403 FORBIDDEN
Content-Type: application/json

{
  "success": false,
  "error": "Keine Berechtigung"
}
```

---

## Component Interaction Map

```
┌─────────────────────┐
│   view_list.html    │
│  (Jinja2 Template)  │
└──────────┬──────────┘
           │
           │ Renders HTML with:
           │ - Edit buttons (.item-edit-btn)
           │ - Edit forms (.shopping-item-edit-form)
           │ - Save buttons (.item-save-btn)
           │ - Cancel buttons (.item-cancel-btn)
           │ - CSRF token (hidden input)
           │
           ▼
┌─────────────────────┐
│      main.js        │
│ (JavaScript Logic)  │
└──────────┬──────────┘
           │
           │ Event Listeners:
           │ - .item-edit-btn → enterEditMode()
           │ - .item-save-btn → saveItem() → AJAX
           │ - .item-cancel-btn → cancelEdit()
           │
           ▼
┌─────────────────────┐
│   Flask Backend     │
│   routes.py         │
└──────────┬──────────┘
           │
           │ Route: /items/<id>/edit
           │ - Authentication (@login_required)
           │ - Authorization (check_list_access)
           │ - Validation (ShoppingListItemForm)
           │ - Database Update (SQLAlchemy)
           │
           ▼
┌─────────────────────┐
│     Database        │
│  (SQLite/PostgreSQL)│
└─────────────────────┘
           │
           │ Table: shopping_list_items
           │ - id (PK)
           │ - shopping_list_id (FK)
           │ - name
           │ - quantity
           │ - is_checked
           │ - order_index
           │
           └──> Updated row returned to Flask
```

---

## Error Handling Flow

```
User Action
    │
    ▼
┌───────────────────────────────────────┐
│ Frontend Validation                   │
│ - Check if name is not empty          │
│ - Check if quantity is not empty      │
└───────┬───────────────────────────────┘
        │
        │ Valid → Send AJAX Request
        │ Invalid → Show toast, focus input
        ▼
┌───────────────────────────────────────┐
│ Network Request                       │
│ try/catch for fetch errors            │
└───────┬───────────────────────────────┘
        │
        │ Success → Parse JSON
        │ Network Error → Show toast
        ▼
┌───────────────────────────────────────┐
│ Backend Processing                    │
│ - Authentication (401/302)            │
│ - Authorization (403)                 │
│ - CSRF Validation (400)               │
│ - Form Validation (400)               │
│ - Database Operation (500)            │
└───────┬───────────────────────────────┘
        │
        │ Success → HTTP 200 + JSON
        │ Error → HTTP 4xx/5xx + JSON
        ▼
┌───────────────────────────────────────┐
│ Frontend Response Handling            │
│ if (data.success) {                   │
│   - Update DOM                        │
│   - Exit edit mode                    │
│   - Show success toast                │
│ } else {                              │
│   - Show error toast                  │
│   - Keep edit mode active             │
│   - Re-enable save button             │
│ }                                     │
└───────────────────────────────────────┘
```

---

## Current Status

```
[✓] Backend Route Implementation
[✓] Backend Validation
[✓] Backend CSRF Protection
[✓] Backend Error Handling
[✓] Backend JSON Response
[✓] HTML Template Structure
[✓] HTML Edit Buttons
[✓] HTML Edit Forms
[✓] HTML CSRF Token
[✗] JavaScript Event Listeners  <-- MISSING
[✗] JavaScript AJAX Request     <-- MISSING
[✗] JavaScript DOM Updates      <-- MISSING
[✗] JavaScript Error Handling   <-- MISSING
```

---

**Conclusion:** The backend is fully functional. Only frontend JavaScript implementation is needed.

See `FRONTEND_IMPLEMENTATION_GUIDE.md` for the complete JavaScript code.
