"""
User Management Endpoints for API v1.

Admin-only endpoints for managing users.
"""

from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import desc

from . import v1_bp
from ...extensions import db, limiter
from ...models import User, ShoppingList
from ..schemas import (
    UserSchema,
    UserCreateSchema,
    UserUpdateSchema,
    ShoppingListSchema
)
from ..errors import (
    error_response,
    success_response,
    paginated_response,
    NotFoundError,
    ConflictError,
    ForbiddenError,
    ErrorCodes
)
from ..decorators import admin_required, get_current_user, self_or_admin_required


# ============================================================================
# User CRUD Operations (Admin Only)
# ============================================================================

@v1_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_users():
    """
    Get all users (Admin only).

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)

    Returns:
        200: Paginated list of users
        401: Unauthorized
        403: Forbidden (not admin)
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = User.query.order_by(desc(User.created_at)).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    user_schema = UserSchema()
    users_data = user_schema.dump(pagination.items, many=True)

    return paginated_response(users_data, pagination)


@v1_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@self_or_admin_required('user_id')
def get_user(user_id: int):
    """
    Get user by ID.

    Users can only access their own information unless they are admin.

    Path Parameters:
        user_id (int): User ID

    Returns:
        200: User information
        401: Unauthorized
        403: Forbidden
        404: User not found
    """
    user = User.query.get(user_id)

    if not user:
        raise NotFoundError('Benutzer nicht gefunden')

    user_schema = UserSchema()
    user_data = user_schema.dump(user)

    return success_response(data=user_data)


@v1_bp.route('/users', methods=['POST'])
@jwt_required()
@admin_required()
@limiter.limit("20 per hour")
def create_user():
    """
    Create a new user (Admin only).

    Request Body:
        {
            "username": "string",
            "email": "string",
            "password": "string",
            "is_admin": boolean (optional, default: false)
        }

    Returns:
        201: User created successfully
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
        409: Username or email already exists
    """
    data = request.get_json()

    # Validate request data
    schema = UserCreateSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return error_response(
            status_code=400,
            message='Validierungsfehler',
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=err.messages
        )

    # Check if username or email already exists
    if User.query.filter_by(username=validated_data['username']).first():
        raise ConflictError('Benutzername bereits vergeben')

    if User.query.filter_by(email=validated_data['email']).first():
        raise ConflictError('E-Mail-Adresse bereits registriert')

    # Create new user
    user = User(
        username=validated_data['username'],
        email=validated_data['email'],
        is_admin=validated_data.get('is_admin', False)
    )
    user.set_password(validated_data['password'])

    db.session.add(user)
    db.session.commit()

    admin = get_current_user()
    current_app.logger.info(
        f'Admin "{admin.username}" (ID: {admin.id}) hat via API Benutzer '
        f'"{user.username}" (ID: {user.id}) erstellt (Admin: {user.is_admin})'
    )

    # Serialize user data
    user_schema = UserSchema()
    user_data = user_schema.dump(user)

    return success_response(
        data=user_data,
        message='Benutzer erfolgreich erstellt',
        status_code=201
    )


@v1_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@self_or_admin_required('user_id')
def update_user(user_id: int):
    """
    Update user information.

    Regular users can only update their own username and email.
    Admins can update any user's information including admin status.

    Path Parameters:
        user_id (int): User ID

    Request Body:
        {
            "username": "string (optional)",
            "email": "string (optional)",
            "is_admin": boolean (optional, admin only)
        }

    Returns:
        200: User updated successfully
        400: Validation error
        401: Unauthorized
        403: Forbidden
        404: User not found
        409: Username or email already exists
    """
    user = User.query.get(user_id)

    if not user:
        raise NotFoundError('Benutzer nicht gefunden')

    current_user = get_current_user()
    data = request.get_json()

    # Only admins can change admin status
    if 'is_admin' in data:
        if not current_user.is_admin:
            raise ForbiddenError('Nur Administratoren können den Admin-Status ändern')
        user.is_admin = data['is_admin']

    # Check for username conflict
    if 'username' in data and data['username'] != user.username:
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            raise ConflictError('Benutzername bereits vergeben')
        user.username = data['username']

    # Check for email conflict
    if 'email' in data and data['email'] != user.email:
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            raise ConflictError('E-Mail-Adresse bereits registriert')
        user.email = data['email']

    db.session.commit()

    user_schema = UserSchema()
    user_data = user_schema.dump(user)

    return success_response(
        data=user_data,
        message='Benutzer erfolgreich aktualisiert'
    )


@v1_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
@limiter.limit("20 per hour")
def delete_user(user_id: int):
    """
    Delete a user (Admin only).

    This will also delete all shopping lists owned by the user.

    Path Parameters:
        user_id (int): User ID

    Returns:
        200: User deleted successfully
        401: Unauthorized
        403: Forbidden (not admin)
        404: User not found
    """
    user = User.query.get(user_id)

    if not user:
        raise NotFoundError('Benutzer nicht gefunden')

    # Prevent deleting yourself
    current_user_id = int(get_jwt_identity())
    if user_id == current_user_id:
        return error_response(
            status_code=400,
            message='Sie können Ihren eigenen Account nicht löschen',
            error_code=ErrorCodes.INVALID_INPUT
        )

    username = user.username
    list_count = user.shopping_lists.count()
    admin = get_current_user()

    db.session.delete(user)
    db.session.commit()

    current_app.logger.info(
        f'Admin "{admin.username}" (ID: {admin.id}) hat via API Benutzer '
        f'"{username}" (ID: {user_id}) und {list_count} zugehörige Listen gelöscht'
    )

    return success_response(
        message=f'Benutzer "{username}" erfolgreich gelöscht'
    )


# ============================================================================
# User's Shopping Lists
# ============================================================================

@v1_bp.route('/users/<int:user_id>/lists', methods=['GET'])
@jwt_required()
@self_or_admin_required('user_id')
def get_user_lists(user_id: int):
    """
    Get all shopping lists for a specific user.

    Path Parameters:
        user_id (int): User ID

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)

    Returns:
        200: Paginated list of shopping lists
        401: Unauthorized
        403: Forbidden
        404: User not found
    """
    user = User.query.get(user_id)

    if not user:
        raise NotFoundError('Benutzer nicht gefunden')

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
            'created_at': shopping_list.created_at.isoformat(),
            'updated_at': shopping_list.updated_at.isoformat(),
            'item_count': shopping_list.items.count()
        }
        lists_data.append(list_data)

    return paginated_response(lists_data, pagination)
