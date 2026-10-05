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

    # Unknown routes, wrong methods and unhandled exceptions also get a JSON body
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify(error=error.description), error.code
