# Grocery Shopping List API Documentation

## Overview

The Grocery Shopping List API is a comprehensive RESTful API for managing grocery shopping lists with sharing capabilities. This API provides secure, JWT-based authentication and supports mobile applications with features like list sharing, soft delete/restore functionality, and role-based access control.

**Base URL**: `http://localhost:5000/api/v1`
**API Version**: 1.0.0
**Interactive Documentation**: `http://localhost:5000/api/v1/docs/`

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Pagination](#pagination)
6. [API Endpoints](#api-endpoints)
7. [Code Examples](#code-examples)
8. [Common Workflows](#common-workflows)
9. [Troubleshooting](#troubleshooting)

## Getting Started

### Interactive API Documentation

The easiest way to explore and test the API is through the interactive Swagger UI:

```
http://localhost:5000/api/v1/docs/
```

The Swagger UI provides:
- Complete endpoint documentation
- Interactive "Try it out" functionality
- Request/response examples
- Schema definitions
- Authentication testing

### Quick Start Example

1. **Register a new account:**
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "password_confirm": "password123"
  }'
```

2. **Login to get tokens:**
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

3. **Create a shopping list:**
```bash
curl -X POST http://localhost:5000/api/v1/lists \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Weekly Groceries"
  }'
```

## Authentication

The API uses JWT (JSON Web Token) authentication with two types of tokens:

### Token Types

1. **Access Token**
   - Used for authenticating API requests
   - Expires after 15 minutes
   - Include in Authorization header: `Bearer <access_token>`

2. **Refresh Token**
   - Used to obtain new access tokens
   - Expires after 30 days
   - Sent to `/auth/refresh` endpoint

### Authentication Flow

```
┌─────────┐                ┌─────────┐
│ Client  │                │   API   │
└────┬────┘                └────┬────┘
     │                          │
     │  POST /auth/login        │
     │─────────────────────────>│
     │                          │
     │  {access_token,          │
     │   refresh_token}         │
     │<─────────────────────────│
     │                          │
     │  GET /lists              │
     │  Authorization: Bearer   │
     │─────────────────────────>│
     │                          │
     │  {lists data}            │
     │<─────────────────────────│
     │                          │
     │  (15 min later)          │
     │  401 Unauthorized        │
     │<─────────────────────────│
     │                          │
     │  POST /auth/refresh      │
     │  Authorization: Bearer   │
     │  (refresh_token)         │
     │─────────────────────────>│
     │                          │
     │  {new access_token}      │
     │<─────────────────────────│
```

### Authentication Endpoints

#### Register
- **Endpoint**: `POST /auth/register`
- **Rate Limit**: 5 requests per hour
- **Request Body**:
```json
{
  "username": "string (3-80 characters)",
  "email": "string (valid email)",
  "password": "string (min 6 characters)",
  "password_confirm": "string"
}
```
- **Response** (201):
```json
{
  "success": true,
  "message": "Registrierung erfolgreich",
  "data": {
    "user": {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com",
      "is_admin": false,
      "created_at": "2025-11-10T10:30:00Z"
    },
    "tokens": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
  }
}
```

#### Login
- **Endpoint**: `POST /auth/login`
- **Rate Limit**: 5 requests per minute
- **Request Body**:
```json
{
  "username": "testuser",
  "password": "password123"
}
```

#### Refresh Token
- **Endpoint**: `POST /auth/refresh`
- **Headers**: `Authorization: Bearer <refresh_token>`
- **Response** (200):
```json
{
  "success": true,
  "message": "Token erfolgreich erneuert",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

#### Logout
- **Endpoint**: `POST /auth/logout`
- **Headers**: `Authorization: Bearer <access_token>`
- **Description**: Revokes the current access token

#### Change Password
- **Endpoint**: `POST /auth/change-password`
- **Rate Limit**: 5 requests per hour
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body**:
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass123",
  "new_password_confirm": "newpass123"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

| Endpoint Category | Rate Limit |
|------------------|------------|
| Registration | 5 requests per hour |
| Login | 5 requests per minute |
| Password Changes | 5 requests per hour |
| General Operations | 30 requests per minute |
| Admin Operations | 20 requests per hour |

### Rate Limit Response Headers

Every API response includes rate limiting information in the headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-RateLimit-Limit` | Maximum number of requests allowed in the time window | `5` |
| `X-RateLimit-Remaining` | Number of requests remaining in the current window | `4` |
| `X-RateLimit-Reset` | Unix timestamp when the rate limit window resets | `1762844996` |
| `Retry-After` | Number of seconds to wait before retrying (seconds) | `60` |

**Example Response Headers:**
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1762844996
Retry-After: 60
```

### Handling Rate Limits

**Best Practices:**
1. **Monitor headers**: Check `X-RateLimit-Remaining` before making requests
2. **Respect limits**: Stop making requests when `X-RateLimit-Remaining` reaches 0
3. **Wait appropriately**: Use `Retry-After` header value to determine wait time
4. **Implement backoff**: Use exponential backoff for retries after rate limit errors
5. **Cache responses**: Cache GET responses to reduce API calls

**Example Implementation (JavaScript):**
```javascript
async function makeAPIRequest(url, options) {
  const response = await fetch(url, options);

  // Check rate limit headers
  const remaining = parseInt(response.headers.get('X-RateLimit-Remaining'));
  const reset = parseInt(response.headers.get('X-RateLimit-Reset'));

  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After'));
    console.log(`Rate limit exceeded. Retry after ${retryAfter} seconds.`);

    // Wait and retry
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    return makeAPIRequest(url, options);
  }

  // Warn when approaching limit
  if (remaining < 2) {
    console.warn(`Approaching rate limit. ${remaining} requests remaining.`);
  }

  return response;
}
```

**Example Implementation (Python):**
```python
import time
import requests

def make_api_request(url, headers=None):
    response = requests.get(url, headers=headers)

    # Check rate limit headers
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    reset = int(response.headers.get('X-RateLimit-Reset', 0))

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limit exceeded. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return make_api_request(url, headers)

    # Warn when approaching limit
    if remaining < 2:
        print(f"Warning: Only {remaining} requests remaining")

    return response
```

### Rate Limit Error Response

When rate limit is exceeded, the API returns:
```json
{
  "error": "Ratenbegrenzung überschritten",
  "message": "Sie haben zu viele Anfragen gesendet. Bitte versuchen Sie es später erneut."
}
```
**Status Code**: 429 Too Many Requests

## Error Handling

All error responses follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}  // Optional additional information
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `INVALID_CREDENTIALS` | 401 | Invalid username or password |
| `UNAUTHORIZED` | 401 | Authentication required |
| `TOKEN_EXPIRED` | 401 | JWT token has expired |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `LIST_NOT_SHARED` | 404 | List is not shared |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

### Error Examples

**Validation Error (400):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validierungsfehler",
    "details": {
      "username": ["Field is required"],
      "password": ["Must be at least 6 characters"]
    }
  }
}
```

**Unauthorized (401):**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

**Not Found (404):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Einkaufsliste nicht gefunden"
  }
}
```

## Pagination

List endpoints support pagination with query parameters:

### Query Parameters
- `page` (integer, default: 1): Page number
- `per_page` (integer, default: 20, max: 100): Items per page

### Response Format
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### Example Request
```bash
curl -X GET "http://localhost:5000/api/v1/lists?page=2&per_page=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login and get tokens | No |
| POST | `/auth/refresh` | Refresh access token | Yes (refresh token) |
| POST | `/auth/logout` | Logout and revoke token | Yes |
| POST | `/auth/logout-all` | Revoke all tokens | Yes |
| GET | `/auth/me` | Get current user info | Yes |
| PUT | `/auth/me` | Update current user | Yes |
| POST | `/auth/change-password` | Change password | Yes |

### User Management (Admin Only)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/users` | Get all users (paginated) | Yes (Admin) |
| POST | `/users` | Create new user | Yes (Admin) |
| GET | `/users/{id}` | Get user by ID | Yes (Self or Admin) |
| PUT | `/users/{id}` | Update user | Yes (Self or Admin) |
| DELETE | `/users/{id}` | Delete user | Yes (Admin) |
| GET | `/users/{id}/lists` | Get user's lists | Yes (Self or Admin) |

### Shopping Lists

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/lists` | Get current user's lists | Yes |
| POST | `/lists` | Create new list | Yes |
| GET | `/lists/{id}` | Get list with items | Yes (Owner/Admin/Shared) |
| PUT | `/lists/{id}` | Update list | Yes (Owner/Admin) |
| DELETE | `/lists/{id}` | Delete list (soft delete) | Yes (Owner/Admin) |
| POST | `/lists/{id}/restore` | Restore deleted list | Yes (Owner/Admin) |
| POST | `/lists/{id}/share` | Toggle sharing status | Yes (Owner/Admin) |
| GET | `/lists/{id}/share-url` | Get share URL | Yes (Owner/Admin) |

### List Items

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/lists/{list_id}/items` | Get all items in list | Yes |
| POST | `/lists/{list_id}/items` | Add item to list | Yes |
| POST | `/lists/{list_id}/items/clear-checked` | Remove checked items | Yes (Owner/Admin) |
| GET | `/items/{id}` | Get item details | Yes |
| PUT | `/items/{id}` | Update item | Yes |
| DELETE | `/items/{id}` | Delete item (soft delete) | Yes |
| POST | `/items/{id}/restore` | Restore deleted item | Yes |
| POST | `/items/{id}/toggle` | Toggle checked status | Yes |
| PUT | `/items/{id}/reorder` | Change item order | Yes (Owner/Admin) |

### Shared Lists (Public Access)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/shared/{guid}` | Get shared list with items | No |
| GET | `/shared/{guid}/items` | Get shared list items only | No |
| GET | `/shared/{guid}/info` | Get shared list info | No |

### Trash/Recycle Bin

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/trash/lists` | Get deleted lists | Yes |
| DELETE | `/trash/lists/{id}` | Permanently delete list | Yes (Admin) |
| GET | `/trash/items` | Get deleted items | Yes |

### Admin Operations

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/stats` | Get system statistics | Yes (Admin) |
| GET | `/admin/lists` | Get all lists from all users | Yes (Admin) |
| DELETE | `/admin/lists/{id}` | Delete any list | Yes (Admin) |
| POST | `/admin/tokens/cleanup` | Cleanup expired tokens | Yes (Admin) |
| GET | `/admin/tokens/stats` | Get token statistics | Yes (Admin) |
| GET | `/admin/users/{id}/activity` | Get user activity stats | Yes (Admin) |

## Code Examples

### JavaScript (Fetch API)

```javascript
// Register
async function register(username, email, password) {
  const response = await fetch('http://localhost:5000/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username,
      email,
      password,
      password_confirm: password
    })
  });

  const data = await response.json();
  if (data.success) {
    // Store tokens
    localStorage.setItem('access_token', data.data.tokens.access_token);
    localStorage.setItem('refresh_token', data.data.tokens.refresh_token);
  }
  return data;
}

// Create shopping list
async function createList(title, isShared = false) {
  const accessToken = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:5000/api/v1/lists', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({ title, is_shared: isShared })
  });

  return await response.json();
}

// Add item to list
async function addItem(listId, name, quantity = '1') {
  const accessToken = localStorage.getItem('access_token');

  const response = await fetch(`http://localhost:5000/api/v1/lists/${listId}/items`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({ name, quantity })
  });

  return await response.json();
}

// Toggle item checked status
async function toggleItem(itemId) {
  const accessToken = localStorage.getItem('access_token');

  const response = await fetch(`http://localhost:5000/api/v1/items/${itemId}/toggle`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  return await response.json();
}

// Refresh access token
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');

  const response = await fetch('http://localhost:5000/api/v1/auth/refresh', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${refreshToken}`
    }
  });

  const data = await response.json();
  if (data.success) {
    localStorage.setItem('access_token', data.data.access_token);
  }
  return data;
}
```

### Python (requests)

```python
import requests
from typing import Optional, Dict, Any

class GroceryListAPI:
    def __init__(self, base_url: str = "http://localhost:5000/api/v1"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def _headers(self, auth: bool = True) -> Dict[str, str]:
        """Get headers with optional authentication."""
        headers = {"Content-Type": "application/json"}
        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "password_confirm": password
            },
            headers=self._headers(auth=False)
        )
        data = response.json()

        if data.get("success"):
            self.access_token = data["data"]["tokens"]["access_token"]
            self.refresh_token = data["data"]["tokens"]["refresh_token"]

        return data

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and get tokens."""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
            headers=self._headers(auth=False)
        )
        data = response.json()

        if data.get("success"):
            self.access_token = data["data"]["tokens"]["access_token"]
            self.refresh_token = data["data"]["tokens"]["refresh_token"]

        return data

    def get_lists(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get current user's shopping lists."""
        response = requests.get(
            f"{self.base_url}/lists",
            params={"page": page, "per_page": per_page},
            headers=self._headers()
        )
        return response.json()

    def create_list(self, title: str, is_shared: bool = False) -> Dict[str, Any]:
        """Create a new shopping list."""
        response = requests.post(
            f"{self.base_url}/lists",
            json={"title": title, "is_shared": is_shared},
            headers=self._headers()
        )
        return response.json()

    def get_list(self, list_id: int) -> Dict[str, Any]:
        """Get a specific list with all items."""
        response = requests.get(
            f"{self.base_url}/lists/{list_id}",
            headers=self._headers()
        )
        return response.json()

    def add_item(self, list_id: int, name: str, quantity: str = "1") -> Dict[str, Any]:
        """Add an item to a shopping list."""
        response = requests.post(
            f"{self.base_url}/lists/{list_id}/items",
            json={"name": name, "quantity": quantity},
            headers=self._headers()
        )
        return response.json()

    def toggle_item(self, item_id: int) -> Dict[str, Any]:
        """Toggle item checked status."""
        response = requests.post(
            f"{self.base_url}/items/{item_id}/toggle",
            headers=self._headers()
        )
        return response.json()

    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token."""
        response = requests.post(
            f"{self.base_url}/auth/refresh",
            headers={"Authorization": f"Bearer {self.refresh_token}"}
        )
        data = response.json()

        if data.get("success"):
            self.access_token = data["data"]["access_token"]

        return data

# Usage example
if __name__ == "__main__":
    api = GroceryListAPI()

    # Register
    result = api.register("testuser", "test@example.com", "password123")
    print(f"Registered: {result.get('success')}")

    # Create list
    list_data = api.create_list("Weekly Groceries")
    list_id = list_data["data"]["id"]
    print(f"Created list: {list_id}")

    # Add items
    api.add_item(list_id, "Milk", "2 liters")
    api.add_item(list_id, "Eggs", "12 pieces")
    api.add_item(list_id, "Bread", "1 loaf")

    # Get list
    full_list = api.get_list(list_id)
    print(f"List has {len(full_list['data']['items'])} items")
```

### cURL

```bash
# Register
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "password_confirm": "password123"
  }'

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# Export access token for convenience
export ACCESS_TOKEN="your_access_token_here"

# Get lists
curl -X GET "http://localhost:5000/api/v1/lists?page=1&per_page=20" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Create list
curl -X POST http://localhost:5000/api/v1/lists \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "title": "Weekly Groceries",
    "is_shared": false
  }'

# Add item to list (replace {list_id})
curl -X POST http://localhost:5000/api/v1/lists/{list_id}/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "Milk",
    "quantity": "2 liters"
  }'

# Toggle item (replace {item_id})
curl -X POST http://localhost:5000/api/v1/items/{item_id}/toggle \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Share list (replace {list_id})
curl -X POST http://localhost:5000/api/v1/lists/{list_id}/share \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "is_shared": true
  }'

# Get share URL
curl -X GET http://localhost:5000/api/v1/lists/{list_id}/share-url \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Access shared list (no auth required, replace {guid})
curl -X GET http://localhost:5000/api/v1/shared/{guid}
```

## Common Workflows

### Complete Shopping Trip Workflow

```javascript
// 1. User registers/logs in
const loginResponse = await fetch('http://localhost:5000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user', password: 'pass' })
});
const { data: { tokens } } = await loginResponse.json();
const accessToken = tokens.access_token;

// 2. Create shopping list
const createListResponse = await fetch('http://localhost:5000/api/v1/lists', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({ title: 'Weekly Shopping' })
});
const { data: list } = await createListResponse.json();

// 3. Add items
const items = [
  { name: 'Milk', quantity: '2 liters' },
  { name: 'Bread', quantity: '1 loaf' },
  { name: 'Eggs', quantity: '12 pieces' }
];

for (const item of items) {
  await fetch(`http://localhost:5000/api/v1/lists/${list.id}/items`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify(item)
  });
}

// 4. While shopping - check off items
async function checkOffItem(itemId) {
  await fetch(`http://localhost:5000/api/v1/items/${itemId}/toggle`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
}

// 5. After shopping - clear checked items
await fetch(`http://localhost:5000/api/v1/lists/${list.id}/items/clear-checked`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
```

### List Sharing Workflow

```javascript
// 1. Create and populate list
const list = await createList('Party Supplies');
await addItem(list.id, 'Chips', '3 bags');
await addItem(list.id, 'Drinks', '2 liters');

// 2. Enable sharing
await fetch(`http://localhost:5000/api/v1/lists/${list.id}/share`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({ is_shared: true })
});

// 3. Get share URL
const shareResponse = await fetch(
  `http://localhost:5000/api/v1/lists/${list.id}/share-url`,
  {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  }
);
const { data: shareData } = await shareResponse.json();
console.log('Share URL:', shareData.full_web_url);

// 4. Others can now access without auth
const publicResponse = await fetch(
  `http://localhost:5000/api/v1/shared/${shareData.guid}`
);
const publicList = await publicResponse.json();
```

### Admin User Management Workflow

```javascript
// 1. Login as admin
const adminLogin = await fetch('http://localhost:5000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
});
const { data: { tokens: adminTokens } } = await adminLogin.json();

// 2. Get all users
const usersResponse = await fetch(
  'http://localhost:5000/api/v1/users?page=1&per_page=50',
  {
    headers: { 'Authorization': `Bearer ${adminTokens.access_token}` }
  }
);
const { data: users } = await usersResponse.json();

// 3. Get system statistics
const statsResponse = await fetch(
  'http://localhost:5000/api/v1/admin/stats',
  {
    headers: { 'Authorization': `Bearer ${adminTokens.access_token}` }
  }
);
const { data: stats } = await statsResponse.json();
console.log('Total users:', stats.users.total);
console.log('Total lists:', stats.lists.total);

// 4. View user activity
const activityResponse = await fetch(
  `http://localhost:5000/api/v1/admin/users/${userId}/activity`,
  {
    headers: { 'Authorization': `Bearer ${adminTokens.access_token}` }
  }
);
```

## Troubleshooting

### Common Issues

#### 401 Unauthorized

**Problem**: API returns 401 when making authenticated requests.

**Solutions**:
1. Check if access token is expired (15 minutes)
   ```javascript
   // Refresh token
   const refreshResponse = await fetch('/api/v1/auth/refresh', {
     method: 'POST',
     headers: { 'Authorization': `Bearer ${refreshToken}` }
   });
   ```

2. Verify token is included in Authorization header:
   ```
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
   ```

3. Check if token was revoked (logout)

#### 429 Rate Limit Exceeded

**Problem**: Too many requests to rate-limited endpoints.

**Solutions**:
1. Implement exponential backoff
2. Cache responses where appropriate
3. For login attempts, wait before retrying
4. Respect rate limit windows (shown in task description)

#### 404 List Not Found

**Problem**: Cannot access a shared list by GUID.

**Solutions**:
1. Verify the list is still shared (`is_shared: true`)
2. Check if GUID is correct (no typos)
3. Confirm list hasn't been deleted
4. If recently changed from shared to private, GUID was regenerated

#### Validation Errors (400)

**Problem**: Request fails with validation errors.

**Solutions**:
1. Check field lengths:
   - Username: 3-80 characters
   - Email: valid email format
   - Password: min 6 characters
   - List title: 1-200 characters
   - Item name: 1-200 characters
   - Quantity: max 50 characters

2. Verify required fields are present
3. Ensure password confirmation matches

#### CORS Errors (Browser)

**Problem**: Browser blocks API requests due to CORS.

**Solutions**:
1. Verify API is configured for your origin (see `config.py`)
2. Check CORS headers in response
3. For development, ensure both frontend and backend use same domain or configure CORS properly

### Debug Tips

1. **Enable logging**: Check `logs/app.log` for detailed error information

2. **Use Swagger UI**: Test endpoints interactively at `/api/v1/docs/`

3. **Check response headers**: Look for rate limit information

4. **Validate JSON**: Ensure request body is valid JSON

5. **Test with cURL**: Simplify by testing with cURL first

6. **Check database state**: Use Flask shell to inspect database:
   ```bash
   flask shell
   >>> from app.models import User, ShoppingList
   >>> User.query.all()
   ```

### Getting Help

1. Check the interactive Swagger documentation: `/api/v1/docs/`
2. Review this documentation
3. Check application logs in `logs/app.log`
4. Verify your request format matches the examples
5. Test with the default admin account: `admin` / `admin123`

## Security Best Practices

1. **Store tokens securely**:
   - Use httpOnly cookies in web apps
   - Use secure storage in mobile apps (Keychain/Keystore)
   - Never expose tokens in URLs or logs

2. **Handle token expiration**:
   - Implement automatic token refresh
   - Handle 401 responses gracefully
   - Re-authenticate when refresh token expires

3. **Use HTTPS in production**:
   - All API calls should use HTTPS
   - Tokens are JWTs but still should be protected

4. **Validate input**:
   - Client-side validation improves UX
   - Server always validates (never trust client)

5. **Logout properly**:
   - Call `/auth/logout` before clearing tokens
   - Use `/auth/logout-all` for security events

## Appendix

### Data Models

#### User
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_admin": false,
  "created_at": "2025-11-10T10:30:00Z"
}
```

#### Shopping List
```json
{
  "id": 1,
  "guid": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Weekly Groceries",
  "is_shared": false,
  "owner_id": 1,
  "owner_username": "john_doe",
  "created_at": "2025-11-10T10:30:00Z",
  "updated_at": "2025-11-10T12:45:00Z",
  "item_count": 5
}
```

#### Shopping List Item
```json
{
  "id": 1,
  "name": "Milk",
  "quantity": "2 liters",
  "is_checked": false,
  "order_index": 5,
  "created_at": "2025-11-10T10:35:00Z"
}
```

### Version History

- **1.0.0** (2025-11-10): Initial API release
  - JWT authentication
  - CRUD operations for lists and items
  - List sharing via GUID
  - Soft delete/restore
  - Admin operations
  - Rate limiting
  - Comprehensive documentation

---

**Last Updated**: 2025-11-10
**API Version**: 1.0.0
**Documentation Version**: 1.0.0
