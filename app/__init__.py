from flask import Flask, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel
from flask_security import Security, SQLAlchemyUserDatastore
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app_config import config
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
babel = Babel()
login_manager = LoginManager()
security = Security()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


def create_app(config_name=None):
    """Application factory pattern"""

    # Determine config
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Set correct translations path (in project root, not app folder)
    # Must be set before initializing Babel
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'translations'
    )

    # Configure Babel locale selector
    def get_locale():
        """Get user's preferred language"""
        # Check if user has set a language preference in session
        if 'language' in session:
            return session['language']
        # Try to get from request headers
        return request.accept_languages.best_match(['en', 'bg']) or 'en'

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app, locale_selector=get_locale)
    login_manager.init_app(app)
    limiter.init_app(app)

    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.session_protection = 'strong'

    # Import models
    from app import models

    # Setup Flask-Security-Too
    user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    security.init_app(app, user_datastore)

    # Register blueprints
    from app.auth import auth_bp
    from app.inventory import inventory_bp
    from app.scanner import scanner_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(scanner_bp)

    # Register main routes
    from app import routes
    app.register_blueprint(routes.main_bp)

    # Add security headers for production
    if config_name == 'production':
        @app.after_request
        def set_security_headers(response):
            for header, value in app.config.get('SECURITY_HEADERS', {}).items():
                response.headers[header] = value
            return response

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register CLI commands
    from app.cli import register_commands
    register_commands(app)

    return app
