"""CLI commands for application management."""

import click
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
    total_lists = ShoppingList.query.count()
    total_shared_lists = ShoppingList.query.filter_by(is_shared=True).count()
    total_items = ShoppingListItem.query.count()

    click.echo('Application Statistics:')
    click.echo('-' * 40)
    click.echo(f'Total Users:        {total_users}')
    click.echo(f'  - Admins:         {total_admins}')
    click.echo(f'  - Regular Users:  {total_users - total_admins}')
    click.echo(f'Total Lists:        {total_lists}')
    click.echo(f'  - Shared Lists:   {total_shared_lists}')
    click.echo(f'  - Private Lists:  {total_lists - total_shared_lists}')
    click.echo(f'Total Items:        {total_items}')


def register_commands(app: Flask):
    """Register all CLI commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(create_user_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(stats_command)
