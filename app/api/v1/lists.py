"""
Shopping Lists Endpoints for API v1.

Handles all operations related to shopping lists.
"""

from datetime import datetime, timezone
from flask import request, current_app
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy import desc

from . import v1_bp
from ...extensions import db, limiter
from ...models import ShoppingList, ShoppingListItem
from ..schemas import (
    ShoppingListSchema,
    ShoppingListDetailSchema,
    ShoppingListCreateSchema,
    ShoppingListUpdateSchema,
    ShareListSchema
)
from ..errors import (
    error_response,
    success_response,
    paginated_response,
    NotFoundError,
    ForbiddenError,
    ErrorCodes
)
from ..decorators import get_current_user, list_owner_or_admin_required, list_access_required


# ============================================================================
# Shopping Lists CRUD
# ============================================================================

@v1_bp.route('/lists', methods=['GET'])
@jwt_required()
def get_lists():
    """
    Get all shopping lists for the current user.

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)

    Returns:
        200: Paginated list of shopping lists
        401: Unauthorized
    """
    user = get_current_user()

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = user.shopping_lists.order_by(desc(ShoppingList.updated_at)).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    # Serialize lists with item count
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


@v1_bp.route('/lists/<int:list_id>', methods=['GET'])
@jwt_required()
@list_access_required(allow_shared=True)
def get_list(list_id: int):
    """
    Get a specific shopping list with all items.

    Path Parameters:
        list_id (int): Shopping list ID

    Returns:
        200: Shopping list with items
        401: Unauthorized
        403: Forbidden
        404: List not found
    """
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    items = shopping_list.items.order_by(ShoppingListItem.order_index.desc()).all()

    list_data = {
        'id': shopping_list.id,
        'guid': shopping_list.guid,
        'title': shopping_list.title,
        'is_shared': shopping_list.is_shared,
        'owner_id': shopping_list.user_id,
        'owner_username': shopping_list.owner.username,
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


@v1_bp.route('/lists', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def create_list():
    """
    Create a new shopping list.

    Request Body:
        {
            "title": "string",
            "is_shared": boolean (optional, default: false)
        }

    Returns:
        201: List created successfully
        400: Validation error
        401: Unauthorized
    """
    user = get_current_user()
    data = request.get_json()

    # Validate request data
    schema = ShoppingListCreateSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return error_response(
            status_code=400,
            message='Validierungsfehler',
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=err.messages
        )

    # Create new shopping list
    shopping_list = ShoppingList(
        title=validated_data['title'],
        user_id=user.id,
        is_shared=validated_data.get('is_shared', False)
    )

    db.session.add(shopping_list)
    db.session.commit()

    current_app.logger.info(
        f'Benutzer "{user.username}" (ID: {user.id}) hat via API Liste '
        f'"{shopping_list.title}" (ID: {shopping_list.id}) erstellt'
    )

    list_data = {
        'id': shopping_list.id,
        'guid': shopping_list.guid,
        'title': shopping_list.title,
        'is_shared': shopping_list.is_shared,
        'owner_id': shopping_list.user_id,
        'owner_username': shopping_list.owner.username,
        'created_at': shopping_list.created_at.isoformat(),
        'updated_at': shopping_list.updated_at.isoformat(),
        'item_count': 0
    }

    return success_response(
        data=list_data,
        message='Einkaufsliste erfolgreich erstellt',
        status_code=201
    )


@v1_bp.route('/lists/<int:list_id>', methods=['PUT'])
@jwt_required()
@list_owner_or_admin_required()
@limiter.limit("30 per minute")
def update_list(list_id: int):
    """
    Update a shopping list.

    Path Parameters:
        list_id (int): Shopping list ID

    Request Body:
        {
            "title": "string (optional)",
            "is_shared": boolean (optional)
        }

    Returns:
        200: List updated successfully
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
    schema = ShoppingListUpdateSchema()
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
    if 'title' in validated_data:
        shopping_list.title = validated_data['title']

    if 'is_shared' in validated_data:
        # If changing from shared to private, regenerate GUID
        # This invalidates the old sharing URL
        if shopping_list.is_shared and not validated_data['is_shared']:
            import uuid
            shopping_list.guid = str(uuid.uuid4())

        shopping_list.is_shared = validated_data['is_shared']

    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    user = get_current_user()
    current_app.logger.info(
        f'Benutzer "{user.username}" (ID: {user.id}) hat via API Liste '
        f'{list_id} aktualisiert'
    )

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

    return success_response(
        data=list_data,
        message='Einkaufsliste erfolgreich aktualisiert'
    )


@v1_bp.route('/lists/<int:list_id>', methods=['DELETE'])
@jwt_required()
@list_owner_or_admin_required()
@limiter.limit("30 per minute")
def delete_list(list_id: int):
    """
    Delete a shopping list.

    This will also delete all items in the list.

    Path Parameters:
        list_id (int): Shopping list ID

    Returns:
        200: List deleted successfully
        401: Unauthorized
        403: Forbidden
        404: List not found
    """
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    title = shopping_list.title
    user = get_current_user()
    item_count = shopping_list.items.count()

    db.session.delete(shopping_list)
    db.session.commit()

    current_app.logger.info(
        f'Benutzer "{user.username}" (ID: {user.id}) hat via API Liste '
        f'"{title}" (ID: {list_id}) mit {item_count} Artikeln gelöscht'
    )

    return success_response(
        message=f'Einkaufsliste "{title}" erfolgreich gelöscht'
    )


# ============================================================================
# List Sharing
# ============================================================================

@v1_bp.route('/lists/<int:list_id>/share', methods=['POST'])
@jwt_required()
@list_owner_or_admin_required()
def toggle_share_list(list_id: int):
    """
    Toggle sharing status of a list.

    Path Parameters:
        list_id (int): Shopping list ID

    Request Body:
        {
            "is_shared": boolean
        }

    Returns:
        200: Sharing status updated
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
    schema = ShareListSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return error_response(
            status_code=400,
            message='Validierungsfehler',
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=err.messages
        )

    # If changing from shared to private, regenerate GUID
    # This invalidates the old sharing URL
    if shopping_list.is_shared and not validated_data['is_shared']:
        import uuid
        shopping_list.guid = str(uuid.uuid4())

    shopping_list.is_shared = validated_data['is_shared']
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    message = 'Liste ist jetzt geteilt' if shopping_list.is_shared else 'Liste ist jetzt privat'

    return success_response(
        data={
            'id': shopping_list.id,
            'is_shared': shopping_list.is_shared
        },
        message=message
    )


@v1_bp.route('/lists/<int:list_id>/share-url', methods=['GET'])
@jwt_required()
@list_owner_or_admin_required()
def get_share_url(list_id: int):
    """
    Get the sharing URL for a list.

    Path Parameters:
        list_id (int): Shopping list ID

    Returns:
        200: Share URL information
        401: Unauthorized
        403: Forbidden
        404: List not found
    """
    shopping_list = ShoppingList.query.get(list_id)

    if not shopping_list:
        raise NotFoundError('Einkaufsliste nicht gefunden')

    # Generate share URL
    # Note: In production, you might want to use url_for with _external=True
    # For API, we return the GUID and let the client construct the URL
    api_url = f"/api/v1/shared/{shopping_list.guid}"
    web_url = f"/shared/{shopping_list.guid}"  # For web frontend

    return success_response(
        data={
            'guid': shopping_list.guid,
            'is_shared': shopping_list.is_shared,
            'api_url': api_url,
            'web_url': web_url,
            'full_api_url': request.host_url.rstrip('/') + api_url,
            'full_web_url': request.host_url.rstrip('/') + web_url
        }
    )
