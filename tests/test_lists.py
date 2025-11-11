"""
Tests for Shopping Lists API Endpoints.

Tests CRUD operations, sharing, pagination, and trash management for shopping lists.
"""

import pytest
import json

from app.models import ShoppingList, ShoppingListItem
from app.extensions import db


# ============================================================================
# Get Lists Tests
# ============================================================================

class TestGetLists:
    """Test GET /api/v1/lists endpoint."""

    def test_get_lists_with_valid_token_returns_200(self, client, app, user_headers, sample_list):
        """Test that getting lists returns 200 with user's lists."""
        response = client.get('/api/v1/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['title'] == sample_list.title
        assert 'pagination' in data

    def test_get_lists_returns_only_user_lists(self, client, app, user_headers, sample_list, admin_list):
        """Test that users only see their own lists."""
        response = client.get('/api/v1/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Should only see sample_list, not admin_list
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == sample_list.id

    def test_get_lists_excludes_deleted_lists(self, client, app, user_headers, sample_list, deleted_list):
        """Test that deleted lists are not included in response."""
        response = client.get('/api/v1/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Should only see sample_list, not deleted_list
        list_ids = [item['id'] for item in data['data']]
        assert sample_list.id in list_ids
        assert deleted_list.id not in list_ids

    def test_get_lists_without_token_returns_401(self, client, app):
        """Test that getting lists without token returns 401."""
        response = client.get('/api/v1/lists', headers={
            'Content-Type': 'application/json'
        })

        assert response.status_code == 401

    def test_get_lists_includes_item_count(self, client, app, user_headers, sample_list, sample_item):
        """Test that list response includes item count."""
        response = client.get('/api/v1/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['data'][0]['item_count'] == 1

    def test_get_lists_pagination(self, client, app, user_headers, regular_user):
        """Test that pagination works correctly."""
        # Create multiple lists
        for i in range(5):
            list_obj = ShoppingList(title=f'Liste {i}', user_id=regular_user.id)
            db.session.add(list_obj)
        db.session.commit()

        # Get first page with 2 items
        response = client.get('/api/v1/lists?page=1&per_page=2', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert len(data['data']) == 2
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 2
        assert data['pagination']['total'] == 5
        assert data['pagination']['has_next'] is True


# ============================================================================
# Get Single List Tests
# ============================================================================

class TestGetList:
    """Test GET /api/v1/lists/<id> endpoint."""

    def test_get_list_with_valid_id_returns_200(self, client, app, user_headers, sample_list):
        """Test that getting a list by ID returns 200."""
        response = client.get(f'/api/v1/lists/{sample_list.id}', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['id'] == sample_list.id
        assert data['data']['title'] == sample_list.title
        assert 'items' in data['data']

    def test_get_list_includes_items(self, client, app, user_headers, sample_list, sample_item):
        """Test that list response includes all items."""
        response = client.get(f'/api/v1/lists/{sample_list.id}', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['name'] == sample_item.name

    def test_get_list_with_nonexistent_id_returns_404(self, client, app, user_headers):
        """Test that getting non-existent list returns 404."""
        response = client.get('/api/v1/lists/99999', headers=user_headers)

        assert response.status_code == 404
        data = response.get_json()

        assert data['success'] is False

    def test_get_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that getting another user's list returns 403."""
        response = client.get(f'/api/v1/lists/{admin_list.id}', headers=user_headers)

        assert response.status_code == 403
        data = response.get_json()

        assert data['success'] is False

    def test_get_shared_list_returns_200(self, client, app, another_user_headers, shared_list):
        """Test that getting a shared list works for other users."""
        response = client.get(f'/api/v1/lists/{shared_list.id}', headers=another_user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['id'] == shared_list.id

    def test_get_deleted_list_returns_404(self, client, app, user_headers, deleted_list):
        """Test that getting a deleted list returns 404."""
        response = client.get(f'/api/v1/lists/{deleted_list.id}', headers=user_headers)

        assert response.status_code == 404


# ============================================================================
# Create List Tests
# ============================================================================

class TestCreateList:
    """Test POST /api/v1/lists endpoint."""

    def test_create_list_with_valid_data_returns_201(self, client, app, user_headers):
        """Test that creating a list with valid data returns 201."""
        response = client.post('/api/v1/lists', headers=user_headers, json={
            'title': 'Neue Einkaufsliste',
            'is_shared': False
        })

        assert response.status_code == 201
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['title'] == 'Neue Einkaufsliste'
        assert data['data']['is_shared'] is False
        assert data['data']['guid'] is not None
        assert data['data']['version'] == 1

        # Verify in database
        list_obj = ShoppingList.query.get(data['data']['id'])
        assert list_obj is not None
        assert list_obj.title == 'Neue Einkaufsliste'

    def test_create_list_without_is_shared_defaults_to_false(self, client, app, user_headers):
        """Test that is_shared defaults to False if not provided."""
        response = client.post('/api/v1/lists', headers=user_headers, json={
            'title': 'Neue Liste'
        })

        assert response.status_code == 201
        data = response.get_json()

        assert data['data']['is_shared'] is False

    def test_create_list_with_empty_title_returns_400(self, client, app, user_headers):
        """Test that creating a list with empty title returns 400."""
        response = client.post('/api/v1/lists', headers=user_headers, json={
            'title': ''
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False

    def test_create_list_without_title_returns_400(self, client, app, user_headers):
        """Test that creating a list without title returns 400."""
        response = client.post('/api/v1/lists', headers=user_headers, json={
            'is_shared': False
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False

    def test_create_list_without_token_returns_401(self, client, app):
        """Test that creating a list without token returns 401."""
        response = client.post('/api/v1/lists', headers={
            'Content-Type': 'application/json'
        }, json={
            'title': 'Test Liste'
        })

        assert response.status_code == 401

    def test_create_list_with_long_title_returns_400(self, client, app, user_headers):
        """Test that creating a list with too long title returns 400."""
        long_title = 'A' * 201  # Exceeds 200 character limit

        response = client.post('/api/v1/lists', headers=user_headers, json={
            'title': long_title
        })

        assert response.status_code == 400


# ============================================================================
# Update List Tests
# ============================================================================

class TestUpdateList:
    """Test PUT /api/v1/lists/<id> endpoint."""

    def test_update_list_title_with_valid_data_returns_200(self, client, app, user_headers, sample_list):
        """Test that updating list title returns 200."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated Title'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['title'] == 'Updated Title'

        # Verify in database
        db.session.refresh(sample_list)
        assert sample_list.title == 'Updated Title'

    def test_update_list_increments_version(self, client, app, user_headers, sample_list):
        """Test that updating a list increments the version."""
        original_version = sample_list.version

        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated Title',
            'version': original_version
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['version'] == original_version + 1

    def test_update_list_is_shared_to_true(self, client, app, user_headers, sample_list):
        """Test that updating is_shared to True works."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'is_shared': True
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['is_shared'] is True

        # Verify in database
        db.session.refresh(sample_list)
        assert sample_list.is_shared is True

    def test_update_list_is_shared_to_false_regenerates_guid(self, client, app, user_headers, shared_list):
        """Test that changing is_shared to False regenerates GUID."""
        original_guid = shared_list.guid

        response = client.put(f'/api/v1/lists/{shared_list.id}', headers=user_headers, json={
            'is_shared': False
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['is_shared'] is False
        assert data['data']['guid'] != original_guid

    def test_update_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that updating another user's list returns 403."""
        response = client.put(f'/api/v1/lists/{admin_list.id}', headers=user_headers, json={
            'title': 'Hacked Title'
        })

        assert response.status_code == 403

    def test_update_nonexistent_list_returns_404(self, client, app, user_headers):
        """Test that updating non-existent list returns 404."""
        response = client.put('/api/v1/lists/99999', headers=user_headers, json={
            'title': 'New Title'
        })

        assert response.status_code == 404

    def test_update_deleted_list_returns_404(self, client, app, user_headers, deleted_list):
        """Test that updating a deleted list returns 404."""
        response = client.put(f'/api/v1/lists/{deleted_list.id}', headers=user_headers, json={
            'title': 'Updated Title'
        })

        assert response.status_code == 404

    def test_admin_can_update_any_list(self, client, app, admin_headers, sample_list):
        """Test that admins can update any user's list."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=admin_headers, json={
            'title': 'Admin Updated'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['title'] == 'Admin Updated'


# ============================================================================
# Delete List Tests (Soft Delete)
# ============================================================================

class TestDeleteList:
    """Test DELETE /api/v1/lists/<id> endpoint."""

    def test_delete_list_with_valid_id_returns_200(self, client, app, user_headers, sample_list):
        """Test that deleting a list returns 200."""
        response = client.delete(f'/api/v1/lists/{sample_list.id}', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'Papierkorb' in data['message']

        # Verify soft delete
        db.session.refresh(sample_list)
        assert sample_list.deleted_at is not None

    def test_delete_list_soft_deletes_items(self, client, app, user_headers, sample_list, sample_item):
        """Test that deleting a list also soft deletes its items."""
        response = client.delete(f'/api/v1/lists/{sample_list.id}', headers=user_headers)

        assert response.status_code == 200

        # Verify items are soft deleted
        db.session.refresh(sample_item)
        assert sample_item.deleted_at is not None

    def test_delete_other_user_list_returns_403(self, client, app, user_headers, admin_list):
        """Test that deleting another user's list returns 403."""
        response = client.delete(f'/api/v1/lists/{admin_list.id}', headers=user_headers)

        assert response.status_code == 403

    def test_delete_nonexistent_list_returns_404(self, client, app, user_headers):
        """Test that deleting non-existent list returns 404."""
        response = client.delete('/api/v1/lists/99999', headers=user_headers)

        assert response.status_code == 404

    def test_admin_can_delete_any_list(self, client, app, admin_headers, sample_list):
        """Test that admins can delete any user's list."""
        response = client.delete(f'/api/v1/lists/{sample_list.id}', headers=admin_headers)

        assert response.status_code == 200


# ============================================================================
# Toggle Share Tests
# ============================================================================

class TestToggleShare:
    """Test POST /api/v1/lists/<id>/share endpoint."""

    def test_toggle_share_to_true_returns_200(self, client, app, user_headers, sample_list):
        """Test that enabling sharing returns 200."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/share', headers=user_headers, json={
            'is_shared': True
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['is_shared'] is True

    def test_toggle_share_to_false_returns_200(self, client, app, user_headers, shared_list):
        """Test that disabling sharing returns 200."""
        response = client.post(f'/api/v1/lists/{shared_list.id}/share', headers=user_headers, json={
            'is_shared': False
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['is_shared'] is False


# ============================================================================
# Get Share URL Tests
# ============================================================================

class TestGetShareUrl:
    """Test GET /api/v1/lists/<id>/share-url endpoint."""

    def test_get_share_url_returns_200(self, client, app, user_headers, sample_list):
        """Test that getting share URL returns 200."""
        response = client.get(f'/api/v1/lists/{sample_list.id}/share-url', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['guid'] == sample_list.guid
        assert 'api_url' in data['data']
        assert 'web_url' in data['data']


# ============================================================================
# Trash Management Tests
# ============================================================================

class TestTrashLists:
    """Test GET /api/v1/trash/lists endpoint."""

    def test_get_trash_lists_returns_200(self, client, app, user_headers, deleted_list):
        """Test that getting trash lists returns 200."""
        response = client.get('/api/v1/trash/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == deleted_list.id

    def test_get_trash_lists_excludes_active_lists(self, client, app, user_headers, sample_list, deleted_list):
        """Test that trash endpoint only returns deleted lists."""
        response = client.get('/api/v1/trash/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        list_ids = [item['id'] for item in data['data']]
        assert deleted_list.id in list_ids
        assert sample_list.id not in list_ids


class TestRestoreList:
    """Test POST /api/v1/lists/<id>/restore endpoint."""

    def test_restore_list_returns_200(self, client, app, user_headers, deleted_list):
        """Test that restoring a list returns 200."""
        response = client.post(f'/api/v1/lists/{deleted_list.id}/restore', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'wiederhergestellt' in data['message']

        # Verify restore
        db.session.refresh(deleted_list)
        assert deleted_list.deleted_at is None

    def test_restore_active_list_returns_404(self, client, app, user_headers, sample_list):
        """Test that restoring an active list returns 404."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/restore', headers=user_headers)

        assert response.status_code == 404


class TestPermanentDeleteList:
    """Test DELETE /api/v1/trash/lists/<id> endpoint."""

    def test_permanent_delete_as_admin_returns_200(self, client, app, admin_headers, deleted_list):
        """Test that admin can permanently delete a list."""
        list_id = deleted_list.id

        response = client.delete(f'/api/v1/trash/lists/{list_id}', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'endgültig gelöscht' in data['message']

        # Verify hard delete
        assert ShoppingList.query.get(list_id) is None

    def test_permanent_delete_as_regular_user_returns_403(self, client, app, user_headers, deleted_list):
        """Test that regular users cannot permanently delete."""
        response = client.delete(f'/api/v1/trash/lists/{deleted_list.id}', headers=user_headers)

        assert response.status_code == 403
        data = response.get_json()

        assert data['success'] is False
