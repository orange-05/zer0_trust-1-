"""
app/extensions.py — Flask Extensions
======================================
WHY A SEPARATE EXTENSIONS FILE?
- Extensions like JWT are created here WITHOUT being tied to an app.
- This avoids circular imports:
    extensions.py creates jwt
    __init__.py imports jwt and calls jwt.init_app(app)
    services can import jwt without needing the full app

This is the standard Flask pattern for extensions.
"""

from flask_jwt_extended import JWTManager

# Create the JWT manager instance.
# It's NOT connected to any app yet — that happens in create_app()
# via jwt.init_app(app).
jwt = JWTManager()
