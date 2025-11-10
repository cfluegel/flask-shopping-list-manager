"""
Authentication Endpoints for API v1.

Handles user registration, login, token refresh, logout, and password management.
"""

from datetime import datetime, timezone
from flask import request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from marshmallow import ValidationError

from . import v1_bp
from ...extensions import db, limiter
from ...models import User, RevokedToken
from ..schemas import (
    LoginSchema,
    RegisterSchema,
    ChangePasswordSchema,
    UserSchema
)
from ..errors import (
    error_response,
    success_response,
    UnauthorizedError,
    ConflictError,
    ErrorCodes
)
from ..decorators import get_current_user


# ============================================================================
# Registration
# ============================================================================

@v1_bp.route('/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """
    Register a new user account.

    Request Body:
        {
            "username": "string",
            "email": "string",
            "password": "string",
            "password_confirm": "string"
        }

    Returns:
        201: User successfully created with tokens
        400: Validation error
        409: Username or email already exists
    """
    data = request.get_json()

    # Validate request data
    schema = RegisterSchema()
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
        current_app.logger.warning(
            f'Registrierungsversuch mit bereits vergebenem Benutzernamen: '
            f'"{validated_data["username"]}" von IP: {request.remote_addr}'
        )
        raise ConflictError('Benutzername bereits vergeben')

    if User.query.filter_by(email=validated_data['email']).first():
        current_app.logger.warning(
            f'Registrierungsversuch mit bereits registrierter E-Mail: '
            f'"{validated_data["email"]}" von IP: {request.remote_addr}'
        )
        raise ConflictError('E-Mail-Adresse bereits registriert')

    # Create new user
    user = User(
        username=validated_data['username'],
        email=validated_data['email'],
        is_admin=False
    )
    user.set_password(validated_data['password'])

    db.session.add(user)
    db.session.commit()

    current_app.logger.info(
        f'Neuer Benutzer registriert: "{user.username}" (ID: {user.id}, E-Mail: {user.email})'
    )

    # Create tokens (convert user.id to string for JWT)
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    # Serialize user data
    user_schema = UserSchema()
    user_data = user_schema.dump(user)

    return success_response(
        data={
            'user': user_data,
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        },
        message='Registrierung erfolgreich',
        status_code=201
    )


# ============================================================================
# Login
# ============================================================================

@v1_bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    Login with username and password.

    Request Body:
        {
            "username": "string",
            "password": "string"
        }

    Returns:
        200: Login successful with tokens
        400: Validation error
        401: Invalid credentials
    """
    data = request.get_json()

    # Validate request data
    schema = LoginSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return error_response(
            status_code=400,
            message='Validierungsfehler',
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=err.messages
        )

    # Find user
    user = User.query.filter_by(username=validated_data['username']).first()

    # Check credentials
    if not user or not user.check_password(validated_data['password']):
        current_app.logger.warning(
            f'Fehlgeschlagener API-Anmeldeversuch für Benutzername: '
            f'"{validated_data["username"]}" von IP: {request.remote_addr}'
        )
        return error_response(
            status_code=401,
            message='Ungültige Anmeldedaten',
            error_code=ErrorCodes.INVALID_CREDENTIALS
        )

    current_app.logger.info(
        f'Benutzer "{user.username}" (ID: {user.id}) hat sich via API erfolgreich angemeldet'
    )

    # Create tokens (convert user.id to string for JWT)
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    # Serialize user data
    user_schema = UserSchema()
    user_data = user_schema.dump(user)

    return success_response(
        data={
            'user': user_data,
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        },
        message='Login erfolgreich'
    )


# ============================================================================
# Token Refresh
# ============================================================================

@v1_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token.

    Headers:
        Authorization: Bearer <refresh_token>

    Returns:
        200: New access token
        401: Invalid or expired refresh token
    """
    current_user_id = get_jwt_identity()

    # Create new access token
    access_token = create_access_token(identity=current_user_id)

    return success_response(
        data={
            'access_token': access_token
        },
        message='Token erfolgreich erneuert'
    )


# ============================================================================
# Logout
# ============================================================================

@v1_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout and revoke current access token.

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: Logout successful
        401: Invalid or missing token
    """
    jwt_data = get_jwt()
    jti = jwt_data['jti']
    token_type = jwt_data['type']
    user_id = int(get_jwt_identity())
    expires_at = datetime.fromtimestamp(jwt_data['exp'], tz=timezone.utc)

    user = User.query.get(user_id)
    username = user.username if user else f"ID:{user_id}"

    # Add token to blacklist
    RevokedToken.add_to_blacklist(
        jti=jti,
        token_type=token_type,
        user_id=user_id,
        expires_at=expires_at
    )

    current_app.logger.info(
        f'Benutzer "{username}" (ID: {user_id}) hat sich via API abgemeldet'
    )

    return success_response(
        message='Logout erfolgreich'
    )


@v1_bp.route('/auth/logout-all', methods=['POST'])
@jwt_required()
def logout_all():
    """
    Logout from all devices by revoking both access and refresh tokens.

    This endpoint should be called twice:
    1. Once with the access token
    2. Once with the refresh token

    Headers:
        Authorization: Bearer <token>

    Returns:
        200: Token revoked
        401: Invalid or missing token
    """
    jwt_data = get_jwt()
    jti = jwt_data['jti']
    token_type = jwt_data['type']
    user_id = int(get_jwt_identity())
    expires_at = datetime.fromtimestamp(jwt_data['exp'], tz=timezone.utc)

    # Add token to blacklist
    RevokedToken.add_to_blacklist(
        jti=jti,
        token_type=token_type,
        user_id=user_id,
        expires_at=expires_at
    )

    return success_response(
        message=f'{token_type.capitalize()}-Token erfolgreich widerrufen'
    )


# ============================================================================
# Current User Info
# ============================================================================

@v1_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """
    Get current authenticated user information.

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: User information
        401: Invalid or missing token
    """
    user = get_current_user()

    user_schema = UserSchema()
    user_data = user_schema.dump(user)

    return success_response(data=user_data)


@v1_bp.route('/auth/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """
    Update current user's profile information.

    Request Body:
        {
            "username": "string (optional)",
            "email": "string (optional)"
        }

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: User updated successfully
        400: Validation error
        401: Invalid or missing token
        409: Username or email already exists
    """
    user = get_current_user()
    data = request.get_json()

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
        message='Profil erfolgreich aktualisiert'
    )


# ============================================================================
# Password Management
# ============================================================================

@v1_bp.route('/auth/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def change_password():
    """
    Change current user's password.

    Request Body:
        {
            "old_password": "string",
            "new_password": "string",
            "new_password_confirm": "string"
        }

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: Password changed successfully
        400: Validation error
        401: Invalid old password or missing token
    """
    user = get_current_user()
    data = request.get_json()

    # Validate request data
    schema = ChangePasswordSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return error_response(
            status_code=400,
            message='Validierungsfehler',
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=err.messages
        )

    # Verify old password
    if not user.check_password(validated_data['old_password']):
        current_app.logger.warning(
            f'Benutzer "{user.username}" (ID: {user.id}) hat ein falsches altes Passwort '
            f'beim Passwort-Änderungsversuch eingegeben'
        )
        return error_response(
            status_code=401,
            message='Aktuelles Passwort ist falsch',
            error_code=ErrorCodes.INVALID_CREDENTIALS
        )

    # Set new password
    user.set_password(validated_data['new_password'])
    db.session.commit()

    current_app.logger.info(
        f'Benutzer "{user.username}" (ID: {user.id}) hat sein Passwort geändert'
    )

    return success_response(
        message='Passwort erfolgreich geändert'
    )
