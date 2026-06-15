from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.container import get_user_story_service
from app.schemas import UserStorySchema

user_story_api_bp = Blueprint("user_story_api", __name__, url_prefix="/api/v1/user-stories")


@user_story_api_bp.get("")
def list_user_stories():
    service = get_user_story_service()
    stories = service.list_all()
    payload = [UserStorySchema.model_validate(s).model_dump(mode="json") for s in stories]
    return jsonify(payload), 200


@user_story_api_bp.get("/<int:story_id>")
def get_user_story(story_id: int):
    service = get_user_story_service()
    story = service.get(story_id)
    if story is None:
        return jsonify({"error": "user_story_not_found", "id": story_id}), 404
    return jsonify(UserStorySchema.model_validate(story).model_dump(mode="json")), 200


@user_story_api_bp.post("")
def create_user_story():
    body = request.get_json(silent=True) or {}
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "prompt_required"}), 400

    service = get_user_story_service()
    try:
        story = service.generate_and_store(prompt)
    except ValueError as exc:
        return jsonify({"error": "invalid_prompt", "detail": str(exc)}), 400
    except Exception as exc:  # surface OpenAI / DB failures
        return jsonify({"error": "generation_failed", "detail": str(exc)}), 502

    return jsonify(UserStorySchema.model_validate(story).model_dump(mode="json")), 201
