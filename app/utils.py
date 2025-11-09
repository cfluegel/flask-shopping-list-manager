"""Utility functions and decorators for the application."""

from functools import wraps
from typing import Callable

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f: Callable) -> Callable:
    """
    Decorator to require admin privileges for a route.

    Usage:
        @app.route('/admin')
        @login_required
        @admin_required
        def admin_page():
            return 'Admin page'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bitte melden Sie sich an, um diese Seite zu sehen.', 'warning')
            return redirect(url_for('main.login'))

        if not current_user.is_admin:
            flash('Sie haben keine Berechtigung, diese Seite zu sehen.', 'danger')
            abort(403)

        return f(*args, **kwargs)

    return decorated_function


def check_list_access(shopping_list, allow_shared: bool = False) -> bool:
    """
    Check if current user has access to a shopping list.

    Args:
        shopping_list: The ShoppingList object to check
        allow_shared: If True, shared lists are accessible to all

    Returns:
        bool: True if user has access, False otherwise
    """
    if not current_user.is_authenticated:
        # Non-authenticated users can only access shared lists
        return allow_shared and shopping_list.is_shared

    # Admins have access to all lists
    if current_user.is_admin:
        return True

    # Owner has access
    if shopping_list.user_id == current_user.id:
        return True

    # Shared lists are accessible to authenticated users
    if allow_shared and shopping_list.is_shared:
        return True

    return False
