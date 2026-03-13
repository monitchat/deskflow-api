import socket

import structlog
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from marshmallow.exceptions import ValidationError
from sqlalchemy import text
from werkzeug.exceptions import HTTPException

from deskflow.common import APIError, BadRequestError


def rename_event_to_message(_, __, event_dict):
    """structlog processor to rename key 'event' to 'message'"""
    event = event_dict.get("event")
    if event:
        event_dict["message"] = event
        del event_dict["event"]
    return event_dict


# Initialize structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper("iso"),
        structlog.processors.add_log_level,
        rename_event_to_message,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()


def api_error_handler(e):
    """Error handler for API errors"""
    return jsonify(e.to_dict()), e.status_code


def validation_error_handler(e):
    """Error handler for validation errors"""
    response = BadRequestError("INVALID_REQUEST", details=e.messages)
    return jsonify(response.to_dict()), response.status_code


def http_error_handler(e):
    """Error handler for errors without payload"""
    response = e.get_response()
    response.content_type = "application/json"
    response.data = b""
    return response


def gethostname():
    """Retrieves the hostname.
    Works with containers that binds /etc/hostname"""
    try:
        with open("/etc/hostname", "r") as fp:
            return fp.read().strip()
    except IOError:
        return socket.gethostname()


# Database object
db = SQLAlchemy()


def health_check_db():
    """Database health check"""
    db.session.query(text("1")).from_statement(text("SELECT 1")).all()


def health_check():
    """Health-check endpoint handler"""
    health_check_db()
    return "OK"


def create_app(settings_override=None):
    """Application factory"""
    app = Flask(__name__, static_folder="../../public", static_url_path="")
    app.config.from_object("deskflow.config")

    if settings_override:
        app.config.update(settings_override)

    # Enable CORS for frontend communication
    # In production, replace origins with specific domains
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    db.init_app(app)

    # Make sure we can connect to the database
    with app.app_context():
        health_check_db()

    # https://stackoverflow.com/a/41839910/1396448
    from deskflow.service import api as from_service_api
    from deskflow.api.flow_api import api as flow_api

    # Add health-check endpoint
    app.add_url_rule(
        "/api/v1/health", "health", view_func=health_check, methods=["GET"]
    )

    app.register_blueprint(from_service_api)
    app.register_blueprint(flow_api)

    app.register_error_handler(APIError, api_error_handler)
    app.register_error_handler(ValidationError, validation_error_handler)
    app.register_error_handler(HTTPException, http_error_handler)

    return app
