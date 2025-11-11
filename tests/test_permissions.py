"""
Tests for Authorization and Permission System.

Tests the decorators and permission checks for API endpoints.
"""

import pytest
import json

from app.models import ShoppingList, ShoppingListItem, User
from app.extensions import db


# ============================================================================
# Admin Required Tests
# ============================================================================

class TestAdminRequired:
    """Test admin_required decorator functionality."""

    def test_admin_can_access_admin_endpoint(self, client, app, admin_headers):
        """Test that admins can access admin-only endpoints."""
        # FIX APPLIED: Use existing admin route /api/v1/admin/stats
        response = client.get('/api/v1/admin/stats', headers=admin_headers)

        # Should succeed (200 or appropriate status, not 403)
        assert response.status_code != 403

    def test_regular_user_cannot_access_admin_endpoint(self, client, app, user_headers):
        """Test that regular users cannot access admin-only endpoints."""
        # FIX APPLIED: Use existing admin route /api/v1/admin/stats
        response = client.get('/api/v1/admin/stats', headers=user_headers)

        assert response.status_code == 403
        data = response.get_json()

        assert data['success'] is False
        assert 'Administrator' in data['error']['message']

    def test_unauthenticated_user_cannot_access_admin_endpoint(self, client, app):
        """Test that unauthenticated users cannot access admin endpoints."""
        # FIX APPLIED: Use existing admin route /api/v1/admin/stats
        response = client.get('/api/v1/admin/stats', headers={
            'Content-Type': 'application/json'
        })

        assert response.status_code == 401


# ============================================================================
# Self or Admin Required Tests
# ============================================================================

class TestSelfOrAdminRequired:
    """Test self_or_admin_required decorator functionality."""

    def test_user_can_access_own_resource(self, client, app, user_headers, regular_user):
        """Test that users can access their own resources."""
        response = client.get(f'/api/v1/users/{regular_user.id}', headers=user_headers)

        # Should succeed
        assert response.status_code == 200

    def test_user_cannot_access_other_user_resource(self, client, app, user_headers, admin_user):
        """Test that users cannot access other users' resources."""
        response = client.get(f'/api/v1/users/{admin_user.id}', headers=user_headers)

        assert response.status_code == 403
        data = response.get_json()

        assert data['success'] is False

    def test_admin_can_access_any_user_resource(self, client, app, admin_headers, regular_user):
        """Test that admins can access any user's resources."""
        response = client.get(f'/api/v1/users/{regular_user.id}', headers=admin_headers)

        # Should succeed
        assert response.status_code == 200

    def test_unauthenticated_cannot_access_user_resource(self, client, app, regular_user):
        """Test that unauthenticated users cannot access user resources."""
        response = client.get(f'/api/v1/users/{regular_user.id}', headers={
            'Content-Type': 'application/json'
        })

        assert response.status_code == 401


# ============================================================================
# List Owner or Admin Required Tests
# ============================================================================

class TestListOwnerOrAdminRequired:
    """Test list_owner_or_admin_required decorator functionality."""

    def test_owner_can_update_own_list(self, client, app, user_headers, sample_list):
        """Test that list owners can update their lists."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated by Owner'
        })

        assert response.status_code == 200

    def test_owner_can_delete_own_list(self, client, app, user_headers, sample_list):
        """Test that list owners can delete their lists."""
        response = client.delete(f'/api/v1/lists/{sample_list.id}', headers=user_headers)

        assert response.status_code == 200

    def test_non_owner_cannot_update_list(self, client, app, another_user_headers, sample_list):
        """Test that non-owners cannot update lists."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=another_user_headers, json={
            'title': 'Hacked Title'
        })

        assert response.status_code == 403

    def test_non_owner_cannot_delete_list(self, client, app, another_user_headers, sample_list):
        """Test that non-owners cannot delete lists."""
        response = client.delete(f'/api/v1/lists/{sample_list.id}', headers=another_user_headers)

        assert response.status_code == 403

    def test_admin_can_update_any_list(self, client, app, admin_headers, sample_list):
        """Test that admins can update any list."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=admin_headers, json={
            'title': 'Updated by Admin'
        })

        assert response.status_code == 200

    def test_admin_can_delete_any_list(self, client, app, admin_headers, sample_list):
        """Test that admins can delete any list."""
        response = client.delete(f'/api/v1/lists/{sample_list.id}', headers=admin_headers)

        assert response.status_code == 200


# ============================================================================
# List Access Required Tests (with sharing)
# ============================================================================

class TestListAccessRequired:
    """Test list_access_required decorator functionality."""

    def test_owner_can_view_own_list(self, client, app, user_headers, sample_list):
        """Test that owners can view their own lists."""
        response = client.get(f'/api/v1/lists/{sample_list.id}', headers=user_headers)

        assert response.status_code == 200

    def test_non_owner_cannot_view_private_list(self, client, app, another_user_headers, sample_list):
        """Test that non-owners cannot view private lists."""
        response = client.get(f'/api/v1/lists/{sample_list.id}', headers=another_user_headers)

        assert response.status_code == 403

    def test_non_owner_can_view_shared_list(self, client, app, another_user_headers, shared_list):
        """Test that anyone can view shared lists."""
        response = client.get(f'/api/v1/lists/{shared_list.id}', headers=another_user_headers)

        assert response.status_code == 200

    def test_admin_can_view_any_list(self, client, app, admin_headers, sample_list):
        """Test that admins can view any list regardless of sharing."""
        response = client.get(f'/api/v1/lists/{sample_list.id}', headers=admin_headers)

        assert response.status_code == 200

    def test_non_owner_can_add_item_to_shared_list(self, client, app, another_user_headers, shared_list):
        """Test that users can add items to shared lists."""
        response = client.post(f'/api/v1/lists/{shared_list.id}/items', headers=another_user_headers, json={
            'name': 'Added by Other User'
        })

        assert response.status_code == 201

    def test_non_owner_cannot_add_item_to_private_list(self, client, app, another_user_headers, sample_list):
        """Test that users cannot add items to private lists."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items', headers=another_user_headers, json={
            'name': 'Unauthorized Item'
        })

        assert response.status_code == 403


# ============================================================================
# Item Access Tests
# ============================================================================

class TestItemAccessPermissions:
    """Test item-level access permissions."""

    def test_owner_can_update_item_in_own_list(self, client, app, user_headers, sample_item):
        """Test that owners can update items in their lists."""
        response = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'name': 'Updated by Owner'
        })

        assert response.status_code == 200

    def test_non_owner_cannot_update_item_in_private_list(self, client, app, another_user_headers, sample_item):
        """Test that non-owners cannot update items in private lists."""
        response = client.put(f'/api/v1/items/{sample_item.id}', headers=another_user_headers, json={
            'name': 'Hacked Name'
        })

        assert response.status_code == 403

    def test_non_owner_can_update_item_in_shared_list(self, client, app, another_user_headers, shared_list):
        """Test that users can update items in shared lists."""
        # Create item in shared list
        item = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Shared Item',
            quantity='1'
        )
        db.session.add(item)
        db.session.commit()

        response = client.put(f'/api/v1/items/{item.id}', headers=another_user_headers, json={
            'name': 'Updated by Other User'
        })

        assert response.status_code == 200

    def test_owner_can_reorder_items(self, client, app, user_headers, sample_item):
        """Test that owners can reorder items."""
        response = client.put(f'/api/v1/items/{sample_item.id}/reorder', headers=user_headers, json={
            'order_index': 10
        })

        assert response.status_code == 200

    def test_non_owner_cannot_reorder_items_in_shared_list(self, client, app, another_user_headers, shared_list):
        """Test that non-owners cannot reorder items even in shared lists."""
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

    def test_admin_can_reorder_any_items(self, client, app, admin_headers, sample_item):
        """Test that admins can reorder any items."""
        response = client.put(f'/api/v1/items/{sample_item.id}/reorder', headers=admin_headers, json={
            'order_index': 99
        })

        assert response.status_code == 200


# ============================================================================
# Bulk Operations Permission Tests
# ============================================================================

class TestBulkOperationsPermissions:
    """Test permissions for bulk operations."""

    def test_owner_can_clear_checked_items(self, client, app, user_headers, sample_list, checked_item):
        """Test that owners can clear checked items."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items/clear-checked', headers=user_headers)

        assert response.status_code == 200

    def test_non_owner_cannot_clear_checked_items_in_shared_list(self, client, app, another_user_headers, shared_list):
        """Test that non-owners cannot clear checked items even in shared lists."""
        response = client.post(f'/api/v1/lists/{shared_list.id}/items/clear-checked', headers=another_user_headers)

        assert response.status_code == 403

    def test_admin_can_clear_checked_items_in_any_list(self, client, app, admin_headers, sample_list):
        """Test that admins can clear checked items in any list."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items/clear-checked', headers=admin_headers)

        assert response.status_code == 200


# ============================================================================
# Sharing Permission Tests
# ============================================================================

class TestSharingPermissions:
    """Test permissions for sharing operations."""

    def test_owner_can_toggle_sharing(self, client, app, user_headers, sample_list):
        """Test that owners can toggle sharing."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/share', headers=user_headers, json={
            'is_shared': True
        })

        assert response.status_code == 200

    def test_non_owner_cannot_toggle_sharing(self, client, app, another_user_headers, shared_list):
        """Test that non-owners cannot toggle sharing."""
        response = client.post(f'/api/v1/lists/{shared_list.id}/share', headers=another_user_headers, json={
            'is_shared': False
        })

        assert response.status_code == 403

    def test_admin_can_toggle_sharing_on_any_list(self, client, app, admin_headers, sample_list):
        """Test that admins can toggle sharing on any list."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/share', headers=admin_headers, json={
            'is_shared': True
        })

        assert response.status_code == 200

    def test_owner_can_get_share_url(self, client, app, user_headers, sample_list):
        """Test that owners can get share URL."""
        response = client.get(f'/api/v1/lists/{sample_list.id}/share-url', headers=user_headers)

        assert response.status_code == 200

    def test_non_owner_cannot_get_share_url(self, client, app, another_user_headers, sample_list):
        """Test that non-owners cannot get share URL."""
        response = client.get(f'/api/v1/lists/{sample_list.id}/share-url', headers=another_user_headers)

        assert response.status_code == 403


# ============================================================================
# Trash Management Permission Tests
# ============================================================================

class TestTrashPermissions:
    """Test permissions for trash management."""

    def test_owner_can_restore_own_list(self, client, app, user_headers, deleted_list):
        """Test that owners can restore their own deleted lists."""
        response = client.post(f'/api/v1/lists/{deleted_list.id}/restore', headers=user_headers)

        assert response.status_code == 200

    def test_non_owner_cannot_restore_list(self, client, app, another_user_headers, deleted_list):
        """Test that non-owners cannot restore lists."""
        response = client.post(f'/api/v1/lists/{deleted_list.id}/restore', headers=another_user_headers)

        assert response.status_code == 403

    def test_admin_can_restore_any_list(self, client, app, admin_headers, deleted_list):
        """Test that admins can restore any list."""
        response = client.post(f'/api/v1/lists/{deleted_list.id}/restore', headers=admin_headers)

        assert response.status_code == 200

    def test_only_admin_can_permanently_delete(self, client, app, user_headers, deleted_list):
        """Test that only admins can permanently delete lists."""
        response = client.delete(f'/api/v1/trash/lists/{deleted_list.id}', headers=user_headers)

        assert response.status_code == 403
        data = response.get_json()

        assert 'Administrator' in data['error']['message']

    def test_admin_can_permanently_delete(self, client, app, admin_headers, deleted_list):
        """Test that admins can permanently delete lists."""
        response = client.delete(f'/api/v1/trash/lists/{deleted_list.id}', headers=admin_headers)

        assert response.status_code == 200
