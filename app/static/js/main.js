/**
 * Grocery Shopping List - Main JavaScript
 * Handles theme switching, mobile menu, dynamic item operations
 */

// ============================================================================
// Theme Management
// ============================================================================

class ThemeManager {
  constructor() {
    this.lightButton = document.getElementById('theme-light');
    this.darkButton = document.getElementById('theme-dark');
    this.currentTheme = this.getTheme();

    this.init();
  }

  init() {
    // Apply theme
    this.applyTheme(this.currentTheme);

    // Add event listeners for manual theme switching
    if (this.lightButton) {
      this.lightButton.addEventListener('click', () => this.setTheme('light'));
    }
    if (this.darkButton) {
      this.darkButton.addEventListener('click', () => this.setTheme('dark'));
    }

    // Listen for system theme changes (only if user hasn't set a preference)
    if (!this.getSavedTheme()) {
      const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
      darkModeQuery.addEventListener('change', (e) => {
        if (!this.getSavedTheme()) {
          this.applyTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
  }

  getTheme() {
    // First check if user has manually set a theme
    const savedTheme = this.getSavedTheme();
    if (savedTheme) {
      return savedTheme;
    }

    // Otherwise, use system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? 'dark' : 'light';
  }

  getSavedTheme() {
    return localStorage.getItem('theme');
  }

  saveTheme(theme) {
    localStorage.setItem('theme', theme);
  }

  setTheme(theme) {
    this.currentTheme = theme;
    this.applyTheme(theme);
    this.saveTheme(theme);
  }

  applyTheme(theme) {
    // Update HTML attribute
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }

    // Update button states
    if (this.lightButton && this.darkButton) {
      if (theme === 'light') {
        this.lightButton.classList.add('active');
        this.darkButton.classList.remove('active');
      } else {
        this.lightButton.classList.remove('active');
        this.darkButton.classList.add('active');
      }
    }
  }
}

// ============================================================================
// Mobile Navigation
// ============================================================================

class MobileNav {
  constructor() {
    this.toggle = document.getElementById('navbar-toggle');
    this.menu = document.getElementById('navbar-menu');

    this.init();
  }

  init() {
    if (!this.toggle || !this.menu) return;

    this.toggle.addEventListener('click', () => this.toggleMenu());

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!this.toggle.contains(e.target) && !this.menu.contains(e.target)) {
        this.closeMenu();
      }
    });

    // Close menu when clicking a link
    const menuLinks = this.menu.querySelectorAll('a');
    menuLinks.forEach(link => {
      link.addEventListener('click', () => this.closeMenu());
    });
  }

  toggleMenu() {
    this.menu.classList.toggle('active');

    // Update aria-label
    const isOpen = this.menu.classList.contains('active');
    this.toggle.setAttribute('aria-label', isOpen ? 'Menü schließen' : 'Menü öffnen');
  }

  closeMenu() {
    this.menu.classList.remove('active');
    this.toggle.setAttribute('aria-label', 'Menü öffnen');
  }
}

// ============================================================================
// Flash Messages Auto-Dismiss
// ============================================================================

class FlashMessages {
  constructor() {
    this.container = document.getElementById('flash-messages');
    this.init();
  }

  init() {
    if (!this.container) return;

    // Auto-dismiss after 5 seconds
    const messages = this.container.querySelectorAll('.flash');
    messages.forEach(message => {
      setTimeout(() => {
        this.dismissMessage(message);
      }, 5000);
    });
  }

  dismissMessage(message) {
    message.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => {
      message.remove();
    }, 300);
  }
}

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// ============================================================================
// Shopping List Item Operations
// ============================================================================

class ShoppingListManager {
  constructor() {
    this.itemsList = document.getElementById('shopping-items');
    this.addItemForm = document.getElementById('add-item-form');

    this.init();
  }

  init() {
    if (!this.itemsList) return;

    // Attach event listeners to checkboxes
    this.attachCheckboxListeners();

    // Attach event listeners for inline editing
    this.attachEditListeners();

    // Handle form submission via AJAX (optional enhancement)
    if (this.addItemForm) {
      this.enhanceAddItemForm();
    }
  }

  attachCheckboxListeners() {
    const checkboxes = this.itemsList.querySelectorAll('.shopping-item-checkbox');

    checkboxes.forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        this.toggleItem(e.target);
      });
    });
  }

  async toggleItem(checkbox) {
    const itemId = checkbox.dataset.itemId;
    const listItem = checkbox.closest('.shopping-item');

    // Optimistic update
    if (checkbox.checked) {
      listItem.classList.add('checked');
    } else {
      listItem.classList.remove('checked');
    }

    try {
      const response = await fetch(`/items/${itemId}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
      });

      const data = await response.json();

      if (!data.success) {
        // Rollback on error
        checkbox.checked = !checkbox.checked;
        if (checkbox.checked) {
          listItem.classList.add('checked');
        } else {
          listItem.classList.remove('checked');
        }
        this.showToast('Fehler beim Aktualisieren des Artikels', 'danger');
      }
    } catch (error) {
      console.error('Error toggling item:', error);
      // Rollback on error
      checkbox.checked = !checkbox.checked;
      if (checkbox.checked) {
        listItem.classList.add('checked');
      } else {
        listItem.classList.remove('checked');
      }
      this.showToast('Netzwerkfehler beim Aktualisieren', 'danger');
    }
  }

  enhanceAddItemForm() {
    const form = this.addItemForm;
    const submitButton = document.getElementById('add-item-btn');
    const nameInput = form.querySelector('input[name="name"]');
    const quantityInput = form.querySelector('input[name="quantity"]');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const name = nameInput.value.trim();
      const quantity = quantityInput.value.trim() || '1';

      if (!name) {
        this.showToast('Bitte einen Artikel-Namen eingeben', 'warning');
        nameInput.focus();
        return;
      }

      // Show loading state
      submitButton.disabled = true;
      const originalButtonContent = submitButton.innerHTML;
      submitButton.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinner">
          <line x1="12" y1="2" x2="12" y2="6"></line>
          <line x1="12" y1="18" x2="12" y2="22"></line>
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
          <line x1="2" y1="12" x2="6" y2="12"></line>
          <line x1="18" y1="12" x2="22" y2="12"></line>
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
          <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
        </svg>
        Wird hinzugefügt...
      `;

      try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
          method: 'POST',
          body: formData,
          credentials: 'same-origin'
        });

        if (response.ok) {
          // Reload page to show new item
          // In a more advanced setup, we could add the item to the DOM without reload
          window.location.reload();
        } else {
          this.showToast('Fehler beim Hinzufügen des Artikels', 'danger');
          submitButton.disabled = false;
          submitButton.innerHTML = originalButtonContent;
        }
      } catch (error) {
        console.error('Error adding item:', error);
        this.showToast('Netzwerkfehler', 'danger');
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonContent;
      }
    });
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

  attachEditListeners() {
    // Edit button clicks
    const editButtons = document.querySelectorAll('.item-edit-btn');
    console.log('[Shopping List] Found edit buttons:', editButtons.length);

    if (editButtons.length === 0) {
      console.warn('[Shopping List] No edit buttons found! Check if items are rendered.');
    }

    editButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const itemId = e.currentTarget.dataset.itemId;
        console.log('[Shopping List] Edit button clicked for item:', itemId);
        this.enterEditMode(itemId);
      });
    });

    // Save button clicks
    const saveButtons = document.querySelectorAll('.item-save-btn');
    console.log('Found save buttons:', saveButtons.length);
    saveButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const itemId = e.currentTarget.dataset.itemId;
        console.log('Save button clicked for item:', itemId);
        this.saveItem(itemId);
      });
    });

    // Cancel button clicks
    const cancelButtons = document.querySelectorAll('.item-cancel-btn');
    console.log('Found cancel buttons:', cancelButtons.length);
    cancelButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const itemId = e.currentTarget.dataset.itemId;
        console.log('Cancel button clicked for item:', itemId);
        this.cancelEdit(itemId);
      });
    });

    // Handle Enter key in edit inputs
    const editInputs = document.querySelectorAll('.shopping-item-edit-form input');
    editInputs.forEach(input => {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const itemId = e.target.closest('.shopping-item').dataset.itemId;
          this.saveItem(itemId);
        } else if (e.key === 'Escape') {
          e.preventDefault();
          const itemId = e.target.closest('.shopping-item').dataset.itemId;
          this.cancelEdit(itemId);
        }
      });
    });
  }

  enterEditMode(itemId) {
    console.log('[Shopping List] Entering edit mode for item:', itemId);
    const listItem = document.querySelector(`.shopping-item[data-item-id="${itemId}"]`);

    if (!listItem) {
      console.error('[Shopping List] Could not find list item with id:', itemId);
      return;
    }

    console.log('[Shopping List] Found list item:', listItem);

    // Store original values for cancel
    const quantitySpan = listItem.querySelector('.shopping-item-quantity');
    const nameSpan = listItem.querySelector('.shopping-item-name');

    if (!quantitySpan || !nameSpan) {
      console.error('[Shopping List] Could not find quantity or name span');
      return;
    }

    listItem.dataset.originalQuantity = quantitySpan.textContent;
    listItem.dataset.originalName = nameSpan.textContent;

    console.log('[Shopping List] Stored original values:', {
      quantity: listItem.dataset.originalQuantity,
      name: listItem.dataset.originalName
    });

    // Set edit mode
    listItem.setAttribute('data-editing', 'true');
    console.log('[Shopping List] Set data-editing attribute to true');

    // Focus the name input
    const nameInput = listItem.querySelector('.item-edit-name');
    if (nameInput) {
      nameInput.focus();
      // Select text for easy editing
      nameInput.select();
      console.log('[Shopping List] Focused and selected name input');
    } else {
      console.error('[Shopping List] Could not find name input');
    }
  }

  cancelEdit(itemId) {
    const listItem = document.querySelector(`.shopping-item[data-item-id="${itemId}"]`);
    if (!listItem) return;

    // Restore original values
    const quantityInput = listItem.querySelector('.item-edit-quantity');
    const nameInput = listItem.querySelector('.item-edit-name');

    quantityInput.value = listItem.dataset.originalQuantity || '';
    nameInput.value = listItem.dataset.originalName || '';

    // Exit edit mode
    listItem.removeAttribute('data-editing');

    // Clean up stored data
    delete listItem.dataset.originalQuantity;
    delete listItem.dataset.originalName;
  }

  async saveItem(itemId) {
    const listItem = document.querySelector(`.shopping-item[data-item-id="${itemId}"]`);
    if (!listItem) return;

    const quantityInput = listItem.querySelector('.item-edit-quantity');
    const nameInput = listItem.querySelector('.item-edit-name');

    const newQuantity = quantityInput.value.trim();
    const newName = nameInput.value.trim();

    // Validation
    if (!newName) {
      this.showToast('Artikelname darf nicht leer sein', 'warning');
      nameInput.focus();
      return;
    }

    if (!newQuantity) {
      this.showToast('Anzahl darf nicht leer sein', 'warning');
      quantityInput.focus();
      return;
    }

    // Show loading state
    listItem.classList.add('item-saving');

    try {
      // Get CSRF token
      const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

      const formData = new FormData();
      formData.append('name', newName);
      formData.append('quantity', newQuantity);
      formData.append('csrf_token', csrfToken);

      const response = await fetch(`/items/${itemId}/edit`, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      });

      const data = await response.json();

      if (data.success) {
        // Update display values
        const quantitySpan = listItem.querySelector('.shopping-item-quantity');
        const nameSpan = listItem.querySelector('.shopping-item-name');

        quantitySpan.textContent = data.item.quantity;
        nameSpan.textContent = data.item.name;

        // Exit edit mode
        listItem.removeAttribute('data-editing');

        // Clean up stored data
        delete listItem.dataset.originalQuantity;
        delete listItem.dataset.originalName;

        this.showToast('Artikel erfolgreich aktualisiert', 'success');
      } else {
        // Show validation errors
        const errorMessages = data.errors ? Object.values(data.errors).join(', ') : 'Fehler beim Speichern';
        this.showToast(errorMessages, 'danger');
      }
    } catch (error) {
      console.error('Error saving item:', error);
      this.showToast('Netzwerkfehler beim Speichern', 'danger');
    } finally {
      listItem.classList.remove('item-saving');
    }
  }
}

// ============================================================================
// Form Enhancements
// ============================================================================

class FormEnhancements {
  constructor() {
    this.init();
  }

  init() {
    // Auto-focus first input on forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
      const firstInput = form.querySelector('input:not([type="hidden"]):not([type="checkbox"])');
      if (firstInput && !firstInput.hasAttribute('autofocus')) {
        // Don't auto-focus on mobile to prevent keyboard popup
        if (window.innerWidth > 768) {
          firstInput.focus();
        }
      }
    });

    // Add loading state to forms
    forms.forEach(form => {
      // Skip forms that already have custom handlers
      if (form.id === 'add-item-form') return;

      form.addEventListener('submit', (e) => {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
          submitButton.disabled = true;

          // Store original content
          const originalContent = submitButton.innerHTML;

          // Add loading spinner
          submitButton.innerHTML = `
            <div class="spinner"></div>
            ${submitButton.textContent.includes('Speichern') ? 'Wird gespeichert...' :
              submitButton.textContent.includes('Erstellen') ? 'Wird erstellt...' :
              submitButton.textContent.includes('Löschen') ? 'Wird gelöscht...' :
              'Wird verarbeitet...'}
          `;

          // Re-enable after 5 seconds as fallback
          setTimeout(() => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalContent;
          }, 5000);
        }
      });
    });
  }
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

class KeyboardShortcuts {
  constructor() {
    this.init();
  }

  init() {
    document.addEventListener('keydown', (e) => {
      // Ctrl/Cmd + K: Focus search or add item input
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const addItemInput = document.querySelector('#add-item-form input[name="name"]');
        if (addItemInput) {
          addItemInput.focus();
        }
      }

      // Escape: Close mobile menu
      if (e.key === 'Escape') {
        const mobileMenu = document.getElementById('navbar-menu');
        if (mobileMenu && mobileMenu.classList.contains('active')) {
          mobileMenu.classList.remove('active');
        }
      }
    });
  }
}

// ============================================================================
// Performance Optimizations
// ============================================================================

// Lazy load images if needed in the future
class LazyLoad {
  constructor() {
    this.images = document.querySelectorAll('img[data-src]');
    this.init();
  }

  init() {
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            observer.unobserve(img);
          }
        });
      });

      this.images.forEach(img => imageObserver.observe(img));
    } else {
      // Fallback for older browsers
      this.images.forEach(img => {
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
      });
    }
  }
}

// ============================================================================
// Accessibility Enhancements
// ============================================================================

class AccessibilityEnhancements {
  constructor() {
    this.init();
  }

  init() {
    // Add skip to main content link
    this.addSkipLink();

    // Ensure all interactive elements are keyboard accessible
    this.ensureKeyboardAccessibility();
  }

  addSkipLink() {
    if (document.querySelector('.skip-link')) return;

    const skipLink = document.createElement('a');
    skipLink.href = '#main';
    skipLink.className = 'skip-link visually-hidden';
    skipLink.textContent = 'Zum Hauptinhalt springen';
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 0;
      background: var(--color-primary);
      color: white;
      padding: 8px;
      text-decoration: none;
      z-index: 100000;
    `;

    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '0';
    });

    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px';
    });

    document.body.insertBefore(skipLink, document.body.firstChild);

    // Add id to main if not present
    const main = document.querySelector('main');
    if (main && !main.id) {
      main.id = 'main';
    }
  }

  ensureKeyboardAccessibility() {
    // Make sure all clickable elements that aren't buttons/links are keyboard accessible
    const clickables = document.querySelectorAll('[onclick]:not(button):not(a)');
    clickables.forEach(element => {
      if (!element.hasAttribute('tabindex')) {
        element.setAttribute('tabindex', '0');
      }
      if (!element.hasAttribute('role')) {
        element.setAttribute('role', 'button');
      }

      // Add keyboard support
      element.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          element.click();
        }
      });
    });
  }
}

// ============================================================================
// Initialize All Features
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Initialize all managers
  new ThemeManager();
  new MobileNav();
  new FlashMessages();
  new ShoppingListManager();
  new FormEnhancements();
  new KeyboardShortcuts();
  new LazyLoad();
  new AccessibilityEnhancements();

  // Log initialization for debugging
  console.log('Grocery Shopping List initialized successfully');
});

// ============================================================================
// Service Worker Registration (for future PWA support)
// ============================================================================

if ('serviceWorker' in navigator) {
  // Uncomment when service worker is ready
  // window.addEventListener('load', () => {
  //   navigator.serviceWorker.register('/sw.js')
  //     .then(registration => console.log('SW registered:', registration))
  //     .catch(error => console.log('SW registration failed:', error));
  // });
}
