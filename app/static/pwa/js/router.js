/**
 * Router — Hash-based SPA router with auth guard.
 */
class Router {
  constructor() {
    this.routes = {};
    this.currentView = null;

    window.addEventListener('hashchange', () => this._onHashChange());
  }

  addRoute(pattern, viewFactory) {
    this.routes[pattern] = viewFactory;
  }

  start() {
    if (!window.location.hash || window.location.hash === '#') {
      window.location.hash = authManager.isAuthenticated() ? '#/lists' : '#/login';
    } else {
      this._onHashChange();
    }
  }

  navigate(hash) {
    window.location.hash = hash;
  }

  _onHashChange() {
    const hash = window.location.hash || '#/login';
    const path = hash.slice(1); // remove #

    // Auth guard: redirect to login if not authenticated (except login route)
    if (path !== '/login' && !authManager.isAuthenticated()) {
      window.location.hash = '#/login';
      return;
    }

    // If authenticated and on login page, redirect to lists
    if (path === '/login' && authManager.isAuthenticated()) {
      window.location.hash = '#/lists';
      return;
    }

    // Match route
    let matched = false;
    for (const pattern in this.routes) {
      const params = this._matchRoute(pattern, path);
      if (params !== null) {
        this._loadView(this.routes[pattern], params);
        matched = true;
        break;
      }
    }

    if (!matched) {
      window.location.hash = '#/lists';
    }
  }

  _matchRoute(pattern, path) {
    const patternParts = pattern.split('/');
    const pathParts = path.split('/');

    if (patternParts.length !== pathParts.length) return null;

    const params = {};
    for (let i = 0; i < patternParts.length; i++) {
      if (patternParts[i].startsWith(':')) {
        params[patternParts[i].slice(1)] = pathParts[i];
      } else if (patternParts[i] !== pathParts[i]) {
        return null;
      }
    }
    return params;
  }

  _loadView(viewFactory, params) {
    // Destroy current view if it has a destroy method
    if (this.currentView && typeof this.currentView.destroy === 'function') {
      this.currentView.destroy();
    }

    const content = document.getElementById('pwa-content');
    content.innerHTML = '';

    this.currentView = viewFactory(params);
    if (typeof this.currentView.render === 'function') {
      this.currentView.render(content);
    }
  }
}

// Global singleton
const router = new Router();
