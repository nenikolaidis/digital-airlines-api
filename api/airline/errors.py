from flask import jsonify
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    """An error returned to the client as {"error": message} with the given status."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def register(app):
    @app.errorhandler(APIError)
    def handle_api_error(error):
        return jsonify(error=error.message), error.status

    @app.errorhandler(429)
    def handle_rate_limit(error):
        # error.description is the limit that was hit, for example "10 per 1 minute"
        return jsonify(error=f"Too many requests ({error.description}). Try again later."), 429

    # Unknown routes, wrong methods and unhandled exceptions also get a JSON body
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify(error=error.description), error.code
