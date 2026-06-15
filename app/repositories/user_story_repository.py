from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy import select

from app.extensions import db
from app.models import UserStory
from app.schemas.user_story import UserStoryGenerationSchema


class IUserStoryRepository(ABC):
    @abstractmethod
    def list_all(self) -> List[UserStory]: ...

    @abstractmethod
    def get(self, story_id: int) -> Optional[UserStory]: ...

    @abstractmethod
    def create_from_generation(self, data: UserStoryGenerationSchema) -> UserStory: ...


class UserStoryRepository(IUserStoryRepository):
    """SQLAlchemy implementation of the user-story repository."""

    def list_all(self) -> List[UserStory]:
        stmt = select(UserStory).order_by(UserStory.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    def get(self, story_id: int) -> Optional[UserStory]:
        return db.session.get(UserStory, story_id)

    def create_from_generation(self, data: UserStoryGenerationSchema) -> UserStory:
        story = UserStory(
            project=data.project,
            role=data.role,
            goal=data.goal,
            reason=data.reason,
            description=data.description,
            priority=data.priority,
            story_points=data.story_points,
            effort_hours=float(data.effort_hours),
            acceptance_criteria=data.acceptance_criteria,
        )
        db.session.add(story)
        db.session.commit()
        db.session.refresh(story)
        return story
