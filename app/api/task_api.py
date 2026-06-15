from __future__ import annotations

from flask import Blueprint, jsonify

from app.container import get_task_service
from app.schemas import TaskSchema

task_api_bp = Blueprint(
    "task_api", __name__, url_prefix="/api/v1/user-stories/<int:story_id>"
)


@task_api_bp.get("/tasks")
def list_tasks(story_id: int):
    service = get_task_service()
    try:
        service.get_story(story_id)
    except LookupError:
        return jsonify({"error": "user_story_not_found", "id": story_id}), 404
    tasks = service.list_for_story(story_id)
    payload = [TaskSchema.model_validate(t).model_dump(mode="json") for t in tasks]
    return jsonify(payload), 200


@task_api_bp.post("/generate-tasks")
def generate_tasks(story_id: int):
    service = get_task_service()
    try:
        tasks = service.generate_and_store(story_id)
    except LookupError:
        return jsonify({"error": "user_story_not_found", "id": story_id}), 404
    except Exception as exc:
        return jsonify({"error": "generation_failed", "detail": str(exc)}), 502
    payload = [TaskSchema.model_validate(t).model_dump(mode="json") for t in tasks]
    return jsonify(payload), 201
