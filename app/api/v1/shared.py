"""
Shared Lists Endpoints for API v1.

Public endpoints for accessing shared shopping lists without authentication.
"""

from flask import request

from . import v1_bp
from ...models import ShoppingList, ShoppingListItem
from ..errors import (
    success_response,
    NotFoundError,
    ErrorCodes,
    error_response
)


# ============================================================================
# Public Shared List Access
# ============================================================================

@v1_bp.route('/shared/<string:guid>', methods=['GET'])
def get_shared_list(guid: str):
    """
    Get a shared shopping list (no authentication required).

    This endpoint is public and allows anyone with the GUID to view the list.

    Path Parameters:
        guid (string): Shopping list GUID

    Returns:
        200: Shopping list with items
        404: List not found or not shared
    """
    # Bug Fix #2: Filter out soft-deleted lists using active() query
    shopping_list = ShoppingList.active().filter_by(guid=guid).first()

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    # Check if list is actually shared
    if not shopping_list.is_shared:
        return error_response(
            status_code=404,
            message='Diese Liste ist nicht geteilt',
            error_code=ErrorCodes.LIST_NOT_SHARED
        )

    # Bug Fix #1: Filter out soft-deleted items using active() query
    items = ShoppingListItem.active().filter_by(
        shopping_list_id=shopping_list.id
    ).order_by(ShoppingListItem.order_index.desc()).all()

    list_data = {
        'id': shopping_list.id,
        'guid': shopping_list.guid,
        'title': shopping_list.title,
        'owner': shopping_list.owner.username,
        'created_at': shopping_list.created_at.isoformat(),
        'updated_at': shopping_list.updated_at.isoformat(),
        'items': [
            {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity,
                'is_checked': item.is_checked,
                'order_index': item.order_index,
                'created_at': item.created_at.isoformat()
            }
            for item in items
        ]
    }

    return success_response(data=list_data)


@v1_bp.route('/shared/<string:guid>/items', methods=['GET'])
def get_shared_list_items(guid: str):
    """
    Get only the items of a shared shopping list (no authentication required).

    Path Parameters:
        guid (string): Shopping list GUID

    Returns:
        200: List of items
        404: List not found or not shared
    """
    # Filter out soft-deleted lists using active() query
    shopping_list = ShoppingList.active().filter_by(guid=guid).first()

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    # Check if list is actually shared
    if not shopping_list.is_shared:
        return error_response(
            status_code=404,
            message='Diese Liste ist nicht geteilt',
            error_code=ErrorCodes.LIST_NOT_SHARED
        )

    # Filter out soft-deleted items using active() query
    items = ShoppingListItem.active().filter_by(
        shopping_list_id=shopping_list.id
    ).order_by(ShoppingListItem.order_index.desc()).all()

    items_data = [
        {
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'is_checked': item.is_checked,
            'order_index': item.order_index,
            'created_at': item.created_at.isoformat()
        }
        for item in items
    ]

    return success_response(data=items_data)


@v1_bp.route('/shared/<string:guid>/info', methods=['GET'])
def get_shared_list_info(guid: str):
    """
    Get basic information about a shared list without items.

    Useful for checking if a list exists and is shared before fetching all items.

    Path Parameters:
        guid (string): Shopping list GUID

    Returns:
        200: List information
        404: List not found or not shared
    """
    # Filter out soft-deleted lists using active() query
    shopping_list = ShoppingList.active().filter_by(guid=guid).first()

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    # Check if list is actually shared
    if not shopping_list.is_shared:
        return error_response(
            status_code=404,
            message='Diese Liste ist nicht geteilt',
            error_code=ErrorCodes.LIST_NOT_SHARED
        )

    # Count only active items (not soft-deleted)
    active_items = ShoppingListItem.active().filter_by(shopping_list_id=shopping_list.id)

    list_data = {
        'id': shopping_list.id,
        'guid': shopping_list.guid,
        'title': shopping_list.title,
        'owner': shopping_list.owner.username,
        'is_shared': shopping_list.is_shared,
        'created_at': shopping_list.created_at.isoformat(),
        'updated_at': shopping_list.updated_at.isoformat(),
        'item_count': active_items.count(),
        'checked_count': active_items.filter_by(is_checked=True).count()
    }

    return success_response(data=list_data)
