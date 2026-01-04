"""
CLI commands for IMS application
"""
import click
import uuid
from flask import Flask
from flask.cli import with_appcontext
from app import db
from app.models import User, Role
from werkzeug.security import generate_password_hash


@click.command('create-user')
@click.option('--username', prompt=True, help='Username for the new user')
@click.option('--email', prompt=True, help='Email address for the new user')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password for the new user')
@click.option('--role', type=click.Choice(['admin', 'manager', 'staff'], case_sensitive=False), default='staff', help='Role for the new user')
@click.option('--language', type=click.Choice(['en', 'bg'], case_sensitive=False), default='en', help='Preferred language')
@with_appcontext
def create_user_command(username, email, password, role, language):
    """Create a new user via CLI"""

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        click.echo(click.style(f'Error: User with email {email} already exists!', fg='red'))
        return

    if User.query.filter_by(username=username).first():
        click.echo(click.style(f'Error: User with username {username} already exists!', fg='red'))
        return

    # Get or create role
    role_obj = Role.query.filter_by(name=role).first()
    if not role_obj:
        role_obj = Role(
            name=role,
            description=f'{role.capitalize()} role'
        )
        db.session.add(role_obj)

    # Create user
    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        fs_uniquifier=str(uuid.uuid4()),
        language=language,
        active=True
    )
    user.roles.append(role_obj)

    db.session.add(user)
    db.session.commit()

    click.echo(click.style(f'✓ User created successfully!', fg='green'))
    click.echo(f'  Username: {username}')
    click.echo(f'  Email: {email}')
    click.echo(f'  Role: {role}')
    click.echo(f'  Language: {language}')


@click.command('list-users')
@with_appcontext
def list_users_command():
    """List all users"""
    users = User.query.all()

    if not users:
        click.echo('No users found.')
        return

    click.echo(f'\n{"ID":<5} {"Username":<20} {"Email":<30} {"Role":<10} {"Active":<10}')
    click.echo('-' * 75)

    for user in users:
        role_names = ', '.join([role.name for role in user.roles])
        active_status = '✓' if user.active else '✗'
        click.echo(f'{user.id:<5} {user.username:<20} {user.email:<30} {role_names:<10} {active_status:<10}')

    click.echo(f'\nTotal users: {len(users)}\n')


@click.command('delete-user')
@click.option('--email', prompt=True, help='Email of the user to delete')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@with_appcontext
def delete_user_command(email, confirm):
    """Delete a user"""
    user = User.query.filter_by(email=email).first()

    if not user:
        click.echo(click.style(f'Error: User with email {email} not found!', fg='red'))
        return

    if not confirm:
        if not click.confirm(f'Are you sure you want to delete user {user.username} ({user.email})?'):
            click.echo('Cancelled.')
            return

    db.session.delete(user)
    db.session.commit()

    click.echo(click.style(f'✓ User {user.username} deleted successfully!', fg='green'))


def register_commands(app: Flask):
    """Register CLI commands with Flask app"""
    app.cli.add_command(create_user_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(delete_user_command)
