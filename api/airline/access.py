from datetime import datetime, timezone
from functools import wraps

import jwt
from flask import current_app, g, request

from . import db
from .errors import APIError

ALGORITHM = "HS256"


def create_token(user):
    """Signed access token for the user, sent back as `Authorization: Bearer <token>`."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["email"],
        # Logging out increments token_version, which invalidates every token issued before it
        "ver": user.get("token_version", 0),
        "iat": now,
        "exp": now + current_app.config["TOKEN_LIFETIME"],
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm=ALGORITHM)


def user_from_token():
    """The user the request's bearer token belongs to, or None when no token was sent."""
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if not token:
        return None
    if scheme.lower() != "bearer":
        raise APIError(401, "Send the token as: Authorization: Bearer <token>.")

    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=[ALGORITHM], options={"require": ["sub", "exp"]})
    except jwt.ExpiredSignatureError:
        raise APIError(401, "Your token has expired. Log in again.") from None
    except jwt.InvalidTokenError:
        raise APIError(401, "Invalid token.") from None

    user = db.users().find_one({"email": payload["sub"]})
    if not user or user.get("token_version", 0) != payload.get("ver"):
        raise APIError(401, "This token is no longer valid. Log in again.")
    return user


def optional_user():
    """Like user_from_token, but public endpoints treat a bad token as no token."""
    try:
        return user_from_token()
    except APIError:
        return None


def login_required(role=None):
    """Reject requests without a valid token, or from the wrong role when one is given.

    The logged-in user is available to the view as g.user.
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = user_from_token()
            if not user:
                raise APIError(401, "You need to log in first.")
            if role and user["role"] != role:
                raise APIError(403, f"This action is only available to {role} accounts.")
            g.user = user
            return view(*args, **kwargs)

        return wrapper

    return decorator
