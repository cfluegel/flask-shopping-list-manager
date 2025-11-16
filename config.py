import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    JWT_ERROR_MESSAGE_KEY = 'error'
    # Allow integer user IDs in JWT tokens
    JWT_ENCODE_ISSUER = None
    JWT_DECODE_ISSUER = None
    JWT_ENCODE_AUDIENCE = None
    JWT_DECODE_AUDIENCE = None
    JWT_ENCODE_NBF = True

    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']

    # API Pagination
    API_DEFAULT_PER_PAGE = 20
    API_MAX_PER_PAGE = 100

    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_HEADERS_ENABLED = True

    # Logging Configuration
    LOG_TO_FILE = True
    LOG_FILE_PATH = 'logs/app.log'
    LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT = 5

    # Receipt Printer Configuration
    PRINTER_ENABLED = os.environ.get('PRINTER_ENABLED', 'False').lower() in ('true', '1', 'yes')
    PRINTER_HOST = os.environ.get('PRINTER_HOST', '192.168.1.230')
    PRINTER_PORT = int(os.environ.get('PRINTER_PORT', '9100'))
    PRINTER_PROTOCOL = os.environ.get('PRINTER_PROTOCOL', 'network')
    PRINTER_TIMEOUT = int(os.environ.get('PRINTER_TIMEOUT', '5'))
    PRINTER_WIDTH = int(os.environ.get('PRINTER_WIDTH', '32'))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

    # Security Settings
    SESSION_COOKIE_SECURE = True  # Cookies nur über HTTPS
    SESSION_COOKIE_HTTPONLY = True  # JavaScript kann nicht auf Cookies zugreifen
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF-Schutz
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # HTTPS Enforcement
    PREFERRED_URL_SCHEME = 'https'

    # CORS - Restriktive Einstellungen für Production
    # Überschreibe die Base-Config CORS_ORIGINS
    @property
    def CORS_ORIGINS(self):
        """Parse CORS_ORIGINS from environment variable.
        Falls nicht gesetzt, wird eine leere Liste zurückgegeben (blockiert alle Origins).
        """
        origins = os.environ.get('CORS_ORIGINS', '')
        if not origins:
            return []
        return [origin.strip() for origin in origins.split(',')]

    # Performance Optimizations
    COMPRESS_ALGORITHM = 'gzip'
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500  # Komprimiere nur Responses > 500 bytes

    # Asset Caching
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 Jahr für statische Files

    # Logging - Nur Warnings und Errors in Production
    LOG_LEVEL = 'WARNING'

    # In Production: Set JWT_SECRET_KEY and SECRET_KEY via environment variables!
    def __init__(self):
        super().__init__()
        # Validiere dass Secret Keys gesetzt sind
        if self.SECRET_KEY == 'dev-secret':
            raise ValueError(
                "CRITICAL: SECRET_KEY must be set via environment variable in production! "
                "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        if self.JWT_SECRET_KEY == 'jwt-dev-secret-change-in-production':
            raise ValueError(
                "CRITICAL: JWT_SECRET_KEY must be set via environment variable in production! "
                "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)
