from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, url_for

from app.container import get_task_service

task_bp = Blueprint("tasks", __name__)


@task_bp.get("/user-stories/<int:story_id>/tasks")
def list_tasks(story_id: int):
    service = get_task_service()
    try:
        story = service.get_story(story_id)
    except LookupError:
        abort(404)
    tasks = service.list_for_story(story_id)
    return render_template("tasks.html", story=story, tasks=tasks)


@task_bp.post("/user-stories/<int:story_id>/generate-tasks")
def generate_tasks(story_id: int):
    service = get_task_service()
    try:
        service.generate_and_store(story_id)
    except LookupError:
        abort(404)
    except Exception as exc:
        flash(f"Failed to generate tasks: {exc}", "error")
        return redirect(url_for("tasks.list_tasks", story_id=story_id))

    flash("Tasks generated successfully.", "success")
    return redirect(url_for("tasks.list_tasks", story_id=story_id))
