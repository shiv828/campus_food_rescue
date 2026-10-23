"""JWT authentication helpers for the campus food rescue API."""

from functools import wraps

import jwt
from flask import current_app, g, jsonify, request


def token_required(view):
    """Require a valid JWT in a Bearer or ``x-access-token`` header."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        scheme, _, bearer_token = authorization.partition(" ")
        token = bearer_token.strip() if scheme.lower() == "bearer" else None
        token = token or request.headers.get("x-access-token")

        if not token:
            return jsonify({"error": "Authentication token is required"}), 401

        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
            username = payload.get("user")
            if not username:
                return jsonify({"error": "Invalid authentication token"}), 401
            g.current_user = username
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Authentication token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid authentication token"}), 401

        return view(*args, **kwargs)

    return wrapped_view
