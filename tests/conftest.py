"""
Pytest fixtures for Flask Grocery Shopping List Application tests.

This module provides reusable fixtures for setting up test environments,
database state, authentication, and test data.
"""

import pytest
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token

from app import create_app
from app.extensions import db
from app.models import User, ShoppingList, ShoppingListItem, RevokedToken


# ============================================================================
# Application & Database Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def app():
    """
    Create and configure a Flask application instance for testing.

    Uses TestingConfig which provides:
    - In-memory SQLite database
    - Testing mode enabled
    - Short token expiration times
    """
    app = create_app('config.TestingConfig')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """
    Create a test client for the Flask application.

    Args:
        app: Flask application fixture

    Returns:
        FlaskClient: Test client for making requests
    """
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """
    Create a CLI test runner.

    Args:
        app: Flask application fixture

    Returns:
        FlaskCliRunner: CLI runner for testing CLI commands
    """
    return app.test_cli_runner()


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def admin_user(app):
    """
    Create an admin user for testing.

    Credentials:
        username: admin_test
        password: AdminPass123
        email: admin@test.com
        is_admin: True

    Returns:
        User: Admin user object
    """
    user = User(
        username='admin_test',
        email='admin@test.com',
        is_admin=True
    )
    user.set_password('AdminPass123')

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture(scope='function')
def regular_user(app):
    """
    Create a regular (non-admin) user for testing.

    Credentials:
        username: regular_test
        password: UserPass123
        email: user@test.com
        is_admin: False

    Returns:
        User: Regular user object
    """
    user = User(
        username='regular_test',
        email='user@test.com',
        is_admin=False
    )
    user.set_password('UserPass123')

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture(scope='function')
def another_user(app):
    """
    Create another regular user for testing multi-user scenarios.

    Credentials:
        username: another_test
        password: AnotherPass123
        email: another@test.com
        is_admin: False

    Returns:
        User: Another regular user object
    """
    user = User(
        username='another_test',
        email='another@test.com',
        is_admin=False
    )
    user.set_password('AnotherPass123')

    db.session.add(user)
    db.session.commit()

    return user


# ============================================================================
# Authentication Fixtures (JWT Headers)
# ============================================================================

@pytest.fixture(scope='function')
def admin_headers(app, admin_user):
    """
    Get JWT authorization headers for admin user.

    Args:
        app: Flask application fixture
        admin_user: Admin user fixture

    Returns:
        dict: Authorization headers with access token
    """
    access_token = create_access_token(identity=str(admin_user.id))
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture(scope='function')
def admin_refresh_token(app, admin_user):
    """
    Get JWT refresh token for admin user.

    Args:
        app: Flask application fixture
        admin_user: Admin user fixture

    Returns:
        str: Refresh token
    """
    return create_refresh_token(identity=str(admin_user.id))


@pytest.fixture(scope='function')
def user_headers(app, regular_user):
    """
    Get JWT authorization headers for regular user.

    Args:
        app: Flask application fixture
        regular_user: Regular user fixture

    Returns:
        dict: Authorization headers with access token
    """
    access_token = create_access_token(identity=str(regular_user.id))
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture(scope='function')
def user_refresh_token(app, regular_user):
    """
    Get JWT refresh token for regular user.

    Args:
        app: Flask application fixture
        regular_user: Regular user fixture

    Returns:
        str: Refresh token
    """
    return create_refresh_token(identity=str(regular_user.id))


@pytest.fixture(scope='function')
def another_user_headers(app, another_user):
    """
    Get JWT authorization headers for another user.

    Args:
        app: Flask application fixture
        another_user: Another user fixture

    Returns:
        dict: Authorization headers with access token
    """
    access_token = create_access_token(identity=str(another_user.id))
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


# ============================================================================
# Shopping List Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def sample_list(app, regular_user):
    """
    Create a sample shopping list owned by regular_user.

    Args:
        app: Flask application fixture
        regular_user: Regular user fixture

    Returns:
        ShoppingList: Sample shopping list object
    """
    shopping_list = ShoppingList(
        title='Einkaufsliste Test',
        user_id=regular_user.id,
        is_shared=False
    )

    db.session.add(shopping_list)
    db.session.commit()

    return shopping_list


@pytest.fixture(scope='function')
def shared_list(app, regular_user):
    """
    Create a shared shopping list owned by regular_user.

    Args:
        app: Flask application fixture
        regular_user: Regular user fixture

    Returns:
        ShoppingList: Shared shopping list object
    """
    shopping_list = ShoppingList(
        title='Geteilte Liste',
        user_id=regular_user.id,
        is_shared=True
    )

    db.session.add(shopping_list)
    db.session.commit()

    return shopping_list


@pytest.fixture(scope='function')
def admin_list(app, admin_user):
    """
    Create a shopping list owned by admin_user.

    Args:
        app: Flask application fixture
        admin_user: Admin user fixture

    Returns:
        ShoppingList: Admin's shopping list object
    """
    shopping_list = ShoppingList(
        title='Admin Liste',
        user_id=admin_user.id,
        is_shared=False
    )

    db.session.add(shopping_list)
    db.session.commit()

    return shopping_list


@pytest.fixture(scope='function')
def deleted_list(app, regular_user):
    """
    Create a soft-deleted shopping list.

    Args:
        app: Flask application fixture
        regular_user: Regular user fixture

    Returns:
        ShoppingList: Soft-deleted shopping list object
    """
    shopping_list = ShoppingList(
        title='Gelöschte Liste',
        user_id=regular_user.id,
        is_shared=False
    )

    db.session.add(shopping_list)
    db.session.commit()

    # Soft delete the list
    shopping_list.soft_delete()
    db.session.commit()

    return shopping_list


# ============================================================================
# Shopping List Item Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def sample_item(app, sample_list):
    """
    Create a sample shopping list item.

    Args:
        app: Flask application fixture
        sample_list: Sample list fixture

    Returns:
        ShoppingListItem: Sample item object
    """
    item = ShoppingListItem(
        shopping_list_id=sample_list.id,
        name='Milch',
        quantity='2 Liter',
        is_checked=False,
        order_index=1
    )

    db.session.add(item)
    db.session.commit()

    return item


@pytest.fixture(scope='function')
def checked_item(app, sample_list):
    """
    Create a checked shopping list item.

    Args:
        app: Flask application fixture
        sample_list: Sample list fixture

    Returns:
        ShoppingListItem: Checked item object
    """
    item = ShoppingListItem(
        shopping_list_id=sample_list.id,
        name='Brot',
        quantity='1',
        is_checked=True,
        order_index=2
    )

    db.session.add(item)
    db.session.commit()

    return item


@pytest.fixture(scope='function')
def deleted_item(app, sample_list):
    """
    Create a soft-deleted shopping list item.

    Args:
        app: Flask application fixture
        sample_list: Sample list fixture

    Returns:
        ShoppingListItem: Soft-deleted item object
    """
    item = ShoppingListItem(
        shopping_list_id=sample_list.id,
        name='Butter',
        quantity='1 Packung',
        is_checked=False,
        order_index=3
    )

    db.session.add(item)
    db.session.commit()

    # Soft delete the item
    item.soft_delete()
    db.session.commit()

    return item


@pytest.fixture(scope='function')
def multiple_items(app, sample_list):
    """
    Create multiple items in a shopping list for testing pagination/ordering.

    Args:
        app: Flask application fixture
        sample_list: Sample list fixture

    Returns:
        list: List of ShoppingListItem objects
    """
    items = []
    item_names = [
        ('Äpfel', '1 kg', False, 1),
        ('Bananen', '500g', False, 2),
        ('Tomaten', '5 Stück', True, 3),
        ('Käse', '200g', False, 4),
        ('Nudeln', '2 Packungen', True, 5)
    ]

    for name, quantity, is_checked, order_index in item_names:
        item = ShoppingListItem(
            shopping_list_id=sample_list.id,
            name=name,
            quantity=quantity,
            is_checked=is_checked,
            order_index=order_index
        )
        db.session.add(item)
        items.append(item)

    db.session.commit()

    return items


# ============================================================================
# Helper Functions
# ============================================================================

@pytest.fixture(scope='function')
def revoked_token_data(app, regular_user):
    """
    Create data for testing revoked tokens.

    Args:
        app: Flask application fixture
        regular_user: Regular user fixture

    Returns:
        dict: Token data including JTI
    """
    access_token = create_access_token(identity=str(regular_user.id))

    from flask_jwt_extended import decode_token
    decoded = decode_token(access_token)

    return {
        'token': access_token,
        'jti': decoded['jti'],
        'user_id': regular_user.id,
        'expires_at': datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
    }
