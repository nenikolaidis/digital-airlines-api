from flask import Blueprint, jsonify

from .openapi import SPEC

bp = Blueprint("docs", __name__)

# Swagger UI is loaded from a CDN, so it adds no Python dependencies
SWAGGER_UI_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Digital Airlines API docs</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({url: "/openapi.json", dom_id: "#swagger-ui", tryItOutEnabled: true});
  </script>
</body>
</html>
"""


@bp.get("/openapi.json")
def openapi_spec():
    return jsonify(SPEC)


@bp.get("/docs")
def swagger_ui():
    return SWAGGER_UI_PAGE
