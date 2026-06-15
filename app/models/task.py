from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import Priority, TaskStatus


class Task(db.Model):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Priority] = mapped_column(
        SAEnum(Priority, name="priority_enum", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=Priority.MEDIUM,
    )
    effort_hours: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status_enum", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=TaskStatus.PENDING,
    )
    assigned_to: Mapped[str] = mapped_column(String(150), nullable=True)
    user_story_id: Mapped[int] = mapped_column(
        ForeignKey("user_stories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user_story = relationship("UserStory", back_populates="tasks")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Task id={self.id} title={self.title!r}>"

    @property
    def priority_label(self) -> str:
        return self.priority.value if isinstance(self.priority, Priority) else str(self.priority)

    @property
    def status_label(self) -> str:
        return self.status.value if isinstance(self.status, TaskStatus) else str(self.status)
