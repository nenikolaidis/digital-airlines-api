import secrets
import string

from flask import current_app
from pymongo.errors import DuplicateKeyError

CODE_ALPHABET = string.ascii_uppercase + string.digits


def users():
    return current_app.extensions["db"]["users"]


def flights():
    return current_app.extensions["db"]["flights"]


def reservations():
    return current_app.extensions["db"]["reservations"]


def insert_with_code(collection, document, field):
    # Store the document under a random 6-character code; the unique index rejects collisions
    for _ in range(10):
        document[field] = "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))
        try:
            collection.insert_one(document)
            return document[field]
        except DuplicateKeyError:
            document.pop("_id", None)
    raise RuntimeError(f"Could not generate a unique {field}")
