"""
Custom Decorators for API Authorization and Access Control.

Provides decorators for JWT-based authentication and role-based access control.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from .errors import ForbiddenError, UnauthorizedError
from ..models import User


def admin_required():
    """
    Decorator that requires the user to be an admin.

    Must be used after @jwt_required() decorator.

    Usage:
        @app.route('/admin/endpoint')
        @jwt_required()
        @admin_required()
        def admin_endpoint():
            ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)

            if not user:
                raise UnauthorizedError('Benutzer nicht gefunden')

            if not user.is_admin:
                raise ForbiddenError('Administrator-Rechte erforderlich')

            return fn(*args, **kwargs)
        return decorator
    return wrapper


def get_current_user() -> User:
    """
    Get the current authenticated user from JWT token.

    Returns:
        User: The current user object

    Raises:
        UnauthorizedError: If user is not found
    """
    verify_jwt_in_request()
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        raise UnauthorizedError('Benutzer nicht gefunden')

    return user


def self_or_admin_required(user_id_param: str = 'user_id'):
    """
    Decorator that requires the user to be either the resource owner or an admin.

    Args:
        user_id_param: Name of the parameter containing the user ID to check

    Usage:
        @app.route('/users/<int:user_id>')
        @jwt_required()
        @self_or_admin_required('user_id')
        def get_user(user_id):
            ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = int(get_jwt_identity())
            current_user = User.query.get(current_user_id)

            if not current_user:
                raise UnauthorizedError('Benutzer nicht gefunden')

            # Get the user_id from the route parameters
            target_user_id = kwargs.get(user_id_param)

            # Allow if user is admin or accessing their own resource
            if not (current_user.is_admin or current_user_id == target_user_id):
                raise ForbiddenError('Zugriff nur auf eigene Ressourcen erlaubt')

            return fn(*args, **kwargs)
        return decorator
    return wrapper


def list_owner_or_admin_required():
    """
    Decorator that requires the user to be the list owner or an admin.

    Expects 'list_id' in the route parameters.

    Usage:
        @app.route('/lists/<int:list_id>')
        @jwt_required()
        @list_owner_or_admin_required()
        def delete_list(list_id):
            ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            from ..models import ShoppingList

            verify_jwt_in_request()
            current_user_id = int(get_jwt_identity())
            current_user = User.query.get(current_user_id)

            if not current_user:
                raise UnauthorizedError('Benutzer nicht gefunden')

            list_id = kwargs.get('list_id')
            shopping_list = ShoppingList.query.get(list_id)

            if not shopping_list:
                from .errors import NotFoundError
                raise NotFoundError('Einkaufsliste nicht gefunden')

            # Allow if user is admin or list owner
            if not (current_user.is_admin or shopping_list.user_id == current_user_id):
                raise ForbiddenError('Zugriff nur auf eigene Listen erlaubt')

            return fn(*args, **kwargs)
        return decorator
    return wrapper


def list_access_required(allow_shared: bool = True):
    """
    Decorator that checks if user has access to a list (owner, admin, or shared).

    Args:
        allow_shared: If True, allows access to shared lists

    Usage:
        @app.route('/lists/<int:list_id>')
        @jwt_required()
        @list_access_required(allow_shared=True)
        def view_list(list_id):
            ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            from ..models import ShoppingList

            verify_jwt_in_request()
            current_user_id = int(get_jwt_identity())
            current_user = User.query.get(current_user_id)

            if not current_user:
                raise UnauthorizedError('Benutzer nicht gefunden')

            list_id = kwargs.get('list_id')
            shopping_list = ShoppingList.query.get(list_id)

            if not shopping_list:
                from .errors import NotFoundError
                raise NotFoundError('Einkaufsliste nicht gefunden')

            # Check access permissions
            is_owner = shopping_list.user_id == current_user_id
            is_admin = current_user.is_admin
            is_shared_access = allow_shared and shopping_list.is_shared

            if not (is_owner or is_admin or is_shared_access):
                raise ForbiddenError('Zugriff auf diese Liste nicht erlaubt')

            return fn(*args, **kwargs)
        return decorator
    return wrapper


def optional_jwt():
    """
    Decorator that allows optional JWT authentication.

    If a valid JWT is provided, the user will be authenticated.
    If no JWT is provided or it's invalid, the request continues without authentication.

    Useful for endpoints that have different behavior for authenticated vs. anonymous users.

    Usage:
        @app.route('/public-or-private')
        @optional_jwt()
        def mixed_endpoint():
            try:
                user = get_current_user()
                # User is authenticated
            except:
                # User is not authenticated
                user = None
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request(optional=True)
            except Exception:
                # JWT verification failed, continue without auth
                pass
            return fn(*args, **kwargs)
        return decorator
    return wrapper
