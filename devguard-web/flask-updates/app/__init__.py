"""
app/__init__.py — Flask Application Factory
UPDATED: Added Flask-CORS for React frontend support
"""

from flask import Flask
from flask_cors import CORS
from app.config import config_by_name
from app.extensions import jwt
from app.errors import register_error_handlers


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # ----------------------------------------------------------------
    # CORS — Allow React frontend to call this API
    # In production, replace "*" with your actual Netlify/GitHub Pages URL
    # e.g., origins=["https://yourname.github.io", "https://devguard.netlify.app"]
    # ----------------------------------------------------------------
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    jwt.init_app(app)

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

    register_error_handlers(app)
    return app
