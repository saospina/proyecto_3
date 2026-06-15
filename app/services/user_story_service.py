from __future__ import annotations

from typing import List, Optional

from app.models import UserStory
from app.repositories import IUserStoryRepository
from app.services.ai_service import IAIService


class UserStoryService:
    """Coordinates AI generation and persistence of user stories."""

    def __init__(self, repository: IUserStoryRepository, ai_service: IAIService) -> None:
        self._repository = repository
        self._ai_service = ai_service

    def list_all(self) -> List[UserStory]:
        return self._repository.list_all()

    def get(self, story_id: int) -> Optional[UserStory]:
        return self._repository.get(story_id)

    def generate_and_store(self, prompt: str) -> UserStory:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        generated = self._ai_service.generate_user_story(prompt)
        return self._repository.create_from_generation(generated)
