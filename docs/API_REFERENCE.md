# REST API Reference

## Base URL

```
/api/v1/
```

## Authentication

The API uses JWT (JSON Web Tokens) via `Authorization: Bearer <token>` headers.

### Obtain Tokens

```http
POST /api/v1/auth/login
Content-Type: application/json

{"username": "testuser", "password": "password123"}
```

Response:
```json
{
    "success": true,
    "data": {
        "user": {"id": 1, "username": "testuser", "is_admin": false},
        "tokens": {
            "access_token": "eyJ...",
            "refresh_token": "eyJ..."
        }
    }
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

---

## Response Format

**Success:**
```json
{"success": true, "data": { ... }}
```

**Error:**
```json
{"success": false, "error": "Error message", "error_code": "VALIDATION_ERROR"}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success (GET, PUT, DELETE) |
| `201` | Created (POST) |
| `400` | Bad Request / Validation error |
| `401` | Unauthorized (missing/invalid token) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Not Found |
| `409` | Conflict (optimistic locking version mismatch) |
| `429` | Rate limit exceeded |

---

## Endpoints

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Login, receive tokens |
| POST | `/auth/refresh` | Refresh | Refresh access token |
| POST | `/auth/logout` | Yes | Revoke current token |
| POST | `/auth/logout-all` | Yes | Revoke all user tokens |
| GET | `/auth/me` | Yes | Get current user |
| PUT | `/auth/me` | Yes | Update current user |
| POST | `/auth/change-password` | Yes | Change password |

### Shopping Lists

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/lists` | Yes | Get user's lists |
| POST | `/lists` | Yes | Create list |
| GET | `/lists/<id>` | Yes | Get list with items |
| PUT | `/lists/<id>` | Yes | Update list (supports `version` for optimistic locking) |
| DELETE | `/lists/<id>` | Yes | Soft-delete list |
| POST | `/lists/<id>/share` | Yes | Toggle sharing |
| GET | `/lists/<id>/share-url` | Yes | Get share URL |
| POST | `/lists/<id>/print` | Yes | Print list (ESC/POS) |
| POST | `/lists/<id>/restore` | Yes | Restore from trash |

### Shopping List Items

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/lists/<id>/items` | Yes | Get items for list |
| POST | `/lists/<id>/items` | Yes | Add item to list |
| GET | `/items/<id>` | Yes | Get single item |
| PUT | `/items/<id>` | Yes | Update item (supports `version`) |
| DELETE | `/items/<id>` | Yes | Soft-delete item |
| POST | `/items/<id>/toggle` | Yes | Toggle checked status |
| PUT | `/items/<id>/reorder` | Yes | Change item order |
| POST | `/lists/<id>/items/clear-checked` | Yes | Soft-delete all checked items |
| POST | `/items/<id>/restore` | Yes | Restore item from trash |

### Trash

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/trash/lists` | Yes | Get trashed lists |
| DELETE | `/trash/lists/<id>` | Yes | Permanently delete trashed list |
| GET | `/trash/items` | Yes | Get trashed items |

### Shared Lists (Public)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/shared/<guid>` | No | Get shared list with items |
| GET | `/shared/<guid>/items` | No | Get shared list items only |
| GET | `/shared/<guid>/info` | No | Get shared list metadata |

### Admin (admin role required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/stats` | System statistics |
| GET | `/admin/lists` | All lists from all users |
| DELETE | `/admin/lists/<id>` | Delete any list |
| POST | `/admin/tokens/cleanup` | Clean up expired tokens |
| GET | `/admin/tokens/stats` | Token statistics |
| GET | `/admin/users/<id>/activity` | User activity info |

### User Management (admin role required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users` | List all users |
| POST | `/users` | Create user |
| GET | `/users/<id>` | Get user details |
| PUT | `/users/<id>` | Update user |
| DELETE | `/users/<id>` | Delete user (cascades) |
| GET | `/users/<id>/lists` | Get user's lists |

---

## Rate Limiting

API endpoints are rate-limited. Rate limit headers are included in responses:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

Backend: configurable via `RATELIMIT_STORAGE_URL` (memory or Redis).

---

## Testing with curl

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['tokens']['access_token'])")

# Get lists
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/lists

# Create list
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Wocheneinkauf"}' \
  http://localhost:8000/api/v1/lists

# Get shared list (no auth)
curl http://localhost:8000/api/v1/shared/<guid>
```

---

## Further Reading

- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) — full German API documentation with detailed examples
- [API_DOCUMENTATION_EN.md](API_DOCUMENTATION_EN.md) — full English API documentation
