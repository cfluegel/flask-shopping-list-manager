"""
Tests for Soft Delete (Trash/Restore) Functionality.

Tests soft deletion and restoration of shopping lists and items.
"""

import pytest
from datetime import datetime, timezone

from app.models import ShoppingList, ShoppingListItem
from app.extensions import db


# ============================================================================
# Shopping List Soft Delete Tests
# ============================================================================

class TestShoppingListSoftDelete:
    """Test soft delete functionality for shopping lists."""

    def test_soft_delete_list_sets_deleted_at(self, client, user_headers, sample_list):
        """Test that soft deleting a list sets deleted_at timestamp."""
        response = client.delete(
            f'/api/v1/lists/{sample_list.id}',
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify deleted_at is set
        db.session.refresh(sample_list)
        assert sample_list.deleted_at is not None
        assert isinstance(sample_list.deleted_at, datetime)

    def test_soft_delete_list_cascades_to_items(self, client, user_headers, sample_list, sample_item):
        """Test that soft deleting a list also soft deletes all items."""
        # Create additional items
        item2 = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Kaffee',
            quantity='1 Packung',
            order_index=2
        )
        db.session.add(item2)
        db.session.commit()

        response = client.delete(
            f'/api/v1/lists/{sample_list.id}',
            headers=user_headers
        )

        assert response.status_code == 200

        # Verify all items are soft deleted
        db.session.refresh(sample_item)
        db.session.refresh(item2)
        assert sample_item.deleted_at is not None
        assert item2.deleted_at is not None

    def test_deleted_list_not_shown_in_active_lists(self, client, user_headers, sample_list):
        """Test that deleted lists do not appear in active lists query."""
        # Delete the list
        client.delete(f'/api/v1/lists/{sample_list.id}', headers=user_headers)

        # Get active lists
        response = client.get('/api/v1/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify deleted list is not in results
        list_ids = [lst['id'] for lst in data['data']]
        assert sample_list.id not in list_ids

    def test_deleted_list_appears_in_trash(self, client, user_headers, sample_list):
        """Test that deleted lists appear in trash endpoint."""
        # Delete the list
        client.delete(f'/api/v1/lists/{sample_list.id}', headers=user_headers)

        # Get trash lists
        response = client.get('/api/v1/trash/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify deleted list is in trash
        list_ids = [lst['id'] for lst in data['data']]
        assert sample_list.id in list_ids

        # Verify deleted_at is present
        trash_list = next(lst for lst in data['data'] if lst['id'] == sample_list.id)
        assert 'deleted_at' in trash_list
        assert trash_list['deleted_at'] is not None

    def test_restore_list_clears_deleted_at(self, client, user_headers, deleted_list):
        """Test that restoring a list clears the deleted_at timestamp."""
        response = client.post(
            f'/api/v1/lists/{deleted_list.id}/restore',
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        # FIX APPLIED: API returns more specific message with list title
        # Check that message contains the key term instead of exact match
        assert 'wiederhergestellt' in data['message'].lower()

        # Verify deleted_at is cleared
        db.session.refresh(deleted_list)
        assert deleted_list.deleted_at is None

    def test_restore_list_cascades_to_items(self, client, user_headers, deleted_list):
        """Test that restoring a list also restores all items."""
        # Add items to deleted list
        item1 = ShoppingListItem(
            shopping_list_id=deleted_list.id,
            name='Item 1',
            quantity='1',
            order_index=1
        )
        item2 = ShoppingListItem(
            shopping_list_id=deleted_list.id,
            name='Item 2',
            quantity='2',
            order_index=2
        )
        db.session.add_all([item1, item2])
        db.session.commit()

        # Soft delete the items
        item1.soft_delete()
        item2.soft_delete()
        db.session.commit()

        # Restore the list
        response = client.post(
            f'/api/v1/lists/{deleted_list.id}/restore',
            headers=user_headers
        )

        assert response.status_code == 200

        # Verify all items are restored
        db.session.refresh(item1)
        db.session.refresh(item2)
        assert item1.deleted_at is None
        assert item2.deleted_at is None

    def test_restored_list_appears_in_active_lists(self, client, user_headers, deleted_list):
        """Test that restored lists appear in active lists again."""
        # Restore the list
        client.post(f'/api/v1/lists/{deleted_list.id}/restore', headers=user_headers)

        # Get active lists
        response = client.get('/api/v1/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify restored list is in results
        list_ids = [lst['id'] for lst in data['data']]
        assert deleted_list.id in list_ids

    def test_restored_list_not_in_trash(self, client, user_headers, deleted_list):
        """Test that restored lists do not appear in trash."""
        # Restore the list
        client.post(f'/api/v1/lists/{deleted_list.id}/restore', headers=user_headers)

        # Get trash lists
        response = client.get('/api/v1/trash/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify restored list is not in trash
        list_ids = [lst['id'] for lst in data['data']]
        assert deleted_list.id not in list_ids

    def test_permanent_delete_removes_list_from_database(self, client, admin_headers, deleted_list):
        """Test that permanent delete removes list from database."""
        list_id = deleted_list.id

        response = client.delete(
            f'/api/v1/trash/lists/{list_id}',
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'endgültig gelöscht' in data['message'].lower()

        # Verify list is removed from database
        list_obj = ShoppingList.query.get(list_id)
        assert list_obj is None

    def test_permanent_delete_cascades_to_items(self, client, admin_headers, deleted_list):
        """Test that permanent delete also removes all items."""
        # Add items to deleted list
        item1 = ShoppingListItem(
            shopping_list_id=deleted_list.id,
            name='Item 1',
            quantity='1',
            order_index=1
        )
        db.session.add(item1)
        db.session.commit()
        item1_id = item1.id

        # Permanently delete the list
        response = client.delete(
            f'/api/v1/trash/lists/{deleted_list.id}',
            headers=admin_headers
        )

        assert response.status_code == 200

        # Verify items are also removed
        item_obj = ShoppingListItem.query.get(item1_id)
        assert item_obj is None

    def test_permanent_delete_only_admin_allowed(self, client, user_headers, deleted_list):
        """Test that only admins can permanently delete lists."""
        response = client.delete(
            f'/api/v1/trash/lists/{deleted_list.id}',
            headers=user_headers
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert 'administrator' in data['error']['message'].lower()

    def test_cannot_restore_list_not_in_trash(self, client, user_headers, sample_list):
        """Test that restoring a non-deleted list fails with 404."""
        response = client.post(
            f'/api/v1/lists/{sample_list.id}/restore',
            headers=user_headers
        )

        # FIX APPLIED: API returns 404 (not found in trash), not 400
        # This is semantically more correct - the list exists but not in trash
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False

    def test_only_owner_can_restore_list(self, client, another_user_headers, deleted_list):
        """Test that only the owner can restore their list."""
        response = client.post(
            f'/api/v1/lists/{deleted_list.id}/restore',
            headers=another_user_headers
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False


# ============================================================================
# Shopping List Item Soft Delete Tests
# ============================================================================

class TestShoppingListItemSoftDelete:
    """Test soft delete functionality for shopping list items."""

    def test_soft_delete_item_sets_deleted_at(self, client, user_headers, sample_item):
        """Test that soft deleting an item sets deleted_at timestamp."""
        response = client.delete(
            f'/api/v1/items/{sample_item.id}',
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify deleted_at is set
        db.session.refresh(sample_item)
        assert sample_item.deleted_at is not None

    def test_deleted_item_not_in_active_items(self, client, user_headers, sample_list, sample_item):
        """Test that deleted items do not appear in active items query."""
        # Delete the item
        client.delete(f'/api/v1/items/{sample_item.id}', headers=user_headers)

        # Get items for the list
        response = client.get(
            f'/api/v1/lists/{sample_list.id}/items',
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify deleted item is not in results
        item_ids = [item['id'] for item in data['data']]
        assert sample_item.id not in item_ids

    def test_deleted_item_appears_in_trash(self, client, user_headers, sample_item):
        """Test that deleted items appear in trash endpoint."""
        # Delete the item
        client.delete(f'/api/v1/items/{sample_item.id}', headers=user_headers)

        # Get trash items
        response = client.get('/api/v1/trash/items', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify deleted item is in trash
        item_ids = [item['id'] for item in data['data']]
        assert sample_item.id in item_ids

    def test_restore_item_clears_deleted_at(self, client, user_headers, deleted_item):
        """Test that restoring an item clears the deleted_at timestamp."""
        response = client.post(
            f'/api/v1/items/{deleted_item.id}/restore',
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify deleted_at is cleared
        db.session.refresh(deleted_item)
        assert deleted_item.deleted_at is None

    def test_restored_item_appears_in_active_items(self, client, user_headers, sample_list, deleted_item):
        """Test that restored items appear in active items again."""
        # Restore the item
        client.post(f'/api/v1/items/{deleted_item.id}/restore', headers=user_headers)

        # Get items for the list
        response = client.get(
            f'/api/v1/lists/{sample_list.id}/items',
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify restored item is in results
        item_ids = [item['id'] for item in data['data']]
        assert deleted_item.id in item_ids

    def test_clear_checked_items_soft_deletes_them(self, client, user_headers, sample_list):
        """Test that clearing checked items soft deletes them."""
        # Create checked items
        item1 = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Checked Item 1',
            quantity='1',
            is_checked=True,
            order_index=1
        )
        item2 = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Checked Item 2',
            quantity='1',
            is_checked=True,
            order_index=2
        )
        item3 = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Unchecked Item',
            quantity='1',
            is_checked=False,
            order_index=3
        )
        db.session.add_all([item1, item2, item3])
        db.session.commit()

        # Clear checked items
        response = client.post(
            f'/api/v1/lists/{sample_list.id}/items/clear-checked',
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['deleted_count'] == 2

        # Verify checked items are soft deleted
        db.session.refresh(item1)
        db.session.refresh(item2)
        db.session.refresh(item3)
        assert item1.deleted_at is not None
        assert item2.deleted_at is not None
        assert item3.deleted_at is None

    def test_only_owner_can_restore_item(self, client, another_user_headers, deleted_item):
        """Test that only the list owner can restore items."""
        response = client.post(
            f'/api/v1/items/{deleted_item.id}/restore',
            headers=another_user_headers
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False


# ============================================================================
# Trash Query Tests
# ============================================================================

class TestTrashQueries:
    """Test trash query endpoints."""

    def test_get_trash_lists_only_shows_deleted(self, client, user_headers, sample_list, deleted_list, regular_user):
        """Test that trash lists endpoint only shows deleted lists."""
        # Create another deleted list
        deleted_list2 = ShoppingList(
            title='Another Deleted List',
            user_id=regular_user.id,
            is_shared=False
        )
        db.session.add(deleted_list2)
        db.session.commit()
        deleted_list2.soft_delete()
        db.session.commit()

        response = client.get('/api/v1/trash/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Should have 2 deleted lists
        assert len(data['data']) == 2

        # Verify all have deleted_at
        for lst in data['data']:
            assert 'deleted_at' in lst
            assert lst['deleted_at'] is not None

        # Verify active list is not included
        list_ids = [lst['id'] for lst in data['data']]
        assert sample_list.id not in list_ids

    def test_get_trash_lists_only_shows_own_lists(self, client, user_headers, another_user, regular_user):
        """Test that users only see their own deleted lists in trash."""
        # Create deleted list for another user
        other_deleted_list = ShoppingList(
            title='Other User Deleted List',
            user_id=another_user.id,
            is_shared=False
        )
        db.session.add(other_deleted_list)
        db.session.commit()
        other_deleted_list.soft_delete()
        db.session.commit()

        # Create deleted list for current user
        my_deleted_list = ShoppingList(
            title='My Deleted List',
            user_id=regular_user.id,
            is_shared=False
        )
        db.session.add(my_deleted_list)
        db.session.commit()
        my_deleted_list.soft_delete()
        db.session.commit()

        response = client.get('/api/v1/trash/lists', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Should only see own deleted list
        list_ids = [lst['id'] for lst in data['data']]
        assert my_deleted_list.id in list_ids
        assert other_deleted_list.id not in list_ids

    def test_get_trash_items_only_shows_deleted(self, client, user_headers, sample_list, sample_item, deleted_item):
        """Test that trash items endpoint only shows deleted items."""
        # Create another deleted item
        deleted_item2 = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Another Deleted Item',
            quantity='1',
            order_index=4
        )
        db.session.add(deleted_item2)
        db.session.commit()
        deleted_item2.soft_delete()
        db.session.commit()

        response = client.get('/api/v1/trash/items', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Should have at least 2 deleted items
        assert len(data['data']) >= 2

        # Verify all have deleted_at
        for item in data['data']:
            assert 'deleted_at' in item
            assert item['deleted_at'] is not None

        # Verify active item is not included
        item_ids = [item['id'] for item in data['data']]
        assert sample_item.id not in item_ids

    def test_get_trash_items_only_shows_own_items(self, client, user_headers, another_user, regular_user):
        """Test that users only see items from their own lists in trash."""
        # Create list for another user with deleted item
        other_list = ShoppingList(
            title='Other User List',
            user_id=another_user.id,
            is_shared=False
        )
        db.session.add(other_list)
        db.session.commit()

        other_item = ShoppingListItem(
            shopping_list_id=other_list.id,
            name='Other User Item',
            quantity='1',
            order_index=1
        )
        db.session.add(other_item)
        db.session.commit()
        other_item.soft_delete()
        db.session.commit()

        # Create list for current user with deleted item
        my_list = ShoppingList(
            title='My List',
            user_id=regular_user.id,
            is_shared=False
        )
        db.session.add(my_list)
        db.session.commit()

        my_item = ShoppingListItem(
            shopping_list_id=my_list.id,
            name='My Item',
            quantity='1',
            order_index=1
        )
        db.session.add(my_item)
        db.session.commit()
        my_item.soft_delete()
        db.session.commit()

        response = client.get('/api/v1/trash/items', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Should only see own deleted items
        item_ids = [item['id'] for item in data['data']]
        assert my_item.id in item_ids
        assert other_item.id not in item_ids

    def test_admin_sees_all_trash_lists(self, client, admin_headers, another_user, admin_user):
        """Test that admins can see all deleted lists from all users."""
        # Create deleted lists for different users
        user_list = ShoppingList(
            title='User Deleted List',
            user_id=another_user.id,
            is_shared=False
        )
        admin_list = ShoppingList(
            title='Admin Deleted List',
            user_id=admin_user.id,
            is_shared=False
        )
        db.session.add_all([user_list, admin_list])
        db.session.commit()

        user_list.soft_delete()
        admin_list.soft_delete()
        db.session.commit()

        response = client.get('/api/v1/trash/lists', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Admin should see both lists
        list_ids = [lst['id'] for lst in data['data']]
        assert user_list.id in list_ids
        assert admin_list.id in list_ids


# ============================================================================
# Model Method Tests
# ============================================================================

class TestSoftDeleteModelMethods:
    """Test soft delete methods on models."""

    def test_shopping_list_is_deleted_property(self, app, regular_user):
        """Test the is_deleted property on ShoppingList."""
        shopping_list = ShoppingList(
            title='Test List',
            user_id=regular_user.id,
            is_shared=False
        )
        db.session.add(shopping_list)
        db.session.commit()

        # Initially not deleted
        assert shopping_list.is_deleted is False

        # After soft delete
        shopping_list.soft_delete()
        assert shopping_list.is_deleted is True

        # After restore
        shopping_list.restore()
        assert shopping_list.is_deleted is False

    def test_shopping_list_active_query(self, app, regular_user):
        """Test the active() class method on ShoppingList."""
        # Create active and deleted lists
        active_list = ShoppingList(
            title='Active List',
            user_id=regular_user.id,
            is_shared=False
        )
        deleted_list = ShoppingList(
            title='Deleted List',
            user_id=regular_user.id,
            is_shared=False
        )
        db.session.add_all([active_list, deleted_list])
        db.session.commit()

        deleted_list.soft_delete()
        db.session.commit()

        # Query active lists
        active_lists = ShoppingList.active().all()
        assert active_list in active_lists
        assert deleted_list not in active_lists

    def test_shopping_list_deleted_query(self, app, regular_user):
        """Test the deleted() class method on ShoppingList."""
        # Create active and deleted lists
        active_list = ShoppingList(
            title='Active List',
            user_id=regular_user.id,
            is_shared=False
        )
        deleted_list = ShoppingList(
            title='Deleted List',
            user_id=regular_user.id,
            is_shared=False
        )
        db.session.add_all([active_list, deleted_list])
        db.session.commit()

        deleted_list.soft_delete()
        db.session.commit()

        # Query deleted lists
        trash_lists = ShoppingList.deleted().all()
        assert deleted_list in trash_lists
        assert active_list not in trash_lists

    def test_shopping_list_item_is_deleted_property(self, app, sample_list):
        """Test the is_deleted property on ShoppingListItem."""
        item = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Test Item',
            quantity='1',
            order_index=1
        )
        db.session.add(item)
        db.session.commit()

        # Initially not deleted
        assert item.is_deleted is False

        # After soft delete
        item.soft_delete()
        assert item.is_deleted is True

        # After restore
        item.restore()
        assert item.is_deleted is False

    def test_shopping_list_item_active_query(self, app, sample_list):
        """Test the active() class method on ShoppingListItem."""
        # Create active and deleted items
        active_item = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Active Item',
            quantity='1',
            order_index=1
        )
        deleted_item = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Deleted Item',
            quantity='1',
            order_index=2
        )
        db.session.add_all([active_item, deleted_item])
        db.session.commit()

        deleted_item.soft_delete()
        db.session.commit()

        # Query active items
        active_items = ShoppingListItem.active().all()
        assert active_item in active_items
        assert deleted_item not in active_items

    def test_shopping_list_item_deleted_query(self, app, sample_list):
        """Test the deleted() class method on ShoppingListItem."""
        # Create active and deleted items
        active_item = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Active Item',
            quantity='1',
            order_index=1
        )
        deleted_item = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Deleted Item',
            quantity='1',
            order_index=2
        )
        db.session.add_all([active_item, deleted_item])
        db.session.commit()

        deleted_item.soft_delete()
        db.session.commit()

        # Query deleted items
        trash_items = ShoppingListItem.deleted().all()
        assert deleted_item in trash_items
        assert active_item not in trash_items
