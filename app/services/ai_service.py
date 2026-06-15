from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from openai import OpenAI

from app.models import UserStory
from app.schemas.task import TaskGenerationSchema, TaskListGenerationSchema
from app.schemas.user_story import UserStoryGenerationSchema


SYSTEM_PROMPT_USER_STORY = (
    "You are a senior agile product owner. Given a free-form description from a stakeholder, "
    "produce a single well-formed user story following the format "
    "'As a <role>, I want <goal> so that <reason>'. "
    "Estimate priority, story points (1-8 Fibonacci-ish) and effort hours conservatively. "
    "Acceptance criteria should be a markdown bullet list."
)

SYSTEM_PROMPT_TASKS = (
    "You are a senior software engineer breaking down a user story into actionable engineering "
    "tasks. Produce between 3 and 8 granular tasks covering analysis, implementation, testing and "
    "review. Each task must have a clear title, a detailed description, a priority, an effort "
    "estimate in hours, an initial status (default 'pending') and optionally an assignee role."
)


class IAIService(ABC):
    @abstractmethod
    def generate_user_story(self, prompt: str) -> UserStoryGenerationSchema: ...

    @abstractmethod
    def generate_tasks(self, story: UserStory) -> List[TaskGenerationSchema]: ...


class AIService(IAIService):
    """OpenAI-backed AI service using structured (Pydantic-parsed) outputs."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate_user_story(self, prompt: str) -> UserStoryGenerationSchema:
        completion = self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_USER_STORY},
                {"role": "user", "content": prompt.strip()},
            ],
            response_format=UserStoryGenerationSchema,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed user story")
        return parsed

    def generate_tasks(self, story: UserStory) -> List[TaskGenerationSchema]:
        context = (
            f"Project: {story.project}\n"
            f"Role: {story.role}\n"
            f"Goal: {story.goal}\n"
            f"Reason: {story.reason}\n"
            f"Priority: {story.priority_label}\n"
            f"Story points: {story.story_points}\n"
            f"Estimated effort hours: {story.effort_hours}\n"
            f"Description:\n{story.description}\n"
            f"Acceptance criteria:\n{story.acceptance_criteria or '-'}"
        )
        completion = self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_TASKS},
                {"role": "user", "content": context},
            ],
            response_format=TaskListGenerationSchema,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed tasks")
        return list(parsed.tasks)
