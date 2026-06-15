from __future__ import annotations

from flask import Blueprint, Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

from app.api.openapi import build_openapi_spec

SWAGGER_URL = "/docs"
SPEC_URL = "/openapi.json"

openapi_bp = Blueprint("openapi", __name__)


@openapi_bp.get(SPEC_URL)
def openapi_spec():
    return jsonify(build_openapi_spec())


def register_docs(app: Flask) -> None:
    """Mount the OpenAPI spec endpoint and Swagger UI on the app."""
    app.register_blueprint(openapi_bp)
    swagger_bp = get_swaggerui_blueprint(
        SWAGGER_URL,
        SPEC_URL,
        config={
            "app_name": "AI Backlog API",
            "displayRequestDuration": True,
            "defaultModelsExpandDepth": 1,
        },
    )
    app.register_blueprint(swagger_bp, url_prefix=SWAGGER_URL)
