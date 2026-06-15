from __future__ import annotations

from typing import List

from app.models import Task, UserStory
from app.repositories import ITaskRepository, IUserStoryRepository
from app.services.ai_service import IAIService


class TaskService:
    """Coordinates AI generation and persistence of tasks for a user story."""

    def __init__(
        self,
        task_repository: ITaskRepository,
        user_story_repository: IUserStoryRepository,
        ai_service: IAIService,
    ) -> None:
        self._task_repository = task_repository
        self._user_story_repository = user_story_repository
        self._ai_service = ai_service

    def list_for_story(self, user_story_id: int) -> List[Task]:
        return self._task_repository.list_for_story(user_story_id)

    def get_story(self, user_story_id: int) -> UserStory:
        story = self._user_story_repository.get(user_story_id)
        if story is None:
            raise LookupError(f"UserStory {user_story_id} not found")
        return story

    def generate_and_store(self, user_story_id: int) -> List[Task]:
        story = self.get_story(user_story_id)
        generated = self._ai_service.generate_tasks(story)
        return self._task_repository.bulk_create_for_story(story.id, generated)
