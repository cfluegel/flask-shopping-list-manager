/**
 * AuthManager — JWT token management in localStorage.
 */
class AuthManager {
  constructor() {
    this.ACCESS_TOKEN_KEY = 'pwa_access_token';
    this.REFRESH_TOKEN_KEY = 'pwa_refresh_token';
    this.USER_KEY = 'pwa_user';
  }

  getAccessToken() {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  getRefreshToken() {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  getUser() {
    const data = localStorage.getItem(this.USER_KEY);
    return data ? JSON.parse(data) : null;
  }

  setTokens(accessToken, refreshToken) {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    if (refreshToken) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
    }
  }

  setUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  clearAll() {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  isAuthenticated() {
    return !!this.getAccessToken();
  }

  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      this.clearAll();
      return false;
    }

    try {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + refreshToken,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        this.clearAll();
        return false;
      }

      const result = await response.json();
      if (result.data && result.data.access_token) {
        localStorage.setItem(this.ACCESS_TOKEN_KEY, result.data.access_token);
        return true;
      }

      this.clearAll();
      return false;
    } catch (e) {
      this.clearAll();
      return false;
    }
  }
}

// Global singleton
const authManager = new AuthManager();
