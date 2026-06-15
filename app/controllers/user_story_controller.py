from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.container import get_user_story_service
from app.models.enums import Priority

user_story_bp = Blueprint("user_stories", __name__)


@user_story_bp.get("/")
def index():
    return redirect(url_for("user_stories.list_user_stories"))


@user_story_bp.get("/user-stories")
def list_user_stories():
    service = get_user_story_service()
    stories = service.list_all()
    return render_template(
        "user_stories.html",
        stories=stories,
        priorities=[p.value for p in Priority],
    )


@user_story_bp.post("/user-stories")
def create_user_story():
    prompt = (request.form.get("prompt") or "").strip()
    if not prompt:
        flash("Prompt is required to generate a user story.", "error")
        return redirect(url_for("user_stories.list_user_stories"))

    service = get_user_story_service()
    try:
        service.generate_and_store(prompt)
    except Exception as exc:  # surface generation errors to the UI
        flash(f"Failed to generate user story: {exc}", "error")
        return redirect(url_for("user_stories.list_user_stories"))

    flash("User story generated successfully.", "success")
    return redirect(url_for("user_stories.list_user_stories"))
