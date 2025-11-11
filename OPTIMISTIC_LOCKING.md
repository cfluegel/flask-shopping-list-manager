# Optimistic Locking - Implementation Guide

## Übersicht

Die Flask Grocery Shopping List API implementiert Optimistic Locking, um Race Conditions bei gleichzeitigen Updates zu verhindern. Dies schützt vor dem "Lost Update Problem", wenn mehrere Clients dieselbe Ressource gleichzeitig bearbeiten.

## Implementation

### Database Schema

Beide Models haben ein `version` Feld:

**shopping_lists Tabelle:**
```sql
version INTEGER NOT NULL DEFAULT 1
```

**shopping_list_items Tabelle:**
```sql
version INTEGER NOT NULL DEFAULT 1
```

### Model Methods

Jedes Model (ShoppingList und ShoppingListItem) hat zwei Methoden:

```python
def check_version(self, expected_version: int) -> None:
    """
    Check if the expected version matches the current version.

    Args:
        expected_version: The version the client expects

    Raises:
        ConflictError: If versions don't match (optimistic locking conflict)
    """
    from .api.errors import ConflictError

    if expected_version is not None and self.version != expected_version:
        raise ConflictError(
            'Die Ressource wurde zwischenzeitlich geändert. Bitte aktualisieren Sie und versuchen es erneut.',
            details={
                'current_version': self.version,
                'expected_version': expected_version
            }
        )

def increment_version(self) -> None:
    """Increment the version number for optimistic locking."""
    self.version += 1
```

### API Schemas

Update-Schemas haben ein optionales `version` Feld:

```python
class ShoppingListUpdateSchema(Schema):
    """Schema for updating a shopping list."""
    title = fields.Str(validate=validate.Length(min=1, max=200))
    is_shared = fields.Bool()
    version = fields.Int(required=False, validate=validate.Range(min=1))

class ShoppingListItemUpdateSchema(Schema):
    """Schema for updating a shopping list item."""
    name = fields.Str(validate=validate.Length(min=1, max=200))
    quantity = fields.Str(validate=validate.Length(max=50))
    is_checked = fields.Bool()
    version = fields.Int(required=False, validate=validate.Range(min=1))
```

### API Endpoints

Update-Endpoints prüfen die Version und inkrementieren sie:

```python
@v1_bp.route('/lists/<int:list_id>', methods=['PUT'])
def update_list(list_id: int):
    # ... validation ...

    # Check version for optimistic locking (if provided)
    if 'version' in validated_data:
        shopping_list.check_version(validated_data['version'])

    # ... update fields ...

    # Increment version after successful update
    shopping_list.increment_version()
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    # Log includes version
    current_app.logger.info(
        f'Benutzer "{user.username}" (ID: {user.id}) hat via API Liste '
        f'{list_id} aktualisiert (Version: {shopping_list.version})'
    )

    # Response includes new version
    return success_response(data={'version': shopping_list.version, ...})
```

## API Usage Examples

### GET Request - Version abrufen

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/lists/1
```

Response:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Wocheneinkauf",
    "version": 3,
    ...
  }
}
```

### PUT Request - OHNE Version (Backwards Compatible)

```bash
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Neuer Titel"}' \
  http://localhost:5000/api/v1/lists/1
```

Response (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Neuer Titel",
    "version": 4,
    ...
  }
}
```

### PUT Request - MIT Version (Optimistic Locking)

```bash
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type": application/json" \
  -d '{"title": "Neuer Titel", "version": 3}' \
  http://localhost:5000/api/v1/lists/1
```

**Erfolg (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Neuer Titel",
    "version": 4,
    ...
  }
}
```

**Konflikt (409 Conflict):**
```json
{
  "success": false,
  "error": {
    "message": "Die Ressource wurde zwischenzeitlich geändert. Bitte aktualisieren Sie und versuchen es erneut.",
    "code": "CONFLICT",
    "details": {
      "current_version": 5,
      "expected_version": 3
    }
  }
}
```

## Client Implementation Examples

### JavaScript/TypeScript (React Native/Expo)

```typescript
interface UpdateListParams {
  listId: number;
  title?: string;
  isShared?: boolean;
}

async function updateListWithOptimisticLocking(
  params: UpdateListParams,
  maxRetries: number = 3
): Promise<any> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      // 1. Fetch current version
      const currentList = await fetch(
        `/api/v1/lists/${params.listId}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      ).then(r => r.json());

      if (!currentList.success) {
        throw new Error('Failed to fetch current list');
      }

      // 2. Send update with current version
      const response = await fetch(
        `/api/v1/lists/${params.listId}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            title: params.title,
            is_shared: params.isShared,
            version: currentList.data.version  // Include version
          })
        }
      );

      const data = await response.json();

      // 3. Handle conflict
      if (response.status === 409) {
        console.log(`Conflict detected on attempt ${attempt + 1}, retrying...`);
        continue;  // Retry
      }

      if (!response.ok) {
        throw new Error(data.error?.message || 'Update failed');
      }

      return data;  // Success
    } catch (error) {
      if (attempt === maxRetries - 1) {
        throw error;  // Give up after max retries
      }
    }
  }

  throw new Error('Max retries exceeded');
}

// Usage
try {
  const result = await updateListWithOptimisticLocking({
    listId: 1,
    title: 'Updated Title'
  });
  console.log('Update successful:', result.data);
} catch (error) {
  console.error('Update failed:', error);
}
```

### Flutter/Dart

```dart
class ShoppingListApi {
  final String baseUrl;
  final String token;

  ShoppingListApi(this.baseUrl, this.token);

  Future<Map<String, dynamic>> updateListWithOptimisticLocking({
    required int listId,
    String? title,
    bool? isShared,
    int maxRetries = 3,
  }) async {
    for (int attempt = 0; attempt < maxRetries; attempt++) {
      try {
        // 1. Fetch current version
        final currentResponse = await http.get(
          Uri.parse('$baseUrl/lists/$listId'),
          headers: {'Authorization': 'Bearer $token'},
        );

        if (currentResponse.statusCode != 200) {
          throw Exception('Failed to fetch current list');
        }

        final currentData = jsonDecode(currentResponse.body);
        final currentVersion = currentData['data']['version'];

        // 2. Send update with current version
        final updateBody = <String, dynamic>{
          'version': currentVersion,
        };
        if (title != null) updateBody['title'] = title;
        if (isShared != null) updateBody['is_shared'] = isShared;

        final updateResponse = await http.put(
          Uri.parse('$baseUrl/lists/$listId'),
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
          body: jsonEncode(updateBody),
        );

        // 3. Handle conflict
        if (updateResponse.statusCode == 409) {
          print('Conflict detected on attempt ${attempt + 1}, retrying...');
          continue;  // Retry
        }

        if (updateResponse.statusCode != 200) {
          final errorData = jsonDecode(updateResponse.body);
          throw Exception(errorData['error']['message']);
        }

        return jsonDecode(updateResponse.body);  // Success
      } catch (e) {
        if (attempt == maxRetries - 1) {
          rethrow;  // Give up after max retries
        }
      }
    }

    throw Exception('Max retries exceeded');
  }
}

// Usage
final api = ShoppingListApi('http://localhost:5000/api/v1', token);
try {
  final result = await api.updateListWithOptimisticLocking(
    listId: 1,
    title: 'Updated Title',
  );
  print('Update successful: ${result['data']}');
} catch (e) {
  print('Update failed: $e');
}
```

## Testing

Ein Test-Skript demonstriert das Optimistic Locking:

```bash
python test_optimistic_locking.py
```

Dies zeigt:
1. Race Conditions ohne Versionskontrolle (Lost Update Problem)
2. Wie Optimistic Locking Datenverlust verhindert
3. Retry-Strategie bei Konflikten

## Audit Logging

Alle Update-Operationen loggen die Version:

```
INFO: Benutzer "admin" (ID: 1) hat via API Liste 5 aktualisiert (Version: 4)
INFO: Benutzer "john" (ID: 2) hat via API Artikel 42 aktualisiert (Version: 7)
```

Bei Konflikten wird der ConflictError automatisch geloggt durch den Error Handler.

## Backwards Compatibility

**Wichtig:** Das `version` Feld ist optional bei Updates. Bestehende Clients, die keine Version mitschicken, funktionieren weiterhin ohne Änderungen.

```json
PUT /api/v1/lists/1
{
  "title": "Neuer Titel"
}
```
→ Wird durchgeführt ohne Version-Check (wie bisher)

```json
PUT /api/v1/lists/1
{
  "title": "Neuer Titel",
  "version": 3
}
```
→ Wird nur durchgeführt wenn Version stimmt (409 bei Konflikt)

## Performance Impact

Optimistic Locking hat minimalen Performance-Overhead:
- Eine Integer-Spalte pro Tabelle
- Ein Integer-Vergleich pro Update
- Version-Inkrement ist O(1)

Im Gegensatz zu Pessimistic Locking (Locks) ist kein Blocking erforderlich.

## Best Practices

1. **Immer Version verwenden bei kritischen Updates**: Wenn Datenverlust verhindert werden muss
2. **Retry-Logik implementieren**: Mit exponentiellen Backoff bei Konflikten
3. **Max Retries limitieren**: Typisch 3-5 Versuche
4. **User informieren**: Bei wiederholten Konflikten dem User melden
5. **Merge-Strategie**: Bei Konflikten ggf. Änderungen mergen statt überschreiben

## Migration

Die Migration erstellt die `version` Spalten:

```bash
flask db upgrade
```

Existierende Datensätze erhalten automatisch `version=1`.
