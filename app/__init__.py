from flask import Flask
from .extensions import db, migrate, login_manager
from .main import main_bp
from .api import api_bp


def create_app(config_object='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Extensions initialisieren
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = 'Bitte melden Sie sich an, um diese Seite zu sehen.'

    # Blueprints registrieren
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # CLI-Kommandos registrieren
    from .cli import register_commands
    register_commands(app)

    # Create default admin user if not exists
    with app.app_context():
        from .models import User

        @app.before_request
        def create_default_admin():
            """Create default admin user on first request."""
            # Check if this is the first request by checking if admin exists
            if not hasattr(app, '_admin_created'):
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
                app._admin_created = True

    return app
