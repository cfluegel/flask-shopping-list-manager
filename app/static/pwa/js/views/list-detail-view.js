/**
 * ListDetailView — Single list with items management.
 */
class ListDetailView {
  constructor(listId) {
    this.listId = listId;
    this.list = null;
  }

  render(container) {
    App.showBackButton(true, () => router.navigate('#/lists'));
    App.showLogoutButton(true);
    App.setTitle('...');

    container.innerHTML =
      '<div class="pwa-detail">' +
        '<form class="pwa-add-item-form" id="add-item-form">' +
          '<input type="text" class="form-control" id="item-name" ' +
            'placeholder="Artikel..." required>' +
          '<input type="text" class="form-control pwa-quantity-input" id="item-quantity" ' +
            'placeholder="Menge" value="1">' +
          '<button type="submit" class="btn btn-primary">Hinzufügen</button>' +
        '</form>' +
        '<ul class="pwa-items-list" id="items-list">' +
          '<div class="pwa-loading"><div class="spinner"></div></div>' +
        '</ul>' +
        '<div class="pwa-clear-checked" id="clear-checked-section" style="display:none;">' +
          '<button class="btn btn-secondary btn-sm" id="clear-checked-btn">' +
            'Abgehakte löschen' +
          '</button>' +
        '</div>' +
      '</div>';

    document.getElementById('add-item-form').addEventListener('submit', (e) => this._onAddItem(e));
    document.getElementById('clear-checked-btn').addEventListener('click', () => this._onClearChecked());
    this._loadList();
  }

  async _loadList() {
    try {
      const result = await apiClient.getList(this.listId);
      this.list = result.data;
      App.setTitle(this.list.title);
      this._renderItems(this.list.items || []);
    } catch (err) {
      document.getElementById('items-list').innerHTML =
        '<p class="text-danger">' + err.message + '</p>';
    }
  }

  _renderItems(items) {
    const list = document.getElementById('items-list');
    const clearSection = document.getElementById('clear-checked-section');

    if (items.length === 0) {
      list.innerHTML =
        '<div class="pwa-empty-state">' +
          '<p>Noch keine Artikel.</p>' +
        '</div>';
      clearSection.style.display = 'none';
      return;
    }

    list.innerHTML = '';
    let hasChecked = false;

    for (const item of items) {
      if (item.is_checked) hasChecked = true;

      const li = document.createElement('li');
      li.className = 'pwa-item' + (item.is_checked ? ' checked' : '');
      li.dataset.id = item.id;
      li.innerHTML =
        '<input type="checkbox" class="pwa-item-checkbox" ' +
          (item.is_checked ? 'checked' : '') + '>' +
        '<div class="pwa-item-content">' +
          '<span class="pwa-item-quantity">' + this._escapeHtml(item.quantity || '') + '</span>' +
          '<span class="pwa-item-name">' + this._escapeHtml(item.name) + '</span>' +
        '</div>' +
        '<button class="pwa-item-delete" aria-label="Löschen">' +
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<polyline points="3 6 5 6 21 6"></polyline>' +
            '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>' +
          '</svg>' +
        '</button>';

      // Toggle checkbox
      li.querySelector('.pwa-item-checkbox').addEventListener('change', () => this._onToggle(item.id, li));

      // Delete button
      li.querySelector('.pwa-item-delete').addEventListener('click', () => this._onDelete(item.id, li));

      list.appendChild(li);
    }

    clearSection.style.display = hasChecked ? '' : 'none';
  }

  async _onAddItem(e) {
    e.preventDefault();

    const nameInput = document.getElementById('item-name');
    const quantityInput = document.getElementById('item-quantity');
    const name = nameInput.value.trim();
    const quantity = quantityInput.value.trim() || '1';

    if (!name) return;

    try {
      await apiClient.createItem(this.listId, name, quantity);
      nameInput.value = '';
      quantityInput.value = '1';
      nameInput.focus();
      await this._loadList();
    } catch (err) {
      App.showToast(err.message, 'error');
    }
  }

  async _onToggle(itemId, li) {
    // Optimistic UI
    li.classList.toggle('checked');
    const checkbox = li.querySelector('.pwa-item-checkbox');
    checkbox.checked = li.classList.contains('checked');

    try {
      await apiClient.toggleItem(itemId);
      // Update clear-checked visibility
      const hasChecked = document.querySelector('.pwa-item.checked') !== null;
      document.getElementById('clear-checked-section').style.display = hasChecked ? '' : 'none';
    } catch (err) {
      // Revert on error
      li.classList.toggle('checked');
      checkbox.checked = li.classList.contains('checked');
      App.showToast(err.message, 'error');
    }
  }

  async _onDelete(itemId, li) {
    const confirmed = await App.confirm('Diesen Artikel wirklich löschen?');
    if (!confirmed) return;

    try {
      await apiClient.deleteItem(itemId);
      li.remove();
      App.showToast('Artikel gelöscht', 'success');

      // Check if list is now empty
      const remaining = document.querySelectorAll('.pwa-item');
      if (remaining.length === 0) {
        this._renderItems([]);
      }
    } catch (err) {
      App.showToast(err.message, 'error');
    }
  }

  async _onClearChecked() {
    const confirmed = await App.confirm('Alle abgehakten Artikel löschen?');
    if (!confirmed) return;

    try {
      const result = await apiClient.clearCheckedItems(this.listId);
      await this._loadList();
      const count = result.data ? result.data.deleted_count : 0;
      App.showToast(count + ' Artikel gelöscht', 'success');
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
