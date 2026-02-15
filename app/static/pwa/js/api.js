/**
 * APIClient — Fetch wrapper with automatic JWT token refresh on 401.
 */
class APIClient {
  constructor(authManager) {
    this.auth = authManager;
    this.baseUrl = '/api/v1';
    this._refreshing = null;
  }

  async _request(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = this.auth.getAccessToken();
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }

    const opts = { method, headers };
    if (body !== null) {
      opts.body = JSON.stringify(body);
    }

    let response = await fetch(this.baseUrl + path, opts);

    // Auto-refresh on 401
    if (response.status === 401 && this.auth.getRefreshToken()) {
      const refreshed = await this._doRefresh();
      if (refreshed) {
        headers['Authorization'] = 'Bearer ' + this.auth.getAccessToken();
        opts.headers = headers;
        response = await fetch(this.baseUrl + path, opts);
      } else {
        this.auth.clearAll();
        window.location.hash = '#/login';
        throw new Error('Sitzung abgelaufen');
      }
    }

    const result = await response.json();

    if (!response.ok) {
      const msg = result.message || result.error || 'Fehler';
      throw new Error(msg);
    }

    return result;
  }

  async _doRefresh() {
    // Deduplicate concurrent refresh calls
    if (this._refreshing) return this._refreshing;
    this._refreshing = this.auth.refreshAccessToken();
    const result = await this._refreshing;
    this._refreshing = null;
    return result;
  }

  // Auth
  async login(username, password) {
    const result = await this._request('POST', '/auth/login', { username, password });
    if (result.data) {
      this.auth.setTokens(result.data.tokens.access_token, result.data.tokens.refresh_token);
      this.auth.setUser(result.data.user);
    }
    return result;
  }

  async logout() {
    try {
      await this._request('POST', '/auth/logout');
    } catch (e) {
      // Ignore logout errors
    }
    this.auth.clearAll();
  }

  // Lists
  async getLists() {
    return this._request('GET', '/lists');
  }

  async getList(id) {
    return this._request('GET', '/lists/' + id);
  }

  async createList(title) {
    return this._request('POST', '/lists', { title });
  }

  async deleteList(id) {
    return this._request('DELETE', '/lists/' + id);
  }

  // Items
  async createItem(listId, name, quantity) {
    return this._request('POST', '/lists/' + listId + '/items', { name, quantity });
  }

  async toggleItem(itemId) {
    return this._request('POST', '/items/' + itemId + '/toggle');
  }

  async deleteItem(itemId) {
    return this._request('DELETE', '/items/' + itemId);
  }

  async clearCheckedItems(listId) {
    return this._request('POST', '/lists/' + listId + '/items/clear-checked');
  }
}

// Global singleton
const apiClient = new APIClient(authManager);
