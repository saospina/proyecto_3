from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List

from sqlalchemy import select

from app.extensions import db
from app.models import Task
from app.schemas.task import TaskGenerationSchema


class ITaskRepository(ABC):
    @abstractmethod
    def list_for_story(self, user_story_id: int) -> List[Task]: ...

    @abstractmethod
    def bulk_create_for_story(
        self, user_story_id: int, tasks: Iterable[TaskGenerationSchema]
    ) -> List[Task]: ...


class TaskRepository(ITaskRepository):
    """SQLAlchemy implementation of the task repository."""

    def list_for_story(self, user_story_id: int) -> List[Task]:
        stmt = (
            select(Task)
            .where(Task.user_story_id == user_story_id)
            .order_by(Task.id.asc())
        )
        return list(db.session.execute(stmt).scalars().all())

    def bulk_create_for_story(
        self, user_story_id: int, tasks: Iterable[TaskGenerationSchema]
    ) -> List[Task]:
        created: List[Task] = []
        for payload in tasks:
            task = Task(
                title=payload.title,
                description=payload.description,
                priority=payload.priority,
                effort_hours=float(payload.effort_hours),
                status=payload.status,
                assigned_to=payload.assigned_to,
                user_story_id=user_story_id,
            )
            db.session.add(task)
            created.append(task)
        db.session.commit()
        for task in created:
            db.session.refresh(task)
        return created
