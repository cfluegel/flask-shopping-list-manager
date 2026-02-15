# Test Suite - Flask Grocery Shopping List

## Übersicht

Umfassende pytest Test-Suite für die Flask Grocery Shopping List REST API mit JWT-Authentifizierung.

## Schnellstart

### Installation der Test-Dependencies

```bash
# Virtual Environment aktivieren
source venv/bin/activate

# Dependencies installieren (wenn noch nicht geschehen)
pip install -r requirements.txt
```

### Tests ausführen

```bash
# Alle Tests ausführen
pytest tests/

# Mit detailliertem Output
pytest tests/ -v

# Mit Coverage Report
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Coverage Report im Browser öffnen
open htmlcov/index.html
```

## Test-Kategorien

### Nach Marker filtern

```bash
# Nur Authentication Tests
pytest tests/ -m auth

# Nur Admin Tests
pytest tests/ -m admin

# Nur Permission Tests
pytest tests/ -m permissions

# Nur API Tests
pytest tests/ -m api

# Nur Model Tests
pytest tests/ -m models

# Nur Soft Delete Tests
pytest tests/ -m soft_delete

# Nur Optimistic Locking Tests
pytest tests/ -m optimistic_locking

# Nur Sharing Tests
pytest tests/ -m sharing

# Ohne Slow Tests
pytest tests/ -m "not slow"
```

### Nach Datei filtern

```bash
# Nur Authentication Tests
pytest tests/test_auth.py

# Nur Model Tests
pytest tests/test_models.py

# Nur Shopping List Tests
pytest tests/test_lists.py

# Nur Shopping List Item Tests
pytest tests/test_items.py

# Nur Admin Tests
pytest tests/test_admin.py

# Nur Permission Tests
pytest tests/test_permissions.py

# Nur Sharing Tests
pytest tests/test_sharing.py

# Nur Optimistic Locking Tests
pytest tests/test_optimistic_locking.py

# Nur Soft Delete Tests
pytest tests/test_soft_delete.py
```

### Spezifische Tests ausführen

```bash
# Spezifische Test-Klasse
pytest tests/test_auth.py::TestRegistration

# Spezifischer Test
pytest tests/test_auth.py::TestRegistration::test_register_with_valid_data_returns_201

# Tests mit Namen-Pattern
pytest tests/ -k "register"
pytest tests/ -k "admin"
pytest tests/ -k "soft_delete"
```

## Test-Dateien

| Datei | Tests | Beschreibung |
|-------|-------|--------------|
| `conftest.py` | - | Fixtures (App, DB, Users, Lists, Items) |
| `test_auth.py` | 25 | Authentication (Register, Login, Token, Password) |
| `test_models.py` | 41 | Database Models (User, List, Item, RevokedToken) |
| `test_lists.py` | 30 | Shopping List CRUD API |
| `test_items.py` | 46 | Shopping List Item CRUD API |
| `test_admin.py` | 44 | Admin Endpoints (Users, Stats, Lists, Tokens) |
| `test_permissions.py` | 29 | Authorization & Access Control |
| `test_sharing.py` | 24 | Shared List Public Access |
| `test_optimistic_locking.py` | 21 | Version Control & Conflicts |
| `test_soft_delete.py` | 60 | Trash & Restore Functionality |
| `test_pwa.py` | 197 | PWA Blueprint, Routes, Templates, Service Worker |
| **GESAMT** | **518** | |

## Fixtures

### Application Fixtures

```python
app           # Flask App mit TestingConfig (in-memory SQLite)
client        # Test Client für HTTP Requests
runner        # CLI Test Runner
```

### User Fixtures

```python
admin_user              # Admin User (admin_test / AdminPass123)
regular_user            # Regular User (regular_test / UserPass123)
another_user            # Another User (another_test / AnotherPass123)

admin_headers           # JWT Authorization Headers für Admin
user_headers            # JWT Authorization Headers für Regular User
another_user_headers    # JWT Authorization Headers für Another User

admin_refresh_token     # JWT Refresh Token für Admin
user_refresh_token      # JWT Refresh Token für Regular User
```

### Shopping List Fixtures

```python
sample_list       # Standard Shopping List (owned by regular_user)
shared_list       # Shared Shopping List (owned by regular_user)
admin_list        # Admin's Shopping List (owned by admin_user)
deleted_list      # Soft-deleted Shopping List (owned by regular_user)
```

### Shopping List Item Fixtures

```python
sample_item       # Standard Item (in sample_list)
checked_item      # Checked Item (in sample_list)
deleted_item      # Soft-deleted Item (in sample_list)
multiple_items    # List of 5 Items (in sample_list)
```

### Token Fixtures

```python
revoked_token_data    # Revoked Token Data für Blacklist-Tests
```

## Test-Struktur

### AAA Pattern (Arrange, Act, Assert)

Alle Tests folgen dem AAA Pattern:

```python
def test_create_list_with_valid_data_returns_201(self, client, user_headers):
    """Test that creating a list with valid data returns 201."""
    # ARRANGE: Prepare test data
    data = {
        'title': 'Einkaufsliste Test',
        'is_shared': False
    }

    # ACT: Make request
    response = client.post('/api/v1/lists', json=data, headers=user_headers)

    # ASSERT: Verify response
    assert response.status_code == 201
    assert response.get_json()['success'] is True
    assert response.get_json()['data']['title'] == 'Einkaufsliste Test'
```

### Test-Klassen

Tests sind in Klassen organisiert:

```python
class TestRegistration:
    """Test user registration endpoint."""

    def test_register_with_valid_data_returns_201(self, client, app):
        """Test that registration with valid data returns 201 and tokens."""
        # Test implementation

    def test_register_with_duplicate_username_returns_409(self, client, admin_user):
        """Test that registration with duplicate username returns 409."""
        # Test implementation
```

## Debugging

### Ausführliche Output

```bash
# Mit Stack Traces
pytest tests/ -v --tb=long

# Mit lokalen Variablen
pytest tests/ -v -l

# Mit print-Statements
pytest tests/ -v -s

# Stop bei erstem Fehler
pytest tests/ -x

# Stop nach N Fehlern
pytest tests/ --maxfail=3
```

### Spezifische Tests debuggen

```bash
# Mit pdb (Python Debugger)
pytest tests/test_auth.py::TestLogin -v --pdb

# Mit ipdb (falls installiert)
pytest tests/test_auth.py::TestLogin -v --pdb --pdbcls=IPython.terminal.debugger:Pdb
```

## Coverage

### Coverage Report generieren

```bash
# Terminal Report
pytest tests/ --cov=app --cov-report=term-missing

# HTML Report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# XML Report (für CI/CD)
pytest tests/ --cov=app --cov-report=xml

# Alle Reports gleichzeitig
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml
```

### Coverage Ziele

| Komponente | Ziel | Aktuell | Status |
|------------|------|---------|--------|
| Models | 90%+ | 98% | ✅ |
| API v1 | 85%+ | 94%+ | ✅ |
| Decorators | 85%+ | 84% | ⚠️ |
| Overall | 80%+ | 73% | ⚠️ |

## Continuous Integration

### GitHub Actions Beispiel

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.13

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests with coverage
      run: |
        pytest tests/ --cov=app --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## Best Practices

### 1. Test Isolation

Jeder Test ist unabhängig und isoliert:
- Eigene Datenbank-Session per Test (in-memory SQLite)
- Fixtures werden pro Test neu erstellt
- Keine Abhängigkeiten zwischen Tests

### 2. Descriptive Test Names

Test-Namen beschreiben was getestet wird und das erwartete Ergebnis:

```python
def test_register_with_valid_data_returns_201(self, client, app):
    """Test that registration with valid data returns 201 and tokens."""
    # ✅ Gut: Klar was getestet wird

def test_register(self, client):
    # ❌ Schlecht: Unklar was getestet wird
```

### 3. Comprehensive Assertions

Tests prüfen mehrere Aspekte:

```python
# HTTP Status Code
assert response.status_code == 201

# Response Structure
data = response.get_json()
assert data['success'] is True
assert 'user' in data['data']
assert 'tokens' in data['data']

# Response Content
assert data['data']['user']['username'] == 'newuser'

# Database State
user = User.query.filter_by(username='newuser').first()
assert user is not None
```

### 4. Positive & Negative Tests

Tests decken sowohl Happy Path als auch Fehler-Szenarien:

```python
# Positive Test
def test_create_list_with_valid_data_returns_201(self, ...):
    """Test that creating a list with valid data succeeds."""

# Negative Tests
def test_create_list_with_empty_title_returns_400(self, ...):
    """Test that creating a list with empty title fails."""

def test_create_list_without_title_returns_400(self, ...):
    """Test that creating a list without title fails."""

def test_create_list_without_token_returns_401(self, ...):
    """Test that creating a list without authentication fails."""
```

## Troubleshooting

### Problem: Tests schlagen fehl mit "No module named 'app'"

**Lösung**: Virtual Environment aktivieren
```bash
source venv/bin/activate
```

### Problem: Tests schlagen fehl mit Datenbank-Errors

**Lösung**: Migrations sind nicht angewendet (sollte bei in-memory DB nicht passieren)
```bash
flask db upgrade
```

### Problem: Langsame Test-Ausführung

**Lösung**: Parallele Ausführung mit pytest-xdist
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

### Problem: ResourceWarnings

**Lösung**: Temporär, kann ignoriert werden. Um sie zu unterdrücken:
```bash
pytest tests/ -W ignore::ResourceWarning
```

## Weitere Ressourcen

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Flask Testing Documentation](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [TEST_SUMMARY.md](./TEST_SUMMARY.md) - Detaillierte Test-Zusammenfassung

## Support

Bei Fragen oder Problemen mit der Test-Suite:

1. Detaillierte Zusammenfassung lesen: `tests/TEST_SUMMARY.md`
2. pytest Documentation konsultieren
3. Tests mit `-v` und `--tb=long` ausführen für mehr Details
4. Spezifische Tests isoliert ausführen zum Debuggen
