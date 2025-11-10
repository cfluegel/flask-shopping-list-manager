"""
Admin Endpoints for API v1.

Administrative endpoints for system management and statistics.
"""

from flask import request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, desc

from . import v1_bp
from ...extensions import db
from ...models import User, ShoppingList, ShoppingListItem, RevokedToken
from ..errors import (
    success_response,
    paginated_response,
    NotFoundError
)
from ..decorators import admin_required


# ============================================================================
# Statistics
# ============================================================================

@v1_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
@admin_required()
def get_statistics():
    """
    Get system statistics (Admin only).

    Returns:
        200: System statistics
        401: Unauthorized
        403: Forbidden (not admin)
    """
    # Count totals
    total_users = User.query.count()
    total_lists = ShoppingList.query.count()
    total_items = ShoppingListItem.query.count()
    total_shared_lists = ShoppingList.query.filter_by(is_shared=True).count()
    total_admins = User.query.filter_by(is_admin=True).count()
    total_revoked_tokens = RevokedToken.query.count()

    # Get items statistics
    total_checked_items = ShoppingListItem.query.filter_by(is_checked=True).count()
    total_unchecked_items = ShoppingListItem.query.filter_by(is_checked=False).count()

    # Get most active users (users with most lists)
    top_users = db.session.query(
        User.id,
        User.username,
        func.count(ShoppingList.id).label('list_count')
    ).join(ShoppingList).group_by(User.id).order_by(desc('list_count')).limit(5).all()

    top_users_data = [
        {
            'user_id': user_id,
            'username': username,
            'list_count': list_count
        }
        for user_id, username, list_count in top_users
    ]

    # Get largest lists (lists with most items)
    largest_lists = db.session.query(
        ShoppingList.id,
        ShoppingList.title,
        ShoppingList.user_id,
        User.username,
        func.count(ShoppingListItem.id).label('item_count')
    ).join(User).outerjoin(ShoppingListItem).group_by(
        ShoppingList.id
    ).order_by(desc('item_count')).limit(5).all()

    largest_lists_data = [
        {
            'list_id': list_id,
            'title': title,
            'owner_id': user_id,
            'owner': username,
            'item_count': item_count
        }
        for list_id, title, user_id, username, item_count in largest_lists
    ]

    stats = {
        'users': {
            'total': total_users,
            'admins': total_admins,
            'regular': total_users - total_admins
        },
        'lists': {
            'total': total_lists,
            'shared': total_shared_lists,
            'private': total_lists - total_shared_lists
        },
        'items': {
            'total': total_items,
            'checked': total_checked_items,
            'unchecked': total_unchecked_items
        },
        'tokens': {
            'revoked': total_revoked_tokens
        },
        'top_users': top_users_data,
        'largest_lists': largest_lists_data
    }

    return success_response(data=stats)


# ============================================================================
# List Management
# ============================================================================

@v1_bp.route('/admin/lists', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_lists():
    """
    Get all shopping lists from all users (Admin only).

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)
        shared_only (bool): Only show shared lists (default: false)

    Returns:
        200: Paginated list of all shopping lists
        401: Unauthorized
        403: Forbidden (not admin)
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    shared_only = request.args.get('shared_only', 'false').lower() == 'true'

    query = ShoppingList.query

    if shared_only:
        query = query.filter_by(is_shared=True)

    pagination = query.order_by(desc(ShoppingList.updated_at)).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    # Serialize lists with owner and item count
    lists_data = []
    for shopping_list in pagination.items:
        list_data = {
            'id': shopping_list.id,
            'guid': shopping_list.guid,
            'title': shopping_list.title,
            'is_shared': shopping_list.is_shared,
            'owner_id': shopping_list.user_id,
            'owner_username': shopping_list.owner.username,
            'created_at': shopping_list.created_at.isoformat(),
            'updated_at': shopping_list.updated_at.isoformat(),
            'item_count': shopping_list.items.count()
        }
        lists_data.append(list_data)

    return paginated_response(lists_data, pagination)


@v1_bp.route('/admin/lists/<int:list_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def admin_delete_list(list_id: int):
    """
    Delete any shopping list (Admin only).

    This will also delete all items in the list.

    Path Parameters:
        list_id (int): Shopping list ID

    Returns:
        200: List deleted successfully
        401: Unauthorized
        403: Forbidden (not admin)
        404: List not found
    """
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    title = shopping_list.title
    owner = shopping_list.owner.username

    db.session.delete(shopping_list)
    db.session.commit()

    return success_response(
        message=f'Einkaufsliste "{title}" von Benutzer "{owner}" erfolgreich gelöscht'
    )


# ============================================================================
# Token Management
# ============================================================================

@v1_bp.route('/admin/tokens/cleanup', methods=['POST'])
@jwt_required()
@admin_required()
def cleanup_revoked_tokens():
    """
    Remove expired tokens from the blacklist (Admin only).

    This helps keep the revoked tokens table clean by removing
    tokens that have already expired naturally.

    Returns:
        200: Cleanup completed
        401: Unauthorized
        403: Forbidden (not admin)
    """
    deleted_count = RevokedToken.cleanup_expired_tokens()

    return success_response(
        data={'deleted_count': deleted_count},
        message=f'{deleted_count} abgelaufene Tokens wurden entfernt'
    )


@v1_bp.route('/admin/tokens/stats', methods=['GET'])
@jwt_required()
@admin_required()
def get_token_stats():
    """
    Get statistics about revoked tokens (Admin only).

    Returns:
        200: Token statistics
        401: Unauthorized
        403: Forbidden (not admin)
    """
    total_revoked = RevokedToken.query.count()

    # Count by type
    access_tokens = RevokedToken.query.filter_by(token_type='access').count()
    refresh_tokens = RevokedToken.query.filter_by(token_type='refresh').count()

    # Get most recent revocations
    recent_revocations = RevokedToken.query.order_by(
        desc(RevokedToken.revoked_at)
    ).limit(10).all()

    recent_data = [
        {
            'jti': token.jti,
            'type': token.token_type,
            'user_id': token.user_id,
            'revoked_at': token.revoked_at.isoformat(),
            'expires_at': token.expires_at.isoformat()
        }
        for token in recent_revocations
    ]

    stats = {
        'total_revoked': total_revoked,
        'by_type': {
            'access': access_tokens,
            'refresh': refresh_tokens
        },
        'recent_revocations': recent_data
    }

    return success_response(data=stats)


# ============================================================================
# User Activity
# ============================================================================

@v1_bp.route('/admin/users/<int:user_id>/activity', methods=['GET'])
@jwt_required()
@admin_required()
def get_user_activity(user_id: int):
    """
    Get activity statistics for a specific user (Admin only).

    Path Parameters:
        user_id (int): User ID

    Returns:
        200: User activity statistics
        401: Unauthorized
        403: Forbidden (not admin)
        404: User not found
    """
    user = User.query.get(user_id)

    if not user:
        raise NotFoundError('Benutzer nicht gefunden')

    # Count user's lists
    total_lists = user.shopping_lists.count()
    shared_lists = user.shopping_lists.filter_by(is_shared=True).count()

    # Count items across all user's lists
    total_items = db.session.query(func.count(ShoppingListItem.id)).join(
        ShoppingList
    ).filter(ShoppingList.user_id == user_id).scalar() or 0

    # Get user's most recent lists
    recent_lists = user.shopping_lists.order_by(
        desc(ShoppingList.updated_at)
    ).limit(5).all()

    recent_lists_data = [
        {
            'id': shopping_list.id,
            'title': shopping_list.title,
            'is_shared': shopping_list.is_shared,
            'updated_at': shopping_list.updated_at.isoformat(),
            'item_count': shopping_list.items.count()
        }
        for shopping_list in recent_lists
    ]

    activity = {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat()
        },
        'lists': {
            'total': total_lists,
            'shared': shared_lists,
            'private': total_lists - shared_lists
        },
        'items': {
            'total': total_items
        },
        'recent_lists': recent_lists_data
    }

    return success_response(data=activity)
