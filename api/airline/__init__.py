"""Digital Airlines: a flight booking REST API built with Flask and MongoDB."""

import os
import secrets
from datetime import timedelta

from flask import Flask, jsonify
from pymongo import MongoClient

from . import auth, docs, errors, flights, reservations
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
    )
    if config:
        app.config.update(config)

    client = MongoClient(app.config["MONGO_URI"])
    app.extensions["db"] = client[app.config["MONGO_DB"]]

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
