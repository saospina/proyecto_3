from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Priority, TaskStatus


class TaskGenerationSchema(BaseModel):
    """Schema used as the OpenAI structured-output target when generating a task."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Short imperative title for the task")
    description: str = Field(..., description="Detailed description of the task work")
    priority: Priority = Field(..., description="Priority level")
    effort_hours: float = Field(..., ge=0, description="Estimated effort in hours")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Initial status")
    assigned_to: Optional[str] = Field(
        default=None, description="Suggested assignee role or empty"
    )


class TaskListGenerationSchema(BaseModel):
    """Schema used as the OpenAI structured-output target when generating a task list."""

    model_config = ConfigDict(extra="forbid")

    tasks: List[TaskGenerationSchema] = Field(
        ..., description="List of granular implementation tasks for the user story"
    )


class TaskSchema(BaseModel):
    """Full task representation, e.g. for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: Priority
    effort_hours: float
    status: TaskStatus
    assigned_to: Optional[str] = None
    user_story_id: int
    created_at: datetime


class TaskSchemas(BaseModel):
    """Wrapper for a collection of tasks."""

    items: List[TaskSchema] = Field(default_factory=list)
