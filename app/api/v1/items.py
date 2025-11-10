"""
Shopping List Items Endpoints for API v1.

Handles all operations related to shopping list items.
"""

from datetime import datetime, timezone
from flask import request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from . import v1_bp
from ...extensions import db
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
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    items = shopping_list.items.order_by(ShoppingListItem.order_index.desc()).all()

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
    shopping_list = ShoppingList.query.get(list_id)

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

    # Get the highest order_index and add 1
    max_order = db.session.query(db.func.max(ShoppingListItem.order_index)).filter_by(
        shopping_list_id=list_id
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
    item = ShoppingListItem.query.get(item_id)

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
    item = ShoppingListItem.query.get(item_id)

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
def delete_item(item_id: int):
    """
    Delete a shopping list item.

    Path Parameters:
        item_id (int): Item ID

    Returns:
        200: Item deleted successfully
        401: Unauthorized
        403: Forbidden
        404: Item not found
    """
    item = ShoppingListItem.query.get(item_id)

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
    db.session.delete(item)
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response(
        message=f'Artikel "{item_name}" erfolgreich gelöscht'
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
    item = ShoppingListItem.query.get(item_id)

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
    item = ShoppingListItem.query.get(item_id)

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
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    # Delete all checked items
    deleted_count = ShoppingListItem.query.filter_by(
        shopping_list_id=list_id,
        is_checked=True
    ).delete()

    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response(
        data={'deleted_count': deleted_count},
        message=f'{deleted_count} abgehakte Artikel wurden entfernt'
    )
