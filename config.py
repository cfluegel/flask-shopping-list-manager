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

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # In Production: Set JWT_SECRET_KEY and SECRET_KEY via environment variables!

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)
