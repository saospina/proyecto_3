from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import Priority


class UserStory(db.Model):
    __tablename__ = "user_stories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(150), nullable=False)
    goal: Mapped[str] = mapped_column(String(500), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Priority] = mapped_column(
        SAEnum(Priority, name="priority_enum", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=Priority.MEDIUM,
    )
    story_points: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    effort_hours: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    acceptance_criteria: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tasks: Mapped[List["Task"]] = relationship(  # noqa: F821
        "Task",
        back_populates="user_story",
        cascade="all, delete-orphan",
        order_by="Task.id",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserStory id={self.id} project={self.project!r}>"

    @property
    def priority_label(self) -> str:
        return self.priority.value if isinstance(self.priority, Priority) else str(self.priority)
