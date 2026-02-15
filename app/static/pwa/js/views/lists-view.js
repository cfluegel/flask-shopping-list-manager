/**
 * ListsView — Shopping lists overview with create form.
 */
class ListsView {
  render(container) {
    App.setTitle('Meine Listen');
    App.showBackButton(false);
    App.showLogoutButton(true);

    container.innerHTML =
      '<div class="pwa-lists">' +
        '<form class="pwa-create-form" id="create-list-form">' +
          '<input type="text" class="form-control" id="new-list-title" ' +
            'placeholder="Neue Liste..." required maxlength="100">' +
          '<button type="submit" class="btn btn-primary">+</button>' +
        '</form>' +
        '<div class="pwa-lists-grid" id="lists-grid">' +
          '<div class="pwa-loading"><div class="spinner"></div></div>' +
        '</div>' +
      '</div>';

    document.getElementById('create-list-form').addEventListener('submit', (e) => this._onCreate(e));
    this._loadLists();
  }

  async _loadLists() {
    const grid = document.getElementById('lists-grid');

    try {
      const result = await apiClient.getLists();
      const lists = result.data || [];

      if (lists.length === 0) {
        grid.innerHTML =
          '<div class="pwa-empty-state">' +
            '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">' +
              '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>' +
              '<polyline points="14 2 14 8 20 8"></polyline>' +
              '<line x1="16" y1="13" x2="8" y2="13"></line>' +
              '<line x1="16" y1="17" x2="8" y2="17"></line>' +
            '</svg>' +
            '<p>Noch keine Listen vorhanden.</p>' +
            '<p class="text-muted">Erstelle oben deine erste Einkaufsliste.</p>' +
          '</div>';
        return;
      }

      grid.innerHTML = '';
      for (const list of lists) {
        const card = document.createElement('div');
        card.className = 'pwa-list-card';
        card.innerHTML =
          '<div>' +
            '<div class="pwa-list-card-title">' + this._escapeHtml(list.title) + '</div>' +
          '</div>' +
          '<div class="pwa-list-card-meta">' +
            '<span class="pwa-list-card-count">' + (list.item_count || 0) + '</span>' +
            '<span class="pwa-list-card-arrow">' +
              '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>' +
            '</span>' +
          '</div>';
        card.addEventListener('click', () => router.navigate('#/lists/' + list.id));
        grid.appendChild(card);
      }
    } catch (err) {
      grid.innerHTML = '<p class="text-danger">' + err.message + '</p>';
    }
  }

  async _onCreate(e) {
    e.preventDefault();

    const input = document.getElementById('new-list-title');
    const title = input.value.trim();
    if (!title) return;

    try {
      const result = await apiClient.createList(title);
      input.value = '';
      // Navigate to the new list
      if (result.data && result.data.id) {
        router.navigate('#/lists/' + result.data.id);
      } else {
        this._loadLists();
      }
    } catch (err) {
      App.showToast(err.message, 'error');
    }
  }

  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  destroy() {}
}
