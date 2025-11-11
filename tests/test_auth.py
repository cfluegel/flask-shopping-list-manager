"""
Tests for Authentication Endpoints.

Tests user registration, login, token refresh, logout, and password management.
"""

import pytest
import json
from flask_jwt_extended import decode_token

from app.models import User, RevokedToken
from app.extensions import db


# ============================================================================
# Registration Tests
# ============================================================================

class TestRegistration:
    """Test user registration endpoint."""

    def test_register_with_valid_data_returns_201(self, client, app):
        """Test that registration with valid data returns 201 and tokens."""
        response = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123'
        })

        assert response.status_code == 201
        data = response.get_json()

        assert data['success'] is True
        assert 'user' in data['data']
        assert 'tokens' in data['data']
        assert data['data']['user']['username'] == 'newuser'
        assert data['data']['user']['email'] == 'newuser@example.com'
        assert data['data']['user']['is_admin'] is False
        assert 'access_token' in data['data']['tokens']
        assert 'refresh_token' in data['data']['tokens']

        # Verify user was created in database
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.check_password('SecurePass123')

    def test_register_with_mismatched_passwords_returns_400(self, client, app):
        """Test that registration with mismatched passwords returns 400."""
        response = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'DifferentPass123'
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False
        assert 'Validierungsfehler' in data['error']['message']

    def test_register_with_duplicate_username_returns_409(self, client, app, regular_user):
        """Test that registration with existing username returns 409."""
        response = client.post('/api/v1/auth/register', json={
            'username': regular_user.username,  # Duplicate
            'email': 'different@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123'
        })

        assert response.status_code == 409
        data = response.get_json()

        assert data['success'] is False
        assert 'bereits vergeben' in data['error']['message']

    def test_register_with_duplicate_email_returns_409(self, client, app, regular_user):
        """Test that registration with existing email returns 409."""
        response = client.post('/api/v1/auth/register', json={
            'username': 'differentuser',
            'email': regular_user.email,  # Duplicate
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123'
        })

        assert response.status_code == 409
        data = response.get_json()

        assert data['success'] is False
        assert 'bereits registriert' in data['error']['message']

    def test_register_with_missing_fields_returns_400(self, client, app):
        """Test that registration with missing fields returns 400."""
        response = client.post('/api/v1/auth/register', json={
            'username': 'newuser'
            # Missing email, password, password_confirm
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False

    def test_register_with_short_password_returns_400(self, client, app):
        """Test that registration with short password returns 400."""
        response = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',  # Too short
            'password_confirm': '123'
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False

    def test_register_with_invalid_email_returns_400(self, client, app):
        """Test that registration with invalid email returns 400."""
        response = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'email': 'not-an-email',  # Invalid email
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123'
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False


# ============================================================================
# Login Tests
# ============================================================================

class TestLogin:
    """Test user login endpoint."""

    def test_login_with_valid_credentials_returns_200(self, client, app, regular_user):
        """Test that login with valid credentials returns 200 and tokens."""
        response = client.post('/api/v1/auth/login', json={
            'username': 'regular_test',
            'password': 'UserPass123'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'user' in data['data']
        assert 'tokens' in data['data']
        assert data['data']['user']['username'] == 'regular_test'
        assert 'access_token' in data['data']['tokens']
        assert 'refresh_token' in data['data']['tokens']

    def test_login_with_invalid_username_returns_401(self, client, app):
        """Test that login with non-existent username returns 401."""
        response = client.post('/api/v1/auth/login', json={
            'username': 'nonexistent',
            'password': 'SomePassword123'
        })

        assert response.status_code == 401
        data = response.get_json()

        assert data['success'] is False
        assert 'Ungültige Anmeldedaten' in data['error']['message']

    def test_login_with_invalid_password_returns_401(self, client, app, regular_user):
        """Test that login with wrong password returns 401."""
        response = client.post('/api/v1/auth/login', json={
            'username': 'regular_test',
            'password': 'WrongPassword123'
        })

        assert response.status_code == 401
        data = response.get_json()

        assert data['success'] is False
        assert 'Ungültige Anmeldedaten' in data['error']['message']

    def test_login_with_missing_fields_returns_400(self, client, app):
        """Test that login with missing fields returns 400."""
        response = client.post('/api/v1/auth/login', json={
            'username': 'testuser'
            # Missing password
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False

    def test_login_as_admin_user_returns_admin_flag(self, client, app, admin_user):
        """Test that logging in as admin sets is_admin flag correctly."""
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin_test',
            'password': 'AdminPass123'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['data']['user']['is_admin'] is True


# ============================================================================
# Token Refresh Tests
# ============================================================================

class TestTokenRefresh:
    """Test token refresh endpoint."""

    def test_refresh_with_valid_refresh_token_returns_200(self, client, app, user_refresh_token):
        """Test that token refresh with valid refresh token returns new access token."""
        response = client.post('/api/v1/auth/refresh', headers={
            'Authorization': f'Bearer {user_refresh_token}',
            'Content-Type': 'application/json'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'access_token' in data['data']

    def test_refresh_with_access_token_returns_422(self, client, app, user_headers):
        """Test that using access token for refresh returns 422."""
        response = client.post('/api/v1/auth/refresh', headers=user_headers)

        # JWT library returns 422 for wrong token type
        assert response.status_code == 422

    def test_refresh_with_invalid_token_returns_401(self, client, app):
        """Test that refresh with invalid token returns 401."""
        response = client.post('/api/v1/auth/refresh', headers={
            'Authorization': 'Bearer invalid-token',
            'Content-Type': 'application/json'
        })

        assert response.status_code in [401, 422]

    def test_refresh_without_token_returns_401(self, client, app):
        """Test that refresh without token returns 401."""
        response = client.post('/api/v1/auth/refresh', headers={
            'Content-Type': 'application/json'
        })

        assert response.status_code == 401


# ============================================================================
# Logout Tests
# ============================================================================

class TestLogout:
    """Test logout endpoint."""

    def test_logout_with_valid_token_returns_200(self, client, app, user_headers, regular_user):
        """Test that logout with valid token returns 200 and revokes token."""
        response = client.post('/api/v1/auth/logout', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'Logout erfolgreich' in data['message']

        # Verify token was added to blacklist
        # Extract JTI from token
        token = user_headers['Authorization'].split(' ')[1]
        decoded = decode_token(token)
        assert RevokedToken.is_jti_blacklisted(decoded['jti']) is True

    def test_logout_without_token_returns_401(self, client, app):
        """Test that logout without token returns 401."""
        response = client.post('/api/v1/auth/logout', headers={
            'Content-Type': 'application/json'
        })

        assert response.status_code == 401

    def test_logout_with_revoked_token_returns_401(self, client, app, revoked_token_data):
        """Test that logout with already revoked token returns 401."""
        # Add token to blacklist
        RevokedToken.add_to_blacklist(
            jti=revoked_token_data['jti'],
            token_type='access',
            user_id=revoked_token_data['user_id'],
            expires_at=revoked_token_data['expires_at']
        )

        response = client.post('/api/v1/auth/logout', headers={
            'Authorization': f"Bearer {revoked_token_data['token']}",
            'Content-Type': 'application/json'
        })

        assert response.status_code == 401


# ============================================================================
# Get Current User Tests
# ============================================================================

class TestGetCurrentUser:
    """Test get current user endpoint."""

    def test_get_current_user_with_valid_token_returns_200(self, client, app, user_headers, regular_user):
        """Test that getting current user info returns 200."""
        response = client.get('/api/v1/auth/me', headers=user_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['username'] == regular_user.username
        assert data['data']['email'] == regular_user.email
        assert data['data']['is_admin'] == regular_user.is_admin

    def test_get_current_user_without_token_returns_401(self, client, app):
        """Test that getting current user without token returns 401."""
        response = client.get('/api/v1/auth/me', headers={
            'Content-Type': 'application/json'
        })

        assert response.status_code == 401


# ============================================================================
# Update Current User Tests
# ============================================================================

class TestUpdateCurrentUser:
    """Test update current user endpoint."""

    def test_update_username_with_valid_data_returns_200(self, client, app, user_headers, regular_user):
        """Test that updating username with valid data returns 200."""
        response = client.put('/api/v1/auth/me', headers=user_headers, json={
            'username': 'updated_username'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['username'] == 'updated_username'

        # Verify in database
        db.session.refresh(regular_user)
        assert regular_user.username == 'updated_username'

    def test_update_email_with_valid_data_returns_200(self, client, app, user_headers, regular_user):
        """Test that updating email with valid data returns 200."""
        response = client.put('/api/v1/auth/me', headers=user_headers, json={
            'email': 'newemail@example.com'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['data']['email'] == 'newemail@example.com'

        # Verify in database
        db.session.refresh(regular_user)
        assert regular_user.email == 'newemail@example.com'

    def test_update_with_existing_username_returns_409(self, client, app, user_headers, another_user):
        """Test that updating to existing username returns 409."""
        response = client.put('/api/v1/auth/me', headers=user_headers, json={
            'username': another_user.username  # Already taken
        })

        assert response.status_code == 409
        data = response.get_json()

        assert data['success'] is False
        assert 'bereits vergeben' in data['error']['message']

    def test_update_with_existing_email_returns_409(self, client, app, user_headers, another_user):
        """Test that updating to existing email returns 409."""
        response = client.put('/api/v1/auth/me', headers=user_headers, json={
            'email': another_user.email  # Already taken
        })

        assert response.status_code == 409
        data = response.get_json()

        assert data['success'] is False
        assert 'bereits registriert' in data['error']['message']


# ============================================================================
# Change Password Tests
# ============================================================================

class TestChangePassword:
    """Test change password endpoint."""

    def test_change_password_with_valid_data_returns_200(self, client, app, user_headers, regular_user):
        """Test that changing password with valid data returns 200."""
        response = client.post('/api/v1/auth/change-password', headers=user_headers, json={
            'old_password': 'UserPass123',
            'new_password': 'NewSecurePass456',
            'new_password_confirm': 'NewSecurePass456'
        })

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert 'Passwort erfolgreich geändert' in data['message']

        # Verify password was changed
        db.session.refresh(regular_user)
        assert regular_user.check_password('NewSecurePass456') is True
        assert regular_user.check_password('UserPass123') is False

    def test_change_password_with_wrong_old_password_returns_401(self, client, app, user_headers):
        """Test that changing password with wrong old password returns 401."""
        response = client.post('/api/v1/auth/change-password', headers=user_headers, json={
            'old_password': 'WrongPassword',
            'new_password': 'NewSecurePass456',
            'new_password_confirm': 'NewSecurePass456'
        })

        assert response.status_code == 401
        data = response.get_json()

        assert data['success'] is False
        assert 'falsch' in data['error']['message'].lower()

    def test_change_password_with_mismatched_new_passwords_returns_400(self, client, app, user_headers):
        """Test that changing password with mismatched new passwords returns 400."""
        response = client.post('/api/v1/auth/change-password', headers=user_headers, json={
            'old_password': 'UserPass123',
            'new_password': 'NewSecurePass456',
            'new_password_confirm': 'DifferentPassword'
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False

    def test_change_password_with_short_new_password_returns_400(self, client, app, user_headers):
        """Test that changing password to short password returns 400."""
        response = client.post('/api/v1/auth/change-password', headers=user_headers, json={
            'old_password': 'UserPass123',
            'new_password': '123',  # Too short
            'new_password_confirm': '123'
        })

        assert response.status_code == 400
        data = response.get_json()

        assert data['success'] is False

    def test_change_password_without_token_returns_401(self, client, app):
        """Test that changing password without token returns 401."""
        response = client.post('/api/v1/auth/change-password', headers={
            'Content-Type': 'application/json'
        }, json={
            'old_password': 'SomePassword',
            'new_password': 'NewPassword123',
            'new_password_confirm': 'NewPassword123'
        })

        assert response.status_code == 401
