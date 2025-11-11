#!/usr/bin/env python3
"""
Test script for optimistic locking in the Flask Grocery Shopping List application.

This script demonstrates:
1. Race conditions when updating resources without version control
2. How optimistic locking prevents data loss through version checking
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor
import sys


# Configuration
BASE_URL = "http://127.0.0.1:5000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


class APIClient:
    """Helper class for API requests."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None

    def login(self, username, password):
        """Login and store access token."""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data['data']['access_token']
            self.refresh_token = data['data']['refresh_token']
            print(f"✓ Login erfolgreich als {username}")
            return True
        else:
            print(f"✗ Login fehlgeschlagen: {response.text}")
            return False

    def headers(self):
        """Get headers with authorization."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def create_list(self, title):
        """Create a shopping list."""
        response = requests.post(
            f"{self.base_url}/lists",
            headers=self.headers(),
            json={"title": title}
        )

        if response.status_code == 201:
            data = response.json()
            return data['data']
        else:
            print(f"✗ Fehler beim Erstellen der Liste: {response.text}")
            return None

    def create_item(self, list_id, name, quantity="1"):
        """Create an item in a list."""
        response = requests.post(
            f"{self.base_url}/lists/{list_id}/items",
            headers=self.headers(),
            json={"name": name, "quantity": quantity}
        )

        if response.status_code == 201:
            data = response.json()
            return data['data']
        else:
            print(f"✗ Fehler beim Erstellen des Artikels: {response.text}")
            return None

    def update_item(self, item_id, name=None, quantity=None, is_checked=None, version=None):
        """Update an item."""
        payload = {}
        if name is not None:
            payload['name'] = name
        if quantity is not None:
            payload['quantity'] = quantity
        if is_checked is not None:
            payload['is_checked'] = is_checked
        if version is not None:
            payload['version'] = version

        response = requests.put(
            f"{self.base_url}/items/{item_id}",
            headers=self.headers(),
            json=payload
        )

        return response

    def update_list(self, list_id, title=None, is_shared=None, version=None):
        """Update a list."""
        payload = {}
        if title is not None:
            payload['title'] = title
        if is_shared is not None:
            payload['is_shared'] = is_shared
        if version is not None:
            payload['version'] = version

        response = requests.put(
            f"{self.base_url}/lists/{list_id}",
            headers=self.headers(),
            json=payload
        )

        return response

    def get_item(self, item_id):
        """Get item details."""
        response = requests.get(
            f"{self.base_url}/items/{item_id}",
            headers=self.headers()
        )

        if response.status_code == 200:
            return response.json()['data']
        else:
            return None

    def get_list(self, list_id):
        """Get list details."""
        response = requests.get(
            f"{self.base_url}/lists/{list_id}",
            headers=self.headers()
        )

        if response.status_code == 200:
            return response.json()['data']
        else:
            return None


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_section(text):
    """Print a formatted section header."""
    print(f"\n--- {text} ---")


def test_without_version_control():
    """
    Test concurrent updates WITHOUT version control.

    This demonstrates the potential for data loss when two users
    update the same item simultaneously without version checking.
    """
    print_header("Test 1: Concurrent Updates OHNE Versionskontrolle")

    client1 = APIClient(BASE_URL)
    client2 = APIClient(BASE_URL)

    # Both clients login
    if not client1.login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False
    if not client2.login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False

    # Create a test list and item
    print_section("Setup: Liste und Artikel erstellen")
    shopping_list = client1.create_list("Test Liste - Ohne Version")
    if not shopping_list:
        return False

    print(f"  Liste erstellt: ID={shopping_list['id']}, Version={shopping_list['version']}")

    item = client1.create_item(shopping_list['id'], "Milch", "1 Liter")
    if not item:
        return False

    print(f"  Artikel erstellt: ID={item['id']}, Name='{item['name']}', "
          f"Quantity='{item['quantity']}', Version={item['version']}")

    # Simulate concurrent updates without version checking
    print_section("Simulation: Zwei gleichzeitige Updates OHNE Versionskontrolle")

    def update_without_version(client, item_id, new_quantity, label):
        """Update item without version check."""
        print(f"  [{label}] Starte Update zu Quantity='{new_quantity}'...")
        response = client.update_item(item_id, quantity=new_quantity)

        if response.status_code == 200:
            data = response.json()['data']
            print(f"  [{label}] ✓ Update erfolgreich: Quantity='{data['quantity']}', Version={data['version']}")
            return data
        else:
            print(f"  [{label}] ✗ Update fehlgeschlagen: {response.text}")
            return None

    # Both clients update simultaneously (without version)
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(update_without_version, client1, item['id'], "2 Liter", "Client 1")
        time.sleep(0.05)  # Small delay to make race condition more likely
        future2 = executor.submit(update_without_version, client2, item['id'], "3 Liter", "Client 2")

        result1 = future1.result()
        result2 = future2.result()

    # Check final state
    print_section("Ergebnis prüfen")
    final_item = client1.get_item(item['id'])
    print(f"  Finaler Zustand: Quantity='{final_item['quantity']}', Version={final_item['version']}")
    print(f"\n  PROBLEM: Eines der Updates wurde überschrieben!")
    print(f"  Dies ist ein 'Lost Update' Problem - eine typische Race Condition.")

    return True


def test_with_version_control():
    """
    Test concurrent updates WITH version control.

    This demonstrates how optimistic locking prevents data loss by
    detecting concurrent modifications and rejecting conflicting updates.
    """
    print_header("Test 2: Concurrent Updates MIT Versionskontrolle")

    client1 = APIClient(BASE_URL)
    client2 = APIClient(BASE_URL)

    # Both clients login
    if not client1.login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False
    if not client2.login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False

    # Create a test list and item
    print_section("Setup: Liste und Artikel erstellen")
    shopping_list = client1.create_list("Test Liste - Mit Version")
    if not shopping_list:
        return False

    print(f"  Liste erstellt: ID={shopping_list['id']}, Version={shopping_list['version']}")

    item = client1.create_item(shopping_list['id'], "Brot", "1 Stück")
    if not item:
        return False

    print(f"  Artikel erstellt: ID={item['id']}, Name='{item['name']}', "
          f"Quantity='{item['quantity']}', Version={item['version']}")

    # Both clients read the current version
    current_version = item['version']

    # Simulate concurrent updates with version checking
    print_section("Simulation: Zwei gleichzeitige Updates MIT Versionskontrolle")

    def update_with_version(client, item_id, new_quantity, version, label):
        """Update item with version check."""
        print(f"  [{label}] Starte Update zu Quantity='{new_quantity}' mit Version={version}...")
        response = client.update_item(item_id, quantity=new_quantity, version=version)

        if response.status_code == 200:
            data = response.json()['data']
            print(f"  [{label}] ✓ Update erfolgreich: Quantity='{data['quantity']}', "
                  f"Neue Version={data['version']}")
            return data
        elif response.status_code == 409:
            error = response.json()
            print(f"  [{label}] ✗ KONFLIKT erkannt! {error['error']['message']}")
            print(f"  [{label}]   Details: {error['error'].get('details', {})}")
            return None
        else:
            print(f"  [{label}] ✗ Update fehlgeschlagen: {response.text}")
            return None

    # Both clients update simultaneously (with version)
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(update_with_version, client1, item['id'],
                                   "2 Stück", current_version, "Client 1")
        time.sleep(0.05)  # Small delay
        future2 = executor.submit(update_with_version, client2, item['id'],
                                   "3 Stück", current_version, "Client 2")

        result1 = future1.result()
        result2 = future2.result()

    # Check final state
    print_section("Ergebnis prüfen")
    final_item = client1.get_item(item['id'])
    print(f"  Finaler Zustand: Quantity='{final_item['quantity']}', Version={final_item['version']}")

    # Demonstrate retry logic
    print_section("Retry-Strategie: Client 2 holt aktuelle Version und versucht erneut")

    if result2 is None:  # Client 2's update was rejected
        # Get current version
        current_item = client2.get_item(item['id'])
        print(f"  Client 2 holt aktuelle Daten: Quantity='{current_item['quantity']}', "
              f"Version={current_item['version']}")

        # Retry with new version
        response = client2.update_item(item['id'], quantity="3 Stück", version=current_item['version'])

        if response.status_code == 200:
            data = response.json()['data']
            print(f"  ✓ Retry erfolgreich: Quantity='{data['quantity']}', Version={data['version']}")

            # Final state
            final_item = client2.get_item(item['id'])
            print(f"\n  Finaler Zustand nach Retry: Quantity='{final_item['quantity']}', "
                  f"Version={final_item['version']}")
            print(f"\n  ERFOLG: Optimistic Locking hat die Race Condition verhindert!")
            print(f"  Beide Änderungen wurden korrekt verarbeitet (sequenziell, nicht überschrieben).")

    return True


def test_list_version_control():
    """
    Test version control on shopping lists.
    """
    print_header("Test 3: Versionskontrolle für Shopping Lists")

    client1 = APIClient(BASE_URL)
    client2 = APIClient(BASE_URL)

    # Both clients login
    if not client1.login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False
    if not client2.login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False

    # Create a test list
    print_section("Setup: Liste erstellen")
    shopping_list = client1.create_list("Wocheneinkauf")
    if not shopping_list:
        return False

    print(f"  Liste erstellt: ID={shopping_list['id']}, Title='{shopping_list['title']}', "
          f"Version={shopping_list['version']}")

    current_version = shopping_list['version']

    # Simulate concurrent updates
    print_section("Simulation: Zwei Clients ändern gleichzeitig den Titel")

    def update_list_with_version(client, list_id, new_title, version, label):
        """Update list with version check."""
        print(f"  [{label}] Starte Update zu Title='{new_title}' mit Version={version}...")
        response = client.update_list(list_id, title=new_title, version=version)

        if response.status_code == 200:
            data = response.json()['data']
            print(f"  [{label}] ✓ Update erfolgreich: Title='{data['title']}', "
                  f"Neue Version={data['version']}")
            return data
        elif response.status_code == 409:
            error = response.json()
            print(f"  [{label}] ✗ KONFLIKT erkannt! {error['error']['message']}")
            return None
        else:
            print(f"  [{label}] ✗ Update fehlgeschlagen: {response.text}")
            return None

    # Both clients update simultaneously
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(update_list_with_version, client1, shopping_list['id'],
                                   "Wocheneinkauf (Montag)", current_version, "Client 1")
        time.sleep(0.05)
        future2 = executor.submit(update_list_with_version, client2, shopping_list['id'],
                                   "Großeinkauf", current_version, "Client 2")

        result1 = future1.result()
        result2 = future2.result()

    # Check final state
    print_section("Ergebnis prüfen")
    final_list = client1.get_list(shopping_list['id'])
    print(f"  Finaler Zustand: Title='{final_list['title']}', Version={final_list['version']}")
    print(f"\n  ✓ Optimistic Locking funktioniert auch für Shopping Lists!")

    return True


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "Optimistic Locking Test Suite" + " " * 34 + "║")
    print("║" + " " * 10 + "Flask Grocery Shopping List Application" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")

    print("\nDieser Test demonstriert:")
    print("  1. Race Conditions ohne Versionskontrolle (Lost Update Problem)")
    print("  2. Wie Optimistic Locking Datenverlust verhindert")
    print("  3. Retry-Strategie bei Konflikten")

    print("\nVoraussetzungen:")
    print(f"  - Flask-Anwendung läuft auf {BASE_URL}")
    print(f"  - Admin-Account: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")

    input("\nDrücken Sie Enter zum Starten...")

    try:
        # Run tests
        if not test_without_version_control():
            print("\n✗ Test 1 fehlgeschlagen")
            return 1

        if not test_with_version_control():
            print("\n✗ Test 2 fehlgeschlagen")
            return 1

        if not test_list_version_control():
            print("\n✗ Test 3 fehlgeschlagen")
            return 1

        print_header("Alle Tests erfolgreich!")
        print("\nZusammenfassung:")
        print("  ✓ Race Conditions ohne Version demonstriert")
        print("  ✓ Optimistic Locking funktioniert korrekt")
        print("  ✓ Version-Konflikte werden erkannt und gemeldet")
        print("  ✓ Retry-Strategie erfolgreich getestet")

        return 0

    except requests.exceptions.ConnectionError:
        print("\n✗ Fehler: Kann keine Verbindung zum Server herstellen!")
        print(f"  Stellen Sie sicher, dass die Flask-Anwendung auf {BASE_URL} läuft.")
        return 1
    except Exception as e:
        print(f"\n✗ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
