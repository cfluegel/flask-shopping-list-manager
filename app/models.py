import uuid
from datetime import datetime, timezone
from typing import List as TypeList

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


class User(UserMixin, db.Model):
    """User model for authentication and authorization."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    shopping_lists = db.relationship('ShoppingList', backref='owner', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the user's password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class ShoppingList(db.Model):
    """Shopping list model with GUID for sharing."""

    __tablename__ = 'shopping_lists'

    id = db.Column(db.Integer, primary_key=True)
    guid = db.Column(db.String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_shared = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True, default=None, index=True)

    # Relationships
    items = db.relationship('ShoppingListItem', backref='shopping_list', lazy='dynamic', cascade='all, delete-orphan', order_by='ShoppingListItem.order_index')

    def __repr__(self) -> str:
        return f'<ShoppingList {self.title}>'

    def get_share_url(self) -> str:
        """Get the sharing URL for this list."""
        from flask import url_for
        return url_for('main.view_shared_list', guid=self.guid, _external=True)

    def soft_delete(self) -> None:
        """Mark this list as deleted and cascade to all items."""
        self.deleted_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        # Cascade soft delete to all items
        for item in self.items:
            item.soft_delete()

    def restore(self) -> None:
        """Restore this list from trash and cascade to all items."""
        self.deleted_at = None
        self.updated_at = datetime.now(timezone.utc)

        # Cascade restore to all items
        for item in self.items:
            item.restore()

    @property
    def is_deleted(self) -> bool:
        """Check if this list is soft deleted."""
        return self.deleted_at is not None

    @classmethod
    def active(cls):
        """Query for active (non-deleted) lists."""
        return cls.query.filter(cls.deleted_at.is_(None))

    @classmethod
    def deleted(cls):
        """Query for deleted lists (trash)."""
        return cls.query.filter(cls.deleted_at.isnot(None))


class ShoppingListItem(db.Model):
    """Shopping list item model."""

    __tablename__ = 'shopping_list_items'

    id = db.Column(db.Integer, primary_key=True)
    shopping_list_id = db.Column(db.Integer, db.ForeignKey('shopping_lists.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.String(50), nullable=False, default='1')
    is_checked = db.Column(db.Boolean, default=False, nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True, default=None, index=True)

    def __repr__(self) -> str:
        return f'<ShoppingListItem {self.name}>'

    def soft_delete(self) -> None:
        """Mark this item as deleted."""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore this item from trash."""
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        """Check if this item is soft deleted."""
        return self.deleted_at is not None

    @classmethod
    def active(cls):
        """Query for active (non-deleted) items."""
        return cls.query.filter(cls.deleted_at.is_(None))

    @classmethod
    def deleted(cls):
        """Query for deleted items (trash)."""
        return cls.query.filter(cls.deleted_at.isnot(None))

class RevokedToken(db.Model):
    """Revoked JWT tokens (Blacklist) for logout and token invalidation."""

    __tablename__ = 'revoked_tokens'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(20), nullable=False)  # 'access' or 'refresh'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    revoked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self) -> str:
        return f'<RevokedToken {self.jti}>'

    @classmethod
    def is_jti_blacklisted(cls, jti: str) -> bool:
        """Check if a token's JTI is blacklisted."""
        return cls.query.filter_by(jti=jti).first() is not None

    @classmethod
    def add_to_blacklist(cls, jti: str, token_type: str, user_id: int, expires_at: datetime) -> None:
        """Add a token to the blacklist."""
        revoked_token = cls(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(revoked_token)
        db.session.commit()

    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """Remove expired tokens from the blacklist. Returns count of deleted tokens."""
        now = datetime.now(timezone.utc)
        deleted = cls.query.filter(cls.expires_at < now).delete()
        db.session.commit()
        return deleted


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    # Flask-Login erwartet hier die Rückgabe eines User-Objekts oder None
    return User.query.get(int(user_id))

