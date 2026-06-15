from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Priority


class UserStoryGenerationSchema(BaseModel):
    """Schema used as the OpenAI structured-output target when generating a user story."""

    model_config = ConfigDict(extra="forbid")

    project: str = Field(..., description="Short name of the project the story belongs to")
    role: str = Field(..., description="User role for the story (e.g. 'registered user')")
    goal: str = Field(..., description="What the role wants to achieve")
    reason: str = Field(..., description="Why the role wants to achieve the goal")
    description: str = Field(..., description="Full narrative of the user story")
    priority: Priority = Field(..., description="Priority level of the story")
    story_points: int = Field(..., ge=1, le=8, description="Story points estimation (1-8)")
    effort_hours: float = Field(..., ge=0, description="Estimated effort in hours")
    acceptance_criteria: str = Field(
        ..., description="Acceptance criteria for the story as a bullet list"
    )


class UserStorySchema(BaseModel):
    """Full user-story representation, e.g. for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project: str
    role: str
    goal: str
    reason: str
    description: str
    priority: Priority
    story_points: int
    effort_hours: float
    acceptance_criteria: Optional[str] = None
    created_at: datetime


class UserStorySchemas(BaseModel):
    """Wrapper for a collection of user stories."""

    items: List[UserStorySchema] = Field(default_factory=list)
