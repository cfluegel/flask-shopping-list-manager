"""
Tests for Shared Lists (Public Access).

Tests public endpoints for accessing shared shopping lists without authentication.
"""

import pytest
import json

from app.models import ShoppingList, ShoppingListItem
from app.extensions import db


# ============================================================================
# Get Shared List Tests
# ============================================================================

class TestGetSharedList:
    """Test GET /api/v1/shared/<guid> endpoint."""

    def test_get_shared_list_without_auth_returns_200(self, client, app, shared_list):
        """Test that anyone can access a shared list without authentication."""
        response = client.get(f'/api/v1/shared/{shared_list.guid}')

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['guid'] == shared_list.guid
        assert data['data']['title'] == shared_list.title
        assert 'items' in data['data']

    def test_get_shared_list_includes_owner_username(self, client, app, shared_list, regular_user):
        """Test that shared list response includes owner username."""
        response = client.get(f'/api/v1/shared/{shared_list.guid}')

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['owner'] == regular_user.username

    def test_get_shared_list_includes_items(self, client, app, shared_list):
        """Test that shared list response includes all items."""
        # Add items to shared list
        item1 = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Item 1',
            quantity='1'
        )
        item2 = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Item 2',
            quantity='2'
        )
        db.session.add_all([item1, item2])
        db.session.commit()

        response = client.get(f'/api/v1/shared/{shared_list.guid}')

        assert response.status_code == 200
        data = response.get_json()

        assert len(data['data']['items']) == 2

    def test_get_private_list_via_shared_endpoint_returns_404(self, client, app, sample_list):
        """Test that private lists cannot be accessed via shared endpoint."""
        response = client.get(f'/api/v1/shared/{sample_list.guid}')

        assert response.status_code == 404
        data = response.get_json()

        assert data['success'] is False
        assert 'nicht geteilt' in data['error']['message']

    def test_get_shared_list_with_invalid_guid_returns_404(self, client, app):
        """Test that invalid GUID returns 404."""
        invalid_guid = '00000000-0000-0000-0000-000000000000'

        response = client.get(f'/api/v1/shared/{invalid_guid}')

        assert response.status_code == 404
        data = response.get_json()

        assert data['success'] is False

    def test_get_shared_list_excludes_deleted_items(self, client, app, shared_list):
        """Test that deleted items are not included in shared list response."""
        # Add active and deleted items
        active_item = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Active Item',
            quantity='1'
        )
        deleted_item = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Deleted Item',
            quantity='1'
        )
        db.session.add_all([active_item, deleted_item])
        db.session.commit()

        deleted_item.soft_delete()
        db.session.commit()

        response = client.get(f'/api/v1/shared/{shared_list.guid}')

        assert response.status_code == 200
        data = response.get_json()

        item_names = [item['name'] for item in data['data']['items']]
        assert 'Active Item' in item_names
        assert 'Deleted Item' not in item_names

    def test_get_deleted_shared_list_returns_404(self, client, app, shared_list):
        """Test that deleted shared lists return 404."""
        shared_list.soft_delete()
        db.session.commit()

        response = client.get(f'/api/v1/shared/{shared_list.guid}')

        assert response.status_code == 404


# ============================================================================
# Get Shared List Items Tests
# ============================================================================

class TestGetSharedListItems:
    """Test GET /api/v1/shared/<guid>/items endpoint."""

    def test_get_shared_list_items_without_auth_returns_200(self, client, app, shared_list):
        """Test that anyone can get items from shared list without authentication."""
        # Add items
        item = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Test Item',
            quantity='1'
        )
        db.session.add(item)
        db.session.commit()

        response = client.get(f'/api/v1/shared/{shared_list.guid}/items')

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['name'] == 'Test Item'

    def test_get_shared_list_items_returns_only_items(self, client, app, shared_list):
        """Test that items endpoint returns only items, not list metadata."""
        response = client.get(f'/api/v1/shared/{shared_list.guid}/items')

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_get_private_list_items_via_shared_endpoint_returns_404(self, client, app, sample_list):
        """Test that private list items cannot be accessed."""
        response = client.get(f'/api/v1/shared/{sample_list.guid}/items')

        assert response.status_code == 404

    def test_get_shared_list_items_with_invalid_guid_returns_404(self, client, app):
        """Test that invalid GUID returns 404."""
        invalid_guid = '00000000-0000-0000-0000-000000000000'

        response = client.get(f'/api/v1/shared/{invalid_guid}/items')

        assert response.status_code == 404


# ============================================================================
# Get Shared List Info Tests
# ============================================================================

class TestGetSharedListInfo:
    """Test GET /api/v1/shared/<guid>/info endpoint."""

    def test_get_shared_list_info_without_auth_returns_200(self, client, app, shared_list):
        """Test that anyone can get shared list info without authentication."""
        response = client.get(f'/api/v1/shared/{shared_list.guid}/info')

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['guid'] == shared_list.guid
        assert data['data']['title'] == shared_list.title
        assert data['data']['is_shared'] is True

    def test_get_shared_list_info_includes_counts(self, client, app, shared_list):
        """Test that info endpoint includes item counts."""
        # Add items
        item1 = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Unchecked',
            quantity='1',
            is_checked=False
        )
        item2 = ShoppingListItem(
            shopping_list_id=shared_list.id,
            name='Checked',
            quantity='1',
            is_checked=True
        )
        db.session.add_all([item1, item2])
        db.session.commit()

        response = client.get(f'/api/v1/shared/{shared_list.guid}/info')

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['item_count'] == 2
        assert data['data']['checked_count'] == 1

    def test_get_shared_list_info_does_not_include_items(self, client, app, shared_list):
        """Test that info endpoint does not include full item list."""
        response = client.get(f'/api/v1/shared/{shared_list.guid}/info')

        assert response.status_code == 200
        data = response.get_json()

        assert 'items' not in data['data']
        assert 'item_count' in data['data']

    def test_get_private_list_info_via_shared_endpoint_returns_404(self, client, app, sample_list):
        """Test that private list info cannot be accessed."""
        response = client.get(f'/api/v1/shared/{sample_list.guid}/info')

        assert response.status_code == 404


# ============================================================================
# Sharing Workflow Tests
# ============================================================================

class TestSharingWorkflow:
    """Test complete sharing workflow scenarios."""

    def test_share_list_and_access_publicly(self, client, app, user_headers, sample_list):
        """Test complete workflow: enable sharing and access publicly."""
        # Initially private
        response = client.get(f'/api/v1/shared/{sample_list.guid}')
        assert response.status_code == 404

        # Enable sharing
        response = client.post(f'/api/v1/lists/{sample_list.id}/share', headers=user_headers, json={
            'is_shared': True
        })
        assert response.status_code == 200

        # Now accessible publicly
        response = client.get(f'/api/v1/shared/{sample_list.guid}')
        assert response.status_code == 200

    def test_unshare_list_removes_public_access(self, client, app, user_headers, shared_list):
        """Test that disabling sharing removes public access."""
        guid = shared_list.guid

        # Initially accessible
        response = client.get(f'/api/v1/shared/{guid}')
        assert response.status_code == 200

        # Disable sharing
        response = client.post(f'/api/v1/lists/{shared_list.id}/share', headers=user_headers, json={
            'is_shared': False
        })
        assert response.status_code == 200

        # GUID should have changed (security feature)
        db.session.refresh(shared_list)
        new_guid = shared_list.guid
        assert new_guid != guid

        # Old GUID no longer works
        response = client.get(f'/api/v1/shared/{guid}')
        assert response.status_code == 404

        # New GUID also doesn't work (list is private now)
        response = client.get(f'/api/v1/shared/{new_guid}')
        assert response.status_code == 404

    def test_shared_list_accessible_by_authenticated_and_unauthenticated(self, client, app, shared_list, another_user_headers):
        """Test that shared list is accessible both with and without auth."""
        # Without authentication
        response1 = client.get(f'/api/v1/shared/{shared_list.guid}')
        assert response1.status_code == 200

        # With authentication (different user)
        response2 = client.get(f'/api/v1/shared/{shared_list.guid}', headers=another_user_headers)
        assert response2.status_code == 200

        # Both should return same data
        data1 = response1.get_json()
        data2 = response2.get_json()
        assert data1['data']['guid'] == data2['data']['guid']

    def test_get_share_url_and_use_it(self, client, app, user_headers, shared_list):
        """Test getting share URL and using it to access list."""
        # Get share URL
        response = client.get(f'/api/v1/lists/{shared_list.id}/share-url', headers=user_headers)
        assert response.status_code == 200
        data = response.get_json()

        guid = data['data']['guid']

        # Use GUID to access list publicly
        response = client.get(f'/api/v1/shared/{guid}')
        assert response.status_code == 200


# ============================================================================
# Security Tests
# ============================================================================

class TestSharingSecurity:
    """Test security aspects of sharing."""

    def test_shared_list_does_not_expose_user_id(self, client, app, shared_list):
        """Test that shared list response doesn't include sensitive user data."""
        response = client.get(f'/api/v1/shared/{shared_list.guid}')

        assert response.status_code == 200
        data = response.get_json()

        # Should include username but not user_id or email
        assert 'owner' in data['data']
        assert 'owner_id' not in data['data']
        assert 'email' not in data['data']

    def test_shared_list_does_not_include_version(self, client, app, shared_list):
        """Test that shared list doesn't expose version field."""
        response = client.get(f'/api/v1/shared/{shared_list.guid}')

        assert response.status_code == 200
        data = response.get_json()

        # Version should not be exposed to prevent manipulation
        assert 'version' not in data['data']

    def test_cannot_modify_shared_list_via_public_endpoint(self, client, app, shared_list):
        """Test that shared endpoint is read-only."""
        # Try to POST/PUT/DELETE (should not be allowed)
        response = client.post(f'/api/v1/shared/{shared_list.guid}', json={
            'title': 'Hacked'
        })
        # Should return 405 Method Not Allowed or 404
        assert response.status_code in [404, 405]

    def test_guid_is_long_and_random(self, client, app, user_headers):
        """Test that GUIDs are sufficiently long and random."""
        # Create multiple lists and check GUIDs
        guids = set()

        for i in range(5):
            response = client.post('/api/v1/lists', headers=user_headers, json={
                'title': f'List {i}'
            })
            data = response.get_json()
            guid = data['data']['guid']

            assert len(guid) == 36  # Standard UUID format
            assert guid not in guids  # Unique
            guids.add(guid)

    def test_guessing_guid_is_impractical(self, client, app):
        """Test that sequential GUIDs don't reveal pattern."""
        # Try accessing with common/predictable GUIDs
        predictable_guids = [
            '00000000-0000-0000-0000-000000000001',
            '11111111-1111-1111-1111-111111111111',
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        ]

        for guid in predictable_guids:
            response = client.get(f'/api/v1/shared/{guid}')
            assert response.status_code == 404  # Should not exist


# ============================================================================
# Edge Cases
# ============================================================================

class TestSharingEdgeCases:
    """Test edge cases for sharing functionality."""

    def test_shared_empty_list_returns_200(self, client, app, shared_list):
        """Test that shared list with no items still returns 200."""
        response = client.get(f'/api/v1/shared/{shared_list.guid}')

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['items'] == []

    def test_shared_list_with_many_items(self, client, app, shared_list):
        """Test that shared list with many items works correctly."""
        # Add many items
        for i in range(50):
            item = ShoppingListItem(
                shopping_list_id=shared_list.id,
                name=f'Item {i}',
                quantity='1'
            )
            db.session.add(item)
        db.session.commit()

        response = client.get(f'/api/v1/shared/{shared_list.guid}')

        assert response.status_code == 200
        data = response.get_json()

        assert len(data['data']['items']) == 50

    def test_shared_list_after_owner_deleted(self, client, app, shared_list, regular_user):
        """Test shared list behavior after owner is deleted (should cascade)."""
        guid = shared_list.guid

        # Delete owner
        db.session.delete(regular_user)
        db.session.commit()

        # List should also be deleted (cascade)
        response = client.get(f'/api/v1/shared/{guid}')
        assert response.status_code == 404
