import os
import json
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""

    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Ensure UTF-8 encoding
    JSON_AS_ASCII = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ims.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Security-Too
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'dev-password-salt'
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_LENGTH_MIN = 12
    SECURITY_PASSWORD_COMPLEXITY_CHECKER = None

    # Two-Factor Authentication
    SECURITY_TWO_FACTOR = True
    SECURITY_TWO_FACTOR_ENABLED_METHODS = ['authenticator']
    # SECURITY FIX: Using json.loads instead of eval() to prevent code injection
    SECURITY_TOTP_SECRETS = json.loads(os.environ.get('SECURITY_TOTP_SECRETS', '{"1": "dev-totp-secret"}'))
    SECURITY_TOTP_ISSUER = 'IMS - Inventory Management'

    # Security Features
    SECURITY_REGISTERABLE = False  # Disabled - use CLI command to create users
    SECURITY_CONFIRMABLE = False
    SECURITY_RECOVERABLE = False  # Disabled - admins can reset passwords via CLI
    SECURITY_CHANGEABLE = True
    SECURITY_TWO_FACTOR_REQUIRED = False  # Optional 2FA

    # Session
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 1800))
    )

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Babel/i18n
    BABEL_DEFAULT_LOCALE = os.environ.get('DEFAULT_LANGUAGE', 'en')
    BABEL_SUPPORTED_LOCALES = ['en', 'bg']
    # BABEL_TRANSLATION_DIRECTORIES set in app/__init__.py to use correct path

    # Application Settings
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))
    LOW_STOCK_THRESHOLD = int(os.environ.get('LOW_STOCK_THRESHOLD', 10))

    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_HEADERS_ENABLED = True


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    # Additional production security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src 'self';"
    }


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_ims.db'
    WTF_CSRF_ENABLED = False
    SECURITY_TWO_FACTOR_REQUIRED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
