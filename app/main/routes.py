from datetime import datetime, timezone

from flask import (
    abort,
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
from ..extensions import db
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
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Erfolgreich angemeldet.', 'success')
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        flash('Ungültige Anmeldedaten.', 'danger')

    return render_template('login.html', form=form)


@main_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('Du wurdest abgemeldet.', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/shared/<string:guid>')
def view_shared_list(guid: str):
    """
    View a shared shopping list (accessible without login).

    Args:
        guid: The GUID of the shared list
    """
    shopping_list = ShoppingList.query.filter_by(guid=guid).first_or_404()

    if not shopping_list.is_shared:
        flash('Diese Liste ist nicht öffentlich geteilt.', 'warning')
        abort(404)

    # Get items ordered by order_index
    items = shopping_list.items.order_by(ShoppingListItem.order_index.desc()).all()

    # Item form for authenticated users
    item_form = ShoppingListItemForm() if current_user.is_authenticated else None

    return render_template(
        'shared_list.html',
        shopping_list=shopping_list,
        items=items,
        item_form=item_form,
        can_edit=current_user.is_authenticated
    )


# ============================================================================
# Dashboard & Shopping List Management (Login Required)
# ============================================================================

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing their shopping lists."""
    shopping_lists = current_user.shopping_lists.order_by(desc(ShoppingList.updated_at)).all()
    return render_template('dashboard.html', shopping_lists=shopping_lists)


@main_bp.route('/lists/create', methods=['GET', 'POST'])
@login_required
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

        flash(f'Liste "{shopping_list.title}" erfolgreich erstellt.', 'success')
        return redirect(url_for('main.view_list', list_id=shopping_list.id))

    return render_template('create_list.html', form=form)


@main_bp.route('/lists/<int:list_id>')
@login_required
def view_list(list_id: int):
    """View a shopping list with all its items."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    # Check access permissions
    if not check_list_access(shopping_list, allow_shared=True):
        flash('Sie haben keine Berechtigung, diese Liste zu sehen.', 'danger')
        abort(403)

    # Get items ordered by order_index (descending, so newest first)
    items = shopping_list.items.order_by(ShoppingListItem.order_index.desc()).all()

    item_form = ShoppingListItemForm()

    return render_template(
        'view_list.html',
        shopping_list=shopping_list,
        items=items,
        item_form=item_form
    )


@main_bp.route('/lists/<int:list_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_list(list_id: int):
    """Edit a shopping list."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    # Only owner or admin can edit list settings
    if shopping_list.user_id != current_user.id and not current_user.is_admin:
        flash('Sie haben keine Berechtigung, diese Liste zu bearbeiten.', 'danger')
        abort(403)

    form = ShoppingListForm(obj=shopping_list)

    if form.validate_on_submit():
        shopping_list.title = form.title.data
        shopping_list.is_shared = form.is_shared.data
        shopping_list.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        flash(f'Liste "{shopping_list.title}" erfolgreich aktualisiert.', 'success')
        return redirect(url_for('main.view_list', list_id=shopping_list.id))

    return render_template('edit_list.html', form=form, shopping_list=shopping_list)


@main_bp.route('/lists/<int:list_id>/delete', methods=['POST'])
@login_required
def delete_list(list_id: int):
    """Delete a shopping list."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    # Only owner or admin can delete
    if shopping_list.user_id != current_user.id and not current_user.is_admin:
        flash('Sie haben keine Berechtigung, diese Liste zu löschen.', 'danger')
        abort(403)

    title = shopping_list.title
    db.session.delete(shopping_list)
    db.session.commit()

    flash(f'Liste "{title}" wurde gelöscht.', 'success')
    return redirect(url_for('main.dashboard'))


# ============================================================================
# Shopping List Items Management
# ============================================================================

@main_bp.route('/lists/<int:list_id>/items/add', methods=['POST'])
@login_required
def add_item(list_id: int):
    """Add an item to a shopping list."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    # Check access permissions
    if not check_list_access(shopping_list, allow_shared=True):
        flash('Sie haben keine Berechtigung, Artikel zu dieser Liste hinzuzufügen.', 'danger')
        abort(403)

    form = ShoppingListItemForm()

    if form.validate_on_submit():
        # Get the highest order_index and add 1
        max_order = db.session.query(db.func.max(ShoppingListItem.order_index)).filter_by(
            shopping_list_id=list_id
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

        flash(f'Artikel "{item.name}" hinzugefügt.', 'success')

    return redirect(url_for('main.view_list', list_id=list_id))


@main_bp.route('/items/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_item(item_id: int):
    """Toggle the checked status of an item."""
    item = ShoppingListItem.query.get_or_404(item_id)
    shopping_list = item.shopping_list

    # Check access permissions
    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    item.is_checked = not item.is_checked
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        'success': True,
        'is_checked': item.is_checked
    })


@main_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id: int):
    """Delete an item from a shopping list."""
    item = ShoppingListItem.query.get_or_404(item_id)
    shopping_list = item.shopping_list

    # Check access permissions
    if not check_list_access(shopping_list, allow_shared=True):
        abort(403)

    list_id = shopping_list.id
    name = item.name
    db.session.delete(item)
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    flash(f'Artikel "{name}" wurde gelöscht.', 'success')
    return redirect(url_for('main.view_list', list_id=list_id))


# ============================================================================
# Admin Routes
# ============================================================================

@main_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard."""
    total_users = User.query.count()
    total_lists = ShoppingList.query.count()
    total_items = ShoppingListItem.query.count()

    recent_lists = ShoppingList.query.order_by(desc(ShoppingList.created_at)).limit(10).all()

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

        flash(f'Benutzer "{user.username}" wurde erstellt.', 'success')
        return redirect(url_for('main.admin_users'))

    return render_template('admin/create_user.html', form=form)


@main_bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id: int):
    """Edit an existing user."""
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    form.user_id.data = str(user.id)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data

        # Only update password if provided
        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()

        flash(f'Benutzer "{user.username}" wurde aktualisiert.', 'success')
        return redirect(url_for('main.admin_users'))

    return render_template('admin/edit_user.html', form=form, user=user)


@main_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id: int):
    """Delete a user and all their lists."""
    user = User.query.get_or_404(user_id)

    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('Sie können sich nicht selbst löschen.', 'danger')
        return redirect(url_for('main.admin_users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'Benutzer "{username}" und alle zugehörigen Listen wurden gelöscht.', 'success')
    return redirect(url_for('main.admin_users'))


@main_bp.route('/admin/lists')
@login_required
@admin_required
def admin_lists():
    """View all shopping lists."""
    lists = ShoppingList.query.order_by(desc(ShoppingList.updated_at)).all()
    return render_template('admin/lists.html', lists=lists)


@main_bp.route('/admin/lists/<int:list_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_list(list_id: int):
    """Delete a shopping list (admin)."""
    shopping_list = ShoppingList.query.get_or_404(list_id)

    title = shopping_list.title
    owner = shopping_list.owner.username
    db.session.delete(shopping_list)
    db.session.commit()

    flash(f'Liste "{title}" von Benutzer "{owner}" wurde gelöscht.', 'success')
    return redirect(url_for('main.admin_lists'))
