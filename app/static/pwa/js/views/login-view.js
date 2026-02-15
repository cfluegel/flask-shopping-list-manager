/**
 * LoginView — Login form view.
 */
class LoginView {
  render(container) {
    App.setTitle('Einkaufsliste');
    App.showBackButton(false);
    App.showLogoutButton(false);

    container.innerHTML =
      '<div class="pwa-login">' +
        '<div class="pwa-login-card">' +
          '<div class="pwa-login-header">' +
            '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
              '<circle cx="9" cy="21" r="1"></circle>' +
              '<circle cx="20" cy="21" r="1"></circle>' +
              '<path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>' +
            '</svg>' +
            '<h2>Anmelden</h2>' +
            '<p>Bitte melde dich an, um fortzufahren.</p>' +
          '</div>' +
          '<div class="pwa-login-error" id="login-error"></div>' +
          '<form class="pwa-login-form" id="login-form">' +
            '<div class="form-group">' +
              '<label class="form-label" for="login-username">Benutzername</label>' +
              '<input type="text" class="form-control" id="login-username" ' +
                'autocomplete="username" required autofocus>' +
            '</div>' +
            '<div class="form-group">' +
              '<label class="form-label" for="login-password">Passwort</label>' +
              '<input type="password" class="form-control" id="login-password" ' +
                'autocomplete="current-password" required>' +
            '</div>' +
            '<button type="submit" class="btn btn-primary btn-block" id="login-submit">' +
              'Anmelden' +
            '</button>' +
          '</form>' +
        '</div>' +
      '</div>';

    document.getElementById('login-form').addEventListener('submit', (e) => this._onSubmit(e));
  }

  async _onSubmit(e) {
    e.preventDefault();

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    const submitBtn = document.getElementById('login-submit');

    if (!username || !password) return;

    errorEl.classList.remove('visible');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Anmelden...';

    try {
      await apiClient.login(username, password);
      router.navigate('#/lists');
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.classList.add('visible');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Anmelden';
    }
  }

  destroy() {}
}
