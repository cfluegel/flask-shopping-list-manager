"""
Tests for Shopping List Items API Endpoints.

Tests CRUD operations, toggling, reordering, and bulk operations for items.
"""

import pytest
import json

from app.models import ShoppingList, ShoppingListItem
from app.extensions import db


# ============================================================================
# Get Items Tests
# ============================================================================

class TestGetItems:
    """Test GET /api/v1/lists/<id>/items endpoint."""

    def test_get_items_with_valid_list_returns_200(self, client, app, user_headers, sample_list, sample_item):
        """Test that getting items returns 200 with list items."""
        response = client.get(f'/api/v1/lists/{sample_list.id}/items', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['name'] == sample_item.name

    def test_get_items_excludes_deleted_items(self, client, app, user_headers, sample_list, sample_item, deleted_item):
        """Test that deleted items are not included."""
        response = client.get(f'/api/v1/lists/{sample_list.id}/items', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        item_ids = [item['id'] for item in data['data']]
        assert sample_item.id in item_ids
        assert deleted_item.id not in item_ids

    def test_get_items_for_shared_list_returns_200(self, client, app, another_user_headers, shared_list):
        """Test that getting items from shared list works."""
        # Add item to shared list
        item = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Test Item',
            quantity='1'
        )
        db.session.add(item)
        db.session.commit()

        response = client.get(f'/api/v1/lists/{shared_list.id}/items', headers=another_user_headers)

        assert response.status_code == 200

    def test_get_items_for_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that getting items from another user's list returns 403."""
        response = client.get(f'/api/v1/lists/{admin_list.id}/items', headers=user_headers)

        assert response.status_code == 403

    def test_get_items_for_nonexistent_list_returns_404(self, client, app, user_headers):
        """Test that getting items from non-existent list returns 404."""
        response = client.get('/api/v1/lists/99999/items', headers=user_headers)

        assert response.status_code == 404


# ============================================================================
# Create Item Tests
# ============================================================================

class TestCreateItem:
    """Test POST /api/v1/lists/<id>/items endpoint."""

    def test_create_item_with_valid_data_returns_201(self, client, app, user_headers, sample_list):
        """Test that creating an item with valid data returns 201."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items', headers=user_headers, json={
            'name': 'Neuer Artikel',
            'quantity': '3 Stück'
        })

        assert response.status_code == 201
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['name'] == 'Neuer Artikel'
        assert data['data']['quantity'] == '3 Stück'
        assert data['data']['is_checked'] is False
        assert data['data']['version'] == 1

        # Verify in database
        item = ShoppingListItem.query.get(data['data']['id'])
        assert item is not None
        assert item.name == 'Neuer Artikel'

    def test_create_item_without_quantity_defaults_to_one(self, client, app, user_headers, sample_list):
        """Test that quantity defaults to '1' if not provided."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items', headers=user_headers, json={
            'name': 'Artikel ohne Menge'
        })

        assert response.status_code == 201
        data = response.get_json()

        assert data['data']['quantity'] == '1'

    def test_create_item_sets_order_index_correctly(self, client, app, user_headers, sample_list, sample_item):
        """Test that order_index is incremented correctly."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items', headers=user_headers, json={
            'name': 'Zweiter Artikel'
        })

        assert response.status_code == 201
        data = response.get_json()

        # Should be higher than existing item
        assert data['data']['order_index'] > sample_item.order_index

    def test_create_item_without_name_returns_400(self, client, app, user_headers, sample_list):
        """Test that creating item without name returns 400."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items', headers=user_headers, json={
            'quantity': '1'
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False

    def test_create_item_with_empty_name_returns_400(self, client, app, user_headers, sample_list):
        """Test that creating item with empty name returns 400."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items', headers=user_headers, json={
            'name': ''
        })

        assert response.status_code == 400

    def test_create_item_in_shared_list_by_other_user_returns_201(self, client, app, another_user_headers, shared_list):
        """Test that other users can add items to shared lists."""
        response = client.post(f'/api/v1/lists/{shared_list.id}/items', headers=another_user_headers, json={
            'name': 'Von anderem Benutzer'
        })

        assert response.status_code == 201

    def test_create_item_in_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that creating item in another user's list returns 403."""
        response = client.post(f'/api/v1/lists/{admin_list.id}/items', headers=user_headers, json={
            'name': 'Unauthorized Item'
        })

        assert response.status_code == 403

    def test_create_item_in_nonexistent_list_returns_404(self, client, app, user_headers):
        """Test that creating item in non-existent list returns 404."""
        response = client.post('/api/v1/lists/99999/items', headers=user_headers, json={
            'name': 'Test Item'
        })

        assert response.status_code == 404


# ============================================================================
# Get Single Item Tests
# ============================================================================

class TestGetItem:
    """Test GET /api/v1/items/<id> endpoint."""

    def test_get_item_with_valid_id_returns_200(self, client, app, user_headers, sample_item):
        """Test that getting an item by ID returns 200."""
        response = client.get(f'/api/v1/items/{sample_item.id}', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['id'] == sample_item.id
        assert data['data']['name'] == sample_item.name

    def test_get_item_includes_list_info(self, client, app, user_headers, sample_item, sample_list):
        """Test that item response includes parent list info."""
        response = client.get(f'/api/v1/items/{sample_item.id}', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['list_id'] == sample_list.id
        assert data['data']['list_title'] == sample_list.title

    def test_get_item_from_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that getting item from another user's list returns 403."""
        # Create item in admin's list
        item = ShoppingListItem(
            shopping_list_id=admin_list.id,
            name='Admin Item',
            quantity='1'
        )
        db.session.add(item)
        db.session.commit()

        response = client.get(f'/api/v1/items/{item.id}', headers=user_headers)

        assert response.status_code == 403

    def test_get_nonexistent_item_returns_404(self, client, app, user_headers):
        """Test that getting non-existent item returns 404."""
        response = client.get('/api/v1/items/99999', headers=user_headers)

        assert response.status_code == 404

    def test_get_deleted_item_returns_404(self, client, app, user_headers, deleted_item):
        """Test that getting deleted item returns 404."""
        response = client.get(f'/api/v1/items/{deleted_item.id}', headers=user_headers)

        assert response.status_code == 404


# ============================================================================
# Update Item Tests
# ============================================================================

class TestUpdateItem:
    """Test PUT /api/v1/items/<id> endpoint."""

    def test_update_item_name_returns_200(self, client, app, user_headers, sample_item):
        """Test that updating item name returns 200."""
        response = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'name': 'Updated Name'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['name'] == 'Updated Name'

        # Verify in database
        db.session.refresh(sample_item)
        assert sample_item.name == 'Updated Name'

    def test_update_item_quantity_returns_200(self, client, app, user_headers, sample_item):
        """Test that updating item quantity returns 200."""
        response = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'quantity': '5 kg'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['quantity'] == '5 kg'

    def test_update_item_checked_status_returns_200(self, client, app, user_headers, sample_item):
        """Test that updating checked status returns 200."""
        response = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'is_checked': True
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['is_checked'] is True

    def test_update_item_increments_version(self, client, app, user_headers, sample_item):
        """Test that updating item increments version."""
        original_version = sample_item.version

        response = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'name': 'New Name',
            'version': original_version
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['version'] == original_version + 1

    def test_update_item_in_shared_list_by_other_user_returns_200(self, client, app, another_user_headers, shared_list):
        """Test that other users can update items in shared lists."""
        # Create item in shared list
        item = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Shared Item',
            quantity='1'
        )
        db.session.add(item)
        db.session.commit()

        response = client.put(f'/api/v1/items/{item.id}', headers=another_user_headers, json={
            'name': 'Updated by Other'
        })

        assert response.status_code == 200

    def test_update_item_in_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that updating item in another user's list returns 403."""
        # Create item in admin's list
        item = ShoppingListItem(
            shopping_list_id=admin_list.id,
            name='Admin Item',
            quantity='1'
        )
        db.session.add(item)
        db.session.commit()

        response = client.put(f'/api/v1/items/{item.id}', headers=user_headers, json={
            'name': 'Hacked Name'
        })

        assert response.status_code == 403

    def test_update_nonexistent_item_returns_404(self, client, app, user_headers):
        """Test that updating non-existent item returns 404."""
        response = client.put('/api/v1/items/99999', headers=user_headers, json={
            'name': 'Test'
        })

        assert response.status_code == 404

    def test_update_deleted_item_returns_404(self, client, app, user_headers, deleted_item):
        """Test that updating deleted item returns 404."""
        response = client.put(f'/api/v1/items/{deleted_item.id}', headers=user_headers, json={
            'name': 'Updated'
        })

        assert response.status_code == 404


# ============================================================================
# Delete Item Tests
# ============================================================================

class TestDeleteItem:
    """Test DELETE /api/v1/items/<id> endpoint."""

    def test_delete_item_with_valid_id_returns_200(self, client, app, user_headers, sample_item):
        """Test that deleting an item returns 200."""
        response = client.delete(f'/api/v1/items/{sample_item.id}', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'Papierkorb' in data['message']

        # Verify soft delete
        db.session.refresh(sample_item)
        assert sample_item.deleted_at is not None

    def test_delete_item_in_shared_list_by_other_user_returns_200(self, client, app, another_user_headers, shared_list):
        """Test that other users can delete items in shared lists."""
        # Create item in shared list
        item = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Shared Item',
            quantity='1'
        )
        db.session.add(item)
        db.session.commit()

        response = client.delete(f'/api/v1/items/{item.id}', headers=another_user_headers)

        assert response.status_code == 200

    def test_delete_item_in_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that deleting item in another user's list returns 403."""
        # Create item in admin's list
        item = ShoppingListItem(
            shopping_list_id=admin_list.id,
            name='Admin Item',
            quantity='1'
        )
        db.session.add(item)
        db.session.commit()

        response = client.delete(f'/api/v1/items/{item.id}', headers=user_headers)

        assert response.status_code == 403

    def test_delete_nonexistent_item_returns_404(self, client, app, user_headers):
        """Test that deleting non-existent item returns 404."""
        response = client.delete('/api/v1/items/99999', headers=user_headers)

        assert response.status_code == 404


# ============================================================================
# Toggle Item Tests
# ============================================================================

class TestToggleItem:
    """Test POST /api/v1/items/<id>/toggle endpoint."""

    def test_toggle_unchecked_item_to_checked_returns_200(self, client, app, user_headers, sample_item):
        """Test that toggling unchecked item to checked returns 200."""
        assert sample_item.is_checked is False

        response = client.post(f'/api/v1/items/{sample_item.id}/toggle', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['is_checked'] is True

        # Verify in database
        db.session.refresh(sample_item)
        assert sample_item.is_checked is True

    def test_toggle_checked_item_to_unchecked_returns_200(self, client, app, user_headers, checked_item):
        """Test that toggling checked item to unchecked returns 200."""
        assert checked_item.is_checked is True

        response = client.post(f'/api/v1/items/{checked_item.id}/toggle', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['is_checked'] is False

    def test_toggle_item_in_shared_list_returns_200(self, client, app, another_user_headers, shared_list):
        """Test that toggling items in shared lists works."""
        # Create item in shared list
        item = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Shared Item',
            quantity='1',
            is_checked=False
        )
        db.session.add(item)
        db.session.commit()

        response = client.post(f'/api/v1/items/{item.id}/toggle', headers=another_user_headers)

        assert response.status_code == 200

    def test_toggle_item_in_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that toggling item in another user's list returns 403."""
        # Create item in admin's list
        item = ShoppingListItem(
            shopping_list_id=admin_list.id,
            name='Admin Item',
            quantity='1'
        )
        db.session.add(item)
        db.session.commit()

        response = client.post(f'/api/v1/items/{item.id}/toggle', headers=user_headers)

        assert response.status_code == 403


# ============================================================================
# Reorder Item Tests
# ============================================================================

class TestReorderItem:
    """Test PUT /api/v1/items/<id>/reorder endpoint."""

    def test_reorder_item_with_valid_index_returns_200(self, client, app, user_headers, sample_item):
        """Test that reordering item returns 200."""
        response = client.put(f'/api/v1/items/{sample_item.id}/reorder', headers=user_headers, json={
            'order_index': 10
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['order_index'] == 10

        # Verify in database
        db.session.refresh(sample_item)
        assert sample_item.order_index == 10

    def test_reorder_item_in_shared_list_by_non_owner_returns_403(self, client, app, another_user_headers, shared_list):
        """Test that non-owners cannot reorder items in shared lists."""
        # Create item in shared list
        item = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Shared Item',
            quantity='1',
            order_index=1
        )
        db.session.add(item)
        db.session.commit()

        response = client.put(f'/api/v1/items/{item.id}/reorder', headers=another_user_headers, json={
            'order_index': 5
        })

        assert response.status_code == 403

    def test_reorder_item_in_own_list_returns_200(self, client, app, user_headers, sample_item):
        """Test that owners can reorder their own items."""
        response = client.put(f'/api/v1/items/{sample_item.id}/reorder', headers=user_headers, json={
            'order_index': 99
        })

        assert response.status_code == 200

    def test_admin_can_reorder_any_item(self, client, app, admin_headers, sample_item):
        """Test that admins can reorder any item."""
        response = client.put(f'/api/v1/items/{sample_item.id}/reorder', headers=admin_headers, json={
            'order_index': 42
        })

        assert response.status_code == 200


# ============================================================================
# Clear Checked Items Tests
# ============================================================================

class TestClearCheckedItems:
    """Test POST /api/v1/lists/<id>/items/clear-checked endpoint."""

    def test_clear_checked_items_returns_200(self, client, app, user_headers, sample_list, checked_item):
        """Test that clearing checked items returns 200."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items/clear-checked', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['deleted_count'] >= 1

        # Verify item was soft deleted
        db.session.refresh(checked_item)
        assert checked_item.deleted_at is not None

    def test_clear_checked_items_keeps_unchecked_items(self, client, app, user_headers, sample_list, sample_item, checked_item):
        """Test that unchecked items are not deleted."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items/clear-checked', headers=user_headers)

        assert response.status_code == 200

        # Verify unchecked item was NOT deleted
        db.session.refresh(sample_item)
        assert sample_item.deleted_at is None

    def test_clear_checked_items_in_shared_list_returns_403(self, client, app, another_user_headers, shared_list):
        """Test that non-owners cannot clear checked items."""
        response = client.post(f'/api/v1/lists/{shared_list.id}/items/clear-checked', headers=another_user_headers)

        assert response.status_code == 403


# ============================================================================
# Trash Management Tests
# ============================================================================

class TestTrashItems:
    """Test GET /api/v1/trash/items endpoint."""

    def test_get_trash_items_returns_200(self, client, app, user_headers, deleted_item):
        """Test that getting trash items returns 200."""
        response = client.get('/api/v1/trash/items', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        item_ids = [item['id'] for item in data['data']]
        assert deleted_item.id in item_ids

    def test_get_trash_items_excludes_active_items(self, client, app, user_headers, sample_item, deleted_item):
        """Test that trash endpoint only returns deleted items."""
        response = client.get('/api/v1/trash/items', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        item_ids = [item['id'] for item in data['data']]
        assert deleted_item.id in item_ids
        assert sample_item.id not in item_ids


class TestRestoreItem:
    """Test POST /api/v1/items/<id>/restore endpoint."""

    def test_restore_item_returns_200(self, client, app, user_headers, deleted_item):
        """Test that restoring an item returns 200."""
        response = client.post(f'/api/v1/items/{deleted_item.id}/restore', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'wiederhergestellt' in data['message']

        # Verify restore
        db.session.refresh(deleted_item)
        assert deleted_item.deleted_at is None

    def test_restore_active_item_returns_404(self, client, app, user_headers, sample_item):
        """Test that restoring an active item returns 404."""
        response = client.post(f'/api/v1/items/{sample_item.id}/restore', headers=user_headers)

        assert response.status_code == 404

    def test_restore_item_from_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that users cannot restore items from other users' lists."""
        # Create and delete item in admin's list
        item = ShoppingListItem(
            shopping_list_id=admin_list.id,
            name='Admin Item',
            quantity='1'
        )
        item.soft_delete()
        db.session.add(item)
        db.session.commit()

        response = client.post(f'/api/v1/items/{item.id}/restore', headers=user_headers)

        assert response.status_code == 403
