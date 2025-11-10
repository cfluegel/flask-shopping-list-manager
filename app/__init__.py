from flask import Flask
from .extensions import db, migrate, login_manager, jwt, cors
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

    # JWT initialisieren
    jwt.init_app(app)

    # CORS für mobile Apps konfigurieren
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": app.config['CORS_METHODS'],
            "allow_headers": app.config['CORS_ALLOW_HEADERS'],
            "supports_credentials": False
        }
    })

    # JWT Callbacks konfigurieren
    from .models import RevokedToken

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if a JWT token has been revoked."""
        jti = jwt_payload['jti']
        return RevokedToken.is_jti_blacklisted(jti)

    # Blueprints registrieren
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Error Handlers registrieren
    from .api.errors import register_error_handlers
    register_error_handlers(app)

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
