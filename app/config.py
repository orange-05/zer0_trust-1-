"""
app/config.py — Configuration Classes
======================================
WHY SEPARATE CONFIG CLASSES?
- Different environments (dev, test, prod) need different settings.
- Dev: debug mode ON, relaxed JWT expiry
- Test: in-memory or temp data, short JWT expiry
- Production: debug OFF, strong secret keys, strict settings

HOW IT WORKS:
- BaseConfig holds shared settings.
- DevelopmentConfig, TestingConfig, ProductionConfig inherit from it
  and override what they need.
- create_app() picks the right class via config_by_name dict.
"""

import os
from datetime import timedelta


class BaseConfig:
    """
    Shared configuration for all environments.
    Every config class inherits these unless it overrides them.
    """

    # ----------------------------------------------------------------
    # Flask Core
    # ----------------------------------------------------------------
    # SECRET_KEY is used to sign session cookies.
    # NEVER hardcode this in production — use environment variables.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Disable JSON key sorting so response order stays predictable
    JSON_SORT_KEYS = False

    # ----------------------------------------------------------------
    # JWT (JSON Web Token) Configuration
    # ----------------------------------------------------------------
    # JWT_SECRET_KEY signs the tokens. If someone gets this, they can
    # forge tokens — so in production, use a strong random key.
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")

    # How long before a token expires. Users must re-login after this.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # ----------------------------------------------------------------
    # Data Storage
    # ----------------------------------------------------------------
    # Path to the folder where our JSON data files live.
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    # ----------------------------------------------------------------
    # Security Settings
    # ----------------------------------------------------------------
    # Minimum password length enforced by validators
    MIN_PASSWORD_LENGTH = 8

    # Allowed scan types that the API will accept
    ALLOWED_SCAN_TYPES = ["dependency", "image", "filesystem"]

    # Allowed deployment environments
    ALLOWED_ENVIRONMENTS = ["development", "staging", "production"]


class DevelopmentConfig(BaseConfig):
    """
    Development environment configuration.
    Debug mode is ON so Flask auto-reloads on code changes.
    """
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    """
    Testing environment configuration.
    - TESTING = True tells Flask/pytest to propagate exceptions.
    - JWT expiry is short to test token expiry quickly.
    - Uses a separate data directory so tests don't corrupt real data.
    """
    DEBUG = False
    TESTING = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_test")


class ProductionConfig(BaseConfig):
    """
    Production environment configuration.
    - Debug is OFF (never expose stack traces in prod).
    - Secret keys MUST come from environment variables.
    """
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")


# ----------------------------------------------------------------
# CONFIG LOOKUP DICTIONARY
# create_app("development") → DevelopmentConfig
# create_app("testing")     → TestingConfig
# create_app("production")  → ProductionConfig
# ----------------------------------------------------------------
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
