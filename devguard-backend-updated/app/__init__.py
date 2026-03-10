"""
DevGuard — Zero-Trust Supply Chain Security Pipeline
=====================================================
This is the Flask Application Factory.

WHY AN APP FACTORY?
- Instead of creating Flask app globally (app = Flask(__name__)),
  we use a function called create_app().
- This pattern lets you create multiple app instances (e.g., one for
  testing, one for production) with different configs.
- It also avoids circular import problems.
"""

from flask import Flask
from flask_cors import CORS
from app.config import config_by_name
from app.extensions import jwt
from app.errors import register_error_handlers


def create_app(config_name: str = "development") -> Flask:
    """
    Application Factory Function.

    Args:
        config_name: One of 'development', 'testing', 'production'

    Returns:
        A configured Flask application instance.
    """
    app = Flask(__name__)

    # ----------------------------------------------------------------
    # 1. LOAD CONFIGURATION
    # ----------------------------------------------------------------
    app.config.from_object(config_by_name[config_name])

    # ----------------------------------------------------------------
    # 2. CORS — Allow React frontend to call this API
    # In production, replace "*" with your Netlify/GitHub Pages URL:
    #   {"origins": ["https://yourname.github.io"]}
    # ----------------------------------------------------------------
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })

    # ----------------------------------------------------------------
    # 3. INITIALIZE EXTENSIONS
    # ----------------------------------------------------------------
    jwt.init_app(app)

    # ----------------------------------------------------------------
    # 3. REGISTER BLUEPRINTS (API Routes)
    # Each module (auth, health, pipelines, scans, deployments) is a
    # Blueprint — a self-contained group of routes.
    # We import and register them here.
    # ----------------------------------------------------------------
    from app.api.health import health_bp
    from app.api.auth import auth_bp
    from app.api.pipelines import pipelines_bp
    from app.api.scans import scans_bp
    from app.api.deployments import deployments_bp

    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(pipelines_bp, url_prefix="/api/v1")
    app.register_blueprint(scans_bp, url_prefix="/api/v1")
    app.register_blueprint(deployments_bp, url_prefix="/api/v1")

    # ----------------------------------------------------------------
    # 4. REGISTER ERROR HANDLERS
    # Centralized error handling so every error returns clean JSON.
    # ----------------------------------------------------------------
    register_error_handlers(app)

    return app
