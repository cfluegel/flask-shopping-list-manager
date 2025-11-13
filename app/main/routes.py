from datetime import datetime, timezone

from flask import (
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import desc

from . import main_bp
from .forms import (
    CreateUserForm,
    EditUserForm,
    LoginForm,
    ShoppingListForm,
    ShoppingListItemForm,
)
from ..extensions import db, limiter
from ..models import ShoppingList, ShoppingListItem, User
from ..utils import admin_required, check_list_access


# ============================================================================
# Public Routes
# ============================================================================

@main_bp.route('/')
def index():
    """Homepage - redirects to dashboard if logged in."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            current_app.logger.info(
                f'Benutzer "{user.username}" (ID: {user.id}) hat sich erfolgreich angemeldet'
            )
            flash('Erfolgreich angemeldet.', 'success')
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            return redirect(next_page)

        # Log failed login attempt
        current_app.logger.warning(
            f'Fehlgeschlagener Anmeldeversuch für Benutzername: "{form.username.data}" von IP: {request.remote_addr}'
        )
        flash('Ungültige Anmeldedaten.', 'danger')

    return render_template('login.html', form=form)


@main_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    username = current_user.username
    user_id = current_user.id
    logout_user()
    current_app.logger.info(f'Benutzer "{username}" (ID: {user_id}) hat sich abgemeldet')
    flash('Du wurdest abgemeldet.', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/shared/<string:guid>')
def view_shared_list(guid: str):
    """
    View a shared shopping list (accessible without login).

    Args:
        guid: The GUID of the shared list
    """
    shopping_list = ShoppingList.active().filter_by(guid=guid).first_or_404()

    if not shopping_list.is_shared:
        flash('Diese Liste ist nicht öffentlich geteilt.', 'warning')
        abort(404)

    # Get items ordered by order_index (only active items)
    items = ShoppingListItem.active().filter_by(shopping_list_id=shopping_list.id).order_by(ShoppingListItem.order_index.desc()).all()

    # Item form for authenticated users
    item_form = ShoppingListItemForm() if current_user.is_authenticated else None

    return render_template(
        'shared_list.html',
        shopping_list=shopping_list,
        items=items,
        item_form=item_form,
        can_edit=current_user.is_authenticated
    )


@main_bp.route('/impressum')
def impressum():
    """Impressum page (legal notice)."""
    return render_template('impressum.html')


@main_bp.route('/datenschutz')
def datenschutz():
    """Datenschutzerklärung (privacy policy)."""
    return render_template('datenschutz.html')


# ============================================================================
# Dashboard & Shopping List Management (Login Required)
# ============================================================================

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing their shopping lists."""
    shopping_lists = ShoppingList.active().filter_by(user_id=current_user.id).order_by(desc(ShoppingList.updated_at)).all()
    return render_template('dashboard.html', shopping_lists=shopping_lists)


@main_bp.route('/lists/create', methods=['GET', 'POST'])
@login_required
@limiter.limit("30 per minute", methods=["POST"])
def create_list():
    """Create a new shopping list."""
    form = ShoppingListForm()

    if form.validate_on_submit():
        shopping_list = ShoppingList(
            title=form.title.data,
            user_id=current_user.id,
            is_shared=form.is_shared.data
        )
        db.session.add(shopping_list)
        db.session.commit()

        current_app.logger.info(
            f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat Liste '
            f'"{shopping_list.title}" (ID: {shopping_list.id}) erstellt'
        )
        flash(f'Liste "{shopping_list.title}" erfolgreich erstellt.', 'success')
        return redirect(url_for('main.view_list', list_id=shopping_list.id))

    return render_template('create_list.html', form=form)


@main_bp.route('/lists/<int:list_id>')
@login_required
def view_list(list_id: int):
    """View a shopping list with all its items."""
    shopping_list = ShoppingList.active().filter_by(id=list_id).first_or_404()

    # Check access permissions
    if not check_list_access(shopping_list, allow_shared=True):
        flash('Sie haben keine Berechtigung, diese Liste zu sehen.', 'danger')
        abort(403)

    # Get items ordered by order_index (descending, so newest first) - only active items
    items = ShoppingListItem.active().filter_by(shopping_list_id=shopping_list.id).order_by(ShoppingListItem.order_index.desc()).all()

    item_form = ShoppingListItemForm()

    return render_template(
        'view_list.html',
        shopping_list=shopping_list,
        items=items,
        item_form=item_form
    )


@main_bp.route('/lists/<int:list_id>/edit', methods=['GET', 'POST'])
@login_required
@limiter.limit("30 per minute", methods=["POST"])
def edit_list(list_id: int):
    """Edit a shopping list."""
    shopping_list = ShoppingList.active().filter_by(id=list_id).first_or_404()

    # Only owner or admin can edit list settings
    if shopping_list.user_id != current_user.id and not current_user.is_admin:
        current_app.logger.warning(
            f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat versucht, '
            f'Liste {list_id} zu bearbeiten (Zugriff verweigert)'
        )
        flash('Sie haben keine Berechtigung, diese Liste zu bearbeiten.', 'danger')
        abort(403)

    form = ShoppingListForm(obj=shopping_list)

    if form.validate_on_submit():
        old_title = shopping_list.title
        old_shared = shopping_list.is_shared

        shopping_list.title = form.title.data

        # If is_shared status changes, regenerate GUID
        # This invalidates the old sharing URL for security
        if old_shared != form.is_shared.data:
            import uuid
            shopping_list.guid = str(uuid.uuid4())
            current_app.logger.info(
                f'GUID regenerated for list {list_id} due to sharing status change '
                f'(was_shared: {old_shared}, now_shared: {form.is_shared.data})'
            )

        shopping_list.is_shared = form.is_shared.data
        shopping_list.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        changes = []
        if old_title != shopping_list.title:
            changes.append(f'Titel: "{old_title}" → "{shopping_list.title}"')
        if old_shared != shopping_list.is_shared:
            shared_status = "geteilt" if shopping_list.is_shared else "privat"
            changes.append(f'Freigabe: {shared_status}')

        if changes:
            current_app.logger.info(
                f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat Liste '
                f'{list_id} bearbeitet: {", ".join(changes)}'
            )

        flash(f'Liste "{shopping_list.title}" erfolgreich aktualisiert.', 'success')
        return redirect(url_for('main.view_list', list_id=shopping_list.id))

    return render_template('edit_list.html', form=form, shopping_list=shopping_list)


@main_bp.route('/lists/<int:list_id>/delete', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def delete_list(list_id: int):
    """Soft delete a shopping list (move to trash)."""
    shopping_list = ShoppingList.active().filter_by(id=list_id).first_or_404()

    # Only owner or admin can delete
    if shopping_list.user_id != current_user.id and not current_user.is_admin:
        current_app.logger.warning(
            f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat versucht, '
            f'Liste {list_id} zu löschen (Zugriff verweigert)'
        )
        flash('Sie haben keine Berechtigung, diese Liste zu löschen.', 'danger')
        abort(403)

    title = shopping_list.title
    shopping_list.soft_delete()
    db.session.commit()

    current_app.logger.info(
        f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat Liste '
        f'"{title}" (ID: {list_id}) in den Papierkorb verschoben'
    )
    flash(f'Liste "{title}" wurde in den Papierkorb verschoben.', 'success')
    return redirect(url_for('main.dashboard'))


# ============================================================================
# Shopping List Items Management
# ============================================================================

@main_bp.route('/lists/<int:list_id>/items/add', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def add_item(list_id: int):
    """Add an item to a shopping list."""
    shopping_list = ShoppingList.active().filter_by(id=list_id).first_or_404()

    # Check access permissions
    if not check_list_access(shopping_list, allow_shared=True):
        current_app.logger.warning(
            f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat versucht, '
            f'Artikel zu Liste {list_id} hinzuzufügen (Zugriff verweigert)'
        )
        flash('Sie haben keine Berechtigung, Artikel zu dieser Liste hinzuzufügen.', 'danger')
        abort(403)

    form = ShoppingListItemForm()

    if form.validate_on_submit():
        # Get the highest order_index and add 1 (only from active items)
        max_order = db.session.query(db.func.max(ShoppingListItem.order_index)).filter(
            ShoppingListItem.shopping_list_id == list_id,
            ShoppingListItem.deleted_at.is_(None)
        ).scalar() or 0

        item = ShoppingListItem(
            shopping_list_id=list_id,
            name=form.name.data,
            quantity=form.quantity.data,
            order_index=max_order + 1
        )
        db.session.add(item)
        shopping_list.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        current_app.logger.info(
            f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat Artikel '
            f'"{item.name}" (ID: {item.id}) zu Liste {list_id} hinzugefügt'
        )
        flash(f'Artikel "{item.name}" hinzugefügt.', 'success')

    return redirect(url_for('main.view_list', list_id=list_id))


@main_bp.route('/items/<int:item_id>/toggle', methods=['POST'])
@login_required
@limiter.limit("100 per minute")
def toggle_item(item_id: int):
    """Toggle the checked status of an item."""
    item = ShoppingListItem.active().filter_by(id=item_id).first_or_404()
    shopping_list = item.shopping_list

    # Check access permissions
    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    old_status = item.is_checked
    item.is_checked = not item.is_checked
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    status_text = "abgehakt" if item.is_checked else "nicht abgehakt"
    current_app.logger.info(
        f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat Artikel '
        f'"{item.name}" (ID: {item.id}) als {status_text} markiert'
    )

    return jsonify({
        'success': True,
        'is_checked': item.is_checked
    })


@main_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def delete_item(item_id: int):
    """Soft delete an item from a shopping list (move to trash)."""
    item = ShoppingListItem.active().filter_by(id=item_id).first_or_404()
    shopping_list = item.shopping_list

    # Check access permissions
    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    list_id = shopping_list.id
    name = item.name
    item.soft_delete()
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    current_app.logger.info(
        f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat Artikel '
        f'"{name}" (ID: {item_id}) in den Papierkorb verschoben'
    )
    flash(f'Artikel "{name}" wurde in den Papierkorb verschoben.', 'success')
    return redirect(url_for('main.view_list', list_id=list_id))


@main_bp.route('/items/<int:item_id>/edit', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def edit_item(item_id: int):
    """Edit an item in a shopping list (AJAX endpoint)."""
    item = ShoppingListItem.active().filter_by(id=item_id).first_or_404()
    shopping_list = item.shopping_list

    # Check access permissions
    if not check_list_access(shopping_list, allow_shared=True):
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403

    form = ShoppingListItemForm()

    if form.validate_on_submit():
        # Track changes
        old_name = item.name
        old_quantity = item.quantity

        # Update item
        item.name = form.name.data.strip()
        item.quantity = form.quantity.data.strip()
        shopping_list.updated_at = datetime.now(timezone.utc)

        try:
            db.session.commit()

            changes = []
            if old_name != item.name:
                changes.append(f'Name: "{old_name}" → "{item.name}"')
            if old_quantity != item.quantity:
                changes.append(f'Menge: "{old_quantity}" → "{item.quantity}"')

            if changes:
                current_app.logger.info(
                    f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat Artikel '
                    f'{item_id} bearbeitet: {", ".join(changes)}'
                )

            return jsonify({
                'success': True,
                'item': {
                    'id': item.id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'is_checked': item.is_checked
                }
            })
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f'Fehler beim Bearbeiten von Artikel {item_id} durch Benutzer '
                f'"{current_user.username}" (ID: {current_user.id}): {str(e)}'
            )
            return jsonify({
                'success': False,
                'error': 'Fehler beim Speichern'
            }), 500

    # Return validation errors
    return jsonify({
        'success': False,
        'errors': {field: errors[0] for field, errors in form.errors.items()}
    }), 400


# ============================================================================
# Admin Routes
# ============================================================================

@main_bp.route('/admin')
@login_required
@admin_required
@limiter.limit("100 per hour")
def admin_dashboard():
    """Admin dashboard."""
    total_users = User.query.count()
    total_lists = ShoppingList.active().count()
    total_items = ShoppingListItem.active().count()

    recent_lists = ShoppingList.active().order_by(desc(ShoppingList.created_at)).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_lists=total_lists,
        total_items=total_items,
        recent_lists=recent_lists
    )


@main_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """User management page."""
    users = User.query.order_by(User.username).all()
    return render_template('admin/users.html', users=users)


@main_bp.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
@limiter.limit("20 per hour", methods=["POST"])
def admin_create_user():
    """Create a new user."""
    form = CreateUserForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        current_app.logger.info(
            f'Admin "{current_user.username}" (ID: {current_user.id}) hat Benutzer '
            f'"{user.username}" (ID: {user.id}) erstellt (Admin: {user.is_admin})'
        )
        flash(f'Benutzer "{user.username}" wurde erstellt.', 'success')
        return redirect(url_for('main.admin_users'))

    return render_template('admin/create_user.html', form=form)


@main_bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
@limiter.limit("20 per hour", methods=["POST"])
def admin_edit_user(user_id: int):
    """Edit an existing user."""
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    form.user_id.data = str(user.id)

    if form.validate_on_submit():
        old_username = user.username
        old_email = user.email
        old_is_admin = user.is_admin

        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data

        changes = []
        if old_username != user.username:
            changes.append(f'Benutzername: "{old_username}" → "{user.username}"')
        if old_email != user.email:
            changes.append(f'E-Mail: "{old_email}" → "{user.email}"')
        if old_is_admin != user.is_admin:
            admin_status = "Admin" if user.is_admin else "Normaler Benutzer"
            changes.append(f'Rolle: {admin_status}')

        # Only update password if provided
        password_changed = False
        if form.password.data:
            user.set_password(form.password.data)
            password_changed = True
            changes.append('Passwort geändert')

        db.session.commit()

        if changes:
            current_app.logger.info(
                f'Admin "{current_user.username}" (ID: {current_user.id}) hat Benutzer '
                f'"{user.username}" (ID: {user_id}) bearbeitet: {", ".join(changes)}'
            )

        flash(f'Benutzer "{user.username}" wurde aktualisiert.', 'success')
        return redirect(url_for('main.admin_users'))

    return render_template('admin/edit_user.html', form=form, user=user)


@main_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
@limiter.limit("20 per hour")
def admin_delete_user(user_id: int):
    """Delete a user and all their lists."""
    user = User.query.get_or_404(user_id)

    # Prevent deleting yourself
    if user.id == current_user.id:
        current_app.logger.warning(
            f'Admin "{current_user.username}" (ID: {current_user.id}) hat versucht, '
            f'sich selbst zu löschen'
        )
        flash('Sie können sich nicht selbst löschen.', 'danger')
        return redirect(url_for('main.admin_users'))

    username = user.username
    list_count = user.shopping_lists.count()
    db.session.delete(user)
    db.session.commit()

    current_app.logger.info(
        f'Admin "{current_user.username}" (ID: {current_user.id}) hat Benutzer '
        f'"{username}" (ID: {user_id}) und {list_count} zugehörige Listen gelöscht'
    )
    flash(f'Benutzer "{username}" und alle zugehörigen Listen wurden gelöscht.', 'success')
    return redirect(url_for('main.admin_users'))


@main_bp.route('/admin/lists')
@login_required
@admin_required
def admin_lists():
    """View all active shopping lists."""
    lists = ShoppingList.active().order_by(desc(ShoppingList.updated_at)).all()
    return render_template('admin/lists.html', lists=lists)


@main_bp.route('/admin/lists/<int:list_id>/delete', methods=['POST'])
@login_required
@admin_required
@limiter.limit("20 per hour")
def admin_delete_list(list_id: int):
    """Soft delete a shopping list (admin)."""
    shopping_list = ShoppingList.active().filter_by(id=list_id).first_or_404()

    title = shopping_list.title
    owner = shopping_list.owner.username
    owner_id = shopping_list.user_id
    item_count = ShoppingListItem.active().filter_by(shopping_list_id=list_id).count()

    shopping_list.soft_delete()
    db.session.commit()

    current_app.logger.info(
        f'Admin "{current_user.username}" (ID: {current_user.id}) hat Liste '
        f'"{title}" (ID: {list_id}) von Benutzer "{owner}" (ID: {owner_id}) '
        f'mit {item_count} Artikeln in den Papierkorb verschoben'
    )
    flash(f'Liste "{title}" von Benutzer "{owner}" wurde in den Papierkorb verschoben.', 'success')
    return redirect(url_for('main.admin_lists'))


# ============================================================================
# Trash Management (Papierkorb)
# ============================================================================

@main_bp.route('/trash')
@login_required
def trash():
    """View deleted shopping lists (trash/recycle bin)."""
    deleted_lists = ShoppingList.deleted().filter_by(user_id=current_user.id).order_by(desc(ShoppingList.deleted_at)).all()
    return render_template('trash.html', deleted_lists=deleted_lists)


@main_bp.route('/lists/<int:list_id>/restore', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def restore_list(list_id: int):
    """Restore a shopping list from trash."""
    shopping_list = ShoppingList.deleted().filter_by(id=list_id).first_or_404()

    # Only owner or admin can restore
    if shopping_list.user_id != current_user.id and not current_user.is_admin:
        current_app.logger.warning(
            f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat versucht, '
            f'Liste {list_id} wiederherzustellen (Zugriff verweigert)'
        )
        flash('Sie haben keine Berechtigung, diese Liste wiederherzustellen.', 'danger')
        abort(403)

    title = shopping_list.title
    shopping_list.restore()
    db.session.commit()

    current_app.logger.info(
        f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat Liste '
        f'"{title}" (ID: {list_id}) aus dem Papierkorb wiederhergestellt'
    )
    flash(f'Liste "{title}" wurde wiederhergestellt.', 'success')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/lists/<int:list_id>/permanent-delete', methods=['POST'])
@login_required
@admin_required
@limiter.limit("20 per hour")
def permanent_delete_list(list_id: int):
    """Permanently delete a shopping list (admin only)."""
    shopping_list = ShoppingList.deleted().filter_by(id=list_id).first_or_404()

    title = shopping_list.title
    owner = shopping_list.owner.username
    owner_id = shopping_list.user_id
    item_count = shopping_list.items.count()

    db.session.delete(shopping_list)
    db.session.commit()

    current_app.logger.warning(
        f'Admin "{current_user.username}" (ID: {current_user.id}) hat Liste '
        f'"{title}" (ID: {list_id}) von Benutzer "{owner}" (ID: {owner_id}) '
        f'mit {item_count} Artikeln endgültig gelöscht'
    )
    flash(f'Liste "{title}" wurde endgültig gelöscht.', 'warning')
    return redirect(url_for('main.trash'))


@main_bp.route('/items/<int:item_id>/restore', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def restore_item(item_id: int):
    """Restore an item from trash."""
    item = ShoppingListItem.deleted().filter_by(id=item_id).first_or_404()
    shopping_list = item.shopping_list

    # Check access permissions
    if shopping_list.user_id != current_user.id and not current_user.is_admin:
        current_app.logger.warning(
            f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat versucht, '
            f'Artikel {item_id} wiederherzustellen (Zugriff verweigert)'
        )
        flash('Sie haben keine Berechtigung, diesen Artikel wiederherzustellen.', 'danger')
        abort(403)

    name = item.name
    list_id = shopping_list.id
    item.restore()
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    current_app.logger.info(
        f'Benutzer "{current_user.username}" (ID: {current_user.id}) hat Artikel '
        f'"{name}" (ID: {item_id}) aus dem Papierkorb wiederhergestellt'
    )
    flash(f'Artikel "{name}" wurde wiederhergestellt.', 'success')
    return redirect(url_for('main.view_list', list_id=list_id))


# ============================================================================
# Admin Trash Management
# ============================================================================

@main_bp.route('/admin/trash')
@login_required
@admin_required
def admin_trash():
    """View all deleted shopping lists (admin)."""
    deleted_lists = ShoppingList.deleted().order_by(desc(ShoppingList.deleted_at)).all()
    return render_template('admin/trash.html', deleted_lists=deleted_lists)
