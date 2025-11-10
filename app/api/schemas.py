"""
Marshmallow Schemas for API Request/Response Validation and Serialization.

These schemas define the structure and validation rules for all API endpoints.
"""

from marshmallow import Schema, fields, validate, ValidationError, validates, validates_schema
from marshmallow.exceptions import ValidationError as MarshmallowValidationError


# ============================================================================
# Authentication Schemas
# ============================================================================

class LoginSchema(Schema):
    """Schema for login requests."""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=255))


class RegisterSchema(Schema):
    """Schema for user registration."""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6, max=255))
    password_confirm = fields.Str(required=True, validate=validate.Length(min=6, max=255))

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that password and password_confirm match."""
        if data.get('password') != data.get('password_confirm'):
            raise ValidationError('Passwörter stimmen nicht überein', field_name='password_confirm')


class ChangePasswordSchema(Schema):
    """Schema for password change requests."""
    old_password = fields.Str(required=True, validate=validate.Length(min=6, max=255))
    new_password = fields.Str(required=True, validate=validate.Length(min=6, max=255))
    new_password_confirm = fields.Str(required=True, validate=validate.Length(min=6, max=255))

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that new password and confirm match."""
        if data.get('new_password') != data.get('new_password_confirm'):
            raise ValidationError('Neue Passwörter stimmen nicht überein', field_name='new_password_confirm')


class ForgotPasswordSchema(Schema):
    """Schema for forgot password requests."""
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    """Schema for password reset with token."""
    token = fields.Str(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6, max=255))
    password_confirm = fields.Str(required=True, validate=validate.Length(min=6, max=255))

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that password and password_confirm match."""
        if data.get('password') != data.get('password_confirm'):
            raise ValidationError('Passwörter stimmen nicht überein', field_name='password_confirm')


# ============================================================================
# User Schemas
# ============================================================================

class UserSchema(Schema):
    """Schema for user responses (without password)."""
    id = fields.Int(dump_only=True)
    username = fields.Str()
    email = fields.Email()
    is_admin = fields.Bool()
    created_at = fields.DateTime(dump_only=True)


class UserCreateSchema(Schema):
    """Schema for creating a new user (Admin only)."""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6, max=255))
    is_admin = fields.Bool(load_default=False)


class UserUpdateSchema(Schema):
    """Schema for updating user information."""
    username = fields.Str(validate=validate.Length(min=3, max=80))
    email = fields.Email()
    is_admin = fields.Bool()


class UserUpdateSelfSchema(Schema):
    """Schema for users updating their own information."""
    username = fields.Str(validate=validate.Length(min=3, max=80))
    email = fields.Email()


# ============================================================================
# Shopping List Schemas
# ============================================================================

class ShoppingListItemSchema(Schema):
    """Schema for shopping list items."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    quantity = fields.Str(load_default='1', validate=validate.Length(max=50))
    is_checked = fields.Bool(load_default=False)
    order_index = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class ShoppingListItemCreateSchema(Schema):
    """Schema for creating a shopping list item."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    quantity = fields.Str(load_default='1', validate=validate.Length(max=50))


class ShoppingListItemUpdateSchema(Schema):
    """Schema for updating a shopping list item."""
    name = fields.Str(validate=validate.Length(min=1, max=200))
    quantity = fields.Str(validate=validate.Length(max=50))
    is_checked = fields.Bool()


class ShoppingListItemReorderSchema(Schema):
    """Schema for reordering items."""
    order_index = fields.Int(required=True, validate=validate.Range(min=0))


class ShoppingListSchema(Schema):
    """Schema for shopping list responses."""
    id = fields.Int(dump_only=True)
    guid = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    is_shared = fields.Bool(load_default=False)
    owner_id = fields.Int(dump_only=True)
    owner_username = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    item_count = fields.Int(dump_only=True)


class ShoppingListDetailSchema(Schema):
    """Schema for detailed shopping list with items."""
    id = fields.Int(dump_only=True)
    guid = fields.Str(dump_only=True)
    title = fields.Str()
    is_shared = fields.Bool()
    owner_id = fields.Int(dump_only=True)
    owner_username = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    items = fields.List(fields.Nested(ShoppingListItemSchema))


class ShoppingListCreateSchema(Schema):
    """Schema for creating a shopping list."""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    is_shared = fields.Bool(load_default=False)


class ShoppingListUpdateSchema(Schema):
    """Schema for updating a shopping list."""
    title = fields.Str(validate=validate.Length(min=1, max=200))
    is_shared = fields.Bool()


class ShareListSchema(Schema):
    """Schema for sharing/unsharing a list."""
    is_shared = fields.Bool(required=True)


# ============================================================================
# Pagination Schema
# ============================================================================

class PaginationSchema(Schema):
    """Schema for pagination metadata."""
    page = fields.Int()
    per_page = fields.Int()
    total = fields.Int()
    pages = fields.Int()
    has_next = fields.Bool()
    has_prev = fields.Bool()


# ============================================================================
# Utility Functions
# ============================================================================

def validate_schema(schema_class, data):
    """
    Validate data against a schema.

    Args:
        schema_class: The Marshmallow schema class to use for validation
        data: The data to validate

    Returns:
        dict: Validated and deserialized data

    Raises:
        ValidationError: If validation fails
    """
    schema = schema_class()
    try:
        return schema.load(data)
    except MarshmallowValidationError as err:
        raise ValidationError(err.messages)
