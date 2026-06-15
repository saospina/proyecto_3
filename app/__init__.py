from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask

from app.config import Config
from app.extensions import db
from app.controllers.user_story_controller import user_story_bp
from app.controllers.task_controller import task_bp
from app.api import register_docs, task_api_bp, user_story_api_bp


def create_app(config_class: type[Config] = Config) -> Flask:
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(config_class())

    db.init_app(app)

    app.register_blueprint(user_story_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(user_story_api_bp)
    app.register_blueprint(task_api_bp)
    register_docs(app)

    with app.app_context():
        from app.models import user_story, task  # noqa: F401  ensure models registered
        db.create_all()

    return app
