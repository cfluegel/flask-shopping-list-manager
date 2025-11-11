"""
Tests for Admin API Endpoints.

Tests administrative functions including user management, statistics, and system operations.
"""

import pytest
import json

from app.models import User, ShoppingList, ShoppingListItem, RevokedToken
from app.extensions import db


# ============================================================================
# Admin User Management Tests
# ============================================================================

class TestAdminUsers:
    """Test admin user management endpoints."""

    def test_admin_get_all_users_returns_200(self, client, app, admin_headers, regular_user, another_user):
        """Test that admin can get all users."""
        response = client.get('/api/v1/users', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        # Should include at least admin, regular_user, another_user
        assert len(data['data']) >= 3

    def test_regular_user_cannot_get_all_users(self, client, app, user_headers):
        """Test that regular users cannot get all users."""
        response = client.get('/api/v1/users', headers=user_headers)

        assert response.status_code == 403

    def test_admin_create_user_returns_201(self, client, app, admin_headers):
        """Test that admin can create new users."""
        response = client.post('/api/v1/users', headers=admin_headers, json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123',
            'is_admin': False
        })

        assert response.status_code == 201
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['username'] == 'newuser'
        assert data['data']['is_admin'] is False

        # Verify in database
        user = User.query.filter_by(username='newuser').first()
        assert user is not None

    def test_admin_create_admin_user_returns_201(self, client, app, admin_headers):
        """Test that admin can create other admin users."""
        response = client.post('/api/v1/users', headers=admin_headers, json={
            'username': 'newadmin',
            'email': 'newadmin@example.com',
            'password': 'SecurePass123',
            'is_admin': True
        })

        assert response.status_code == 201
        data = response.get_json()

        assert data['data']['is_admin'] is True

    def test_regular_user_cannot_create_users(self, client, app, user_headers):
        """Test that regular users cannot create users."""
        response = client.post('/api/v1/users', headers=user_headers, json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123'
        })

        assert response.status_code == 403

    def test_admin_delete_user_returns_200(self, client, app, admin_headers, another_user):
        """Test that admin can delete users."""
        user_id = another_user.id

        response = client.delete(f'/api/v1/users/{user_id}', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True

        # Verify deletion
        assert User.query.get(user_id) is None

    def test_admin_cannot_delete_self(self, client, app, admin_headers, admin_user):
        """Test that admin cannot delete their own account."""
        response = client.delete(f'/api/v1/users/{admin_user.id}', headers=admin_headers)

        assert response.status_code == 400
        data = response.get_json()

        assert 'eigenen Account' in data['error']['message']

    def test_admin_delete_user_cascades_to_lists(self, client, app, admin_headers, another_user):
        """Test that deleting user also deletes their lists."""
        # Create list for user
        shopping_list = ShoppingList(title='Test List', user_id=another_user.id)
        db.session.add(shopping_list)
        db.session.commit()

        list_id = shopping_list.id
        user_id = another_user.id

        # Delete user
        response = client.delete(f'/api/v1/users/{user_id}', headers=admin_headers)

        assert response.status_code == 200

        # Verify list was also deleted
        assert ShoppingList.query.get(list_id) is None

    def test_regular_user_cannot_delete_users(self, client, app, user_headers, another_user):
        """Test that regular users cannot delete users."""
        response = client.delete(f'/api/v1/users/{another_user.id}', headers=user_headers)

        assert response.status_code == 403


# ============================================================================
# Admin Statistics Tests
# ============================================================================

class TestAdminStatistics:
    """Test admin statistics endpoint."""

    def test_admin_get_statistics_returns_200(self, client, app, admin_headers):
        """Test that admin can get system statistics."""
        response = client.get('/api/v1/admin/stats', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'users' in data['data']
        assert 'lists' in data['data']
        assert 'items' in data['data']
        assert 'tokens' in data['data']

    def test_statistics_include_correct_counts(self, client, app, admin_headers, regular_user, sample_list, sample_item):
        """Test that statistics contain correct counts."""
        response = client.get('/api/v1/admin/stats', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['users']['total'] >= 2  # admin + regular_user
        assert data['data']['lists']['total'] >= 1
        assert data['data']['items']['total'] >= 1

    def test_statistics_include_top_users(self, client, app, admin_headers, regular_user):
        """Test that statistics include top users."""
        # Create multiple lists for regular_user
        for i in range(3):
            shopping_list = ShoppingList(title=f'List {i}', user_id=regular_user.id)
            db.session.add(shopping_list)
        db.session.commit()

        response = client.get('/api/v1/admin/stats', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert 'top_users' in data['data']
        assert len(data['data']['top_users']) > 0

    def test_statistics_include_largest_lists(self, client, app, admin_headers, sample_list):
        """Test that statistics include largest lists."""
        # Add items to list
        for i in range(5):
            item = ShoppingListItem(
                shopping_list_id=sample_list.id,
                name=f'Item {i}',
                quantity='1'
            )
            db.session.add(item)
        db.session.commit()

        response = client.get('/api/v1/admin/stats', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert 'largest_lists' in data['data']

    def test_regular_user_cannot_get_statistics(self, client, app, user_headers):
        """Test that regular users cannot get statistics."""
        response = client.get('/api/v1/admin/stats', headers=user_headers)

        assert response.status_code == 403


# ============================================================================
# Admin List Management Tests
# ============================================================================

class TestAdminLists:
    """Test admin list management endpoints."""

    def test_admin_get_all_lists_returns_200(self, client, app, admin_headers, sample_list, admin_list):
        """Test that admin can get all lists from all users."""
        response = client.get('/api/v1/admin/lists', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert len(data['data']) >= 2  # sample_list + admin_list

    def test_admin_get_all_lists_includes_owner_info(self, client, app, admin_headers, sample_list):
        """Test that list response includes owner information."""
        response = client.get('/api/v1/admin/lists', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Find sample_list in response
        list_data = next(item for item in data['data'] if item['id'] == sample_list.id)
        assert 'owner_username' in list_data
        assert 'owner_id' in list_data

    def test_admin_get_all_lists_with_shared_only_filter(self, client, app, admin_headers, sample_list, shared_list):
        """Test that shared_only filter works."""
        response = client.get('/api/v1/admin/lists?shared_only=true', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        # All lists should be shared
        for list_data in data['data']:
            assert list_data['is_shared'] is True

    def test_admin_delete_any_list_returns_200(self, client, app, admin_headers, sample_list):
        """Test that admin can delete any user's list."""
        list_id = sample_list.id

        response = client.delete(f'/api/v1/admin/lists/{list_id}', headers=admin_headers)

        assert response.status_code == 200

        # Verify deletion
        assert ShoppingList.query.get(list_id) is None

    def test_regular_user_cannot_get_all_lists(self, client, app, user_headers):
        """Test that regular users cannot get all lists."""
        response = client.get('/api/v1/admin/lists', headers=user_headers)

        assert response.status_code == 403

    def test_regular_user_cannot_admin_delete_lists(self, client, app, user_headers, sample_list):
        """Test that regular users cannot use admin delete."""
        response = client.delete(f'/api/v1/admin/lists/{sample_list.id}', headers=user_headers)

        assert response.status_code == 403


# ============================================================================
# Admin Token Management Tests
# ============================================================================

class TestAdminTokenManagement:
    """Test admin token management endpoints."""

    def test_admin_cleanup_revoked_tokens_returns_200(self, client, app, admin_headers):
        """Test that admin can cleanup expired tokens."""
        response = client.post('/api/v1/admin/tokens/cleanup', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'deleted_count' in data['data']

    def test_admin_get_token_stats_returns_200(self, client, app, admin_headers):
        """Test that admin can get token statistics."""
        response = client.get('/api/v1/admin/tokens/stats', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'total_revoked' in data['data']
        assert 'by_type' in data['data']
        assert 'recent_revocations' in data['data']

    def test_token_stats_include_correct_data(self, client, app, admin_headers, revoked_token_data):
        """Test that token stats include correct information."""
        # Add revoked token
        RevokedToken.add_to_blacklist(
            jti=revoked_token_data['jti'],
            token_type='access',
            user_id=revoked_token_data['user_id'],
            expires_at=revoked_token_data['expires_at']
        )

        response = client.get('/api/v1/admin/tokens/stats', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['total_revoked'] >= 1
        assert 'access' in data['data']['by_type']
        assert 'refresh' in data['data']['by_type']

    def test_regular_user_cannot_cleanup_tokens(self, client, app, user_headers):
        """Test that regular users cannot cleanup tokens."""
        response = client.post('/api/v1/admin/tokens/cleanup', headers=user_headers)

        assert response.status_code == 403

    def test_regular_user_cannot_get_token_stats(self, client, app, user_headers):
        """Test that regular users cannot get token stats."""
        response = client.get('/api/v1/admin/tokens/stats', headers=user_headers)

        assert response.status_code == 403


# ============================================================================
# Admin User Activity Tests
# ============================================================================

class TestAdminUserActivity:
    """Test admin user activity endpoint."""

    def test_admin_get_user_activity_returns_200(self, client, app, admin_headers, regular_user):
        """Test that admin can get user activity."""
        response = client.get(f'/api/v1/admin/users/{regular_user.id}/activity', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'user' in data['data']
        assert 'lists' in data['data']
        assert 'items' in data['data']
        assert 'recent_lists' in data['data']

    def test_user_activity_includes_correct_counts(self, client, app, admin_headers, regular_user, sample_list, sample_item):
        """Test that user activity includes correct counts."""
        response = client.get(f'/api/v1/admin/users/{regular_user.id}/activity', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['lists']['total'] >= 1
        assert data['data']['items']['total'] >= 1

    def test_user_activity_includes_user_info(self, client, app, admin_headers, regular_user):
        """Test that user activity includes user information."""
        response = client.get(f'/api/v1/admin/users/{regular_user.id}/activity', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['user']['id'] == regular_user.id
        assert data['data']['user']['username'] == regular_user.username
        assert data['data']['user']['email'] == regular_user.email

    def test_admin_get_nonexistent_user_activity_returns_404(self, client, app, admin_headers):
        """Test that getting activity for non-existent user returns 404."""
        response = client.get('/api/v1/admin/users/99999/activity', headers=admin_headers)

        assert response.status_code == 404

    def test_regular_user_cannot_get_user_activity(self, client, app, user_headers, another_user):
        """Test that regular users cannot get user activity."""
        response = client.get(f'/api/v1/admin/users/{another_user.id}/activity', headers=user_headers)

        assert response.status_code == 403


# ============================================================================
# User Resource Access Tests
# ============================================================================

class TestUserResourceAccess:
    """Test user-specific resource access with self_or_admin_required."""

    def test_user_get_own_info_returns_200(self, client, app, user_headers, regular_user):
        """Test that users can get their own information."""
        response = client.get(f'/api/v1/users/{regular_user.id}', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['id'] == regular_user.id

    def test_user_cannot_get_other_user_info(self, client, app, user_headers, another_user):
        """Test that users cannot get other users' information."""
        response = client.get(f'/api/v1/users/{another_user.id}', headers=user_headers)

        assert response.status_code == 403

    def test_admin_can_get_any_user_info(self, client, app, admin_headers, regular_user):
        """Test that admin can get any user's information."""
        response = client.get(f'/api/v1/users/{regular_user.id}', headers=admin_headers)

        assert response.status_code == 200

    def test_user_update_own_info_returns_200(self, client, app, user_headers, regular_user):
        """Test that users can update their own information."""
        response = client.put(f'/api/v1/users/{regular_user.id}', headers=user_headers, json={
            'username': 'updated_username'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['username'] == 'updated_username'

    def test_user_cannot_update_other_user_info(self, client, app, user_headers, another_user):
        """Test that users cannot update other users' information."""
        response = client.put(f'/api/v1/users/{another_user.id}', headers=user_headers, json={
            'username': 'hacked'
        })

        assert response.status_code == 403

    def test_user_cannot_change_own_admin_status(self, client, app, user_headers, regular_user):
        """Test that regular users cannot make themselves admin."""
        response = client.put(f'/api/v1/users/{regular_user.id}', headers=user_headers, json={
            'is_admin': True
        })

        assert response.status_code == 403
        data = response.get_json()

        assert 'Admin-Status' in data['error']['message']

    def test_admin_can_change_user_admin_status(self, client, app, admin_headers, regular_user):
        """Test that admins can change user's admin status."""
        response = client.put(f'/api/v1/users/{regular_user.id}', headers=admin_headers, json={
            'is_admin': True
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['is_admin'] is True

    def test_user_get_own_lists_returns_200(self, client, app, user_headers, regular_user, sample_list):
        """Test that users can get their own lists."""
        response = client.get(f'/api/v1/users/{regular_user.id}/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert len(data['data']) >= 1

    def test_user_cannot_get_other_user_lists(self, client, app, user_headers, admin_user):
        """Test that users cannot get other users' lists."""
        response = client.get(f'/api/v1/users/{admin_user.id}/lists', headers=user_headers)

        assert response.status_code == 403

    def test_admin_can_get_any_user_lists(self, client, app, admin_headers, regular_user):
        """Test that admin can get any user's lists."""
        response = client.get(f'/api/v1/users/{regular_user.id}/lists', headers=admin_headers)

        assert response.status_code == 200


# ============================================================================
# Admin Pagination Tests
# ============================================================================

class TestAdminPagination:
    """Test pagination for admin endpoints."""

    def test_admin_users_pagination(self, client, app, admin_headers):
        """Test that user list pagination works."""
        # Create multiple users
        for i in range(5):
            user = User(
                username=f'user{i}',
                email=f'user{i}@example.com',
                is_admin=False
            )
            user.set_password('Password123')
            db.session.add(user)
        db.session.commit()

        # Get first page with 3 items
        response = client.get('/api/v1/users?page=1&per_page=3', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert len(data['data']) == 3
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 3
        assert data['pagination']['has_next'] is True

    def test_admin_lists_pagination(self, client, app, admin_headers, regular_user):
        """Test that list pagination works."""
        # Create multiple lists
        for i in range(5):
            shopping_list = ShoppingList(title=f'List {i}', user_id=regular_user.id)
            db.session.add(shopping_list)
        db.session.commit()

        # Get first page with 2 items
        response = client.get('/api/v1/admin/lists?page=1&per_page=2', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert len(data['data']) == 2
        assert data['pagination']['has_next'] is True
