import math
import re
from datetime import date, datetime

from flask import request

from .errors import APIError

DATE_FORMAT = "%Y-%m-%d"
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TICKET_CLASSES = ("business", "economy")


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError(400, "The request body must be a JSON object.")
    return data


def require_text(data, *fields):
    # Returns the fields as stripped strings, or fails listing every missing one
    values = {field: data.get(field).strip() if isinstance(data.get(field), str) else None for field in fields}
    missing = [field for field, value in values.items() if not value]
    if missing:
        raise APIError(400, "Missing or invalid field(s): {}".format(", ".join(missing)))
    return values


def parse_date(value, field):
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except (TypeError, ValueError):
        raise APIError(400, f"{field} must be a date in YYYY-MM-DD format.") from None


def parse_past_date(value, field):
    parsed = parse_date(value, field)
    if parsed >= date.today():
        raise APIError(400, f"{field} must be in the past.")
    return parsed


def parse_number(value, field, integer=False):
    # Accepts finite numbers >= 0, as JSON numbers or numeric strings
    kind = "a whole number" if integer else "a number"
    error = APIError(400, f"{field} must be {kind} that is 0 or more.")
    if isinstance(value, bool):
        raise error
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise error from None
    if not math.isfinite(number) or number < 0 or (integer and not number.is_integer()):
        raise error
    return int(number) if integer else number


def normalize_email(value, field="email"):
    email = value.strip().lower() if isinstance(value, str) else ""
    if not EMAIL_PATTERN.match(email):
        raise APIError(400, f"{field} must be a valid email address.")
    return email


def parse_ticket_class(value):
    if value not in TICKET_CLASSES:
        raise APIError(400, "ticket_class must be one of: {}.".format(", ".join(TICKET_CLASSES)))
    return value
