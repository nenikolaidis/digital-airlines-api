from functools import wraps

from flask import session

from .errors import APIError


def login_required(role=None):
    """Reject requests without a session, or from the wrong role when one is given."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if "email" not in session:
                raise APIError(401, "You need to log in first.")
            if role and session.get("role") != role:
                raise APIError(403, f"This action is only available to {role} accounts.")
            return view(*args, **kwargs)

        return wrapper

    return decorator
