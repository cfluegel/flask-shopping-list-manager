"""
REST API Routes for Shopping List Application.

This API is prepared for future JWT-based authentication for mobile apps.
For now, it mirrors the main blueprint functionality but returns JSON responses.
"""

from datetime import datetime, timezone

from flask import abort, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import desc

from . import api_bp
from ..extensions import db
from ..models import ShoppingList, ShoppingListItem, User
from ..utils import check_list_access


# ============================================================================
# Status & Health Check
# ============================================================================

@api_bp.route('/status')
def status():
    """API health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'message': 'Grocery Shopping List API is running'
    })


# ============================================================================
# Shopping Lists API
# ============================================================================

@api_bp.route('/lists', methods=['GET'])
@login_required
def get_lists():
    """Get all shopping lists for the current user."""
    shopping_lists = current_user.shopping_lists.order_by(desc(ShoppingList.updated_at)).all()

    return jsonify({
        'success': True,
        'data': [
            {
                'id': sl.id,
                'guid': sl.guid,
                'title': sl.title,
                'is_shared': sl.is_shared,
                'created_at': sl.created_at.isoformat(),
                'updated_at': sl.updated_at.isoformat(),
                'item_count': sl.items.count()
            }
            for sl in shopping_lists
        ]
    })


@api_bp.route('/lists/<int:list_id>', methods=['GET'])
@login_required
def get_list(list_id: int):
    """Get a specific shopping list with all items."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    items = shopping_list.items.order_by(ShoppingListItem.order_index.desc()).all()

    return jsonify({
        'success': True,
        'data': {
            'id': shopping_list.id,
            'guid': shopping_list.guid,
            'title': shopping_list.title,
            'is_shared': shopping_list.is_shared,
            'owner': shopping_list.owner.username,
            'created_at': shopping_list.created_at.isoformat(),
            'updated_at': shopping_list.updated_at.isoformat(),
            'items': [
                {
                    'id': item.id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'is_checked': item.is_checked,
                    'order_index': item.order_index
                }
                for item in items
            ]
        }
    })


@api_bp.route('/lists', methods=['POST'])
@login_required
def create_list():
    """Create a new shopping list."""
    data = request.get_json()

    if not data or 'title' not in data:
        return jsonify({'success': False, 'error': 'Title is required'}), 400

    shopping_list = ShoppingList(
        title=data['title'],
        user_id=current_user.id,
        is_shared=data.get('is_shared', False)
    )
    db.session.add(shopping_list)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'id': shopping_list.id,
            'guid': shopping_list.guid,
            'title': shopping_list.title,
            'is_shared': shopping_list.is_shared
        }
    }), 201


@api_bp.route('/lists/<int:list_id>', methods=['PUT'])
@login_required
def update_list(list_id: int):
    """Update a shopping list."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    if shopping_list.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    data = request.get_json()

    if 'title' in data:
        shopping_list.title = data['title']
    if 'is_shared' in data:
        shopping_list.is_shared = data['is_shared']

    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'id': shopping_list.id,
            'title': shopping_list.title,
            'is_shared': shopping_list.is_shared
        }
    })


@api_bp.route('/lists/<int:list_id>', methods=['DELETE'])
@login_required
def delete_list(list_id: int):
    """Delete a shopping list."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    if shopping_list.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    db.session.delete(shopping_list)
    db.session.commit()

    return jsonify({'success': True, 'message': 'List deleted'})


# ============================================================================
# Shopping List Items API
# ============================================================================

@api_bp.route('/lists/<int:list_id>/items', methods=['GET'])
@login_required
def get_items(list_id: int):
    """Get all items for a shopping list."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    items = shopping_list.items.order_by(ShoppingListItem.order_index.desc()).all()

    return jsonify({
        'success': True,
        'data': [
            {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity,
                'is_checked': item.is_checked,
                'order_index': item.order_index
            }
            for item in items
        ]
    })


@api_bp.route('/lists/<int:list_id>/items', methods=['POST'])
@login_required
def create_item(list_id: int):
    """Add an item to a shopping list."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    # Get the highest order_index and add 1
    max_order = db.session.query(db.func.max(ShoppingListItem.order_index)).filter_by(
        shopping_list_id=list_id
    ).scalar() or 0

    item = ShoppingListItem(
        shopping_list_id=list_id,
        name=data['name'],
        quantity=data.get('quantity', '1'),
        order_index=max_order + 1
    )
    db.session.add(item)
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'is_checked': item.is_checked,
            'order_index': item.order_index
        }
    }), 201


@api_bp.route('/items/<int:item_id>', methods=['PUT'])
@login_required
def update_item(item_id: int):
    """Update a shopping list item."""
    item = ShoppingListItem.query.get_or_404(item_id)
    shopping_list = item.shopping_list

    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    data = request.get_json()

    if 'name' in data:
        item.name = data['name']
    if 'quantity' in data:
        item.quantity = data['quantity']
    if 'is_checked' in data:
        item.is_checked = data['is_checked']

    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'is_checked': item.is_checked
        }
    })


@api_bp.route('/items/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_item(item_id: int):
    """Toggle the checked status of an item."""
    item = ShoppingListItem.query.get_or_404(item_id)
    shopping_list = item.shopping_list

    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    item.is_checked = not item.is_checked
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'id': item.id,
            'is_checked': item.is_checked
        }
    })


@api_bp.route('/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id: int):
    """Delete a shopping list item."""
    item = ShoppingListItem.query.get_or_404(item_id)
    shopping_list = item.shopping_list

    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    db.session.delete(item)
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Item deleted'})


# ============================================================================
# Shared Lists API (Public Access)
# ============================================================================

@api_bp.route('/shared/<string:guid>', methods=['GET'])
def get_shared_list(guid: str):
    """Get a shared shopping list (no authentication required)."""
    shopping_list = ShoppingList.query.filter_by(guid=guid).first_or_404()

    if not shopping_list.is_shared:
        abort(404)

    items = shopping_list.items.order_by(ShoppingListItem.order_index.desc()).all()

    return jsonify({
        'success': True,
        'data': {
            'id': shopping_list.id,
            'guid': shopping_list.guid,
            'title': shopping_list.title,
            'owner': shopping_list.owner.username,
            'created_at': shopping_list.created_at.isoformat(),
            'updated_at': shopping_list.updated_at.isoformat(),
            'items': [
                {
                    'id': item.id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'is_checked': item.is_checked,
                    'order_index': item.order_index
                }
                for item in items
            ]
        }
    })
