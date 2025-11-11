# Frontend-Implementierung: Edit-Item-Funktionalität

## Für: Frontend-Design-Architect Agent

Diese Datei enthält die vollständige JavaScript-Implementierung für die Edit-Item-Funktionalität.

---

## Problem

Die Edit-Buttons in der Web-UI funktionieren nicht, weil das zugehörige JavaScript fehlt.

**Backend:** ✓ Funktioniert korrekt
**Frontend:** ✗ JavaScript fehlt

---

## Lösung: JavaScript-Code für main.js

### Option 1: Neue Klasse hinzufügen (Empfohlen)

Füge diese Klasse zu `/Users/cfluegel/Nextcloud/Development/flask-grocery-shopping-list/app/static/js/main.js` hinzu:

```javascript
// ============================================================================
// Shopping Item Edit Operations
// ============================================================================

class ShoppingItemEditor {
  constructor() {
    this.itemsList = document.getElementById('shopping-items');
    this.init();
  }

  init() {
    if (!this.itemsList) return;

    // Attach event listeners to all edit buttons
    this.attachEditListeners();
    this.attachSaveListeners();
    this.attachCancelListeners();
  }

  attachEditListeners() {
    const editButtons = this.itemsList.querySelectorAll('.item-edit-btn');

    editButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        const listItem = e.currentTarget.closest('.shopping-item');
        this.enterEditMode(listItem);
      });
    });
  }

  attachSaveListeners() {
    const saveButtons = this.itemsList.querySelectorAll('.item-save-btn');

    saveButtons.forEach(button => {
      button.addEventListener('click', async (e) => {
        const itemId = e.currentTarget.dataset.itemId;
        const listItem = e.currentTarget.closest('.shopping-item');
        await this.saveItem(itemId, listItem);
      });
    });
  }

  attachCancelListeners() {
    const cancelButtons = this.itemsList.querySelectorAll('.item-cancel-btn');

    cancelButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        const listItem = e.currentTarget.closest('.shopping-item');
        this.cancelEdit(listItem);
      });
    });
  }

  enterEditMode(listItem) {
    // Hide display elements
    const content = listItem.querySelector('.shopping-item-content');
    const editBtn = listItem.querySelector('.item-edit-btn');

    if (content) content.style.display = 'none';
    if (editBtn) editBtn.style.display = 'none';

    // Show edit elements
    const editForm = listItem.querySelector('.shopping-item-edit-form');
    const saveBtn = listItem.querySelector('.item-save-btn');
    const cancelBtn = listItem.querySelector('.item-cancel-btn');

    if (editForm) editForm.style.display = 'flex';
    if (saveBtn) saveBtn.style.display = 'inline-block';
    if (cancelBtn) cancelBtn.style.display = 'inline-block';

    // Focus on name input
    const nameInput = listItem.querySelector('.item-edit-name');
    if (nameInput) {
      nameInput.focus();
      nameInput.select();
    }
  }

  exitEditMode(listItem) {
    // Hide edit elements
    const editForm = listItem.querySelector('.shopping-item-edit-form');
    const saveBtn = listItem.querySelector('.item-save-btn');
    const cancelBtn = listItem.querySelector('.item-cancel-btn');

    if (editForm) editForm.style.display = 'none';
    if (saveBtn) saveBtn.style.display = 'none';
    if (cancelBtn) cancelBtn.style.display = 'none';

    // Show display elements
    const content = listItem.querySelector('.shopping-item-content');
    const editBtn = listItem.querySelector('.item-edit-btn');

    if (content) content.style.display = 'flex';
    if (editBtn) editBtn.style.display = 'inline-block';
  }

  cancelEdit(listItem) {
    // Restore original values from display elements
    const originalName = listItem.querySelector('.shopping-item-name').textContent;
    const originalQuantity = listItem.querySelector('.shopping-item-quantity').textContent;

    const nameInput = listItem.querySelector('.item-edit-name');
    const quantityInput = listItem.querySelector('.item-edit-quantity');

    if (nameInput) nameInput.value = originalName;
    if (quantityInput) quantityInput.value = originalQuantity;

    // Exit edit mode
    this.exitEditMode(listItem);
  }

  async saveItem(itemId, listItem) {
    // Get values from edit inputs
    const nameInput = listItem.querySelector('.item-edit-name');
    const quantityInput = listItem.querySelector('.item-edit-quantity');

    const name = nameInput ? nameInput.value.trim() : '';
    const quantity = quantityInput ? quantityInput.value.trim() : '1';

    // Validate
    if (!name) {
      this.showToast('Bitte einen Artikel-Namen eingeben', 'warning');
      if (nameInput) nameInput.focus();
      return;
    }

    if (!quantity) {
      this.showToast('Bitte eine Anzahl eingeben', 'warning');
      if (quantityInput) quantityInput.focus();
      return;
    }

    // Get CSRF token
    const csrfToken = this.getCSRFToken();
    if (!csrfToken) {
      this.showToast('CSRF-Token nicht gefunden', 'danger');
      return;
    }

    // Show loading state on save button
    const saveBtn = listItem.querySelector('.item-save-btn');
    const originalSaveBtnContent = saveBtn ? saveBtn.innerHTML : '';
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinner">
          <line x1="12" y1="2" x2="12" y2="6"></line>
          <line x1="12" y1="18" x2="12" y2="22"></line>
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
          <line x1="2" y1="12" x2="6" y2="12"></line>
          <line x1="18" y1="12" x2="22" y2="12"></line>
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
          <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
        </svg>
      `;
    }

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('name', name);
      formData.append('quantity', quantity);
      formData.append('csrf_token', csrfToken);

      // Send request
      const response = await fetch(`/items/${itemId}/edit`, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      });

      const data = await response.json();

      if (data.success) {
        // Update display elements with new values
        const nameDisplay = listItem.querySelector('.shopping-item-name');
        const quantityDisplay = listItem.querySelector('.shopping-item-quantity');

        if (nameDisplay) nameDisplay.textContent = data.item.name;
        if (quantityDisplay) quantityDisplay.textContent = data.item.quantity;

        // Exit edit mode
        this.exitEditMode(listItem);

        // Show success message
        this.showToast('Artikel aktualisiert', 'success');
      } else {
        // Handle validation errors
        const errorMsg = data.errors
          ? Object.values(data.errors).join(', ')
          : data.error || 'Unbekannter Fehler';

        this.showToast(errorMsg, 'danger');

        // Restore save button
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.innerHTML = originalSaveBtnContent;
        }
      }
    } catch (error) {
      console.error('Error editing item:', error);
      this.showToast('Netzwerkfehler beim Aktualisieren', 'danger');

      // Restore save button
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalSaveBtnContent;
      }
    }
  }

  getCSRFToken() {
    // Try to get CSRF token from hidden input
    const csrfInput = document.querySelector('input[name="csrf_token"]');
    if (csrfInput) {
      return csrfInput.value;
    }

    // Try to get from meta tag (alternative)
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
      return csrfMeta.getAttribute('content');
    }

    return null;
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('flash-messages');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `flash ${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div style="flex: 1;">${message}</div>
      <button class="flash-close" aria-label="Schließen" onclick="this.parentElement.remove()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    `;

    container.appendChild(toast);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, 5000);
  }
}
```

### Initialisierung hinzufügen

Füge in der `DOMContentLoaded`-Event-Listener-Funktion (Zeile 548) diese Zeile hinzu:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  // Initialize all managers
  new ThemeManager();
  new MobileNav();
  new FlashMessages();
  new ShoppingListManager();
  new ShoppingItemEditor();  // <-- NEU HINZUFÜGEN
  new FormEnhancements();
  new KeyboardShortcuts();
  new LazyLoad();
  new AccessibilityEnhancements();

  // Log initialization for debugging
  console.log('Grocery Shopping List initialized successfully');
});
```

---

## Option 2: Minimale Implementierung

Falls du eine kompaktere Lösung bevorzugst, kannst du dies direkt am Ende von `main.js` hinzufügen:

```javascript
// ============================================================================
// Shopping Item Edit Operations (Minimal Implementation)
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  const itemsList = document.getElementById('shopping-items');
  if (!itemsList) return;

  // Get CSRF token
  function getCSRFToken() {
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : null;
  }

  // Show toast message
  function showToast(message, type = 'info') {
    const container = document.getElementById('flash-messages');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `flash ${type}`;
    toast.innerHTML = `
      <div style="flex: 1;">${message}</div>
      <button class="flash-close" onclick="this.parentElement.remove()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
  }

  // Edit button click
  itemsList.querySelectorAll('.item-edit-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const item = e.currentTarget.closest('.shopping-item');
      item.querySelector('.shopping-item-content').style.display = 'none';
      item.querySelector('.item-edit-btn').style.display = 'none';
      item.querySelector('.shopping-item-edit-form').style.display = 'flex';
      item.querySelector('.item-save-btn').style.display = 'inline-block';
      item.querySelector('.item-cancel-btn').style.display = 'inline-block';
      item.querySelector('.item-edit-name').focus();
    });
  });

  // Cancel button click
  itemsList.querySelectorAll('.item-cancel-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const item = e.currentTarget.closest('.shopping-item');
      item.querySelector('.shopping-item-edit-form').style.display = 'none';
      item.querySelector('.item-save-btn').style.display = 'none';
      item.querySelector('.item-cancel-btn').style.display = 'none';
      item.querySelector('.shopping-item-content').style.display = 'flex';
      item.querySelector('.item-edit-btn').style.display = 'inline-block';
    });
  });

  // Save button click
  itemsList.querySelectorAll('.item-save-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const itemId = e.currentTarget.dataset.itemId;
      const item = e.currentTarget.closest('.shopping-item');
      const name = item.querySelector('.item-edit-name').value.trim();
      const quantity = item.querySelector('.item-edit-quantity').value.trim();
      const csrfToken = getCSRFToken();

      if (!name) {
        showToast('Bitte einen Artikel-Namen eingeben', 'warning');
        return;
      }

      const formData = new FormData();
      formData.append('name', name);
      formData.append('quantity', quantity);
      formData.append('csrf_token', csrfToken);

      try {
        const response = await fetch(`/items/${itemId}/edit`, {
          method: 'POST',
          body: formData,
          credentials: 'same-origin'
        });

        const data = await response.json();

        if (data.success) {
          item.querySelector('.shopping-item-name').textContent = data.item.name;
          item.querySelector('.shopping-item-quantity').textContent = data.item.quantity;
          item.querySelector('.shopping-item-edit-form').style.display = 'none';
          item.querySelector('.item-save-btn').style.display = 'none';
          item.querySelector('.item-cancel-btn').style.display = 'none';
          item.querySelector('.shopping-item-content').style.display = 'flex';
          item.querySelector('.item-edit-btn').style.display = 'inline-block';
          showToast('Artikel aktualisiert', 'success');
        } else {
          const errorMsg = data.errors ? Object.values(data.errors).join(', ') : data.error;
          showToast(errorMsg, 'danger');
        }
      } catch (error) {
        console.error('Error:', error);
        showToast('Netzwerkfehler', 'danger');
      }
    });
  });
});
```

---

## CSS für Spinner-Animation (Optional)

Falls die Spinner-Animation nicht funktioniert, füge dies zu `/Users/cfluegel/Nextcloud/Development/flask-grocery-shopping-list/app/static/css/main.css` hinzu:

```css
/* Spinner Animation */
.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
```

---

## Keyboard-Support (Optional Enhancement)

Für bessere Usability kannst du auch Enter/Escape-Support hinzufügen:

```javascript
// In der ShoppingItemEditor-Klasse, in enterEditMode():
const nameInput = listItem.querySelector('.item-edit-name');
const quantityInput = listItem.querySelector('.item-edit-quantity');

// Enter key saves
[nameInput, quantityInput].forEach(input => {
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const saveBtn = listItem.querySelector('.item-save-btn');
        if (saveBtn) saveBtn.click();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        const cancelBtn = listItem.querySelector('.item-cancel-btn');
        if (cancelBtn) cancelBtn.click();
      }
    });
  }
});
```

---

## Testing

Nach der Implementierung:

1. **Browser-Console öffnen** (F12)
2. **Auf Edit-Button klicken**
3. **Werte ändern**
4. **Auf Save klicken**
5. **Network-Tab prüfen:**
   - Request URL: `/items/{id}/edit`
   - Method: `POST`
   - Status: `200 OK`
   - Response: `{"success": true, "item": {...}}`

---

## Debug-Tipps

Falls es nicht funktioniert:

```javascript
// CSRF-Token prüfen
console.log('CSRF Token:', document.querySelector('input[name="csrf_token"]')?.value);

// Event-Listener prüfen
console.log('Edit buttons:', document.querySelectorAll('.item-edit-btn').length);
console.log('Save buttons:', document.querySelectorAll('.item-save-btn').length);

// Request-Daten prüfen
console.log('FormData:', [...formData.entries()]);
```

---

## Zusammenfassung

**Was zu tun ist:**
1. Option 1 ODER Option 2 implementieren
2. CSS für Spinner hinzufügen (optional)
3. Testen im Browser
4. ggf. Debug-Code hinzufügen

**Backend:** Keine Änderungen nötig ✓
**Frontend:** JavaScript-Code hinzufügen wie oben beschrieben

---

**Erstellt von:** Backend-Agent
**Für:** Frontend-Design-Architect Agent
**Datum:** 2025-11-10
