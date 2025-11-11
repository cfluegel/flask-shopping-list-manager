"""
Flask-RESTX API Documentation.

This module provides comprehensive Swagger/OpenAPI documentation for all API endpoints
using Flask-RESTX. It creates an interactive documentation interface accessible at /api/v1/docs.

The documentation is organized into namespaces:
- auth: Authentication operations (register, login, logout, token management)
- users: User management (CRUD operations, admin only)
- lists: Shopping list management
- items: Shopping list item management
- shared: Public shared list access
- admin: Administrative operations
- trash: Trash/recycle bin operations
"""

from flask import Blueprint
from flask_restx import Api, Resource, fields, Namespace

# Create documentation blueprint
docs_bp = Blueprint('api_docs', __name__)

# Initialize API with comprehensive configuration
api = Api(
    docs_bp,
    version='1.0.0',
    title='Grocery Shopping List API',
    description='''
# Grocery Shopping List REST API

A comprehensive RESTful API for managing grocery shopping lists with sharing capabilities.

## Features

- **User Authentication**: JWT-based authentication with access and refresh tokens
- **Shopping Lists**: Create, read, update, and delete shopping lists
- **Items Management**: Add, edit, remove, and check off items in lists
- **Sharing**: Share lists via unique GUID links (public access)
- **Soft Delete**: Trash/restore functionality for lists and items
- **Role-Based Access**: Admin and regular user roles
- **Rate Limiting**: Protection against abuse
- **Pagination**: Efficient data retrieval for large datasets

## Authentication

Most endpoints require authentication using JWT Bearer tokens:

1. Register a new account or login to get tokens
2. Include the access token in the Authorization header: `Bearer <access_token>`
3. Refresh expired access tokens using the refresh endpoint
4. Access tokens expire after 15 minutes, refresh tokens after 30 days

## Rate Limits

- Registration: 5 requests per hour
- Login: 5 requests per minute
- Password changes: 5 requests per hour
- General operations: 30 requests per minute
- Admin operations: 20 requests per hour

## Error Responses

All error responses follow a consistent format:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {} // Optional additional information
  }
}
```

## Success Responses

All success responses follow a consistent format:
```json
{
  "success": true,
  "message": "Human-readable success message",
  "data": {} // Response data (optional)
}
```
    ''',
    doc='/docs/',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Bearer {access_token}"'
        }
    },
    security='Bearer',
    ordered=True,
    validate=True
)

# ============================================================================
# Namespaces
# ============================================================================

auth_ns = api.namespace('auth', description='Authentication operations')
users_ns = api.namespace('users', description='User management (admin only for most operations)')
lists_ns = api.namespace('lists', description='Shopping list operations')
items_ns = api.namespace('items', description='Shopping list item operations')
shared_ns = api.namespace('shared', description='Public shared list access (no authentication required)')
admin_ns = api.namespace('admin', description='Administrative operations (admin only)')
trash_ns = api.namespace('trash', description='Trash/recycle bin operations')

# ============================================================================
# Reusable Models (Schemas)
# ============================================================================

# Error Models
error_details = api.model('ErrorDetails', {
    'code': fields.String(required=True, description='Error code', example='VALIDATION_ERROR'),
    'message': fields.String(required=True, description='Error message', example='Validation failed'),
    'details': fields.Raw(description='Additional error details', example={'username': ['Field is required']})
})

error_response = api.model('ErrorResponse', {
    'success': fields.Boolean(required=True, description='Always false for errors', example=False),
    'error': fields.Nested(error_details, required=True)
})

# User Models
user_model = api.model('User', {
    'id': fields.Integer(readonly=True, description='User ID', example=1),
    'username': fields.String(required=True, description='Username (3-80 characters)', min_length=3, max_length=80, example='john_doe'),
    'email': fields.String(required=True, description='Email address', example='john@example.com'),
    'is_admin': fields.Boolean(description='Admin status', example=False),
    'created_at': fields.DateTime(readonly=True, description='Account creation timestamp')
})

login_request = api.model('LoginRequest', {
    'username': fields.String(required=True, description='Username', example='john_doe'),
    'password': fields.String(required=True, description='Password', example='password123')
})

register_request = api.model('RegisterRequest', {
    'username': fields.String(required=True, description='Username (3-80 characters)', min_length=3, max_length=80, example='john_doe'),
    'email': fields.String(required=True, description='Email address', example='john@example.com'),
    'password': fields.String(required=True, description='Password (min 6 characters)', min_length=6, example='password123'),
    'password_confirm': fields.String(required=True, description='Password confirmation', min_length=6, example='password123')
})

change_password_request = api.model('ChangePasswordRequest', {
    'old_password': fields.String(required=True, description='Current password', example='oldpass123'),
    'new_password': fields.String(required=True, description='New password (min 6 characters)', min_length=6, example='newpass123'),
    'new_password_confirm': fields.String(required=True, description='New password confirmation', example='newpass123')
})

tokens_model = api.model('Tokens', {
    'access_token': fields.String(description='JWT access token (expires in 15 minutes)', example='eyJ0eXAiOiJKV1QiLCJhbGc...'),
    'refresh_token': fields.String(description='JWT refresh token (expires in 30 days)', example='eyJ0eXAiOiJKV1QiLCJhbGc...')
})

token_data = api.model('TokenData', {
    'user': fields.Nested(user_model, description='User information'),
    'tokens': fields.Nested(tokens_model, description='Authentication tokens')
})

auth_success_response = api.model('AuthSuccessResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'message': fields.String(description='Response message', example='Login erfolgreich'),
    'data': fields.Nested(token_data)
})

refresh_token_response = api.model('RefreshTokenResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'message': fields.String(description='Response message', example='Token erfolgreich erneuert'),
    'data': fields.Nested(api.model('AccessToken', {
        'access_token': fields.String(description='New JWT access token', example='eyJ0eXAiOiJKV1QiLCJhbGc...')
    }))
})

user_response = api.model('UserResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'message': fields.String(description='Response message'),
    'data': fields.Nested(user_model)
})

# Shopping List Models
shopping_list_item = api.model('ShoppingListItem', {
    'id': fields.Integer(readonly=True, description='Item ID', example=1),
    'name': fields.String(required=True, description='Item name (1-200 characters)', min_length=1, max_length=200, example='Milk'),
    'quantity': fields.String(description='Quantity (max 50 characters)', max_length=50, example='2 liters'),
    'is_checked': fields.Boolean(description='Checked status', example=False),
    'order_index': fields.Integer(readonly=True, description='Display order (higher = newer)', example=5),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp')
})

shopping_list = api.model('ShoppingList', {
    'id': fields.Integer(readonly=True, description='List ID', example=1),
    'guid': fields.String(readonly=True, description='Unique identifier for sharing (UUID)', example='550e8400-e29b-41d4-a716-446655440000'),
    'title': fields.String(required=True, description='List title (1-200 characters)', min_length=1, max_length=200, example='Weekly Groceries'),
    'is_shared': fields.Boolean(description='Sharing status', example=False),
    'owner_id': fields.Integer(readonly=True, description='Owner user ID', example=1),
    'owner_username': fields.String(readonly=True, description='Owner username', example='john_doe'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(readonly=True, description='Last update timestamp'),
    'item_count': fields.Integer(readonly=True, description='Number of active items in list', example=5)
})

shopping_list_detail = api.model('ShoppingListDetail', {
    'id': fields.Integer(readonly=True, description='List ID', example=1),
    'guid': fields.String(readonly=True, description='Unique identifier for sharing', example='550e8400-e29b-41d4-a716-446655440000'),
    'title': fields.String(description='List title', example='Weekly Groceries'),
    'is_shared': fields.Boolean(description='Sharing status', example=False),
    'owner_id': fields.Integer(readonly=True, description='Owner user ID', example=1),
    'owner_username': fields.String(readonly=True, description='Owner username', example='john_doe'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(readonly=True, description='Last update timestamp'),
    'items': fields.List(fields.Nested(shopping_list_item), description='List items ordered by order_index (descending)')
})

create_list_request = api.model('CreateListRequest', {
    'title': fields.String(required=True, description='List title (1-200 characters)', min_length=1, max_length=200, example='Weekly Groceries'),
    'is_shared': fields.Boolean(description='Initial sharing status (default: false)', example=False)
})

update_list_request = api.model('UpdateListRequest', {
    'title': fields.String(description='List title (1-200 characters)', min_length=1, max_length=200, example='Monthly Groceries'),
    'is_shared': fields.Boolean(description='Sharing status', example=True)
})

share_list_request = api.model('ShareListRequest', {
    'is_shared': fields.Boolean(required=True, description='Sharing status', example=True)
})

create_item_request = api.model('CreateItemRequest', {
    'name': fields.String(required=True, description='Item name (1-200 characters)', min_length=1, max_length=200, example='Eggs'),
    'quantity': fields.String(description='Quantity (max 50 characters, default: "1")', max_length=50, example='12 pieces')
})

update_item_request = api.model('UpdateItemRequest', {
    'name': fields.String(description='Item name (1-200 characters)', min_length=1, max_length=200, example='Eggs'),
    'quantity': fields.String(description='Quantity (max 50 characters)', max_length=50, example='6 pieces'),
    'is_checked': fields.Boolean(description='Checked status', example=True)
})

reorder_item_request = api.model('ReorderItemRequest', {
    'order_index': fields.Integer(required=True, description='New order index (must be >= 0)', min=0, example=10)
})

# Response Models
list_response = api.model('ListResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'message': fields.String(description='Response message', example='Einkaufsliste erfolgreich erstellt'),
    'data': fields.Nested(shopping_list)
})

list_detail_response = api.model('ListDetailResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'message': fields.String(description='Response message'),
    'data': fields.Nested(shopping_list_detail)
})

item_response = api.model('ItemResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'message': fields.String(description='Response message', example='Artikel erfolgreich hinzugefügt'),
    'data': fields.Nested(shopping_list_item)
})

# Pagination Model
pagination_meta = api.model('PaginationMeta', {
    'page': fields.Integer(description='Current page number', example=1),
    'per_page': fields.Integer(description='Items per page', example=20),
    'total': fields.Integer(description='Total number of items', example=45),
    'pages': fields.Integer(description='Total number of pages', example=3),
    'has_next': fields.Boolean(description='Has next page', example=True),
    'has_prev': fields.Boolean(description='Has previous page', example=False)
})

paginated_lists_response = api.model('PaginatedListsResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'data': fields.List(fields.Nested(shopping_list), description='List of shopping lists'),
    'pagination': fields.Nested(pagination_meta, description='Pagination metadata')
})

paginated_users_response = api.model('PaginatedUsersResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'data': fields.List(fields.Nested(user_model), description='List of users'),
    'pagination': fields.Nested(pagination_meta, description='Pagination metadata')
})

# Share URL Response
share_url_response = api.model('ShareUrlResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'data': fields.Nested(api.model('ShareUrlData', {
        'guid': fields.String(description='List GUID', example='550e8400-e29b-41d4-a716-446655440000'),
        'is_shared': fields.Boolean(description='Sharing status', example=True),
        'api_url': fields.String(description='Relative API URL', example='/api/v1/shared/550e8400-e29b-41d4-a716-446655440000'),
        'web_url': fields.String(description='Relative web URL', example='/shared/550e8400-e29b-41d4-a716-446655440000'),
        'full_api_url': fields.String(description='Full API URL', example='http://localhost:5000/api/v1/shared/550e8400-e29b-41d4-a716-446655440000'),
        'full_web_url': fields.String(description='Full web URL', example='http://localhost:5000/shared/550e8400-e29b-41d4-a716-446655440000')
    }))
})

# Admin Statistics
admin_stats = api.model('AdminStatistics', {
    'users': fields.Nested(api.model('UserStats', {
        'total': fields.Integer(description='Total users', example=10),
        'admins': fields.Integer(description='Admin users', example=1),
        'regular': fields.Integer(description='Regular users', example=9)
    })),
    'lists': fields.Nested(api.model('ListStats', {
        'total': fields.Integer(description='Total lists', example=45),
        'shared': fields.Integer(description='Shared lists', example=5),
        'private': fields.Integer(description='Private lists', example=40)
    })),
    'items': fields.Nested(api.model('ItemStats', {
        'total': fields.Integer(description='Total items', example=250),
        'checked': fields.Integer(description='Checked items', example=100),
        'unchecked': fields.Integer(description='Unchecked items', example=150)
    })),
    'tokens': fields.Nested(api.model('TokenStats', {
        'revoked': fields.Integer(description='Revoked tokens', example=23)
    }))
})

# Generic Success Response
success_response_model = api.model('SuccessResponse', {
    'success': fields.Boolean(description='Success status', example=True),
    'message': fields.String(description='Response message', example='Operation completed successfully'),
    'data': fields.Raw(description='Response data (optional)')
})

# ============================================================================
# Authentication Namespace
# ============================================================================

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc('register_user',
                 description='Register a new user account and receive authentication tokens.',
                 responses={
                     201: ('User registered successfully', auth_success_response),
                     400: ('Validation error', error_response),
                     409: ('Username or email already exists', error_response),
                     429: 'Rate limit exceeded (5 requests per hour)'
                 })
    @auth_ns.expect(register_request, validate=True)
    @auth_ns.marshal_with(auth_success_response, code=201)
    def post(self):
        """Register a new user account"""
        pass


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login_user',
                 description='Authenticate with username and password to receive JWT tokens.',
                 responses={
                     200: ('Login successful', auth_success_response),
                     400: ('Validation error', error_response),
                     401: ('Invalid credentials', error_response),
                     429: 'Rate limit exceeded (5 requests per minute)'
                 })
    @auth_ns.expect(login_request, validate=True)
    @auth_ns.marshal_with(auth_success_response)
    def post(self):
        """Login and receive JWT tokens"""
        pass


@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @auth_ns.doc('refresh_token',
                 description='Refresh an expired access token using a valid refresh token.',
                 responses={
                     200: ('Token refreshed successfully', refresh_token_response),
                     401: ('Invalid or expired refresh token', error_response)
                 },
                 security='Bearer')
    @auth_ns.marshal_with(refresh_token_response)
    def post(self):
        """Refresh access token using refresh token"""
        pass


@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('logout_user',
                 description='Logout and revoke the current access token.',
                 responses={
                     200: ('Logout successful', success_response_model),
                     401: ('Invalid or missing token', error_response)
                 },
                 security='Bearer')
    @auth_ns.marshal_with(success_response_model)
    def post(self):
        """Logout and revoke current token"""
        pass


@auth_ns.route('/logout-all')
class LogoutAll(Resource):
    @auth_ns.doc('logout_all_devices',
                 description='Logout from all devices by revoking both access and refresh tokens. Call twice (once with access token, once with refresh token).',
                 responses={
                     200: ('Token revoked', success_response_model),
                     401: ('Invalid or missing token', error_response)
                 },
                 security='Bearer')
    @auth_ns.marshal_with(success_response_model)
    def post(self):
        """Revoke token (call with both access and refresh tokens)"""
        pass


@auth_ns.route('/me')
class CurrentUser(Resource):
    @auth_ns.doc('get_current_user',
                 description='Get information about the currently authenticated user.',
                 responses={
                     200: ('User information retrieved', user_response),
                     401: ('Unauthorized', error_response)
                 },
                 security='Bearer')
    @auth_ns.marshal_with(user_response)
    def get(self):
        """Get current user information"""
        pass

    @auth_ns.doc('update_current_user',
                 description='Update the current user\'s profile information.',
                 responses={
                     200: ('Profile updated successfully', user_response),
                     400: ('Validation error', error_response),
                     401: ('Unauthorized', error_response),
                     409: ('Username or email already exists', error_response)
                 },
                 security='Bearer')
    @auth_ns.expect(api.model('UpdateSelfRequest', {
        'username': fields.String(description='New username (optional)', example='new_username'),
        'email': fields.String(description='New email (optional)', example='newemail@example.com')
    }))
    @auth_ns.marshal_with(user_response)
    def put(self):
        """Update current user's profile"""
        pass


@auth_ns.route('/change-password')
class ChangePassword(Resource):
    @auth_ns.doc('change_password',
                 description='Change the current user\'s password.',
                 responses={
                     200: ('Password changed successfully', success_response_model),
                     400: ('Validation error', error_response),
                     401: ('Invalid old password or unauthorized', error_response),
                     429: 'Rate limit exceeded (5 requests per hour)'
                 },
                 security='Bearer')
    @auth_ns.expect(change_password_request, validate=True)
    @auth_ns.marshal_with(success_response_model)
    def post(self):
        """Change user password"""
        pass


# ============================================================================
# Users Namespace
# ============================================================================

@users_ns.route('')
class UserList(Resource):
    @users_ns.doc('get_all_users',
                  description='Get all users with pagination (Admin only).',
                  params={
                      'page': 'Page number (default: 1)',
                      'per_page': 'Items per page (default: 20, max: 100)'
                  },
                  responses={
                      200: ('Users retrieved successfully', paginated_users_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response)
                  },
                  security='Bearer')
    @users_ns.marshal_with(paginated_users_response)
    def get(self):
        """Get all users (Admin only)"""
        pass

    @users_ns.doc('create_user',
                  description='Create a new user (Admin only).',
                  responses={
                      201: ('User created successfully', user_response),
                      400: ('Validation error', error_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response),
                      409: ('Username or email already exists', error_response),
                      429: 'Rate limit exceeded (20 requests per hour)'
                  },
                  security='Bearer')
    @users_ns.expect(api.model('CreateUserRequest', {
        'username': fields.String(required=True, description='Username (3-80 characters)', example='jane_doe'),
        'email': fields.String(required=True, description='Email address', example='jane@example.com'),
        'password': fields.String(required=True, description='Password (min 6 characters)', example='password123'),
        'is_admin': fields.Boolean(description='Admin status (default: false)', example=False)
    }), validate=True)
    @users_ns.marshal_with(user_response, code=201)
    def post(self):
        """Create new user (Admin only)"""
        pass


@users_ns.route('/<int:user_id>')
@users_ns.param('user_id', 'User ID')
class UserResource(Resource):
    @users_ns.doc('get_user',
                  description='Get user by ID. Users can only access their own information unless they are admin.',
                  responses={
                      200: ('User retrieved successfully', user_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('User not found', error_response)
                  },
                  security='Bearer')
    @users_ns.marshal_with(user_response)
    def get(self, user_id):
        """Get user by ID"""
        pass

    @users_ns.doc('update_user',
                  description='Update user information. Regular users can only update their own username and email. Admins can update any user.',
                  responses={
                      200: ('User updated successfully', user_response),
                      400: ('Validation error', error_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('User not found', error_response),
                      409: ('Username or email already exists', error_response)
                  },
                  security='Bearer')
    @users_ns.expect(api.model('UpdateUserRequest', {
        'username': fields.String(description='New username (optional)', example='updated_username'),
        'email': fields.String(description='New email (optional)', example='updated@example.com'),
        'is_admin': fields.Boolean(description='Admin status (admin only, optional)', example=True)
    }))
    @users_ns.marshal_with(user_response)
    def put(self, user_id):
        """Update user"""
        pass

    @users_ns.doc('delete_user',
                  description='Delete a user and all their shopping lists (Admin only). Cannot delete yourself.',
                  responses={
                      200: ('User deleted successfully', success_response_model),
                      400: ('Cannot delete yourself', error_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response),
                      404: ('User not found', error_response),
                      429: 'Rate limit exceeded (20 requests per hour)'
                  },
                  security='Bearer')
    @users_ns.marshal_with(success_response_model)
    def delete(self, user_id):
        """Delete user (Admin only)"""
        pass


@users_ns.route('/<int:user_id>/lists')
@users_ns.param('user_id', 'User ID')
class UserLists(Resource):
    @users_ns.doc('get_user_lists',
                  description='Get all shopping lists for a specific user.',
                  params={
                      'page': 'Page number (default: 1)',
                      'per_page': 'Items per page (default: 20, max: 100)'
                  },
                  responses={
                      200: ('Lists retrieved successfully', paginated_lists_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('User not found', error_response)
                  },
                  security='Bearer')
    @users_ns.marshal_with(paginated_lists_response)
    def get(self, user_id):
        """Get user's shopping lists"""
        pass


# ============================================================================
# Shopping Lists Namespace
# ============================================================================

@lists_ns.route('')
class ListCollection(Resource):
    @lists_ns.doc('get_user_lists',
                  description='Get all shopping lists for the current user (paginated, active lists only).',
                  params={
                      'page': 'Page number (default: 1)',
                      'per_page': 'Items per page (default: 20, max: 100)'
                  },
                  responses={
                      200: ('Lists retrieved successfully', paginated_lists_response),
                      401: ('Unauthorized', error_response)
                  },
                  security='Bearer')
    @lists_ns.marshal_with(paginated_lists_response)
    def get(self):
        """Get current user's shopping lists"""
        pass

    @lists_ns.doc('create_list',
                  description='Create a new shopping list.',
                  responses={
                      201: ('List created successfully', list_response),
                      400: ('Validation error', error_response),
                      401: ('Unauthorized', error_response),
                      429: 'Rate limit exceeded (30 requests per minute)'
                  },
                  security='Bearer')
    @lists_ns.expect(create_list_request, validate=True)
    @lists_ns.marshal_with(list_response, code=201)
    def post(self):
        """Create new shopping list"""
        pass


@lists_ns.route('/<int:list_id>')
@lists_ns.param('list_id', 'Shopping list ID')
class ListResource(Resource):
    @lists_ns.doc('get_list',
                  description='Get a specific shopping list with all items. Accessible by owner, admin, or if shared.',
                  responses={
                      200: ('List retrieved successfully', list_detail_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('List not found', error_response)
                  },
                  security='Bearer')
    @lists_ns.marshal_with(list_detail_response)
    def get(self, list_id):
        """Get shopping list with items"""
        pass

    @lists_ns.doc('update_list',
                  description='Update a shopping list. Only owner or admin can update.',
                  responses={
                      200: ('List updated successfully', list_response),
                      400: ('Validation error', error_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('List not found', error_response),
                      429: 'Rate limit exceeded (30 requests per minute)'
                  },
                  security='Bearer')
    @lists_ns.expect(update_list_request)
    @lists_ns.marshal_with(list_response)
    def put(self, list_id):
        """Update shopping list"""
        pass

    @lists_ns.doc('delete_list',
                  description='Soft delete a shopping list (move to trash). Also soft deletes all items.',
                  responses={
                      200: ('List moved to trash', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('List not found', error_response),
                      429: 'Rate limit exceeded (30 requests per minute)'
                  },
                  security='Bearer')
    @lists_ns.marshal_with(success_response_model)
    def delete(self, list_id):
        """Delete shopping list (move to trash)"""
        pass


@lists_ns.route('/<int:list_id>/restore')
@lists_ns.param('list_id', 'Shopping list ID')
class RestoreList(Resource):
    @lists_ns.doc('restore_list',
                  description='Restore a shopping list from trash. Also restores all items.',
                  responses={
                      200: ('List restored successfully', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('List not found in trash', error_response),
                      429: 'Rate limit exceeded (30 requests per minute)'
                  },
                  security='Bearer')
    @lists_ns.marshal_with(success_response_model)
    def post(self, list_id):
        """Restore list from trash"""
        pass


@lists_ns.route('/<int:list_id>/share')
@lists_ns.param('list_id', 'Shopping list ID')
class ShareList(Resource):
    @lists_ns.doc('toggle_share',
                  description='Toggle sharing status of a list. When changing from shared to private, the GUID is regenerated (invalidating old links).',
                  responses={
                      200: ('Sharing status updated', success_response_model),
                      400: ('Validation error', error_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('List not found', error_response)
                  },
                  security='Bearer')
    @lists_ns.expect(share_list_request, validate=True)
    @lists_ns.marshal_with(success_response_model)
    def post(self, list_id):
        """Toggle list sharing status"""
        pass


@lists_ns.route('/<int:list_id>/share-url')
@lists_ns.param('list_id', 'Shopping list ID')
class ShareUrl(Resource):
    @lists_ns.doc('get_share_url',
                  description='Get the sharing URL for a list.',
                  responses={
                      200: ('Share URL retrieved', share_url_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('List not found', error_response)
                  },
                  security='Bearer')
    @lists_ns.marshal_with(share_url_response)
    def get(self, list_id):
        """Get share URL for list"""
        pass


# ============================================================================
# Items Namespace
# ============================================================================

@items_ns.route('/lists/<int:list_id>/items')
@items_ns.param('list_id', 'Shopping list ID')
class ItemCollection(Resource):
    @items_ns.doc('get_list_items',
                  description='Get all items for a shopping list.',
                  responses={
                      200: ('Items retrieved successfully', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('List not found', error_response)
                  },
                  security='Bearer')
    def get(self, list_id):
        """Get all items in list"""
        pass

    @items_ns.doc('create_item',
                  description='Add an item to a shopping list.',
                  responses={
                      201: ('Item created successfully', item_response),
                      400: ('Validation error', error_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('List not found', error_response),
                      429: 'Rate limit exceeded (30 requests per minute)'
                  },
                  security='Bearer')
    @items_ns.expect(create_item_request, validate=True)
    @items_ns.marshal_with(item_response, code=201)
    def post(self, list_id):
        """Add item to list"""
        pass


@items_ns.route('/lists/<int:list_id>/items/clear-checked')
@items_ns.param('list_id', 'Shopping list ID')
class ClearCheckedItems(Resource):
    @items_ns.doc('clear_checked_items',
                  description='Remove all checked items from a list (soft delete). Useful for clearing completed items.',
                  responses={
                      200: ('Checked items cleared', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('List not found', error_response)
                  },
                  security='Bearer')
    @items_ns.marshal_with(success_response_model)
    def post(self, list_id):
        """Clear all checked items"""
        pass


@items_ns.route('/items/<int:item_id>')
@items_ns.param('item_id', 'Item ID')
class ItemResource(Resource):
    @items_ns.doc('get_item',
                  description='Get a specific item.',
                  responses={
                      200: ('Item retrieved successfully', item_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('Item not found', error_response)
                  },
                  security='Bearer')
    @items_ns.marshal_with(item_response)
    def get(self, item_id):
        """Get item details"""
        pass

    @items_ns.doc('update_item',
                  description='Update a shopping list item.',
                  responses={
                      200: ('Item updated successfully', item_response),
                      400: ('Validation error', error_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('Item not found', error_response),
                      429: 'Rate limit exceeded (30 requests per minute)'
                  },
                  security='Bearer')
    @items_ns.expect(update_item_request)
    @items_ns.marshal_with(item_response)
    def put(self, item_id):
        """Update item"""
        pass

    @items_ns.doc('delete_item',
                  description='Soft delete a shopping list item (move to trash).',
                  responses={
                      200: ('Item moved to trash', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('Item not found', error_response),
                      429: 'Rate limit exceeded (30 requests per minute)'
                  },
                  security='Bearer')
    @items_ns.marshal_with(success_response_model)
    def delete(self, item_id):
        """Delete item (move to trash)"""
        pass


@items_ns.route('/items/<int:item_id>/restore')
@items_ns.param('item_id', 'Item ID')
class RestoreItem(Resource):
    @items_ns.doc('restore_item',
                  description='Restore an item from trash.',
                  responses={
                      200: ('Item restored successfully', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('Item not found in trash', error_response),
                      429: 'Rate limit exceeded (30 requests per minute)'
                  },
                  security='Bearer')
    @items_ns.marshal_with(success_response_model)
    def post(self, item_id):
        """Restore item from trash"""
        pass


@items_ns.route('/items/<int:item_id>/toggle')
@items_ns.param('item_id', 'Item ID')
class ToggleItem(Resource):
    @items_ns.doc('toggle_item',
                  description='Toggle the checked status of an item.',
                  responses={
                      200: ('Item toggled successfully', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden', error_response),
                      404: ('Item not found', error_response)
                  },
                  security='Bearer')
    @items_ns.marshal_with(success_response_model)
    def post(self, item_id):
        """Toggle item checked status"""
        pass


@items_ns.route('/items/<int:item_id>/reorder')
@items_ns.param('item_id', 'Item ID')
class ReorderItem(Resource):
    @items_ns.doc('reorder_item',
                  description='Change the order index of an item for custom sorting.',
                  responses={
                      200: ('Item reordered successfully', success_response_model),
                      400: ('Validation error', error_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Owner or admin only', error_response),
                      404: ('Item not found', error_response)
                  },
                  security='Bearer')
    @items_ns.expect(reorder_item_request, validate=True)
    @items_ns.marshal_with(success_response_model)
    def put(self, item_id):
        """Reorder item"""
        pass


# ============================================================================
# Shared Lists Namespace (Public Access)
# ============================================================================

@shared_ns.route('/<string:guid>')
@shared_ns.param('guid', 'Shopping list GUID')
class SharedList(Resource):
    @shared_ns.doc('get_shared_list',
                    description='Get a shared shopping list by GUID. No authentication required.',
                    responses={
                        200: ('Shared list retrieved successfully', list_detail_response),
                        404: ('List not found or not shared', error_response)
                    })
    def get(self, guid):
        """Get shared list (public)"""
        pass


@shared_ns.route('/<string:guid>/items')
@shared_ns.param('guid', 'Shopping list GUID')
class SharedListItems(Resource):
    @shared_ns.doc('get_shared_list_items',
                    description='Get only the items of a shared list. No authentication required.',
                    responses={
                        200: ('Items retrieved successfully', success_response_model),
                        404: ('List not found or not shared', error_response)
                    })
    def get(self, guid):
        """Get shared list items (public)"""
        pass


@shared_ns.route('/<string:guid>/info')
@shared_ns.param('guid', 'Shopping list GUID')
class SharedListInfo(Resource):
    @shared_ns.doc('get_shared_list_info',
                    description='Get basic information about a shared list without items. No authentication required.',
                    responses={
                        200: ('List info retrieved successfully', success_response_model),
                        404: ('List not found or not shared', error_response)
                    })
    def get(self, guid):
        """Get shared list info (public)"""
        pass


# ============================================================================
# Trash Namespace
# ============================================================================

@trash_ns.route('/lists')
class TrashLists(Resource):
    @trash_ns.doc('get_trash_lists',
                  description='Get all deleted shopping lists for the current user.',
                  params={
                      'page': 'Page number (default: 1)',
                      'per_page': 'Items per page (default: 20, max: 100)'
                  },
                  responses={
                      200: ('Deleted lists retrieved successfully', paginated_lists_response),
                      401: ('Unauthorized', error_response)
                  },
                  security='Bearer')
    @trash_ns.marshal_with(paginated_lists_response)
    def get(self):
        """Get deleted lists (trash)"""
        pass


@trash_ns.route('/lists/<int:list_id>')
@trash_ns.param('list_id', 'Shopping list ID')
class TrashListResource(Resource):
    @trash_ns.doc('permanent_delete_list',
                  description='Permanently delete a shopping list from trash (Admin only). This action is irreversible.',
                  responses={
                      200: ('List permanently deleted', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response),
                      404: ('List not found in trash', error_response),
                      429: 'Rate limit exceeded (20 requests per hour)'
                  },
                  security='Bearer')
    @trash_ns.marshal_with(success_response_model)
    def delete(self, list_id):
        """Permanently delete list (Admin only)"""
        pass


@trash_ns.route('/items')
class TrashItems(Resource):
    @trash_ns.doc('get_trash_items',
                  description='Get all deleted items for the current user.',
                  responses={
                      200: ('Deleted items retrieved successfully', success_response_model),
                      401: ('Unauthorized', error_response)
                  },
                  security='Bearer')
    def get(self):
        """Get deleted items (trash)"""
        pass


# ============================================================================
# Admin Namespace
# ============================================================================

@admin_ns.route('/stats')
class AdminStats(Resource):
    @admin_ns.doc('get_statistics',
                  description='Get comprehensive system statistics (Admin only).',
                  responses={
                      200: ('Statistics retrieved successfully', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response)
                  },
                  security='Bearer')
    def get(self):
        """Get system statistics (Admin only)"""
        pass


@admin_ns.route('/lists')
class AdminLists(Resource):
    @admin_ns.doc('get_all_lists',
                  description='Get all shopping lists from all users (Admin only).',
                  params={
                      'page': 'Page number (default: 1)',
                      'per_page': 'Items per page (default: 20, max: 100)',
                      'shared_only': 'Only show shared lists (default: false)'
                  },
                  responses={
                      200: ('Lists retrieved successfully', paginated_lists_response),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response)
                  },
                  security='Bearer')
    @admin_ns.marshal_with(paginated_lists_response)
    def get(self):
        """Get all lists from all users (Admin only)"""
        pass


@admin_ns.route('/lists/<int:list_id>')
@admin_ns.param('list_id', 'Shopping list ID')
class AdminListResource(Resource):
    @admin_ns.doc('admin_delete_list',
                  description='Delete any shopping list and all items (Admin only).',
                  responses={
                      200: ('List deleted successfully', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response),
                      404: ('List not found', error_response)
                  },
                  security='Bearer')
    @admin_ns.marshal_with(success_response_model)
    def delete(self, list_id):
        """Delete any list (Admin only)"""
        pass


@admin_ns.route('/tokens/cleanup')
class TokenCleanup(Resource):
    @admin_ns.doc('cleanup_tokens',
                  description='Remove expired tokens from the blacklist (Admin only).',
                  responses={
                      200: ('Cleanup completed', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response)
                  },
                  security='Bearer')
    @admin_ns.marshal_with(success_response_model)
    def post(self):
        """Cleanup expired tokens (Admin only)"""
        pass


@admin_ns.route('/tokens/stats')
class TokenStats(Resource):
    @admin_ns.doc('get_token_stats',
                  description='Get statistics about revoked tokens (Admin only).',
                  responses={
                      200: ('Token stats retrieved', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response)
                  },
                  security='Bearer')
    def get(self):
        """Get token statistics (Admin only)"""
        pass


@admin_ns.route('/users/<int:user_id>/activity')
@admin_ns.param('user_id', 'User ID')
class UserActivity(Resource):
    @admin_ns.doc('get_user_activity',
                  description='Get activity statistics for a specific user (Admin only).',
                  responses={
                      200: ('User activity retrieved', success_response_model),
                      401: ('Unauthorized', error_response),
                      403: ('Forbidden - Admin only', error_response),
                      404: ('User not found', error_response)
                  },
                  security='Bearer')
    def get(self, user_id):
        """Get user activity (Admin only)"""
        pass
