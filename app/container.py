from __future__ import annotations

from flask import current_app

from app.repositories import TaskRepository, UserStoryRepository
from app.services import AIService, TaskService, UserStoryService


def _build_ai_service() -> AIService:
    return AIService(
        api_key=current_app.config["OPENAI_API_KEY"],
        model=current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
    )


def get_user_story_service() -> UserStoryService:
    return UserStoryService(
        repository=UserStoryRepository(),
        ai_service=_build_ai_service(),
    )


def get_task_service() -> TaskService:
    return TaskService(
        task_repository=TaskRepository(),
        user_story_repository=UserStoryRepository(),
        ai_service=_build_ai_service(),
    )
