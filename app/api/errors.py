"""
Centralized Error Handling for API Endpoints.

Provides consistent error responses across all API endpoints.
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
from flask_jwt_extended.exceptions import JWTExtendedException
from sqlalchemy.exc import IntegrityError


# ============================================================================
# Error Response Helpers
# ============================================================================

def error_response(status_code: int, message: str, error_code: str = None, details: dict = None):
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details

    Returns:
        tuple: (response, status_code)
    """
    payload = {
        'success': False,
        'error': {
            'message': message,
            'code': error_code or f'ERROR_{status_code}'
        }
    }

    if details:
        payload['error']['details'] = details

    return jsonify(payload), status_code


def success_response(data=None, message: str = None, status_code: int = 200):
    """
    Create a standardized success response.

    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code (default: 200)

    Returns:
        tuple: (response, status_code)
    """
    payload = {'success': True}

    if data is not None:
        payload['data'] = data

    if message:
        payload['message'] = message

    return jsonify(payload), status_code


def paginated_response(items, pagination, schema=None):
    """
    Create a paginated response.

    Args:
        items: List of items to return
        pagination: SQLAlchemy pagination object
        schema: Optional Marshmallow schema for serialization

    Returns:
        tuple: (response, status_code)
    """
    if schema:
        items = schema.dump(items, many=True)

    payload = {
        'success': True,
        'data': items,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }

    return jsonify(payload), 200


# ============================================================================
# Error Code Constants
# ============================================================================

class ErrorCodes:
    """Centralized error codes for the API."""

    # Authentication & Authorization
    UNAUTHORIZED = 'UNAUTHORIZED'
    FORBIDDEN = 'FORBIDDEN'
    INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
    TOKEN_EXPIRED = 'TOKEN_EXPIRED'
    TOKEN_INVALID = 'TOKEN_INVALID'
    TOKEN_REVOKED = 'TOKEN_REVOKED'

    # Validation
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    MISSING_FIELD = 'MISSING_FIELD'
    INVALID_INPUT = 'INVALID_INPUT'

    # Resource Errors
    NOT_FOUND = 'NOT_FOUND'
    ALREADY_EXISTS = 'ALREADY_EXISTS'
    CONFLICT = 'CONFLICT'

    # Server Errors
    INTERNAL_ERROR = 'INTERNAL_ERROR'
    DATABASE_ERROR = 'DATABASE_ERROR'

    # Business Logic
    LIST_NOT_SHARED = 'LIST_NOT_SHARED'
    INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS'


# ============================================================================
# Custom Exception Classes
# ============================================================================

class APIError(Exception):
    """Base class for API errors."""

    def __init__(self, message: str, status_code: int = 400, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or ErrorCodes.INVALID_INPUT
        self.details = details


class ValidationError(APIError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=details
        )


class UnauthorizedError(APIError):
    """Raised when authentication is required but not provided."""

    def __init__(self, message: str = 'Authentifizierung erforderlich'):
        super().__init__(
            message=message,
            status_code=401,
            error_code=ErrorCodes.UNAUTHORIZED
        )


class ForbiddenError(APIError):
    """Raised when user lacks permissions."""

    def __init__(self, message: str = 'Zugriff verweigert'):
        super().__init__(
            message=message,
            status_code=403,
            error_code=ErrorCodes.FORBIDDEN
        )


class NotFoundError(APIError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = 'Ressource nicht gefunden'):
        super().__init__(
            message=message,
            status_code=404,
            error_code=ErrorCodes.NOT_FOUND
        )


class ConflictError(APIError):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code=ErrorCodes.CONFLICT,
            details=details
        )


# ============================================================================
# Error Handler Registration
# ============================================================================

def register_error_handlers(app):
    """
    Register error handlers with the Flask app.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors."""
        return error_response(
            status_code=error.status_code,
            message=error.message,
            error_code=error.error_code,
            details=error.details
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle Marshmallow validation errors."""
        return error_response(
            status_code=400,
            message='Validierungsfehler',
            error_code=ErrorCodes.VALIDATION_ERROR,
            details=error.messages if hasattr(error, 'messages') else None
        )

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        """Handle database integrity errors (e.g., unique constraint violations)."""
        # Check for common integrity errors
        error_msg = str(error.orig) if hasattr(error, 'orig') else str(error)

        if 'UNIQUE constraint failed' in error_msg or 'unique constraint' in error_msg.lower():
            if 'username' in error_msg.lower():
                message = 'Benutzername bereits vergeben'
            elif 'email' in error_msg.lower():
                message = 'E-Mail-Adresse bereits registriert'
            else:
                message = 'Dieser Eintrag existiert bereits'

            return error_response(
                status_code=409,
                message=message,
                error_code=ErrorCodes.ALREADY_EXISTS
            )

        # Generic database error
        return error_response(
            status_code=500,
            message='Datenbankfehler',
            error_code=ErrorCodes.DATABASE_ERROR
        )

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_error(error):
        """Handle JWT-related errors."""
        error_type = type(error).__name__

        if 'ExpiredSignature' in error_type:
            message = 'Token abgelaufen'
            code = ErrorCodes.TOKEN_EXPIRED
        elif 'InvalidToken' in error_type or 'DecodeError' in error_type:
            message = 'Ungültiger Token'
            code = ErrorCodes.TOKEN_INVALID
        elif 'RevokedToken' in error_type:
            message = 'Token wurde widerrufen'
            code = ErrorCodes.TOKEN_REVOKED
        else:
            message = str(error)
            code = ErrorCodes.UNAUTHORIZED

        return error_response(
            status_code=401,
            message=message,
            error_code=code
        )

    @app.errorhandler(404)
    def handle_404_error(error):
        """Handle 404 Not Found errors."""
        return error_response(
            status_code=404,
            message='Ressource nicht gefunden',
            error_code=ErrorCodes.NOT_FOUND
        )

    @app.errorhandler(403)
    def handle_403_error(error):
        """Handle 403 Forbidden errors."""
        return error_response(
            status_code=403,
            message='Zugriff verweigert',
            error_code=ErrorCodes.FORBIDDEN
        )

    @app.errorhandler(401)
    def handle_401_error(error):
        """Handle 401 Unauthorized errors."""
        return error_response(
            status_code=401,
            message='Authentifizierung erforderlich',
            error_code=ErrorCodes.UNAUTHORIZED
        )

    @app.errorhandler(500)
    def handle_500_error(error):
        """Handle 500 Internal Server errors."""
        # Log the error here if you have logging configured
        return error_response(
            status_code=500,
            message='Interner Serverfehler',
            error_code=ErrorCodes.INTERNAL_ERROR
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle other HTTP exceptions."""
        return error_response(
            status_code=error.code,
            message=error.description or 'Ein Fehler ist aufgetreten',
            error_code=f'HTTP_{error.code}'
        )
