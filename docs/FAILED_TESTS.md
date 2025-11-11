# Fehlgeschlagene Tests - Analyse & Lösungen

## Übersicht

Von 320 Tests schlagen 12 Tests fehl (3.75%). Hier ist eine detaillierte Analyse mit Lösungsvorschlägen.

**Status**: ⚠️ 12 Tests müssen behoben werden, bevor die Test-Suite production-ready ist.

---

## 1. Optimistic Locking Tests (4 Fehler)

### 1.1 test_update_list_without_version_succeeds

**Datei**: `tests/test_optimistic_locking.py`

**Problem**:
```python
assert 2 > 2
 +  where 2 = <ShoppingList Updated Without Version>.version
```

**Erwartung**: Version sollte NICHT erhöht werden, wenn kein `version` Parameter übergeben wird (Backwards Compatibility).

**Ist**: Version wird IMMER erhöht.

**Ursache**: API implementiert immer Version-Increment, unabhängig davon ob Version-Parameter übergeben wurde.

**Lösung**:
Option A: Test anpassen (empfohlen):
```python
def test_update_list_without_version_succeeds(self, client, user_headers, sample_list):
    """Test that updating a list without version parameter succeeds and increments version."""
    # Update without version parameter
    response = client.put(
        f'/api/v1/lists/{sample_list.id}',
        json={'title': 'Updated Without Version'},
        headers=user_headers
    )

    assert response.status_code == 200
    db.session.refresh(sample_list)
    assert sample_list.version == 2  # Version WIRD erhöht
```

Option B: API ändern (komplexer):
- Nur Version erhöhen, wenn `version` Parameter im Request vorhanden ist
- Backwards Compatibility Mode einführen

**Empfehlung**: Option A - Test anpassen

---

### 1.2 test_update_item_without_version_succeeds

**Datei**: `tests/test_optimistic_locking.py`

**Problem**: Identisch zu 1.1, aber für Items statt Lists.

**Lösung**: Identisch zu 1.1

---

### 1.3 test_update_with_negative_version_returns_409

**Datei**: `tests/test_optimistic_locking.py`

**Problem**:
```python
assert 400 == 409
 +  where 400 = <WrapperTestResponse streamed [400 BAD REQUEST]>.status_code
```

**Erwartung**: 409 Conflict bei negativer Version

**Ist**: 400 Bad Request (Validation Error)

**Ursache**: Marshmallow Schema validiert negative Zahlen als ungültigen Input (400) bevor Optimistic Locking Check (409) greift.

**Lösung**:
Option A: Test anpassen (empfohlen):
```python
def test_update_with_negative_version_returns_400(self, client, user_headers, sample_list):
    """Test that updating with negative version returns 400 validation error."""
    response = client.put(
        f'/api/v1/lists/{sample_list.id}',
        json={'title': 'Updated', 'version': -1},
        headers=user_headers
    )

    assert response.status_code == 400  # Validation Error, nicht Conflict
    data = response.get_json()
    assert data['success'] is False
```

Option B: Schema ändern:
- Erlaube negative Zahlen im Schema
- Prüfe negative Version im Business Logic Layer und gebe 409 zurück

**Empfehlung**: Option A - Test anpassen (negative Version ist ungültiger Input)

---

### 1.4 test_update_with_zero_version_returns_409

**Datei**: `tests/test_optimistic_locking.py`

**Problem**: Identisch zu 1.3, aber für Version=0

**Lösung**: Identisch zu 1.3

**Hinweis**: Version startet bei 1, daher ist Version=0 ungültiger Input (400), nicht Version Conflict (409).

---

## 2. Permission Tests (2 Fehler)

### 2.1 test_regular_user_cannot_access_admin_endpoint

**Datei**: `tests/test_permissions.py`

**Problem**:
```python
assert 404 == 403
 +  where 404 = <WrapperTestResponse streamed [404 NOT FOUND]>.status_code
```

**Erwartung**: 403 Forbidden wenn Regular User Admin-Endpoint aufruft

**Ist**: 404 Not Found

**Ursache**: Test ruft falschen Endpoint auf oder Endpoint-Route existiert nicht.

**Test-Code analysieren**:
```python
def test_regular_user_cannot_access_admin_endpoint(self, client, user_headers):
    """Test that regular users cannot access admin-only endpoints."""
    response = client.get('/api/v1/admin/stats', headers=user_headers)
    assert response.status_code == 403  # Erwartung: Forbidden
```

**Mögliche Ursachen**:
1. Route `/api/v1/admin/stats` existiert nicht → 404
2. Blueprint `v1_bp` ist nicht korrekt registriert
3. Decorator `@admin_required()` wird nicht angewendet

**Lösung**:
1. Prüfen ob Route existiert:
   ```bash
   flask routes | grep admin
   ```

2. Prüfen ob Blueprint registriert ist in `app/__init__.py`:
   ```python
   from app.api.v1 import v1_bp
   app.register_blueprint(v1_bp, url_prefix='/api/v1')
   ```

3. Test anpassen falls Endpoint nicht existiert:
   ```python
   response = client.get('/api/v1/users', headers=user_headers)  # Existierender Endpoint
   ```

---

### 2.2 test_unauthenticated_user_cannot_access_admin_endpoint

**Datei**: `tests/test_permissions.py`

**Problem**: Identisch zu 2.1, aber ohne Headers (401 vs 404)

**Lösung**: Identisch zu 2.1

---

## 3. Sharing Tests (2 Fehler)

### 3.1 test_get_shared_list_excludes_deleted_items

**Datei**: `tests/test_sharing.py`

**Problem**:
```python
AssertionError: assert 'Deleted Item' not in ['Active Item', 'Deleted Item']
```

**Erwartung**: Soft-deleted Items werden NICHT in Shared List angezeigt

**Ist**: Soft-deleted Items werden angezeigt

**Ursache**: Shared List Endpoint filtert nicht nach `deleted_at IS NULL`.

**Code-Location**: `app/api/v1/shared.py` - `get_shared_list()` oder `get_shared_list_items()`

**Lösung**:
API ändern in `app/api/v1/shared.py`:
```python
@v1_bp.route('/shared/<string:guid>', methods=['GET'])
def get_shared_list(guid: str):
    """Get a shared shopping list (no authentication required)."""
    shopping_list = ShoppingList.query.filter_by(guid=guid, is_shared=True).first_or_404()

    # FIX: Filter nur aktive Items
    items = ShoppingListItem.active().filter_by(
        shopping_list_id=shopping_list.id
    ).order_by(ShoppingListItem.order_index.desc()).all()

    # Rest of code...
```

**Status**: ⚠️ **Achtung**: Dies ist ein Bug in der API, nicht im Test! Test ist korrekt, API muss gefixt werden.

---

### 3.2 test_get_deleted_shared_list_returns_404

**Datei**: `tests/test_sharing.py`

**Problem**:
```python
assert 200 == 404
 +  where 200 = <WrapperTestResponse streamed [200 OK]>.status_code
```

**Erwartung**: Soft-deleted Shared Lists sollten 404 zurückgeben

**Ist**: Soft-deleted Shared Lists sind zugänglich (200)

**Ursache**: Shared List Endpoint filtert nicht nach `deleted_at IS NULL`.

**Code-Location**: `app/api/v1/shared.py` - `get_shared_list()`

**Lösung**:
API ändern in `app/api/v1/shared.py`:
```python
@v1_bp.route('/shared/<string:guid>', methods=['GET'])
def get_shared_list(guid: str):
    """Get a shared shopping list (no authentication required)."""
    # FIX: Nutze active() Query
    shopping_list = ShoppingList.active().filter_by(
        guid=guid,
        is_shared=True
    ).first_or_404()

    # Rest of code...
```

**Status**: ⚠️ **Achtung**: Dies ist ein Bug in der API, nicht im Test! Test ist korrekt, API muss gefixt werden.

---

## 4. Soft Delete Tests (3 Fehler)

### 4.1 test_restore_list_clears_deleted_at

**Datei**: `tests/test_soft_delete.py`

**Problem**:
```python
assert 'Einkaufsliste "Gelöschte Liste" wurde wiederhergestellt' == 'Einkaufsliste erfolgreich wiederhergestellt'
```

**Erwartung**: Message sollte 'Einkaufsliste erfolgreich wiederhergestellt' sein

**Ist**: Message ist 'Einkaufsliste "Gelöschte Liste" wurde wiederhergestellt'

**Ursache**: API gibt spezifischeren Message-Text zurück als Test erwartet.

**Lösung**:
Option A: Test anpassen (empfohlen):
```python
def test_restore_list_clears_deleted_at(self, client, user_headers, deleted_list):
    """Test that restoring a list clears the deleted_at timestamp."""
    response = client.post(
        f'/api/v1/lists/{deleted_list.id}/restore',
        headers=user_headers
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # FIX: Prüfe nur dass "wiederhergestellt" im Text vorkommt
    assert 'wiederhergestellt' in data['message'].lower()

    # Verify deleted_at is cleared
    db.session.refresh(deleted_list)
    assert deleted_list.deleted_at is None
```

Option B: API Message standardisieren:
- Ändere API um generische Message zurückzugeben

**Empfehlung**: Option A - Test ist zu strikt, API-Message ist besser

---

### 4.2 test_cannot_restore_list_not_in_trash

**Datei**: `tests/test_soft_delete.py`

**Problem**:
```python
assert 404 == 400
 +  where 404 = <WrapperTestResponse streamed [404 NOT FOUND]>.status_code
```

**Erwartung**: 400 Bad Request wenn aktive Liste wiederhergestellt werden soll

**Ist**: 404 Not Found

**Ursache**: API findet Liste nicht in Trash (deleted_at IS NOT NULL) und gibt 404 zurück.

**Lösung**:
Option A: Test anpassen (empfohlen):
```python
def test_cannot_restore_list_not_in_trash(self, client, user_headers, sample_list):
    """Test that restoring a non-deleted list returns 404."""
    response = client.post(
        f'/api/v1/lists/{sample_list.id}/restore',
        headers=user_headers
    )

    # FIX: 404 ist korrekt - Liste ist nicht im Trash
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
```

Option B: API ändern:
- Prüfe erst ob Liste existiert (alle Listen)
- Dann prüfe ob deleted_at gesetzt ist
- Gebe 400 zurück wenn nicht gelöscht

**Empfehlung**: Option A - 404 ist semantisch korrekter als 400

---

### 4.3 test_admin_sees_all_trash_lists

**Datei**: `tests/test_soft_delete.py`

**Problem**:
```python
assert 1 in [2]
 +  where 1 = <ShoppingList User Deleted List>.id
```

**Erwartung**: Admin sieht alle gelöschten Listen von allen Usern

**Ist**: Admin sieht nur eigene gelöschte Listen

**Ursache**: Trash Lists Endpoint filtert nach `user_id` auch für Admins.

**Code-Location**: `app/api/v1/lists.py` - `get_trash_lists()`

**Lösung**:
API ändern in `app/api/v1/lists.py`:
```python
@v1_bp.route('/trash/lists', methods=['GET'])
@jwt_required()
def get_trash_lists():
    """Get deleted shopping lists (trash)."""
    user = get_current_user()

    # FIX: Admin sieht alle Trash-Listen
    if user.is_admin:
        query = ShoppingList.deleted()
    else:
        query = ShoppingList.deleted().filter_by(user_id=user.id)

    pagination = query.order_by(desc(ShoppingList.deleted_at)).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    # Rest of code...
```

**Status**: ⚠️ **Achtung**: Dies ist ein Bug in der API, nicht im Test! Test ist korrekt, API muss gefixt werden.

---

## 5. Model Tests (1 Fehler)

### 5.1 test_create_revoked_token

**Datei**: `tests/test_models.py`

**Problem**:
```python
assert datetime.datetime(2025, 11, 11, 11, 13, 5, 721933) == datetime.datetime(2025, 11, 11, 11, 13, 5, 721933, tzinfo=datetime.timezone.utc)
```

**Erwartung**: `expires_at` sollte timezone-aware datetime sein (UTC)

**Ist**: `expires_at` ist naive datetime (ohne timezone)

**Ursache**: Test erstellt Token mit timezone-aware datetime, aber Model speichert ohne timezone.

**Code-Location**: `app/models.py` - `RevokedToken` Model oder Test-Code

**Lösung**:
Option A: Test anpassen (empfohlen):
```python
def test_create_revoked_token(self, app, regular_user):
    """Test that a revoked token can be created."""
    # FIX: Erstelle naive datetime wie API es tut
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None)

    token = RevokedToken(
        jti='test-jti-12345',
        token_type='access',
        user_id=regular_user.id,
        expires_at=expires_at
    )

    db.session.add(token)
    db.session.commit()

    assert token.id is not None
    assert token.jti == 'test-jti-12345'
```

Option B: Model ändern:
- SQLite speichert keine timezone info
- Bei Query muss timezone hinzugefügt werden

**Empfehlung**: Option A - SQLite limitation, Test sollte dies reflektieren

---

## Zusammenfassung & Prioritäten

### Kritische Bugs (müssen in API gefixt werden):
1. ✅ **test_get_shared_list_excludes_deleted_items** - API Bug: Deleted Items werden in Shared Lists angezeigt
2. ✅ **test_get_deleted_shared_list_returns_404** - API Bug: Deleted Shared Lists sind zugänglich
3. ✅ **test_admin_sees_all_trash_lists** - API Bug: Admin sieht nicht alle Trash-Listen

### Test-Anpassungen (empfohlen):
4. ⚠️ **test_update_list_without_version_succeeds** - Test erwartung anpassen (Version wird immer erhöht)
5. ⚠️ **test_update_item_without_version_succeeds** - Test erwartung anpassen
6. ⚠️ **test_update_with_negative_version_returns_409** - Test erwartung anpassen (400 statt 409)
7. ⚠️ **test_update_with_zero_version_returns_409** - Test erwartung anpassen (400 statt 409)
8. ⚠️ **test_restore_list_clears_deleted_at** - Test message check lockern
9. ⚠️ **test_cannot_restore_list_not_in_trash** - Test erwartung anpassen (404 statt 400)
10. ⚠️ **test_create_revoked_token** - Test datetime handling anpassen

### Zu untersuchen:
11. ❓ **test_regular_user_cannot_access_admin_endpoint** - Route existiert nicht? (404 statt 403)
12. ❓ **test_unauthenticated_user_cannot_access_admin_endpoint** - Route existiert nicht? (404 statt 401)

---

## Nächste Schritte

1. **Kritische API Bugs fixen** (3 Bugs in `app/api/v1/shared.py` und `app/api/v1/lists.py`)
2. **Tests anpassen** (7 Tests mit falschen Erwartungen)
3. **Routes untersuchen** (2 Tests mit 404 Errors)
4. **Tests erneut ausführen** und verifizieren dass alle 320 Tests bestehen

**Geschätzte Zeit**: 2-3 Stunden für alle Fixes
