"""CLI commands for application management."""

import click
from datetime import datetime, timedelta, timezone
from flask import Flask
from flask.cli import with_appcontext

from .extensions import db
from .models import User, ShoppingList, ShoppingListItem


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Create database tables and initialize default data."""
    db.create_all()
    click.echo('Database tables created.')

    # Create default admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        click.echo('Default admin user created (username: admin, password: admin123)')
    else:
        click.echo('Admin user already exists.')


@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin_command(username: str, email: str, password: str):
    """Create a new admin user."""
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        click.echo(f'Error: User "{username}" already exists.', err=True)
        return

    if User.query.filter_by(email=email).first():
        click.echo(f'Error: Email "{email}" is already in use.', err=True)
        return

    user = User(
        username=username,
        email=email,
        is_admin=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo(f'Admin user "{username}" created successfully.')


@click.command('create-user')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_user_command(username: str, email: str, password: str):
    """Create a new regular user."""
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        click.echo(f'Error: User "{username}" already exists.', err=True)
        return

    if User.query.filter_by(email=email).first():
        click.echo(f'Error: Email "{email}" is already in use.', err=True)
        return

    user = User(
        username=username,
        email=email,
        is_admin=False
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo(f'User "{username}" created successfully.')


@click.command('list-users')
@with_appcontext
def list_users_command():
    """List all users."""
    users = User.query.order_by(User.username).all()

    if not users:
        click.echo('No users found.')
        return

    click.echo(f'{"ID":<5} {"Username":<20} {"Email":<30} {"Admin":<10} {"Lists":<10}')
    click.echo('-' * 80)

    for user in users:
        lists_count = user.shopping_lists.count()
        click.echo(
            f'{user.id:<5} {user.username:<20} {user.email:<30} '
            f'{"Yes" if user.is_admin else "No":<10} {lists_count:<10}'
        )


@click.command('stats')
@with_appcontext
def stats_command():
    """Show application statistics."""
    total_users = User.query.count()
    total_admins = User.query.filter_by(is_admin=True).count()
    total_lists = ShoppingList.active().count()
    total_shared_lists = ShoppingList.active().filter_by(is_shared=True).count()
    total_items = ShoppingListItem.active().count()

    # Trash statistics
    trashed_lists = ShoppingList.deleted().count()
    trashed_items = ShoppingListItem.deleted().count()

    click.echo('Application Statistics:')
    click.echo('-' * 40)
    click.echo(f'Total Users:        {total_users}')
    click.echo(f'  - Admins:         {total_admins}')
    click.echo(f'  - Regular Users:  {total_users - total_admins}')
    click.echo(f'Total Lists:        {total_lists}')
    click.echo(f'  - Shared Lists:   {total_shared_lists}')
    click.echo(f'  - Private Lists:  {total_lists - total_shared_lists}')
    click.echo(f'Total Items:        {total_items}')
    click.echo(f'Trash (Papierkorb):')
    click.echo(f'  - Deleted Lists:  {trashed_lists}')
    click.echo(f'  - Deleted Items:  {trashed_items}')


@click.command('cleanup-trash')
@click.option('--days', default=30, help='Delete items older than N days (default: 30)')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
@with_appcontext
def cleanup_trash_command(days: int, dry_run: bool):
    """Permanently delete items that have been in trash for N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Find old items
    old_items = ShoppingListItem.deleted().filter(
        ShoppingListItem.deleted_at < cutoff
    ).all()

    # Find old lists
    old_lists = ShoppingList.deleted().filter(
        ShoppingList.deleted_at < cutoff
    ).all()

    if dry_run:
        click.echo(f'DRY RUN: Would permanently delete items older than {days} days (before {cutoff.isoformat()}):')
        click.echo('-' * 80)
        click.echo(f'Lists to delete:  {len(old_lists)}')
        if old_lists:
            for shopping_list in old_lists:
                click.echo(f'  - [{shopping_list.id}] "{shopping_list.title}" (deleted: {shopping_list.deleted_at.isoformat()})')

        click.echo(f'Items to delete:  {len(old_items)}')
        if old_items:
            for item in old_items:
                click.echo(f'  - [{item.id}] "{item.name}" from list {item.shopping_list.title} (deleted: {item.deleted_at.isoformat()})')

        click.echo('\nTo actually delete, run without --dry-run flag.')
        return

    # Actually delete
    for item in old_items:
        db.session.delete(item)

    for shopping_list in old_lists:
        db.session.delete(shopping_list)

    db.session.commit()

    click.echo(f'Permanently deleted {len(old_items)} items and {len(old_lists)} lists older than {days} days.')
    click.echo(f'Cutoff date: {cutoff.isoformat()}')


@click.command('trash-stats')
@with_appcontext
def trash_stats_command():
    """Show detailed trash statistics."""
    trashed_lists = ShoppingList.deleted().all()
    trashed_items = ShoppingListItem.deleted().all()

    click.echo('Trash Statistics (Papierkorb):')
    click.echo('=' * 80)

    # Lists in trash
    click.echo(f'\nDeleted Lists: {len(trashed_lists)}')
    click.echo('-' * 80)
    if trashed_lists:
        click.echo(f'{"ID":<5} {"Title":<30} {"Owner":<15} {"Deleted At":<25}')
        click.echo('-' * 80)
        for shopping_list in trashed_lists:
            click.echo(
                f'{shopping_list.id:<5} {shopping_list.title[:28]:<30} '
                f'{shopping_list.owner.username[:13]:<15} '
                f'{shopping_list.deleted_at.isoformat():<25}'
            )
    else:
        click.echo('No deleted lists in trash.')

    # Items in trash
    click.echo(f'\nDeleted Items: {len(trashed_items)}')
    click.echo('-' * 80)
    if trashed_items:
        click.echo(f'{"ID":<5} {"Name":<25} {"List":<25} {"Deleted At":<25}')
        click.echo('-' * 80)
        for item in trashed_items[:20]:  # Show first 20
            click.echo(
                f'{item.id:<5} {item.name[:23]:<25} '
                f'{item.shopping_list.title[:23]:<25} '
                f'{item.deleted_at.isoformat():<25}'
            )
        if len(trashed_items) > 20:
            click.echo(f'... and {len(trashed_items) - 20} more')
    else:
        click.echo('No deleted items in trash.')


def register_commands(app: Flask):
    """Register all CLI commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(create_user_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(stats_command)
    app.cli.add_command(cleanup_trash_command)
    app.cli.add_command(trash_stats_command)
