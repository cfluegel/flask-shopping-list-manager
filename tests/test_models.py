"""
Tests for Database Models.

Tests User, ShoppingList, ShoppingListItem, and RevokedToken models
including relationships, methods, and database constraints.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User, ShoppingList, ShoppingListItem, RevokedToken
from app.api.errors import ConflictError


# ============================================================================
# User Model Tests
# ============================================================================

class TestUserModel:
    """Test User model functionality."""

    def test_create_user_with_valid_data(self, app):
        """Test that a user can be created with valid data."""
        user = User(
            username='testuser',
            email='test@example.com',
            is_admin=False
        )
        user.set_password('SecurePass123')

        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_admin is False
        assert user.password_hash is not None
        assert user.password_hash != 'SecurePass123'  # Password should be hashed
        assert user.created_at is not None

    def test_password_hashing(self, app):
        """Test that passwords are properly hashed."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('MyPassword123')

        assert user.password_hash != 'MyPassword123'
        assert len(user.password_hash) > 20  # Hashed passwords are long

    def test_password_verification_success(self, app):
        """Test that correct passwords are verified successfully."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('CorrectPassword')

        assert user.check_password('CorrectPassword') is True

    def test_password_verification_failure(self, app):
        """Test that incorrect passwords fail verification."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('CorrectPassword')

        assert user.check_password('WrongPassword') is False

    def test_unique_username_constraint(self, app, regular_user):
        """Test that duplicate usernames are not allowed."""
        duplicate_user = User(
            username=regular_user.username,  # Duplicate
            email='different@example.com',
            is_admin=False
        )
        duplicate_user.set_password('Password123')

        db.session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_unique_email_constraint(self, app, regular_user):
        """Test that duplicate emails are not allowed."""
        duplicate_user = User(
            username='different_user',
            email=regular_user.email,  # Duplicate
            is_admin=False
        )
        duplicate_user.set_password('Password123')

        db.session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_user_shopping_lists_relationship(self, app, regular_user):
        """Test that user's shopping lists relationship works."""
        # Create lists for user
        list1 = ShoppingList(title='List 1', user_id=regular_user.id)
        list2 = ShoppingList(title='List 2', user_id=regular_user.id)

        db.session.add_all([list1, list2])
        db.session.commit()

        # Check relationship
        assert regular_user.shopping_lists.count() == 2
        assert list1 in regular_user.shopping_lists.all()
        assert list2 in regular_user.shopping_lists.all()

    def test_user_cascade_delete(self, app, regular_user):
        """Test that deleting a user cascades to their shopping lists."""
        # Create lists for user
        list1 = ShoppingList(title='List 1', user_id=regular_user.id)
        list2 = ShoppingList(title='List 2', user_id=regular_user.id)

        db.session.add_all([list1, list2])
        db.session.commit()

        list1_id = list1.id
        list2_id = list2.id

        # Delete user
        db.session.delete(regular_user)
        db.session.commit()

        # Lists should be deleted
        assert ShoppingList.query.get(list1_id) is None
        assert ShoppingList.query.get(list2_id) is None

    def test_user_repr(self, app, regular_user):
        """Test User __repr__ method."""
        assert repr(regular_user) == f'<User {regular_user.username}>'


# ============================================================================
# ShoppingList Model Tests
# ============================================================================

class TestShoppingListModel:
    """Test ShoppingList model functionality."""

    def test_create_list_with_valid_data(self, app, regular_user):
        """Test that a shopping list can be created with valid data."""
        shopping_list = ShoppingList(
            title='Wocheneinkauf',
            user_id=regular_user.id,
            is_shared=False
        )

        db.session.add(shopping_list)
        db.session.commit()

        assert shopping_list.id is not None
        assert shopping_list.guid is not None  # Auto-generated GUID
        assert len(shopping_list.guid) == 36  # UUID format
        assert shopping_list.title == 'Wocheneinkauf'
        assert shopping_list.user_id == regular_user.id
        assert shopping_list.is_shared is False
        assert shopping_list.version == 1
        assert shopping_list.created_at is not None
        assert shopping_list.updated_at is not None
        assert shopping_list.deleted_at is None

    def test_guid_is_unique(self, app, regular_user):
        """Test that each list gets a unique GUID."""
        list1 = ShoppingList(title='List 1', user_id=regular_user.id)
        list2 = ShoppingList(title='List 2', user_id=regular_user.id)

        db.session.add_all([list1, list2])
        db.session.commit()

        assert list1.guid != list2.guid

    def test_list_items_relationship(self, app, sample_list):
        """Test that list's items relationship works."""
        item1 = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Item 1',
            quantity='1'
        )
        item2 = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Item 2',
            quantity='2'
        )

        db.session.add_all([item1, item2])
        db.session.commit()

        assert sample_list.items.count() == 2
        assert item1 in sample_list.items.all()
        assert item2 in sample_list.items.all()

    def test_soft_delete_list(self, app, sample_list):
        """Test that soft_delete marks list as deleted."""
        assert sample_list.deleted_at is None
        assert sample_list.is_deleted is False

        sample_list.soft_delete()
        db.session.commit()

        assert sample_list.deleted_at is not None
        assert sample_list.is_deleted is True

    def test_soft_delete_cascades_to_items(self, app, sample_list, sample_item):
        """Test that soft deleting a list cascades to items."""
        assert sample_item.deleted_at is None

        sample_list.soft_delete()
        db.session.commit()

        db.session.refresh(sample_item)
        assert sample_item.deleted_at is not None

    def test_restore_list(self, app, deleted_list):
        """Test that restore removes deleted_at timestamp."""
        assert deleted_list.is_deleted is True

        deleted_list.restore()
        db.session.commit()

        assert deleted_list.deleted_at is None
        assert deleted_list.is_deleted is False

    def test_restore_cascades_to_items(self, app, deleted_list):
        """Test that restoring a list cascades to items."""
        # Add deleted item to deleted list
        item = ShoppingListItem(
            shopping_list_id=deleted_list.id,
            name='Test Item',
            quantity='1'
        )
        item.soft_delete()
        db.session.add(item)
        db.session.commit()

        assert item.is_deleted is True

        deleted_list.restore()
        db.session.commit()

        db.session.refresh(item)
        assert item.deleted_at is None

    def test_active_query_excludes_deleted(self, app, regular_user, deleted_list):
        """Test that active() query excludes soft-deleted lists."""
        # Create active list
        active_list = ShoppingList(title='Active', user_id=regular_user.id)
        db.session.add(active_list)
        db.session.commit()

        # Query active lists
        active_lists = ShoppingList.active().all()

        assert active_list in active_lists
        assert deleted_list not in active_lists

    def test_deleted_query_includes_only_deleted(self, app, regular_user, deleted_list):
        """Test that deleted() query includes only soft-deleted lists."""
        # Create active list
        active_list = ShoppingList(title='Active', user_id=regular_user.id)
        db.session.add(active_list)
        db.session.commit()

        # Query deleted lists
        deleted_lists = ShoppingList.deleted().all()

        assert deleted_list in deleted_lists
        assert active_list not in deleted_lists

    def test_check_version_with_matching_version(self, app, sample_list):
        """Test that check_version passes with correct version."""
        current_version = sample_list.version

        # Should not raise exception
        sample_list.check_version(current_version)

    def test_check_version_with_mismatched_version(self, app, sample_list):
        """Test that check_version raises ConflictError with wrong version."""
        wrong_version = sample_list.version + 1

        with pytest.raises(ConflictError) as exc_info:
            sample_list.check_version(wrong_version)

        assert exc_info.value.status_code == 409
        assert 'zwischenzeitlich geändert' in exc_info.value.message

    def test_check_version_with_none(self, app, sample_list):
        """Test that check_version allows None for backwards compatibility."""
        # Should not raise exception
        sample_list.check_version(None)

    def test_increment_version(self, app, sample_list):
        """Test that increment_version increases version by 1."""
        original_version = sample_list.version

        sample_list.increment_version()
        db.session.commit()

        assert sample_list.version == original_version + 1

    def test_list_owner_relationship(self, app, sample_list, regular_user):
        """Test that list.owner relationship works."""
        assert sample_list.owner == regular_user

    def test_list_repr(self, app, sample_list):
        """Test ShoppingList __repr__ method."""
        assert repr(sample_list) == f'<ShoppingList {sample_list.title}>'


# ============================================================================
# ShoppingListItem Model Tests
# ============================================================================

class TestShoppingListItemModel:
    """Test ShoppingListItem model functionality."""

    def test_create_item_with_valid_data(self, app, sample_list):
        """Test that an item can be created with valid data."""
        item = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Kartoffeln',
            quantity='2 kg',
            is_checked=False,
            order_index=1
        )

        db.session.add(item)
        db.session.commit()

        assert item.id is not None
        assert item.shopping_list_id == sample_list.id
        assert item.name == 'Kartoffeln'
        assert item.quantity == '2 kg'
        assert item.is_checked is False
        assert item.order_index == 1
        assert item.version == 1
        assert item.created_at is not None
        assert item.deleted_at is None

    def test_item_default_values(self, app, sample_list):
        """Test that item fields have correct default values."""
        item = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name='Test Item'
        )

        db.session.add(item)
        db.session.commit()

        assert item.quantity == '1'  # Default
        assert item.is_checked is False  # Default
        assert item.order_index == 0  # Default
        assert item.version == 1  # Default

    def test_soft_delete_item(self, app, sample_item):
        """Test that soft_delete marks item as deleted."""
        assert sample_item.deleted_at is None
        assert sample_item.is_deleted is False

        sample_item.soft_delete()
        db.session.commit()

        assert sample_item.deleted_at is not None
        assert sample_item.is_deleted is True

    def test_restore_item(self, app, deleted_item):
        """Test that restore removes deleted_at timestamp."""
        assert deleted_item.is_deleted is True

        deleted_item.restore()
        db.session.commit()

        assert deleted_item.deleted_at is None
        assert deleted_item.is_deleted is False

    def test_active_query_excludes_deleted(self, app, sample_item, deleted_item):
        """Test that active() query excludes soft-deleted items."""
        active_items = ShoppingListItem.active().all()

        assert sample_item in active_items
        assert deleted_item not in active_items

    def test_deleted_query_includes_only_deleted(self, app, sample_item, deleted_item):
        """Test that deleted() query includes only soft-deleted items."""
        deleted_items = ShoppingListItem.deleted().all()

        assert deleted_item in deleted_items
        assert sample_item not in deleted_items

    def test_check_version_with_matching_version(self, app, sample_item):
        """Test that check_version passes with correct version."""
        current_version = sample_item.version

        # Should not raise exception
        sample_item.check_version(current_version)

    def test_check_version_with_mismatched_version(self, app, sample_item):
        """Test that check_version raises ConflictError with wrong version."""
        wrong_version = sample_item.version + 1

        with pytest.raises(ConflictError) as exc_info:
            sample_item.check_version(wrong_version)

        assert exc_info.value.status_code == 409

    def test_increment_version(self, app, sample_item):
        """Test that increment_version increases version by 1."""
        original_version = sample_item.version

        sample_item.increment_version()
        db.session.commit()

        assert sample_item.version == original_version + 1

    def test_item_shopping_list_relationship(self, app, sample_item, sample_list):
        """Test that item.shopping_list relationship works."""
        assert sample_item.shopping_list == sample_list

    def test_item_repr(self, app, sample_item):
        """Test ShoppingListItem __repr__ method."""
        assert repr(sample_item) == f'<ShoppingListItem {sample_item.name}>'


# ============================================================================
# RevokedToken Model Tests
# ============================================================================

class TestRevokedTokenModel:
    """Test RevokedToken model functionality."""

    def test_create_revoked_token(self, app, regular_user):
        """Test that a revoked token can be created."""
        # FIX APPLIED: SQLite stores naive datetime, not timezone-aware
        # Create naive datetime to match SQLite behavior
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None)

        token = RevokedToken(
            jti='test-jti-12345',
            token_type='access',
            user_id=regular_user.id,
            expires_at=expires_at
        )

        db.session.add(token)
        db.session.commit()

        assert token.id is not None
        assert token.jti == 'test-jti-12345'
        assert token.token_type == 'access'
        assert token.user_id == regular_user.id
        assert token.revoked_at is not None
        assert token.expires_at == expires_at

    def test_is_jti_blacklisted_returns_true_for_revoked(self, app, regular_user):
        """Test that is_jti_blacklisted returns True for revoked tokens."""
        expires_at = datetime.now(timezone.utc)
        RevokedToken.add_to_blacklist(
            jti='revoked-jti',
            token_type='access',
            user_id=regular_user.id,
            expires_at=expires_at
        )

        assert RevokedToken.is_jti_blacklisted('revoked-jti') is True

    def test_is_jti_blacklisted_returns_false_for_valid(self, app):
        """Test that is_jti_blacklisted returns False for non-revoked tokens."""
        assert RevokedToken.is_jti_blacklisted('not-revoked-jti') is False

    def test_add_to_blacklist(self, app, regular_user):
        """Test that add_to_blacklist creates a revoked token entry."""
        expires_at = datetime.now(timezone.utc)

        RevokedToken.add_to_blacklist(
            jti='new-jti',
            token_type='refresh',
            user_id=regular_user.id,
            expires_at=expires_at
        )

        token = RevokedToken.query.filter_by(jti='new-jti').first()
        assert token is not None
        assert token.token_type == 'refresh'
        assert token.user_id == regular_user.id

    def test_cleanup_expired_tokens(self, app, regular_user):
        """Test that cleanup_expired_tokens removes expired tokens."""
        # Create expired token
        past_time = datetime.now(timezone.utc)
        expired_token = RevokedToken(
            jti='expired-jti',
            token_type='access',
            user_id=regular_user.id,
            expires_at=past_time
        )

        # Create future token
        from datetime import timedelta
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        future_token = RevokedToken(
            jti='future-jti',
            token_type='access',
            user_id=regular_user.id,
            expires_at=future_time
        )

        db.session.add_all([expired_token, future_token])
        db.session.commit()

        # Cleanup
        deleted_count = RevokedToken.cleanup_expired_tokens()

        # Expired should be deleted, future should remain
        assert deleted_count == 1
        assert RevokedToken.query.filter_by(jti='expired-jti').first() is None
        assert RevokedToken.query.filter_by(jti='future-jti').first() is not None

    def test_revoked_token_repr(self, app, regular_user):
        """Test RevokedToken __repr__ method."""
        expires_at = datetime.now(timezone.utc)
        token = RevokedToken(
            jti='test-jti',
            token_type='access',
            user_id=regular_user.id,
            expires_at=expires_at
        )

        assert repr(token) == '<RevokedToken test-jti>'
