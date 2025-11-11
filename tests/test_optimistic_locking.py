"""
Tests for Optimistic Locking / Version Control.

Tests that concurrent updates are detected and prevented using version fields.
"""

import pytest
import json

from app.models import ShoppingList, ShoppingListItem
from app.extensions import db
from app.api.errors import ConflictError


# ============================================================================
# Shopping List Version Tests
# ============================================================================

class TestListVersionControl:
    """Test optimistic locking for shopping lists."""

    def test_update_list_without_version_succeeds(self, client, app, user_headers, sample_list):
        """Test that updates without version field still work (backwards compatibility)."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated Without Version'
        })

        assert response.status_code == 200
        data = response.get_json()

        # FIX APPLIED: API always increments version, even without version parameter
        # Version is incremented from 1 to 2 (correct behavior)
        assert data['data']['version'] == 2

    def test_update_list_with_correct_version_succeeds(self, client, app, user_headers, sample_list):
        """Test that update with correct version succeeds."""
        current_version = sample_list.version

        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated with Correct Version',
            'version': current_version
        })

        assert response.status_code == 200
        data = response.get_json()

        # Version should be incremented
        assert data['data']['version'] == current_version + 1

    def test_update_list_with_wrong_version_returns_409(self, client, app, user_headers, sample_list):
        """Test that update with wrong version returns 409 Conflict."""
        wrong_version = sample_list.version + 5  # Future version

        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated with Wrong Version',
            'version': wrong_version
        })

        assert response.status_code == 409
        data = response.get_json()

        assert data['success'] is False
        assert 'zwischenzeitlich geändert' in data['error']['message']
        assert 'current_version' in data['error']['details']
        assert 'expected_version' in data['error']['details']

    def test_concurrent_updates_scenario(self, client, app, user_headers, sample_list):
        """Test concurrent update scenario (race condition)."""
        # Simulate two clients reading the same list at the same time
        original_version = sample_list.version

        # Client 1 updates successfully
        response1 = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated by Client 1',
            'version': original_version
        })

        assert response1.status_code == 200
        new_version = response1.get_json()['data']['version']

        # Client 2 tries to update with old version (should fail)
        response2 = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated by Client 2',
            'version': original_version  # Stale version
        })

        assert response2.status_code == 409
        data = response2.get_json()

        assert data['error']['details']['current_version'] == new_version
        assert data['error']['details']['expected_version'] == original_version

    def test_version_increments_on_each_update(self, client, app, user_headers, sample_list):
        """Test that version increments correctly on multiple updates."""
        versions = [sample_list.version]

        for i in range(3):
            response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
                'title': f'Update {i + 1}',
                'version': versions[-1]
            })

            assert response.status_code == 200
            data = response.get_json()
            versions.append(data['data']['version'])

        # Verify versions increased sequentially
        assert versions == [1, 2, 3, 4]

    def test_model_check_version_with_none(self, app, sample_list):
        """Test that model's check_version allows None (backwards compatibility)."""
        # Should not raise exception
        sample_list.check_version(None)

    def test_model_check_version_with_correct_version(self, app, sample_list):
        """Test that model's check_version passes with correct version."""
        current_version = sample_list.version

        # Should not raise exception
        sample_list.check_version(current_version)

    def test_model_check_version_with_wrong_version_raises_conflict(self, app, sample_list):
        """Test that model's check_version raises ConflictError with wrong version."""
        wrong_version = sample_list.version + 10

        with pytest.raises(ConflictError) as exc_info:
            sample_list.check_version(wrong_version)

        assert exc_info.value.status_code == 409
        assert exc_info.value.details['current_version'] == sample_list.version
        assert exc_info.value.details['expected_version'] == wrong_version

    def test_model_increment_version(self, app, sample_list):
        """Test that model's increment_version increases version by 1."""
        original_version = sample_list.version

        sample_list.increment_version()

        assert sample_list.version == original_version + 1


# ============================================================================
# Shopping List Item Version Tests
# ============================================================================

class TestItemVersionControl:
    """Test optimistic locking for shopping list items."""

    def test_update_item_without_version_succeeds(self, client, app, user_headers, sample_item):
        """Test that item updates without version field still work."""
        response = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'name': 'Updated Without Version'
        })

        assert response.status_code == 200
        data = response.get_json()

        # FIX APPLIED: API always increments version, even without version parameter
        # Version is incremented from 1 to 2 (correct behavior)
        assert data['data']['version'] == 2

    def test_update_item_with_correct_version_succeeds(self, client, app, user_headers, sample_item):
        """Test that item update with correct version succeeds."""
        current_version = sample_item.version

        response = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'name': 'Updated with Correct Version',
            'version': current_version
        })

        assert response.status_code == 200
        data = response.get_json()

        # Version should be incremented
        assert data['data']['version'] == current_version + 1

    def test_update_item_with_wrong_version_returns_409(self, client, app, user_headers, sample_item):
        """Test that item update with wrong version returns 409."""
        wrong_version = sample_item.version + 5

        response = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'name': 'Updated with Wrong Version',
            'version': wrong_version
        })

        assert response.status_code == 409
        data = response.get_json()

        assert data['success'] is False
        assert 'zwischenzeitlich geändert' in data['error']['message']

    def test_concurrent_item_updates_scenario(self, client, app, user_headers, sample_item):
        """Test concurrent item update scenario."""
        original_version = sample_item.version

        # Client 1 updates successfully
        response1 = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'name': 'Updated by Client 1',
            'version': original_version
        })

        assert response1.status_code == 200

        # Client 2 tries to update with old version (should fail)
        response2 = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'name': 'Updated by Client 2',
            'version': original_version  # Stale version
        })

        assert response2.status_code == 409

    def test_item_version_increments_on_multiple_updates(self, client, app, user_headers, sample_item):
        """Test that item version increments correctly on multiple updates."""
        versions = [sample_item.version]

        for i in range(3):
            response = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
                'name': f'Update {i + 1}',
                'version': versions[-1]
            })

            assert response.status_code == 200
            data = response.get_json()
            versions.append(data['data']['version'])

        # Verify versions increased sequentially
        assert versions == [1, 2, 3, 4]

    def test_item_model_check_version_with_correct_version(self, app, sample_item):
        """Test that item model's check_version passes with correct version."""
        current_version = sample_item.version

        # Should not raise exception
        sample_item.check_version(current_version)

    def test_item_model_check_version_with_wrong_version_raises_conflict(self, app, sample_item):
        """Test that item model's check_version raises ConflictError with wrong version."""
        wrong_version = sample_item.version + 10

        with pytest.raises(ConflictError) as exc_info:
            sample_item.check_version(wrong_version)

        assert exc_info.value.status_code == 409

    def test_item_model_increment_version(self, app, sample_item):
        """Test that item model's increment_version increases version by 1."""
        original_version = sample_item.version

        sample_item.increment_version()

        assert sample_item.version == original_version + 1


# ============================================================================
# Mixed Update Tests
# ============================================================================

class TestMixedVersionUpdates:
    """Test version control with mixed update scenarios."""

    def test_updating_list_and_items_independently(self, client, app, user_headers, sample_list, sample_item):
        """Test that list and item versions are independent."""
        list_version = sample_list.version
        item_version = sample_item.version

        # Update list
        response1 = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated List',
            'version': list_version
        })

        assert response1.status_code == 200

        # Update item - item version should still be valid
        response2 = client.put(f'/api/v1/items/{sample_item.id}', headers=user_headers, json={
            'name': 'Updated Item',
            'version': item_version
        })

        assert response2.status_code == 200

    def test_stale_version_after_other_field_update(self, client, app, user_headers, sample_list):
        """Test that version check fails after any field update."""
        original_version = sample_list.version

        # Update title
        client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'New Title',
            'version': original_version
        })

        # Try to update is_shared with old version
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'is_shared': True,
            'version': original_version  # Stale
        })

        assert response.status_code == 409

    def test_error_response_includes_both_versions(self, client, app, user_headers, sample_list):
        """Test that 409 error response includes current and expected versions."""
        # Update to increment version
        client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'First Update'
        })

        db.session.refresh(sample_list)
        current_version = sample_list.version

        # Try to update with old version
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Second Update',
            'version': 1  # Original version
        })

        assert response.status_code == 409
        data = response.get_json()

        assert data['error']['details']['current_version'] == current_version
        assert data['error']['details']['expected_version'] == 1


# ============================================================================
# Edge Cases
# ============================================================================

class TestVersionEdgeCases:
    """Test edge cases for version control."""

    def test_update_with_negative_version_returns_409(self, client, app, user_headers, sample_list):
        """Test that negative version numbers are rejected with 400 (validation error)."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated',
            'version': -1
        })

        # FIX APPLIED: Negative version is invalid input (400 Validation Error), not version conflict (409)
        # Schema validation catches this before optimistic locking check
        assert response.status_code == 400

    def test_update_with_zero_version_returns_409(self, client, app, user_headers, sample_list):
        """Test that version 0 is rejected with 400 (validation error)."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated',
            'version': 0
        })

        # FIX APPLIED: Version 0 is invalid input (400 Validation Error), not version conflict (409)
        # Versions start at 1, so 0 is caught by schema validation
        assert response.status_code == 400

    def test_update_with_very_large_version_returns_409(self, client, app, user_headers, sample_list):
        """Test that very large version numbers are rejected."""
        response = client.put(f'/api/v1/lists/{sample_list.id}', headers=user_headers, json={
            'title': 'Updated',
            'version': 999999
        })

        assert response.status_code == 409

    def test_new_list_starts_with_version_one(self, client, app, user_headers):
        """Test that newly created lists start with version 1."""
        response = client.post('/api/v1/lists', headers=user_headers, json={
            'title': 'New List'
        })

        assert response.status_code == 201
        data = response.get_json()

        assert data['data']['version'] == 1

    def test_new_item_starts_with_version_one(self, client, app, user_headers, sample_list):
        """Test that newly created items start with version 1."""
        response = client.post(f'/api/v1/lists/{sample_list.id}/items', headers=user_headers, json={
            'name': 'New Item'
        })

        assert response.status_code == 201
        data = response.get_json()

        assert data['data']['version'] == 1
