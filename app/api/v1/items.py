"""
Shopping List Items Endpoints for API v1.

Handles all operations related to shopping list items.
"""

from datetime import datetime, timezone
from flask import request, current_app
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from . import v1_bp
from ...extensions import db, limiter
from ...models import ShoppingList, ShoppingListItem
from ..schemas import (
    ShoppingListItemSchema,
    ShoppingListItemCreateSchema,
    ShoppingListItemUpdateSchema,
    ShoppingListItemReorderSchema
)
from ..errors import (
    error_response,
    success_response,
    NotFoundError,
    ForbiddenError,
    ErrorCodes
)
from ..decorators import get_current_user, list_access_required


# ============================================================================
# Shopping List Items CRUD
# ============================================================================

@v1_bp.route('/lists/<int:list_id>/items', methods=['GET'])
@jwt_required()
@list_access_required(allow_shared=True)
def get_items(list_id: int):
    """
    Get all items for a shopping list.

    Path Parameters:
        list_id (int): Shopping list ID

    Returns:
        200: List of items
        401: Unauthorized
        403: Forbidden
        404: List not found
    """
    shopping_list = ShoppingList.active().filter_by(id=list_id).first()

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    items = ShoppingListItem.active().filter_by(shopping_list_id=list_id).order_by(ShoppingListItem.order_index.desc()).all()

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


@v1_bp.route('/lists/<int:list_id>/items', methods=['POST'])
@jwt_required()
@list_access_required(allow_shared=True)
@limiter.limit("30 per minute")
def create_item(list_id: int):
    """
    Add an item to a shopping list.

    Path Parameters:
        list_id (int): Shopping list ID

    Request Body:
        {
            "name": "string",
            "quantity": "string (optional, default: '1')"
        }

    Returns:
        201: Item created successfully
        400: Validation error
        401: Unauthorized
        403: Forbidden
        404: List not found
    """
    shopping_list = ShoppingList.active().filter_by(id=list_id).first()

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    data = request.get_json()

    # Validate request data
    schema = ShoppingListItemCreateSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return error_response(
            status_code=400,
            message='Validierungsfehler',
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=err.messages
        )

    # Get the highest order_index and add 1 (only from active items)
    max_order = db.session.query(db.func.max(ShoppingListItem.order_index)).filter(
        ShoppingListItem.shopping_list_id == list_id,
        ShoppingListItem.deleted_at.is_(None)
    ).scalar() or 0

    # Create new item
    item = ShoppingListItem(
        shopping_list_id=list_id,
        name=validated_data['name'],
        quantity=validated_data.get('quantity', '1'),
        order_index=max_order + 1
    )

    db.session.add(item)
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    user = get_current_user()
    current_app.logger.info(
        f'Benutzer "{user.username}" (ID: {user.id}) hat via API Artikel '
        f'"{item.name}" (ID: {item.id}) zu Liste {list_id} hinzugefügt'
    )

    item_data = {
        'id': item.id,
        'name': item.name,
        'quantity': item.quantity,
        'is_checked': item.is_checked,
        'order_index': item.order_index,
        'created_at': item.created_at.isoformat()
    }

    return success_response(
        data=item_data,
        message='Artikel erfolgreich hinzugefügt',
        status_code=201
    )


@v1_bp.route('/items/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id: int):
    """
    Get a specific item.

    Path Parameters:
        item_id (int): Item ID

    Returns:
        200: Item details
        401: Unauthorized
        403: Forbidden
        404: Item not found
    """
    item = ShoppingListItem.active().filter_by(id=item_id).first()

    if not item:
        raise NotFoundError('Artikel nicht gefunden')

    shopping_list = item.shopping_list
    user = get_current_user()

    # Check access permissions
    is_owner = shopping_list.user_id == user.id
    is_admin = user.is_admin
    is_shared = shopping_list.is_shared

    if not (is_owner or is_admin or is_shared):
        raise ForbiddenError('Zugriff auf diesen Artikel nicht erlaubt')

    item_data = {
        'id': item.id,
        'name': item.name,
        'quantity': item.quantity,
        'is_checked': item.is_checked,
        'order_index': item.order_index,
        'created_at': item.created_at.isoformat(),
        'list_id': shopping_list.id,
        'list_title': shopping_list.title
    }

    return success_response(data=item_data)


@v1_bp.route('/items/<int:item_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("30 per minute")
def update_item(item_id: int):
    """
    Update a shopping list item.

    Path Parameters:
        item_id (int): Item ID

    Request Body:
        {
            "name": "string (optional)",
            "quantity": "string (optional)",
            "is_checked": boolean (optional)
        }

    Returns:
        200: Item updated successfully
        400: Validation error
        401: Unauthorized
        403: Forbidden
        404: Item not found
    """
    item = ShoppingListItem.active().filter_by(id=item_id).first()

    if not item:
        raise NotFoundError('Artikel nicht gefunden')

    shopping_list = item.shopping_list
    user = get_current_user()

    # Check access permissions
    is_owner = shopping_list.user_id == user.id
    is_admin = user.is_admin
    is_shared = shopping_list.is_shared

    if not (is_owner or is_admin or is_shared):
        raise ForbiddenError('Zugriff auf diesen Artikel nicht erlaubt')

    data = request.get_json()

    # Validate request data
    schema = ShoppingListItemUpdateSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return error_response(
            status_code=400,
            message='Validierungsfehler',
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=err.messages
        )

    # Update fields
    if 'name' in validated_data:
        item.name = validated_data['name']

    if 'quantity' in validated_data:
        item.quantity = validated_data['quantity']

    if 'is_checked' in validated_data:
        item.is_checked = validated_data['is_checked']

    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    item_data = {
        'id': item.id,
        'name': item.name,
        'quantity': item.quantity,
        'is_checked': item.is_checked,
        'order_index': item.order_index,
        'created_at': item.created_at.isoformat()
    }

    return success_response(
        data=item_data,
        message='Artikel erfolgreich aktualisiert'
    )


@v1_bp.route('/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("30 per minute")
def delete_item(item_id: int):
    """
    Soft delete a shopping list item (move to trash).

    Path Parameters:
        item_id (int): Item ID

    Returns:
        200: Item moved to trash successfully
        401: Unauthorized
        403: Forbidden
        404: Item not found
    """
    item = ShoppingListItem.active().filter_by(id=item_id).first()

    if not item:
        raise NotFoundError('Artikel nicht gefunden')

    shopping_list = item.shopping_list
    user = get_current_user()

    # Check access permissions
    is_owner = shopping_list.user_id == user.id
    is_admin = user.is_admin
    is_shared = shopping_list.is_shared

    if not (is_owner or is_admin or is_shared):
        raise ForbiddenError('Zugriff auf diesen Artikel nicht erlaubt')

    item_name = item.name

    item.soft_delete()
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    current_app.logger.info(
        f'Benutzer "{user.username}" (ID: {user.id}) hat via API Artikel '
        f'"{item_name}" (ID: {item_id}) in den Papierkorb verschoben'
    )

    return success_response(
        message=f'Artikel "{item_name}" wurde in den Papierkorb verschoben'
    )


# ============================================================================
# Item Actions
# ============================================================================

@v1_bp.route('/items/<int:item_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_item(item_id: int):
    """
    Toggle the checked status of an item.

    Path Parameters:
        item_id (int): Item ID

    Returns:
        200: Item toggled successfully
        401: Unauthorized
        403: Forbidden
        404: Item not found
    """
    item = ShoppingListItem.active().filter_by(id=item_id).first()

    if not item:
        raise NotFoundError('Artikel nicht gefunden')

    shopping_list = item.shopping_list
    user = get_current_user()

    # Check access permissions
    is_owner = shopping_list.user_id == user.id
    is_admin = user.is_admin
    is_shared = shopping_list.is_shared

    if not (is_owner or is_admin or is_shared):
        raise ForbiddenError('Zugriff auf diesen Artikel nicht erlaubt')

    # Toggle checked status
    item.is_checked = not item.is_checked
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    status_text = 'abgehakt' if item.is_checked else 'nicht abgehakt'

    return success_response(
        data={
            'id': item.id,
            'is_checked': item.is_checked
        },
        message=f'Artikel "{item.name}" {status_text}'
    )


@v1_bp.route('/items/<int:item_id>/reorder', methods=['PUT'])
@jwt_required()
def reorder_item(item_id: int):
    """
    Change the order index of an item.

    This allows for custom sorting of items in the list.

    Path Parameters:
        item_id (int): Item ID

    Request Body:
        {
            "order_index": integer
        }

    Returns:
        200: Item reordered successfully
        400: Validation error
        401: Unauthorized
        403: Forbidden
        404: Item not found
    """
    item = ShoppingListItem.active().filter_by(id=item_id).first()

    if not item:
        raise NotFoundError('Artikel nicht gefunden')

    shopping_list = item.shopping_list
    user = get_current_user()

    # Check access permissions (only owner or admin can reorder)
    is_owner = shopping_list.user_id == user.id
    is_admin = user.is_admin

    if not (is_owner or is_admin):
        raise ForbiddenError('Nur der Besitzer kann die Reihenfolge ändern')

    data = request.get_json()

    # Validate request data
    schema = ShoppingListItemReorderSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return error_response(
            status_code=400,
            message='Validierungsfehler',
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=err.messages
        )

    # Update order index
    item.order_index = validated_data['order_index']
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response(
        data={
            'id': item.id,
            'order_index': item.order_index
        },
        message='Reihenfolge erfolgreich geändert'
    )


# ============================================================================
# Bulk Operations
# ============================================================================

@v1_bp.route('/lists/<int:list_id>/items/clear-checked', methods=['POST'])
@jwt_required()
@list_access_required(allow_shared=False)
def clear_checked_items(list_id: int):
    """
    Remove all checked items from a list.

    Useful for clearing completed items after shopping.

    Path Parameters:
        list_id (int): Shopping list ID

    Returns:
        200: Checked items removed
        401: Unauthorized
        403: Forbidden
        404: List not found
    """
    shopping_list = ShoppingList.active().filter_by(id=list_id).first()

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    # Soft delete all checked items
    checked_items = ShoppingListItem.active().filter_by(
        shopping_list_id=list_id,
        is_checked=True
    ).all()

    for item in checked_items:
        item.soft_delete()

    deleted_count = len(checked_items)
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response(
        data={'deleted_count': deleted_count},
        message=f'{deleted_count} abgehakte Artikel wurden in den Papierkorb verschoben'
    )


# ============================================================================
# Trash Management (Papierkorb)
# ============================================================================

@v1_bp.route('/trash/items', methods=['GET'])
@jwt_required()
def get_trash_items():
    """
    Get all deleted items for the current user (trash).

    Returns:
        200: List of deleted items
        401: Unauthorized
    """
    user = get_current_user()

    # Get all deleted items from user's lists
    deleted_items = ShoppingListItem.deleted().join(ShoppingList).filter(
        ShoppingList.user_id == user.id
    ).order_by(ShoppingListItem.deleted_at.desc()).all()

    items_data = [
        {
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'is_checked': item.is_checked,
            'order_index': item.order_index,
            'created_at': item.created_at.isoformat(),
            'deleted_at': item.deleted_at.isoformat(),
            'list_id': item.shopping_list.id,
            'list_title': item.shopping_list.title
        }
        for item in deleted_items
    ]

    return success_response(data=items_data)


@v1_bp.route('/items/<int:item_id>/restore', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def restore_item(item_id: int):
    """
    Restore an item from trash.

    Path Parameters:
        item_id (int): Item ID

    Returns:
        200: Item restored successfully
        401: Unauthorized
        403: Forbidden
        404: Item not found
    """
    item = ShoppingListItem.deleted().filter_by(id=item_id).first()

    if not item:
        raise NotFoundError('Artikel nicht im Papierkorb gefunden')

    shopping_list = item.shopping_list
    user = get_current_user()

    # Check access permissions
    is_owner = shopping_list.user_id == user.id
    is_admin = user.is_admin

    if not (is_owner or is_admin):
        raise ForbiddenError('Keine Berechtigung, diesen Artikel wiederherzustellen')

    item_name = item.name
    item.restore()
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    current_app.logger.info(
        f'Benutzer "{user.username}" (ID: {user.id}) hat via API Artikel '
        f'"{item_name}" (ID: {item_id}) aus dem Papierkorb wiederhergestellt'
    )

    return success_response(
        message=f'Artikel "{item_name}" wurde wiederhergestellt'
    )
