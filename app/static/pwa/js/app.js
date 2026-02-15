/**
 * App — Main PWA controller.
 * Handles service worker registration, theme toggle, and toast notifications.
 */
class App {
  constructor() {
    this._initTheme();
    this._initRoutes();
    this._initHeader();
    this._registerServiceWorker();
    router.start();
  }

  _initRoutes() {
    router.addRoute('/login', () => new LoginView());
    router.addRoute('/lists', () => new ListsView());
    router.addRoute('/lists/:id', (params) => new ListDetailView(params.id));
  }

  _initHeader() {
    document.getElementById('logout-btn').addEventListener('click', async () => {
      await apiClient.logout();
      router.navigate('#/login');
    });

    document.getElementById('theme-btn').addEventListener('click', () => {
      this._toggleTheme();
    });
  }

  _initTheme() {
    const saved = localStorage.getItem('pwa_theme');
    if (saved === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    this._updateThemeIcon();
  }

  _toggleTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('pwa_theme', 'light');
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('pwa_theme', 'dark');
    }
    this._updateThemeIcon();
  }

  _updateThemeIcon() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const icon = document.getElementById('theme-icon');
    if (isDark) {
      icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    } else {
      icon.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
    }
  }

  async _registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        await navigator.serviceWorker.register('/pwa/sw.js', { scope: '/pwa/' });
      } catch (e) {
        console.warn('Service worker registration failed:', e);
      }
    }
  }

  static showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'pwa-toast ' + type;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('removing');
      toast.addEventListener('animationend', () => toast.remove());
    }, duration);
  }

  static setTitle(title) {
    document.getElementById('pwa-title').textContent = title;
  }

  static showBackButton(show, onClick) {
    const btn = document.getElementById('back-btn');
    btn.style.display = show ? '' : 'none';
    btn.onclick = onClick || null;
  }

  static showLogoutButton(show) {
    document.getElementById('logout-btn').style.display = show ? '' : 'none';
  }

  static confirm(message) {
    return new Promise((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'pwa-confirm-overlay';
      overlay.innerHTML =
        '<div class="pwa-confirm-dialog">' +
          '<p>' + message + '</p>' +
          '<div class="pwa-confirm-actions">' +
            '<button class="btn btn-secondary" data-action="cancel">Abbrechen</button>' +
            '<button class="btn btn-danger" data-action="confirm">Löschen</button>' +
          '</div>' +
        '</div>';

      overlay.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action === 'confirm') {
          overlay.remove();
          resolve(true);
        } else if (action === 'cancel' || e.target === overlay) {
          overlay.remove();
          resolve(false);
        }
      });

      document.body.appendChild(overlay);
    });
  }
}

// Boot the app
document.addEventListener('DOMContentLoaded', () => {
  new App();
});
