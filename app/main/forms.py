from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from ..models import User


class LoginForm(FlaskForm):
    """Form for user login."""

    username = StringField('Benutzername', validators=[DataRequired(message='Benutzername ist erforderlich.')])
    password = PasswordField('Passwort', validators=[DataRequired(message='Passwort ist erforderlich.')])
    submit = SubmitField('Anmelden')


class ShoppingListForm(FlaskForm):
    """Form for creating and editing shopping lists."""

    title = StringField(
        'Listenname',
        validators=[
            DataRequired(message='Listenname ist erforderlich.'),
            Length(min=1, max=200, message='Listenname muss zwischen 1 und 200 Zeichen lang sein.')
        ]
    )
    is_shared = BooleanField('Liste teilen (öffentlich zugänglich)')
    submit = SubmitField('Speichern')


class ShoppingListItemForm(FlaskForm):
    """Form for adding and editing shopping list items."""

    name = StringField(
        'Artikel',
        validators=[
            DataRequired(message='Artikelbezeichnung ist erforderlich.'),
            Length(min=1, max=200, message='Artikelbezeichnung muss zwischen 1 und 200 Zeichen lang sein.')
        ]
    )
    quantity = StringField(
        'Anzahl',
        validators=[
            DataRequired(message='Anzahl ist erforderlich.'),
            Length(min=1, max=50, message='Anzahl muss zwischen 1 und 50 Zeichen lang sein.')
        ],
        default='1'
    )
    submit = SubmitField('Hinzufügen')


class CreateUserForm(FlaskForm):
    """Form for creating new users (admin only)."""

    username = StringField(
        'Benutzername',
        validators=[
            DataRequired(message='Benutzername ist erforderlich.'),
            Length(min=3, max=80, message='Benutzername muss zwischen 3 und 80 Zeichen lang sein.')
        ]
    )
    email = StringField(
        'E-Mail',
        validators=[
            DataRequired(message='E-Mail ist erforderlich.'),
            Email(message='Ungültige E-Mail-Adresse.')
        ]
    )
    password = PasswordField(
        'Passwort',
        validators=[
            DataRequired(message='Passwort ist erforderlich.'),
            Length(min=6, message='Passwort muss mindestens 6 Zeichen lang sein.')
        ]
    )
    password_confirm = PasswordField(
        'Passwort bestätigen',
        validators=[
            DataRequired(message='Passwortbestätigung ist erforderlich.'),
            EqualTo('password', message='Passwörter müssen übereinstimmen.')
        ]
    )
    is_admin = BooleanField('Administrator')
    submit = SubmitField('Benutzer erstellen')

    def validate_username(self, field):
        """Check if username already exists."""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Benutzername wird bereits verwendet.')

    def validate_email(self, field):
        """Check if email already exists."""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('E-Mail-Adresse wird bereits verwendet.')


class EditUserForm(FlaskForm):
    """Form for editing existing users (admin only)."""

    user_id = HiddenField()
    username = StringField(
        'Benutzername',
        validators=[
            DataRequired(message='Benutzername ist erforderlich.'),
            Length(min=3, max=80, message='Benutzername muss zwischen 3 und 80 Zeichen lang sein.')
        ]
    )
    email = StringField(
        'E-Mail',
        validators=[
            DataRequired(message='E-Mail ist erforderlich.'),
            Email(message='Ungültige E-Mail-Adresse.')
        ]
    )
    password = PasswordField(
        'Neues Passwort (optional)',
        validators=[
            Optional(),
            Length(min=6, message='Passwort muss mindestens 6 Zeichen lang sein.')
        ]
    )
    password_confirm = PasswordField(
        'Neues Passwort bestätigen',
        validators=[
            Optional(),
            EqualTo('password', message='Passwörter müssen übereinstimmen.')
        ]
    )
    is_admin = BooleanField('Administrator')
    submit = SubmitField('Benutzer aktualisieren')

    def validate_username(self, field):
        """Check if username already exists (excluding current user)."""
        user = User.query.filter_by(username=field.data).first()
        if user and str(user.id) != self.user_id.data:
            raise ValidationError('Benutzername wird bereits verwendet.')

    def validate_email(self, field):
        """Check if email already exists (excluding current user)."""
        user = User.query.filter_by(email=field.data).first()
        if user and str(user.id) != self.user_id.data:
            raise ValidationError('E-Mail-Adresse wird bereits verwendet.')
