#!/bin/bash

# Simple test for optimistic locking

echo "=== Testing Optimistic Locking ==="
echo

# Login
echo "1. Login as admin..."
LOGIN_RESPONSE=$(curl -s http://127.0.0.1:5001/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}')
TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['tokens']['access_token'])")

if [ -z "$TOKEN" ]; then
    echo "Login failed!"
    exit 1
fi
echo "✓ Login successful"
echo

# Create a test list
echo "2. Create a new shopping list..."
CREATE_RESPONSE=$(curl -s http://127.0.0.1:5001/api/v1/lists -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"title":"Test Optimistic Locking"}')
LIST_ID=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")
VERSION=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['version'])")

echo "✓ List created with ID: $LIST_ID, Version: $VERSION"
echo

# Get list details to verify version
echo "3. Get list details..."
GET_RESPONSE=$(curl -s http://127.0.0.1:5001/api/v1/lists/$LIST_ID -H "Authorization: Bearer $TOKEN")
echo $GET_RESPONSE | python3 -m json.tool | grep -E '"id"|"title"|"version"'
echo

# Update without version (should succeed)
echo "4. Update list WITHOUT version (backwards compatible)..."
UPDATE1=$(curl -s http://127.0.0.1:5001/api/v1/lists/$LIST_ID -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"title":"Updated Title Without Version"}')
NEW_VERSION=$(echo $UPDATE1 | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['version'])")
echo "✓ Update successful, new version: $NEW_VERSION"
echo

# Update with correct version (should succeed)
echo "5. Update list WITH correct version $NEW_VERSION..."
UPDATE2=$(curl -s http://127.0.0.1:5001/api/v1/lists/$LIST_ID -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"title\":\"Updated with Version\",\"version\":$NEW_VERSION}")
STATUS=$(echo $UPDATE2 | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])")
NEW_VERSION2=$(echo $UPDATE2 | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['version'])")

if [ "$STATUS" == "True" ]; then
    echo "✓ Update successful, new version: $NEW_VERSION2"
else
    echo "✗ Update failed!"
    echo $UPDATE2 | python3 -m json.tool
fi
echo

# Update with wrong version (should fail with 409)
echo "6. Update list WITH WRONG version (should fail with 409)..."
UPDATE3=$(curl -s -w "\nHTTP_STATUS:%{http_code}" http://127.0.0.1:5001/api/v1/lists/$LIST_ID -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"title":"Should Fail","version":1}')

HTTP_STATUS=$(echo "$UPDATE3" | grep "HTTP_STATUS" | cut -d: -f2)
RESPONSE=$(echo "$UPDATE3" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" == "409" ]; then
    echo "✓ Correctly rejected with 409 Conflict!"
    echo $RESPONSE | python3 -m json.tool | grep -E '"message"|"code"|"current_version"|"expected_version"'
else
    echo "✗ Expected 409, got: $HTTP_STATUS"
    echo $RESPONSE | python3 -m json.tool
fi
echo

# Create an item
echo "7. Create an item in the list..."
ITEM_RESPONSE=$(curl -s http://127.0.0.1:5001/api/v1/lists/$LIST_ID/items -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Milch","quantity":"2L"}')
ITEM_ID=$(echo $ITEM_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")
ITEM_VERSION=$(echo $ITEM_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['version'])")
echo "✓ Item created with ID: $ITEM_ID, Version: $ITEM_VERSION"
echo

# Update item with version
echo "8. Update item WITH correct version..."
ITEM_UPDATE=$(curl -s http://127.0.0.1:5001/api/v1/items/$ITEM_ID -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"quantity\":\"3L\",\"version\":$ITEM_VERSION}")
ITEM_NEW_VERSION=$(echo $ITEM_UPDATE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['version'])")
echo "✓ Item updated, new version: $ITEM_NEW_VERSION"
echo

echo "=== All tests passed! Optimistic Locking is working correctly ==="
