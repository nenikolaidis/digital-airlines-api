"""Digital Airlines: a flight booking REST API built with Flask and MongoDB."""

import os
import secrets
from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

from . import auth, docs, errors, flights, reservations
from .limits import limiter
from .openapi import openapi_path
from .seed import create_indexes, seed_database


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        MONGO_URI=os.environ.get("MONGO_URI", "mongodb://localhost:27017"),
        MONGO_DB=os.environ.get("MONGO_DB", "DigitalAirlines"),
        # Signs the access tokens; set it in production so tokens survive restarts
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        TOKEN_LIFETIME=timedelta(minutes=int(os.environ.get("TOKEN_LIFETIME_MINUTES", "60"))),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD"),
        SEED_DATABASE=True,
        # Rate limits per client IP; in memory, which is enough for a single gunicorn worker
        RATELIMIT_ENABLED=os.environ.get("RATELIMIT_ENABLED", "true").lower() == "true",
        RATELIMIT_DEFAULT="200 per minute",
        RATELIMIT_HEADERS_ENABLED=True,
        RATELIMIT_STORAGE_URI=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
        LOGIN_RATE_LIMIT="10 per minute;50 per hour",
        REGISTER_RATE_LIMIT="5 per hour",
        CLIENT_IP_HEADER=os.environ.get("CLIENT_IP_HEADER"),
        # Websites allowed to call the API from a browser, e.g. the deployed frontend
        CORS_ORIGINS=[origin.strip() for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin.strip()],
    )
    if config:
        app.config.update(config)

    client = MongoClient(app.config["MONGO_URI"])
    app.extensions["mongo_client"] = client
    app.extensions["db"] = client[app.config["MONGO_DB"]]

    limiter.init_app(app)
    if app.config["CORS_ORIGINS"]:
        CORS(
            app,
            origins=app.config["CORS_ORIGINS"],
            allow_headers=["Authorization", "Content-Type"],
            expose_headers=["Location", "Retry-After"],
            max_age=600,
        )
    errors.register(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(flights.bp)
    app.register_blueprint(reservations.bp)
    app.register_blueprint(docs.bp)

    @app.get("/")
    def index():
        return jsonify(
            name="Digital Airlines API",
            docs="/docs",
            endpoints=sorted(
                f"{method} {openapi_path(rule.rule)}"
                for rule in app.url_map.iter_rules()
                if rule.endpoint != "static"
                for method in rule.methods - {"HEAD", "OPTIONS"}
            ),
        )

    with app.app_context():
        create_indexes()
        if app.config["SEED_DATABASE"]:
            seed_database()

    return app
