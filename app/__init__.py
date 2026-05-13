import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from flask_login import current_user, login_user
from .extensions import db, migrate, login_manager, jwt, cors, limiter, compress
from .main import main_bp
from .api import api_bp
from .pwa import pwa_bp


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

    # Rate Limiter initialisieren
    limiter.init_app(app)

    # Response Compression initialisieren
    compress.init_app(app)

    # Rate Limiter Error Handler - German error message
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {
            "error": "Ratenbegrenzung überschritten",
            "message": "Sie haben zu viele Anfragen gesendet. Bitte versuchen Sie es später erneut."
        }, 429

    # Logging konfigurieren
    if not app.debug and not app.testing:
        # Erstelle logs Verzeichnis falls nicht vorhanden
        if not os.path.exists('logs'):
            os.mkdir('logs')

        # Rotating File Handler für Audit Logs
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Set log level
    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask Grocery Shopping List Anwendung gestartet')

    # JWT Callbacks konfigurieren
    from .models import RevokedToken

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if a JWT token has been revoked."""
        jti = jwt_payload['jti']
        return RevokedToken.is_jti_blacklisted(jti)

    @app.context_processor
    def inject_printer_config():
        return {'printer_enabled': app.config.get('PRINTER_ENABLED', False)}

    @app.context_processor
    def inject_auto_login():
        return {'auto_login_enabled': app.config.get('AUTO_LOGIN', False)}

    # Blueprints registrieren
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(pwa_bp, url_prefix='/pwa')

    # Error Handlers registrieren (before docs blueprint to avoid conflicts)
    from .api.errors import register_error_handlers
    register_error_handlers(app)

    # API Documentation Blueprint registrieren (AFTER error handlers)
    # This ensures Flask-RESTX handles its own 404s
    from .api.docs import docs_bp
    app.register_blueprint(docs_bp, url_prefix='/api/v1')

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

        @app.before_request
        def auto_login_admin():
            """In Auto-Login-Modus den Admin transparent in die Session loggen.

            API-Pfade werden ausgeschlossen: dort wird JWT erwartet, eine
            Session-Identität würde die Token-Validierung nicht ersetzen und
            könnte Tests/externe Clients verwirren.
            """
            if not app.config.get('AUTO_LOGIN', False):
                return
            if request.path.startswith('/api/'):
                return
            if current_user.is_authenticated:
                return
            admin = User.query.filter_by(username='admin').first()
            if admin is not None:
                login_user(admin)

    return app
